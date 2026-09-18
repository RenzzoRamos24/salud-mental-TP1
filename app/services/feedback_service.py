"""
Feedback de la psicóloga sobre el análisis de BETO.

El clasificador de frases es zero-shot: no se entrenó con datos del colegio,
así que su precisión real solo se conoce viéndolo trabajar. Al revisar el
resultado de un cuestionario, la psicóloga dice si el análisis del modelo
sirvió o lo descarta por incorrecto, y este servicio agrega esos veredictos
en métricas.

Métrica principal: `tasa_acierto` = aceptados / (aceptados + rechazados).
Es la precisión percibida sobre los cuestionarios efectivamente revisados —
no sobre todos, porque los que nadie revisó no aportan información en
ninguna dirección.
"""
import json
import logging

from sqlalchemy.orm import Session

from app.models.bank import AplicacionCuestionario, ResultadoFeedback

logger = logging.getLogger(__name__)

VEREDICTOS = ("aceptado", "rechazado")


class FeedbackService:

    # ── Escritura ──────────────────────────────────────────────────────────

    @staticmethod
    def registrar(
        db: Session,
        psicologo_id: str,
        aplicacion_id: int,
        veredicto: str,
        comentario: str | None = None,
        es_admin: bool = False,
    ) -> ResultadoFeedback:
        """Guarda (o reemplaza) el veredicto sobre el análisis del modelo."""
        if veredicto not in VEREDICTOS:
            raise ValueError(
                f"Veredicto inválido '{veredicto}'. Usá uno de: {', '.join(VEREDICTOS)}."
            )

        apl = FeedbackService._aplicacion_accesible(
            db, psicologo_id, aplicacion_id, es_admin
        )
        resultado = FeedbackService._resultado(apl)
        if resultado is None:
            raise ValueError(
                f"La aplicación #{aplicacion_id} todavía no tiene un análisis que juzgar."
            )

        fb = (
            db.query(ResultadoFeedback)
            .filter(ResultadoFeedback.aplicacion_id == aplicacion_id)
            .first()
        )
        if fb is None:
            fb = ResultadoFeedback(aplicacion_id=aplicacion_id)
            db.add(fb)

        fb.psicologo_id = psicologo_id
        fb.veredicto = veredicto
        fb.comentario = (comentario or "").strip() or None
        fb.riesgo_modelo = resultado.get("riesgo_global")
        fb.crisis_modelo = bool(resultado.get("crisis_activada"))
        fb.n_frases = len(resultado.get("frases") or [])

        db.commit()
        db.refresh(fb)
        return fb

    @staticmethod
    def quitar(
        db: Session, psicologo_id: str, aplicacion_id: int, es_admin: bool = False
    ) -> bool:
        """Deshace el veredicto — el resultado vuelve a quedar sin juzgar."""
        FeedbackService._aplicacion_accesible(db, psicologo_id, aplicacion_id, es_admin)
        fb = (
            db.query(ResultadoFeedback)
            .filter(ResultadoFeedback.aplicacion_id == aplicacion_id)
            .first()
        )
        if fb is None:
            return False
        db.delete(fb)
        db.commit()
        return True

    # ── Lectura por aplicación ─────────────────────────────────────────────

    @staticmethod
    def por_aplicacion(db: Session, aplicacion_id: int) -> dict | None:
        """Veredicto actual de esta aplicación, o None si nadie la juzgó."""
        fb = (
            db.query(ResultadoFeedback)
            .filter(ResultadoFeedback.aplicacion_id == aplicacion_id)
            .first()
        )
        if fb is None:
            return None
        return {
            "veredicto": fb.veredicto,
            "comentario": fb.comentario,
            "actualizado_at": fb.updated_at.isoformat() if fb.updated_at else None,
        }

    # ── Métricas globales ──────────────────────────────────────────────────

    @staticmethod
    def metricas_globales(
        db: Session, psicologo_id: str, es_admin: bool = False
    ) -> dict:
        """
        Acumulado de todos los veredictos. La psicóloga ve los suyos; el admin
        ve los de todo el sistema.
        """
        q = db.query(ResultadoFeedback)
        if not es_admin:
            q = q.filter(ResultadoFeedback.psicologo_id == psicologo_id)
        filas = q.all()

        aceptados = sum(1 for f in filas if f.veredicto == "aceptado")
        rechazados = sum(1 for f in filas if f.veredicto == "rechazado")
        revisados = aceptados + rechazados

        # Desglose por nivel de riesgo que había dado el modelo — sirve para
        # ver si los errores se concentran en un nivel concreto.
        por_riesgo: dict[str, dict] = {}
        for f in filas:
            clave = f.riesgo_modelo or "(sin riesgo calculado)"
            slot = por_riesgo.setdefault(
                clave, {"riesgo": clave, "aceptados": 0, "rechazados": 0}
            )
            slot["aceptados" if f.veredicto == "aceptado" else "rechazados"] += 1
        for slot in por_riesgo.values():
            tot = slot["aceptados"] + slot["rechazados"]
            slot["total"] = tot
            slot["tasa_acierto"] = round(slot["aceptados"] / tot, 4) if tot else None

        # Los resultados con bandera de crisis se miran aparte: un falso
        # positivo ahí cuesta mucho más que en un caso cualquiera.
        crisis = [f for f in filas if f.crisis_modelo]
        crisis_ok = sum(1 for f in crisis if f.veredicto == "aceptado")
        crisis_no = sum(1 for f in crisis if f.veredicto == "rechazado")

        # Total de cuestionarios evaluados por el modelo, para saber cuántos
        # faltan por juzgar.
        q_total = db.query(AplicacionCuestionario).filter(
            AplicacionCuestionario.resultado_json.isnot(None)
        )
        if not es_admin:
            q_total = q_total.filter(
                AplicacionCuestionario.psicologo_id == psicologo_id
            )
        total_evaluados = q_total.count()

        return {
            "aceptados": aceptados,
            "rechazados": rechazados,
            "revisados": revisados,
            "sin_revisar": max(0, total_evaluados - revisados),
            "total_evaluados": total_evaluados,
            "tasa_acierto": round(aceptados / revisados, 4) if revisados else None,
            "por_riesgo": sorted(por_riesgo.values(), key=lambda x: -x["total"]),
            "crisis": {
                "aceptados": crisis_ok,
                "rechazados": crisis_no,
                "revisados": crisis_ok + crisis_no,
                "tasa_acierto": (
                    round(crisis_ok / (crisis_ok + crisis_no), 4)
                    if (crisis_ok + crisis_no)
                    else None
                ),
            },
        }

    # ── Helpers internos ───────────────────────────────────────────────────

    @staticmethod
    def _aplicacion_accesible(
        db: Session, psicologo_id: str, aplicacion_id: int, es_admin: bool
    ) -> AplicacionCuestionario:
        apl = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.id == aplicacion_id)
            .first()
        )
        if apl is None:
            raise ValueError("Aplicación no encontrada.")
        if not es_admin and apl.psicologo_id != psicologo_id:
            raise ValueError("No tienes acceso a esta aplicación.")
        return apl

    @staticmethod
    def _resultado(apl: AplicacionCuestionario) -> dict | None:
        if not apl.resultado_json:
            return None
        try:
            return json.loads(apl.resultado_json)
        except (ValueError, TypeError):
            logger.warning("resultado_json ilegible en aplicación %s", apl.id)
            return None
