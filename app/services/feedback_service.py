"""
Feedback de la psicóloga sobre las clasificaciones de BETO.

El clasificador de frases es zero-shot: no se entrenó con datos del colegio,
así que su precisión real solo se conoce viéndolo trabajar. Este servicio
recoge el veredicto de la psicóloga frase por frase y lo agrega en métricas.

Métrica principal: `tasa_acierto` = aceptados / (aceptados + rechazados).
Es la precisión percibida sobre las frases efectivamente revisadas — no sobre
todas, porque las que nadie revisó no aportan información en ninguna dirección.
"""
import json
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.bank import AplicacionCuestionario, FraseFeedback

logger = logging.getLogger(__name__)

VEREDICTOS = ("aceptado", "rechazado")


class FeedbackService:

    # ── Escritura ──────────────────────────────────────────────────────────

    @staticmethod
    def registrar(
        db: Session,
        psicologo_id: str,
        aplicacion_id: int,
        frase_numero: int,
        veredicto: str,
        comentario: str | None = None,
        es_admin: bool = False,
    ) -> FraseFeedback:
        """Guarda (o reemplaza) el veredicto sobre una frase."""
        if veredicto not in VEREDICTOS:
            raise ValueError(
                f"Veredicto inválido '{veredicto}'. Usá uno de: {', '.join(VEREDICTOS)}."
            )

        apl = FeedbackService._aplicacion_accesible(
            db, psicologo_id, aplicacion_id, es_admin
        )
        frase = FeedbackService._frase_del_resultado(apl, frase_numero)
        if frase is None:
            raise ValueError(
                f"La aplicación #{aplicacion_id} no tiene una frase #{frase_numero} analizada."
            )

        fb = (
            db.query(FraseFeedback)
            .filter(
                FraseFeedback.aplicacion_id == aplicacion_id,
                FraseFeedback.frase_numero == frase_numero,
            )
            .first()
        )
        if fb is None:
            fb = FraseFeedback(
                aplicacion_id=aplicacion_id,
                frase_numero=frase_numero,
            )
            db.add(fb)

        fb.psicologo_id = psicologo_id
        fb.veredicto = veredicto
        fb.comentario = (comentario or "").strip() or None
        fb.categoria_modelo = frase.get("dominante")
        fb.crisis_modelo = bool(frase.get("crisis"))

        db.commit()
        db.refresh(fb)
        return fb

    @staticmethod
    def quitar(
        db: Session,
        psicologo_id: str,
        aplicacion_id: int,
        frase_numero: int,
        es_admin: bool = False,
    ) -> bool:
        """Deshace el veredicto — la frase vuelve a quedar sin revisar."""
        FeedbackService._aplicacion_accesible(db, psicologo_id, aplicacion_id, es_admin)
        fb = (
            db.query(FraseFeedback)
            .filter(
                FraseFeedback.aplicacion_id == aplicacion_id,
                FraseFeedback.frase_numero == frase_numero,
            )
            .first()
        )
        if fb is None:
            return False
        db.delete(fb)
        db.commit()
        return True

    # ── Lectura por aplicación ─────────────────────────────────────────────

    @staticmethod
    def por_aplicacion(db: Session, aplicacion_id: int) -> dict:
        """
        Devuelve {numero_de_frase: {veredicto, comentario}} para pintar el
        estado de cada botón al cargar el resultado.
        """
        filas = (
            db.query(FraseFeedback)
            .filter(FraseFeedback.aplicacion_id == aplicacion_id)
            .all()
        )
        return {
            f.frase_numero: {
                "veredicto": f.veredicto,
                "comentario": f.comentario,
                "actualizado_at": f.updated_at.isoformat() if f.updated_at else None,
            }
            for f in filas
        }

    @staticmethod
    def resumen_aplicacion(db: Session, aplicacion_id: int, total_frases: int) -> dict:
        """Conteo de aceptados / rechazados / pendientes de esta aplicación."""
        filas = (
            db.query(FraseFeedback.veredicto, func.count(FraseFeedback.id))
            .filter(FraseFeedback.aplicacion_id == aplicacion_id)
            .group_by(FraseFeedback.veredicto)
            .all()
        )
        conteo = {v: n for v, n in filas}
        aceptados = conteo.get("aceptado", 0)
        rechazados = conteo.get("rechazado", 0)
        revisadas = aceptados + rechazados
        return {
            "aceptados": aceptados,
            "rechazados": rechazados,
            "revisadas": revisadas,
            "sin_revisar": max(0, total_frases - revisadas),
            "total": total_frases,
            "tasa_acierto": round(aceptados / revisadas, 4) if revisadas else None,
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
        q = db.query(FraseFeedback)
        if not es_admin:
            q = q.filter(FraseFeedback.psicologo_id == psicologo_id)
        filas = q.all()

        aceptados = sum(1 for f in filas if f.veredicto == "aceptado")
        rechazados = sum(1 for f in filas if f.veredicto == "rechazado")
        revisadas = aceptados + rechazados

        # Desglose por categoría que había predicho el modelo — sirve para ver
        # si los errores se concentran en una clase concreta.
        por_categoria: dict[str, dict] = {}
        for f in filas:
            cat = f.categoria_modelo or "(sin categoría)"
            slot = por_categoria.setdefault(
                cat, {"categoria": cat, "aceptados": 0, "rechazados": 0}
            )
            slot["aceptados" if f.veredicto == "aceptado" else "rechazados"] += 1
        for slot in por_categoria.values():
            tot = slot["aceptados"] + slot["rechazados"]
            slot["total"] = tot
            slot["tasa_acierto"] = round(slot["aceptados"] / tot, 4) if tot else None

        # Las frases marcadas como crisis se miran aparte: un falso positivo
        # ahí cuesta mucho más que en una categoría cualquiera.
        crisis = [f for f in filas if f.crisis_modelo]
        crisis_aceptados = sum(1 for f in crisis if f.veredicto == "aceptado")
        crisis_rechazados = sum(1 for f in crisis if f.veredicto == "rechazado")

        return {
            "aceptados": aceptados,
            "rechazados": rechazados,
            "revisadas": revisadas,
            "tasa_acierto": round(aceptados / revisadas, 4) if revisadas else None,
            "por_categoria": sorted(
                por_categoria.values(), key=lambda x: -x["total"]
            ),
            "crisis": {
                "aceptados": crisis_aceptados,
                "rechazados": crisis_rechazados,
                "revisadas": crisis_aceptados + crisis_rechazados,
                "tasa_acierto": (
                    round(crisis_aceptados / (crisis_aceptados + crisis_rechazados), 4)
                    if (crisis_aceptados + crisis_rechazados)
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
    def _frase_del_resultado(apl: AplicacionCuestionario, numero: int) -> dict | None:
        """Busca la frase dentro del resultado ya evaluado."""
        if not apl.resultado_json:
            return None
        try:
            resultado = json.loads(apl.resultado_json)
        except (ValueError, TypeError):
            logger.warning("resultado_json ilegible en aplicación %s", apl.id)
            return None
        for f in resultado.get("frases") or []:
            if int(f.get("numero", -1)) == int(numero):
                return f
        return None
