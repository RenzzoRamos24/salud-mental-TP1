"""
Encuesta clínica al cierre de cada ciclo (PHQ-A 9 ítems + GAD-7 7 ítems).

Reglas:
- Se ofrece al alumno cuando el ciclo actual supera el día 14 o cuando se
  acaba de cerrar el último ciclo.
- Mientras la encuesta esté pendiente, el resto del diario sigue accesible,
  pero la app muestra un banner llevando a responderla.
- Una vez completada, calcula los totales (Kroenke & Spitzer / Spitzer & Löwe),
  el nivel de severidad y dispara `crisis_protocolo` si el PHQ-9 ítem 9 ≥ 1.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import settings
from app.models.cycle_survey import CycleSurvey
from app.services.ciclo_service import info_ciclo_estudiante

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# CATÁLOGO DE ÍTEMS
# ─────────────────────────────────────────────────────────────────────────

def items_para_estudiante() -> list[dict]:
    """
    Devuelve los 16 ítems en orden de aplicación, con solo la información que
    necesita la UI (no exponemos criterio DSM ni keywords).
    """
    items = []
    for it in settings.PHQ9_ITEMS:
        items.append({
            "id": it["id"],
            "modulo": it["modulo"],
            "numero": it["numero_oficial"],
            "texto": it["texto"],
            "es_critica": it.get("es_critica", False),
        })
    for it in settings.GAD7_ITEMS:
        items.append({
            "id": it["id"],
            "modulo": it["modulo"],
            "numero": it["numero_oficial"],
            "texto": it["texto"],
            "es_critica": False,
        })
    return items


def opciones_likert() -> list[dict]:
    return settings.OPCIONES_LIKERT


# ─────────────────────────────────────────────────────────────────────────
# PENDIENTE / OBTENER / INICIAR
# ─────────────────────────────────────────────────────────────────────────

def _ciclo_objetivo(info: dict) -> Optional[dict]:
    """
    Decide a qué ciclo le toca encuesta:
    - Si el ciclo en curso está "vencido" (día > 14), es ese.
    - Si no, y la última sesión cerrada fue muy reciente, es la última cerrada.
    Devuelve None si no hay encuesta que corresponder.
    """
    if not info:
        return None

    # Caso 1: ciclo actual ya vencido (debió cerrar) → encuesta de ese ciclo.
    actual = info.get("ciclo_actual")
    if actual and info.get("estado") == "vencido":
        return {
            "numero": actual["numero"],
            "inicio": actual["inicio"],
            "fin": actual["fecha_limite"],
        }

    # Caso 2: hay una sesión recién cerrada y no se respondió aún.
    cerradas = info.get("sesiones_cerradas") or []
    if cerradas:
        ultima = cerradas[-1]
        return {
            "numero": ultima["numero"],
            "inicio": ultima["inicio"],
            "fin": ultima["cierre"],
        }

    return None


def encuesta_pendiente(db: Session, user_id: str) -> Optional[CycleSurvey]:
    """
    Encuentra o crea la encuesta pendiente del ciclo correspondiente.
    Devuelve None si no hay ningún ciclo que requiera encuesta.
    """
    info = info_ciclo_estudiante(db, user_id)
    objetivo = _ciclo_objetivo(info)
    if not objetivo:
        return None

    encuesta = (
        db.query(CycleSurvey)
        .filter(
            CycleSurvey.user_id == user_id,
            CycleSurvey.ciclo_numero == objetivo["numero"],
        )
        .first()
    )

    if encuesta and encuesta.completada_at:
        # Esta encuesta ya se completó. Solo aparecerá una nueva cuando el
        # siguiente ciclo vuelva a cumplir 14 días.
        return None

    if not encuesta:
        encuesta = CycleSurvey(
            user_id=user_id,
            ciclo_numero=objetivo["numero"],
            ciclo_inicio=date.fromisoformat(objetivo["inicio"]),
            ciclo_fin=date.fromisoformat(objetivo["fin"]),
            respuestas_json=json.dumps({}),
        )
        db.add(encuesta)
        db.commit()
        db.refresh(encuesta)
        logger.info(
            f"📋 Encuesta clínica abierta para {user_id} (ciclo {objetivo['numero']})"
        )

    return encuesta


# ─────────────────────────────────────────────────────────────────────────
# RESPUESTAS
# ─────────────────────────────────────────────────────────────────────────

_IDS_VALIDOS = {it["id"] for it in (settings.PHQ9_ITEMS + settings.GAD7_ITEMS)}


def guardar_respuesta(
    db: Session, encuesta: CycleSurvey, item_id: str, valor: int
) -> CycleSurvey:
    if item_id not in _IDS_VALIDOS:
        raise ValueError(f"Ítem desconocido: {item_id}")
    if valor not in (0, 1, 2, 3):
        raise ValueError("El valor debe ser 0, 1, 2 o 3.")
    if encuesta.completada_at is not None:
        raise ValueError("La encuesta ya fue cerrada.")

    respuestas = json.loads(encuesta.respuestas_json or "{}")
    respuestas[item_id] = valor
    encuesta.respuestas_json = json.dumps(respuestas)
    db.commit()
    db.refresh(encuesta)
    return encuesta


# ─────────────────────────────────────────────────────────────────────────
# CIERRE
# ─────────────────────────────────────────────────────────────────────────

def _severidad(total: int, tabla: list) -> dict:
    for rango in tabla:
        if rango["min"] <= total <= rango["max"]:
            return rango
    return tabla[-1]


def cerrar_encuesta(db: Session, encuesta: CycleSurvey) -> dict:
    if encuesta.completada_at:
        raise ValueError("La encuesta ya estaba cerrada.")

    respuestas = json.loads(encuesta.respuestas_json or "{}")
    faltantes = [it_id for it_id in _IDS_VALIDOS if it_id not in respuestas]
    if faltantes:
        raise ValueError(
            f"Faltan {len(faltantes)} respuestas para cerrar la encuesta."
        )

    phq_total = sum(respuestas[it["id"]] for it in settings.PHQ9_ITEMS)
    gad_total = sum(respuestas[it["id"]] for it in settings.GAD7_ITEMS)

    phq_sev = _severidad(phq_total, settings.PHQ9_SEVERIDAD)
    gad_sev = _severidad(gad_total, settings.GAD7_SEVERIDAD)

    crisis = respuestas.get("phq9_9", 0) >= 1

    encuesta.phq9_total = phq_total
    encuesta.gad7_total = gad_total
    encuesta.phq9_severidad = phq_sev["nivel"]
    encuesta.gad7_severidad = gad_sev["nivel"]
    encuesta.crisis_protocolo = crisis
    encuesta.completada_at = datetime.utcnow()
    db.commit()
    db.refresh(encuesta)

    logger.info(
        f"✅ Encuesta cerrada · user={encuesta.user_id} ciclo={encuesta.ciclo_numero} · "
        f"PHQ-A {phq_total}/27 ({phq_sev['nivel']}) · GAD-7 {gad_total}/21 ({gad_sev['nivel']}) · "
        f"crisis={crisis}"
    )

    return {
        "phq9_total": phq_total,
        "gad7_total": gad_total,
        "phq9_severidad": phq_sev["nivel"],
        "phq9_accion": phq_sev["accion"],
        "gad7_severidad": gad_sev["nivel"],
        "gad7_accion": gad_sev["accion"],
        "crisis_protocolo": crisis,
    }


# ─────────────────────────────────────────────────────────────────────────
# SERIALIZACIÓN PARA EL FRONTEND
# ─────────────────────────────────────────────────────────────────────────

def serializar(encuesta: CycleSurvey) -> dict:
    respuestas = json.loads(encuesta.respuestas_json or "{}")
    return {
        "id": encuesta.id,
        "ciclo_numero": encuesta.ciclo_numero,
        "ciclo_inicio": encuesta.ciclo_inicio.isoformat(),
        "ciclo_fin": encuesta.ciclo_fin.isoformat(),
        "iniciada_at": encuesta.iniciada_at.isoformat() if encuesta.iniciada_at else None,
        "completada_at": encuesta.completada_at.isoformat() if encuesta.completada_at else None,
        "respuestas": respuestas,
        "phq9_total": encuesta.phq9_total,
        "gad7_total": encuesta.gad7_total,
        "phq9_severidad": encuesta.phq9_severidad,
        "gad7_severidad": encuesta.gad7_severidad,
        "crisis_protocolo": encuesta.crisis_protocolo,
        "items": items_para_estudiante(),
        "opciones": opciones_likert(),
    }


def ultima_completada(db: Session, user_id: str) -> Optional[CycleSurvey]:
    return (
        db.query(CycleSurvey)
        .filter(
            CycleSurvey.user_id == user_id,
            CycleSurvey.completada_at.is_not(None),
        )
        .order_by(desc(CycleSurvey.completada_at))
        .first()
    )
