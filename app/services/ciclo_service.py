"""
Servicio de "ciclos de seguimiento" del estudiante.

MODELO (acordado con el usuario el 2026-05-29):

  Cada ciclo dura 14 días desde la PRIMERA ENTRADA del alumno en ese
  ciclo. Cierra automáticamente al cumplirse el día 14, INDEPENDIENTE
  del resultado clínico o de citas con la psicóloga.

  Día 15 = Día 1 del Ciclo N+1, sin importar nada más. El diario no
  se detiene.

  Excepción: si la psicóloga atiende al alumno por una crisis y marca
  esa cita con `es_crisis=True` + `estado='completada'`, ese día CIERRA
  el ciclo en curso anticipadamente. El ciclo N+1 arranca al día
  siguiente.

  Las citas REGULARES (es_crisis=False) corren EN PARALELO al ciclo y
  NO afectan su temporalidad. La psicóloga ve al alumno cuando tiene
  que verlo; ese encuentro no detiene ni reinicia el diario.

El estudiante ve:
  - En qué día del ciclo va (1, 2, ... 14)
  - Cuándo empezó el ciclo
  - Cuándo es su próxima cita (si hay)
  - Historial de ciclos cerrados (Ciclo 1, 2, ...) con su resumen.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.models.cita import Cita
from app.models.diario_entrada import DiarioEntrada
from app.models.user import User

logger = logging.getLogger(__name__)

DIAS_POR_CICLO = 14


# ─────────────────────────────────────────────────────────────────────────
# CÁLCULO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────

def info_ciclo_estudiante(db: Session, user_id: str) -> dict:
    """
    Devuelve la foto actual del proceso del alumno:
      - estado: "sin_iniciar" | "en_curso" | "vencido"
      - ciclo_actual: { numero, inicio, dia_actual, dias_objetivo,
                        fecha_limite, entradas_escritas, fechas_con_entrada }
      - sesiones_cerradas: [{ numero, inicio, cierre, dias_del_ciclo,
                              entradas_escritas, motivo_cierre, ... }]
      - proxima_cita: dict o None
      - mensaje: texto para mostrar al alumno
    """
    estudiante = (
        db.query(User)
        .filter(User.id == user_id, User.role == "estudiante")
        .first()
    )
    if not estudiante:
        raise ValueError("Estudiante no encontrado")

    # ── Primera entrada de TODO el diario (anclaje del Ciclo 1) ────────
    primera_entrada = (
        db.query(DiarioEntrada)
        .filter(DiarioEntrada.user_id == user_id)
        .order_by(asc(DiarioEntrada.timestamp))
        .first()
    )

    if not primera_entrada:
        return {
            "estado": "sin_iniciar",
            "dias_por_ciclo": DIAS_POR_CICLO,
            "ciclo_actual": None,
            "sesiones_cerradas": [],
            "proxima_cita": _proxima_cita_dict(db, user_id),
            "mensaje": (
                f"Cuando escribas tu primera entrada, ese será tu Día 1 de "
                f"{DIAS_POR_CICLO}. El sistema cuenta los días automáticamente."
            ),
        }

    # ── Citas de CRISIS completadas (cada una puede cerrar un ciclo) ──
    crisis_completadas = (
        db.query(Cita)
        .filter(
            Cita.estudiante_id == user_id,
            Cita.estado == "completada",
            Cita.es_crisis == True,  # noqa: E712
        )
        .all()
    )
    fechas_cierre_crisis = sorted(
        {
            (c.completada_at.date() if c.completada_at else _parse_fecha(c.fecha))
            for c in crisis_completadas
        }
    )

    hoy = date.today()
    primera_fecha = primera_entrada.fecha or primera_entrada.timestamp.date()

    # ── Recorrido de ciclos: arrancamos en la primera entrada y avanzamos ─
    sesiones_cerradas = []
    inicio_ciclo = primera_fecha
    numero_ciclo = 1

    while True:
        fin_natural = inicio_ciclo + timedelta(days=DIAS_POR_CICLO - 1)

        # ¿Hay una crisis dentro de la ventana del ciclo? La primera crisis
        # que caiga en el rango cierra el ciclo en su fecha (cierre anticipado).
        cierre_crisis = next(
            (
                f for f in fechas_cierre_crisis
                if inicio_ciclo <= f <= fin_natural
            ),
            None,
        )
        fin_ciclo = cierre_crisis or fin_natural
        motivo = "crisis" if cierre_crisis else "tiempo"

        # Si el cierre es a futuro, este ciclo todavía está abierto: lo
        # consideramos el ciclo ACTUAL y rompemos el loop.
        if fin_ciclo >= hoy:
            ciclo_actual_inicio = inicio_ciclo
            ciclo_actual_fin = fin_ciclo
            ciclo_actual_motivo = motivo
            break

        # Ciclo cerrado en el pasado → al historial.
        entradas_count, fechas_con_entrada = _contar_entradas(
            db, user_id, inicio_ciclo, fin_ciclo
        )
        sesiones_cerradas.append({
            "numero": numero_ciclo,
            "inicio": inicio_ciclo.isoformat(),
            "cierre": fin_ciclo.isoformat(),
            "dias_del_ciclo": (fin_ciclo - inicio_ciclo).days + 1,
            "entradas_escritas": entradas_count,
            "fechas_con_entrada": fechas_con_entrada,
            "motivo_cierre": motivo,
        })

        # Avanzar al siguiente ciclo
        inicio_ciclo = fin_ciclo + timedelta(days=1)
        numero_ciclo += 1

    # ── Ciclo ACTUAL (abierto) ─────────────────────────────────────────
    dia_actual = (hoy - ciclo_actual_inicio).days + 1
    if dia_actual < 1:
        dia_actual = 1
    estado_ciclo = "en_curso" if dia_actual <= DIAS_POR_CICLO else "vencido"

    entradas_actual, fechas_actual = _contar_entradas(
        db, user_id, ciclo_actual_inicio, ciclo_actual_fin
    )

    proxima_cita = _proxima_cita_dict(db, user_id)
    mensaje = _construir_mensaje(
        estado_ciclo,
        dia_actual,
        numero_ciclo,
        len(sesiones_cerradas),
        proxima_cita,
    )

    return {
        "estado": estado_ciclo,
        "dias_por_ciclo": DIAS_POR_CICLO,
        "ciclo_actual": {
            "numero": numero_ciclo,
            "inicio": ciclo_actual_inicio.isoformat(),
            "fecha_limite": ciclo_actual_fin.isoformat(),
            "dia_actual": dia_actual,
            "porcentaje": min(round((dia_actual / DIAS_POR_CICLO) * 100), 100),
            "entradas_escritas": entradas_actual,
            "fechas_con_entrada": fechas_actual,
            "motivo_cierre_esperado": ciclo_actual_motivo,
        },
        "sesiones_cerradas": sesiones_cerradas,
        "proxima_cita": proxima_cita,
        "mensaje": mensaje,
    }


# ─────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────

def _contar_entradas(
    db: Session, user_id: str, desde: date, hasta: date
) -> tuple[int, list[str]]:
    """Cuenta entradas y devuelve también las fechas (ISO) en que hubo entrada."""
    rows = (
        db.query(DiarioEntrada.fecha)
        .filter(
            DiarioEntrada.user_id == user_id,
            DiarioEntrada.fecha >= desde,
            DiarioEntrada.fecha <= hasta,
        )
        .all()
    )
    fechas = sorted({r[0].isoformat() for r in rows if r[0]})
    return len(rows), fechas


def _parse_fecha(s: str) -> date:
    """Parsea 'YYYY-MM-DD' a date."""
    return datetime.strptime(s, "%Y-%m-%d").date()


def _proxima_cita_dict(db: Session, user_id: str) -> Optional[dict]:
    hoy = date.today().isoformat()
    cita = (
        db.query(Cita)
        .filter(
            Cita.estudiante_id == user_id,
            Cita.estado.in_(("pendiente", "confirmada")),
            Cita.fecha >= hoy,
        )
        .order_by(asc(Cita.fecha), asc(Cita.hora))
        .first()
    )
    if not cita:
        return None
    return {
        "id": cita.id,
        "fecha": cita.fecha,
        "hora": cita.hora,
        "modalidad": cita.modalidad,
        "estado": cita.estado,
        "notas": cita.notas,
        "es_crisis": cita.es_crisis,
    }


def _construir_mensaje(
    estado: str,
    dia: int,
    numero_ciclo: int,
    sesiones_previas: int,
    proxima_cita: Optional[dict],
) -> str:
    if estado == "vencido":
        return (
            f"Tu ciclo {numero_ciclo} debió cerrar al día {DIAS_POR_CICLO}. "
            "Volverá a cerrarse automáticamente cuando el sistema procese."
        )
    if dia == 1:
        if sesiones_previas == 0:
            return (
                f"Estás en el día 1 de {DIAS_POR_CICLO}. Empezó tu primer "
                f"ciclo de seguimiento."
            )
        return (
            f"Estás en el día 1 de {DIAS_POR_CICLO} — Ciclo {numero_ciclo}. "
            f"Tu ciclo anterior cerró ayer."
        )
    base = f"Estás en el día {dia} de {DIAS_POR_CICLO} — Ciclo {numero_ciclo}."
    if proxima_cita:
        if proxima_cita.get("es_crisis"):
            base += f" Tienes una cita de atención el {proxima_cita['fecha']}."
        else:
            base += (
                f" Tu próxima cita con la psicóloga es el "
                f"{proxima_cita['fecha']} (el diario sigue corriendo en paralelo)."
            )
    return base
