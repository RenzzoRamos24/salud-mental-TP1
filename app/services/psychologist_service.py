"""
Servicio para el rol psicólogo (HU-20):
Acceso a la lista de estudiantes y al historial emocional individual.

Desde el Paso 3 del refactor a Diario, las consultas combinan dos fuentes:
  · `risk_results`     → análisis de sesiones del chatbot (legacy)
  · `diario_analisis`  → análisis BETO de entradas del diario (nuevo)

El "estado actual" del estudiante = el más reciente entre ambas tablas.
"""
import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.session import UserSession
from app.models.response import UserResponse
from app.models.risk import RiskResult
from app.models.diario_entrada import DiarioEntrada
from app.models.diario_analisis import DiarioAnalisis

VENTANA_EVALUACION_DIAS = 14

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Helpers internos: "última señal" por estudiante (chatbot o diario)
# ─────────────────────────────────────────────────────────────────────────

def _ultimo_riesgo_unificado(db: Session, user_id: str):
    """
    Devuelve la última señal de riesgo del estudiante combinando
    `risk_results` y `diario_analisis`. Devuelve un dict con:
      { nivel, score, fecha, fuente: "chatbot"|"diario", crisis }
    o None si no hay ninguna evaluación.
    """
    risk = (
        db.query(RiskResult)
        .filter(RiskResult.user_id == user_id)
        .order_by(desc(RiskResult.timestamp))
        .first()
    )
    diario = (
        db.query(DiarioAnalisis)
        .filter(DiarioAnalisis.user_id == user_id)
        .order_by(desc(DiarioAnalisis.timestamp))
        .first()
    )

    if not risk and not diario:
        return None
    if risk and (not diario or risk.timestamp >= diario.timestamp):
        return {
            "nivel": risk.nivel_riesgo,
            "score": risk.score,
            "fecha": risk.timestamp,
            "fuente": "chatbot",
            "crisis": bool(getattr(risk, "crisis_protocolo", False)),
        }
    return {
        "nivel": diario.nivel_riesgo,
        "score": diario.score,
        "fecha": diario.timestamp,
        "fuente": "diario",
        "crisis": bool(diario.crisis_protocolo),
    }


class PsychologistService:

    @staticmethod
    def stats_dashboard(db: Session) -> dict:
        """
        Métricas agregadas para el dashboard del psicólogo (HU-15 / HU-16).

        Distribución y alertas usan la fuente MÁS RECIENTE por estudiante
        (chatbot o diario, lo que sea más nuevo).
        """
        estudiantes = (
            db.query(User)
            .filter(User.role == "estudiante", User.activo == True)
            .all()
        )
        total = len(estudiantes)
        distribucion = {
            "CRÍTICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0, "sin_evaluacion": 0,
        }
        alertas = []

        for est in estudiantes:
            ultimo = _ultimo_riesgo_unificado(db, est.id)
            if not ultimo:
                distribucion["sin_evaluacion"] += 1
                continue

            nivel = ultimo["nivel"]
            if nivel in distribucion:
                distribucion[nivel] += 1

            if nivel in ("CRÍTICO", "ALTO"):
                alertas.append({
                    "id": est.id,
                    "nombre": est.nombre,
                    "apellido": est.apellido,
                    "email": est.email,
                    "nivel_riesgo": nivel,
                    "score": ultimo["score"],
                    "fecha_evaluacion": ultimo["fecha"],
                    "fuente": ultimo["fuente"],   # ← nuevo: "chatbot" | "diario"
                    "crisis_protocolo": ultimo["crisis"],
                })

        # CRÍTICO primero, luego ALTO, ordenados por fecha más reciente
        alertas.sort(key=lambda x: (
            0 if x["nivel_riesgo"] == "CRÍTICO" else 1,
            -(x["fecha_evaluacion"].timestamp() if x["fecha_evaluacion"] else 0),
        ))

        return {
            "total_estudiantes": total,
            "distribucion_riesgo": distribucion,
            "estudiantes_en_alerta": alertas,
        }

    @staticmethod
    def listar_estudiantes(db: Session) -> list:
        """
        Devuelve todos los estudiantes activos con un resumen.

        El "último riesgo" es el más reciente entre chatbot y diario.
        Se incluyen contadores separados por fuente.
        """
        estudiantes = (
            db.query(User)
            .filter(User.role == "estudiante", User.activo == True)
            .order_by(User.created_at.desc())
            .all()
        )

        resumen = []
        for est in estudiantes:
            # Sesiones del chatbot (legacy)
            sesiones = (
                db.query(UserSession)
                .filter(UserSession.user_id == est.id)
                .all()
            )
            total_sesiones = len(sesiones)
            completadas = sum(1 for s in sesiones if s.estado == "completada")

            # Entradas del diario
            total_entradas_diario = (
                db.query(DiarioEntrada)
                .filter(DiarioEntrada.user_id == est.id)
                .count()
            )

            # Última señal de riesgo (combinada)
            ultimo = _ultimo_riesgo_unificado(db, est.id)

            resumen.append({
                "id": est.id,
                "nombre": est.nombre,
                "apellido": est.apellido,
                "email": est.email,
                "total_sesiones": total_sesiones,
                "sesiones_completadas": completadas,
                "total_entradas_diario": total_entradas_diario,
                "ultimo_riesgo": ultimo["nivel"] if ultimo else None,
                "ultimo_score": ultimo["score"] if ultimo else None,
                "ultima_evaluacion": ultimo["fecha"] if ultimo else None,
                "fuente_ultima": ultimo["fuente"] if ultimo else None,   # ← nuevo
                # ── HU-35 / HU-38 ────────────────────────────────────
                "estado_caso": getattr(est, "estado_caso", None) or "activo",
                "psicologo_id": getattr(est, "psicologo_id", None),
                "grado": getattr(est, "grado", None),
            })

        return resumen

    # ── HU-35: cambiar estado del caso ──────────────────────────────
    @staticmethod
    def cambiar_estado_caso(db: Session, student_id: str, nuevo_estado: str) -> dict:
        if nuevo_estado not in ("activo", "seguimiento", "cerrado"):
            raise ValueError("Estado inválido. Usa: activo | seguimiento | cerrado")
        est = (db.query(User)
                 .filter(User.id == student_id, User.role == "estudiante")
                 .first())
        if not est:
            raise ValueError("Estudiante no encontrado")
        est.estado_caso = nuevo_estado
        db.commit()
        db.refresh(est)
        return {"id": est.id, "estado_caso": est.estado_caso}

    # ── HU-18: reportes mensuales agregados ─────────────────────────
    @staticmethod
    def reporte_mensual(db: Session, year: int, month: int) -> dict:
        from datetime import datetime as _dt
        from calendar import monthrange
        ini = _dt(year, month, 1)
        fin = _dt(year, month, monthrange(year, month)[1], 23, 59, 59)

        risks = (db.query(RiskResult)
                   .filter(RiskResult.timestamp >= ini, RiskResult.timestamp <= fin)
                   .all())
        sesiones = (db.query(UserSession)
                      .filter(UserSession.timestamp_inicio >= ini,
                              UserSession.timestamp_inicio <= fin)
                      .all())

        dist = {"CRÍTICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0}
        crisis = 0
        phq9_totales, gad7_totales = [], []
        for r in risks:
            if r.nivel_riesgo in dist:
                dist[r.nivel_riesgo] += 1
            if r.crisis_protocolo:
                crisis += 1
            if r.phq9_total is not None:
                phq9_totales.append(r.phq9_total)
            if r.gad7_total is not None:
                gad7_totales.append(r.gad7_total)

        def _avg(xs):
            return round(sum(xs) / len(xs), 2) if xs else 0

        return {
            "periodo": f"{year}-{month:02d}",
            "rango": {"inicio": ini.isoformat(), "fin": fin.isoformat()},
            "sesiones_iniciadas": len(sesiones),
            "sesiones_completadas": sum(1 for s in sesiones if s.estado == "completada"),
            "evaluaciones_analizadas": len(risks),
            "distribucion_riesgo": dist,
            "crisis_detectadas": crisis,
            "promedio_phq9": _avg(phq9_totales),
            "promedio_gad7": _avg(gad7_totales),
        }

    @staticmethod
    def historial_estudiante(db: Session, student_id: str) -> dict:
        """
        Historial emocional completo de un estudiante (chatbot + diario).

        Devuelve:
          - estudiante: resumen con la última señal combinada
          - sesiones[]: sesiones del chatbot legacy (igual que antes)
          - entradas_diario[]: entradas del diario con su análisis BETO
          - serie_temporal[]: puntos unificados con campo `fuente`
        """
        estudiante = (
            db.query(User)
            .filter(User.id == student_id, User.role == "estudiante")
            .first()
        )
        if not estudiante:
            raise ValueError("Estudiante no encontrado")

        # ── 1) Sesiones del chatbot ──────────────────────────────────
        sesiones_db = (
            db.query(UserSession)
            .filter(UserSession.user_id == student_id)
            .order_by(desc(UserSession.timestamp_inicio))
            .all()
        )

        sesiones_out = []
        serie_temporal = []
        completadas = 0

        for s in sesiones_db:
            respuestas = (
                db.query(UserResponse)
                .filter(UserResponse.session_id == s.id)
                .order_by(UserResponse.numero_pregunta)
                .all()
            )
            risk = (
                db.query(RiskResult)
                .filter(RiskResult.session_id == s.id)
                .first()
            )

            if s.estado == "completada":
                completadas += 1
            if risk:
                serie_temporal.append({
                    "fecha": risk.timestamp.isoformat(),
                    "nivel": risk.nivel_riesgo,
                    "score": risk.score,
                    "fuente": "chatbot",
                })

            sesiones_out.append({
                "session_id": s.id,
                "fecha_inicio": s.timestamp_inicio,
                "fecha_fin": s.timestamp_fin,
                "estado": s.estado,
                "nivel_riesgo": risk.nivel_riesgo if risk else None,
                "score": risk.score if risk else None,
                "explicacion": risk.explicacion if risk else None,
                "conversacion": [
                    {
                        "numero": r.numero_pregunta,
                        "pregunta": r.pregunta,
                        "respuesta": r.respuesta,
                        "score_riesgo": r.score_riesgo,
                        "nivel_riesgo": r.nivel_riesgo,
                        "condicion_dominante": r.condicion_dominante,
                    }
                    for r in respuestas
                ],
            })

        # ── 2) Entradas del diario con su análisis ───────────────────
        entradas_db = (
            db.query(DiarioEntrada)
            .filter(DiarioEntrada.user_id == student_id)
            .order_by(desc(DiarioEntrada.timestamp))
            .all()
        )
        entradas_out = []
        for e in entradas_db:
            analisis = None
            if e.analisis_id:
                analisis = (
                    db.query(DiarioAnalisis)
                    .filter(DiarioAnalisis.id == e.analisis_id)
                    .first()
                )
            if analisis:
                serie_temporal.append({
                    "fecha": analisis.timestamp.isoformat(),
                    "nivel": analisis.nivel_riesgo,
                    "score": analisis.score,
                    "fuente": "diario",
                })
            entradas_out.append({
                "id": e.id,
                "fecha": e.fecha.isoformat() if e.fecha else None,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "estado_animo": e.estado_animo,
                "prompt_del_dia": e.prompt_del_dia,
                "texto": e.texto,
                "analisis": (
                    {
                        "nivel_riesgo": analisis.nivel_riesgo,
                        "score": analisis.score,
                        "phq9_total": analisis.phq9_total,
                        "gad7_total": analisis.gad7_total,
                        "phq9_severidad": analisis.phq9_severidad,
                        "gad7_severidad": analisis.gad7_severidad,
                        "crisis_protocolo": analisis.crisis_protocolo,
                        "items_detectados": _safe_json(analisis.items_detectados_json, default=[]),
                        "condiciones_detectadas": _safe_json(analisis.condiciones_detectadas_json, default={}),
                        "scores_completos": _safe_json(analisis.scores_completos_json, default={}),
                        "modelo": analisis.modelo,
                        "timestamp": analisis.timestamp.isoformat() if analisis.timestamp else None,
                    }
                    if analisis else None
                ),
            })

        # ── 3) Serie temporal en orden cronológico ascendente ────────
        serie_temporal.sort(key=lambda x: x["fecha"])

        # ── 4) Última señal combinada ────────────────────────────────
        ultimo = _ultimo_riesgo_unificado(db, student_id)

        return {
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "email": estudiante.email,
                "total_sesiones": len(sesiones_db),
                "sesiones_completadas": completadas,
                "total_entradas_diario": len(entradas_db),
                "ultimo_riesgo": ultimo["nivel"] if ultimo else None,
                "ultimo_score": ultimo["score"] if ultimo else None,
                "ultima_evaluacion": ultimo["fecha"] if ultimo else None,
                "fuente_ultima": ultimo["fuente"] if ultimo else None,
            },
            "sesiones": sesiones_out,
            "entradas_diario": entradas_out,
            "serie_temporal": serie_temporal,
        }


def _safe_json(raw, default):
    """Parse JSON-Text columns de forma tolerante."""
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


def _extraer_frases_alerta(items: list, condiciones: dict) -> list:
    """
    Devuelve las frases-keyword cortas que dispararon la alerta crítica,
    deduplicadas y ordenadas por gravedad clínica.

    Prioridad:
      1. Keywords del ítem PHQ-9 #9 (ideación suicida).
      2. Keywords de condición 'riesgo_suicida' (si vienen en items).
      3. Keywords del resto de ítems con score ≥ 2.

    El psicólogo solo ve estas frases — nunca el texto completo del diario.
    """
    vistas = set()
    frases_prioridad = []
    frases_secundarias = []

    for it in items or []:
        item_id = it.get("item", "")
        score = it.get("score", 0)
        keywords = it.get("keywords") or []

        es_critico = item_id == "phq9_9" or "suicid" in item_id.lower()
        for kw in keywords:
            kw_norm = (kw or "").strip().lower()
            if not kw_norm or kw_norm in vistas:
                continue
            vistas.add(kw_norm)
            if es_critico:
                frases_prioridad.append(kw.strip())
            elif score >= 2:
                frases_secundarias.append(kw.strip())

    return (frases_prioridad + frases_secundarias)[:8]


# ─────────────────────────────────────────────────────────────────────────
# RESUMEN BISEMANAL DEL DIARIO (Paso 4 — panel psicólogo)
# ─────────────────────────────────────────────────────────────────────────

def resumen_diario_estudiante(db: Session, student_id: str) -> dict:
    """
    Análisis agregado del diario en una ventana de 14 días.

    Estados de evaluación:
      - "en_proceso": el alumno tiene primera entrada con menos de 14 días.
        Devuelve días transcurridos + porcentaje + resumen aproximado.
      - "completo":   ya pasaron ≥14 días desde la primera entrada.
      - "sin_datos":  el alumno aún no escribió nada.

    Alerta crítica: se dispara si CUALQUIER entrada de los últimos 14 días
    tiene crisis_protocolo=True. La alerta es inmediata, no espera a la
    ventana completa.
    """
    estudiante = (
        db.query(User)
        .filter(User.id == student_id, User.role == "estudiante")
        .first()
    )
    if not estudiante:
        raise ValueError("Estudiante no encontrado")

    ahora = datetime.utcnow()
    desde = ahora - timedelta(days=VENTANA_EVALUACION_DIAS)

    # ── Todas las entradas del alumno (para calcular días desde la 1ra) ──
    primera_entrada = (
        db.query(DiarioEntrada)
        .filter(DiarioEntrada.user_id == student_id)
        .order_by(DiarioEntrada.timestamp.asc())
        .first()
    )

    if not primera_entrada:
        return {
            "estado_evaluacion": "sin_datos",
            "dias_transcurridos": 0,
            "dias_objetivo": VENTANA_EVALUACION_DIAS,
            "porcentaje_completado": 0,
            "alerta_critica": None,
            "resumen": None,
            "mensaje": (
                "El estudiante todavía no ha escrito ninguna entrada en el "
                "diario. El análisis empezará con la primera entrada."
            ),
        }

    dias_transcurridos = (ahora - primera_entrada.timestamp).days
    dias_efectivos = min(dias_transcurridos, VENTANA_EVALUACION_DIAS)
    porcentaje = round((dias_efectivos / VENTANA_EVALUACION_DIAS) * 100)
    estado = "completo" if dias_transcurridos >= VENTANA_EVALUACION_DIAS else "en_proceso"

    # ── Entradas dentro de la ventana de 14 días ──────────────────────
    entradas_ventana = (
        db.query(DiarioEntrada)
        .filter(
            DiarioEntrada.user_id == student_id,
            DiarioEntrada.timestamp >= desde,
        )
        .order_by(DiarioEntrada.timestamp.asc())
        .all()
    )

    # Análisis correspondientes (los que ya corrieron)
    analisis_ventana = []
    for e in entradas_ventana:
        if not e.analisis_id:
            continue
        a = (
            db.query(DiarioAnalisis)
            .filter(DiarioAnalisis.id == e.analisis_id)
            .first()
        )
        if a:
            analisis_ventana.append((e, a))

    # ── Alerta crítica: cualquier crisis_protocolo en la ventana ──────
    # Por privacidad NO se expone el texto del diario, solo las frases
    # cortas (keywords) que el sistema detectó como señal.
    alerta_critica = None
    for e, a in analisis_ventana:
        if a.crisis_protocolo:
            items = _safe_json(a.items_detectados_json, default=[])
            condiciones = _safe_json(a.condiciones_detectadas_json, default={})
            frases = _extraer_frases_alerta(items, condiciones)
            alerta_critica = {
                "entrada_id": e.id,
                "fecha": e.timestamp.isoformat(),
                "nivel_riesgo": a.nivel_riesgo,
                "frases_detectadas": frases,
                "motivo": "El sistema detectó señales críticas (ideación "
                          "suicida o riesgo elevado) en una entrada reciente.",
            }
            break  # con una basta para encender la alerta

    # ── Resumen numérico (PHQ-9 / GAD-7 promedios + severidad dominante) ──
    if not analisis_ventana:
        resumen = {
            "entradas_en_ventana": 0,
            "phq9_promedio": None,
            "gad7_promedio": None,
            "severidad_dominante": None,
            "nivel_dominante": None,
            "mood_distribucion": {},
            "condiciones_top": [],
        }
    else:
        phq9 = [a.phq9_total for _, a in analisis_ventana if a.phq9_total is not None]
        gad7 = [a.gad7_total for _, a in analisis_ventana if a.gad7_total is not None]
        niveles = [a.nivel_riesgo for _, a in analisis_ventana if a.nivel_riesgo]
        severidades_phq = [a.phq9_severidad for _, a in analisis_ventana if a.phq9_severidad]
        moods = [e.estado_animo for e, _ in analisis_ventana if e.estado_animo]

        # Condiciones BERT más recurrentes en la ventana
        cond_counter = Counter()
        cond_confianzas = {}
        for _, a in analisis_ventana:
            cd = _safe_json(a.condiciones_detectadas_json, default={})
            for k, v in cd.items():
                cond_counter[k] += 1
                cond_confianzas.setdefault(k, []).append(v.get("confianza", 0))

        condiciones_top = [
            {
                "condicion": k,
                "etiqueta": k.replace("_", " ").capitalize(),
                "veces_detectada": cond_counter[k],
                "confianza_promedio": round(
                    sum(cond_confianzas[k]) / len(cond_confianzas[k]), 1
                ),
            }
            for k in sorted(cond_counter, key=cond_counter.get, reverse=True)[:5]
        ]

        resumen = {
            "entradas_en_ventana": len(analisis_ventana),
            "phq9_promedio": round(sum(phq9) / len(phq9), 1) if phq9 else None,
            "gad7_promedio": round(sum(gad7) / len(gad7), 1) if gad7 else None,
            "severidad_dominante": (
                Counter(severidades_phq).most_common(1)[0][0]
                if severidades_phq else None
            ),
            "nivel_dominante": (
                Counter(niveles).most_common(1)[0][0]
                if niveles else None
            ),
            "mood_distribucion": dict(Counter(moods)),
            "condiciones_top": condiciones_top,
        }

    # ── Mensaje al psicólogo (cambia según estado) ────────────────────
    if estado == "en_proceso":
        mensaje = (
            f"Análisis en proceso de evaluación. Van {dias_transcurridos} "
            f"de {VENTANA_EVALUACION_DIAS} días desde la primera entrada "
            f"({porcentaje}%). El resumen actual es aproximado y se "
            f"consolidará al completar la ventana."
        )
    else:
        mensaje = (
            f"Análisis completo: {VENTANA_EVALUACION_DIAS} días de datos "
            f"considerados. Resumen consolidado."
        )

    return {
        "estado_evaluacion": estado,
        "dias_transcurridos": dias_transcurridos,
        "dias_objetivo": VENTANA_EVALUACION_DIAS,
        "porcentaje_completado": porcentaje,
        "primera_entrada_fecha": primera_entrada.timestamp.isoformat(),
        "ventana_desde": desde.isoformat(),
        "ventana_hasta": ahora.isoformat(),
        "alerta_critica": alerta_critica,
        "resumen": resumen,
        "mensaje": mensaje,
    }
