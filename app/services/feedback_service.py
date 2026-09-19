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
ALERTA_VEREDICTOS = ("mantener", "descartar", "incierto")

# Sentinela para distinguir "no me mandaron este campo" de "mandame null".
_SIN_CAMBIO = object()


class FeedbackService:

    # ── Escritura ──────────────────────────────────────────────────────────

    @staticmethod
    def registrar(
        db: Session,
        psicologo_id: str,
        aplicacion_id: int,
        veredicto=_SIN_CAMBIO,
        alerta_veredicto=_SIN_CAMBIO,
        comentario=_SIN_CAMBIO,
        es_admin: bool = False,
    ) -> ResultadoFeedback:
        """
        Guarda (o reemplaza) los veredictos sobre un cuestionario.

        Las dos dimensiones son independientes: se puede mandar solo una y la
        otra queda como estaba. Pasar None en un campo lo deja sin juzgar.
        """
        if veredicto is _SIN_CAMBIO and alerta_veredicto is _SIN_CAMBIO:
            raise ValueError("No mandaste ningún veredicto que guardar.")
        if veredicto not in (None, _SIN_CAMBIO) and veredicto not in VEREDICTOS:
            raise ValueError(
                f"Veredicto inválido '{veredicto}'. Usá uno de: {', '.join(VEREDICTOS)}."
            )
        if (alerta_veredicto not in (None, _SIN_CAMBIO)
                and alerta_veredicto not in ALERTA_VEREDICTOS):
            raise ValueError(
                f"Veredicto de alerta inválido '{alerta_veredicto}'. "
                f"Usá uno de: {', '.join(ALERTA_VEREDICTOS)}."
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
        if veredicto is not _SIN_CAMBIO:
            fb.veredicto = veredicto
        if alerta_veredicto is not _SIN_CAMBIO:
            fb.alerta_veredicto = alerta_veredicto
        if comentario is not _SIN_CAMBIO:
            fb.comentario = (comentario or "").strip() or None

        fb.riesgo_modelo = resultado.get("riesgo_global")
        fb.crisis_modelo = bool(resultado.get("crisis_activada"))
        fb.n_frases = len(resultado.get("frases") or [])

        # Si quedaron las dos dimensiones sin juzgar, la fila ya no aporta.
        if fb.veredicto is None and fb.alerta_veredicto is None:
            if fb.id is not None:
                db.delete(fb)
            else:
                db.expunge(fb)
            db.commit()
            return None

        db.commit()
        db.refresh(fb)
        return fb

    @staticmethod
    def quitar(
        db: Session,
        psicologo_id: str,
        aplicacion_id: int,
        campo: str = "todo",
        es_admin: bool = False,
    ) -> bool:
        """
        Deshace un veredicto. `campo` puede ser 'analisis', 'alerta' o 'todo'.
        Si al quitar uno la fila queda sin ningún veredicto, se elimina.
        """
        if campo not in ("analisis", "alerta", "todo"):
            raise ValueError(
                f"Campo inválido '{campo}'. Usá: analisis, alerta o todo."
            )
        FeedbackService._aplicacion_accesible(db, psicologo_id, aplicacion_id, es_admin)
        fb = (
            db.query(ResultadoFeedback)
            .filter(ResultadoFeedback.aplicacion_id == aplicacion_id)
            .first()
        )
        if fb is None:
            return False

        if campo in ("analisis", "todo"):
            fb.veredicto = None
        if campo in ("alerta", "todo"):
            fb.alerta_veredicto = None

        if fb.veredicto is None and fb.alerta_veredicto is None:
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
            "alerta_veredicto": fb.alerta_veredicto,
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

        # Dimensión 2: qué decidió la psicóloga sobre la alerta.
        mantener = sum(1 for f in filas if f.alerta_veredicto == "mantener")
        descartar = sum(1 for f in filas if f.alerta_veredicto == "descartar")
        incierto = sum(1 for f in filas if f.alerta_veredicto == "incierto")
        alerta_revisados = mantener + descartar + incierto

        # Desglose por nivel de riesgo que había dado el modelo — sirve para
        # ver si los errores se concentran en un nivel concreto.
        por_riesgo: dict[str, dict] = {}
        for f in filas:
            if f.veredicto is None:
                continue
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
        crisis = [f for f in filas if f.crisis_modelo and f.veredicto is not None]
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
            "alerta": {
                "mantener": mantener,
                "descartar": descartar,
                "incierto": incierto,
                "revisados": alerta_revisados,
                "sin_revisar": max(0, total_evaluados - alerta_revisados),
                # Proporción de alertas que la psicóloga sostuvo, sobre las
                # que se pronunció con certeza. Las inciertas se excluyen del
                # denominador: no afirman ni niegan.
                "tasa_confirmacion": (
                    round(mantener / (mantener + descartar), 4)
                    if (mantener + descartar) else None
                ),
            },
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
