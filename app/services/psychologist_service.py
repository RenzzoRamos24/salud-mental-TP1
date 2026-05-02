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
            })

        return resumen

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
