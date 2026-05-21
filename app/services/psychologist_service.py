"""
Servicio para el rol psicólogo (HU-20):
Acceso a la lista de estudiantes y al historial emocional individual.
"""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.session import UserSession
from app.models.response import UserResponse
from app.models.risk import RiskResult

logger = logging.getLogger(__name__)


class PsychologistService:

    @staticmethod
    def stats_dashboard(db: Session) -> dict:
        """
        Métricas agregadas para el dashboard del psicólogo (HU-15 / HU-16).
        Devuelve distribución de riesgo y lista de estudiantes en alerta.
        """
        estudiantes = (
            db.query(User)
            .filter(User.role == "estudiante", User.activo == True)
            .all()
        )
        total = len(estudiantes)
        distribucion = {"CRÍTICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0, "sin_evaluacion": 0}
        alertas = []

        for est in estudiantes:
            ultimo_risk = (
                db.query(RiskResult)
                .filter(RiskResult.user_id == est.id)
                .order_by(desc(RiskResult.timestamp))
                .first()
            )
            if ultimo_risk:
                nivel = ultimo_risk.nivel_riesgo
                if nivel in distribucion:
                    distribucion[nivel] += 1
                if nivel in ("CRÍTICO", "ALTO"):
                    alertas.append({
                        "id": est.id,
                        "nombre": est.nombre,
                        "apellido": est.apellido,
                        "email": est.email,
                        "nivel_riesgo": nivel,
                        "score": ultimo_risk.score,
                        "fecha_evaluacion": ultimo_risk.timestamp,
                    })
            else:
                distribucion["sin_evaluacion"] += 1

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
        Devuelve todos los estudiantes activos con un resumen
        (sesiones realizadas y último nivel de riesgo).
        """
        estudiantes = (
            db.query(User)
            .filter(User.role == "estudiante", User.activo == True)
            .order_by(User.created_at.desc())
            .all()
        )

        resumen = []
        for est in estudiantes:
            sesiones = (
                db.query(UserSession)
                .filter(UserSession.user_id == est.id)
                .order_by(desc(UserSession.timestamp_inicio))
                .all()
            )
            total = len(sesiones)
            completadas = sum(1 for s in sesiones if s.estado == "completada")

            ultimo_riesgo = None
            ultimo_score = None
            ultima_eval = None
            if sesiones:
                ids_completadas = [s.id for s in sesiones if s.estado == "completada"]
                if ids_completadas:
                    ultimo_risk = (
                        db.query(RiskResult)
                        .filter(RiskResult.session_id.in_(ids_completadas))
                        .order_by(desc(RiskResult.timestamp))
                        .first()
                    )
                    if ultimo_risk:
                        ultimo_riesgo = ultimo_risk.nivel_riesgo
                        ultimo_score = ultimo_risk.score
                        ultima_eval = ultimo_risk.timestamp

            resumen.append({
                "id": est.id,
                "nombre": est.nombre,
                "apellido": est.apellido,
                "email": est.email,
                "total_sesiones": total,
                "sesiones_completadas": completadas,
                "ultimo_riesgo": ultimo_riesgo,
                "ultimo_score": ultimo_score,
                "ultima_evaluacion": ultima_eval,
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
        Historial emocional completo de un estudiante:
        sesiones cronológicas con conversación + análisis de riesgo.
        """
        estudiante = (
            db.query(User)
            .filter(User.id == student_id, User.role == "estudiante")
            .first()
        )
        if not estudiante:
            raise ValueError("Estudiante no encontrado")

        sesiones_db = (
            db.query(UserSession)
            .filter(UserSession.user_id == student_id)
            .order_by(desc(UserSession.timestamp_inicio))
            .all()
        )

        sesiones_out = []
        serie_temporal = []
        ultimo_riesgo = None
        ultimo_score = None
        ultima_eval = None
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
                })
                if ultima_eval is None or risk.timestamp > ultima_eval:
                    ultima_eval = risk.timestamp
                    ultimo_riesgo = risk.nivel_riesgo
                    ultimo_score = risk.score

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

        # Serie temporal en orden cronológico ascendente para el gráfico
        serie_temporal.sort(key=lambda x: x["fecha"])

        return {
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "email": estudiante.email,
                "total_sesiones": len(sesiones_db),
                "sesiones_completadas": completadas,
                "ultimo_riesgo": ultimo_riesgo,
                "ultimo_score": ultimo_score,
                "ultima_evaluacion": ultima_eval,
            },
            "sesiones": sesiones_out,
            "serie_temporal": serie_temporal,
        }
