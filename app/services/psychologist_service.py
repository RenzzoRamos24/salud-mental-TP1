"""
Servicio del rol psicólogo (Sprint 9 — cuestionarios).

El modelo de "diario + ciclos" ya no aplica. Las métricas se calculan ahora
sobre AplicacionCuestionario (asignaciones a alumnos) y su evaluación.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.bank import AplicacionCuestionario

logger = logging.getLogger(__name__)


def _ultima_aplicacion_revisada(db: Session, user_id: str):
    return (
        db.query(AplicacionCuestionario)
        .filter(
            AplicacionCuestionario.estudiante_id == user_id,
            AplicacionCuestionario.completada_at.isnot(None),
        )
        .order_by(desc(AplicacionCuestionario.completada_at))
        .first()
    )


class PsychologistService:

    @staticmethod
    def stats_dashboard(db: Session) -> dict:
        """Métricas agregadas para el dashboard del psicólogo."""
        estudiantes = (
            db.query(User)
            .filter(User.role == "estudiante", User.activo == True)
            .all()
        )
        total = len(estudiantes)
        distribucion = {
            "CRITICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0,
            "SIN_RIESGO": 0, "sin_evaluacion": 0,
        }
        alertas = []

        for est in estudiantes:
            ultima = _ultima_aplicacion_revisada(db, est.id)
            if not ultima or not ultima.riesgo_global:
                distribucion["sin_evaluacion"] += 1
                continue
            clave = ultima.riesgo_global.upper().replace("Í", "I")
            if clave in distribucion:
                distribucion[clave] += 1
            if clave in ("CRITICO", "ALTO") or ultima.crisis_activada:
                alertas.append({
                    "id": est.id,
                    "nombre": est.nombre,
                    "apellido": est.apellido,
                    "email": est.email,
                    "riesgo_global": ultima.riesgo_global,
                    "crisis_activada": bool(ultima.crisis_activada),
                    "fecha_evaluacion": ultima.completada_at.isoformat() if ultima.completada_at else None,
                    "aplicacion_id": ultima.id,
                })

        alertas.sort(key=lambda x: (
            0 if (x["riesgo_global"] or "").upper().startswith("C") else 1,
            -(datetime.fromisoformat(x["fecha_evaluacion"]).timestamp() if x["fecha_evaluacion"] else 0),
        ))

        return {
            "total_estudiantes": total,
            "distribucion_riesgo": distribucion,
            "estudiantes_en_alerta": alertas,
            "total_cuestionarios_asignados": db.query(AplicacionCuestionario).count(),
            "total_cuestionarios_completados": db.query(AplicacionCuestionario)
                .filter(AplicacionCuestionario.completada_at.isnot(None)).count(),
        }

    @staticmethod
    def listar_estudiantes(db: Session) -> list:
        estudiantes = (
            db.query(User)
            .filter(User.role == "estudiante", User.activo == True)
            .order_by(User.created_at.desc())
            .all()
        )
        out = []
        for est in estudiantes:
            ultima = _ultima_aplicacion_revisada(db, est.id)
            total_apps = (
                db.query(AplicacionCuestionario)
                .filter(AplicacionCuestionario.estudiante_id == est.id)
                .count()
            )
            out.append({
                "id": est.id,
                "nombre": est.nombre,
                "apellido": est.apellido,
                "email": est.email,
                "total_cuestionarios": total_apps,
                "ultimo_riesgo": ultima.riesgo_global if ultima else None,
                "ultima_evaluacion": ultima.completada_at.isoformat() if ultima and ultima.completada_at else None,
                "crisis_activada": bool(ultima.crisis_activada) if ultima else False,
                "estado_caso": getattr(est, "estado_caso", None) or "activo",
                "psicologo_id": getattr(est, "psicologo_id", None),
                "grado": getattr(est, "grado", None),
            })
        return out

    @staticmethod
    def cambiar_estado_caso(db: Session, student_id: str, nuevo_estado: str) -> dict:
        if nuevo_estado not in ("activo", "seguimiento", "cerrado"):
            raise ValueError("Estado inválido. Usa: activo | seguimiento | cerrado")
        est = (
            db.query(User)
            .filter(User.id == student_id, User.role == "estudiante")
            .first()
        )
        if not est:
            raise ValueError("Estudiante no encontrado")
        est.estado_caso = nuevo_estado
        db.commit()
        db.refresh(est)
        return {"id": est.id, "estado_caso": est.estado_caso}

    @staticmethod
    def historial_estudiante(db: Session, student_id: str) -> dict:
        estudiante = (
            db.query(User)
            .filter(User.id == student_id, User.role == "estudiante")
            .first()
        )
        if not estudiante:
            raise ValueError("Estudiante no encontrado")

        aplicaciones = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.estudiante_id == student_id)
            .order_by(desc(AplicacionCuestionario.asignada_at))
            .all()
        )

        return {
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "email": estudiante.email,
                "grado": getattr(estudiante, "grado", None),
                "estado_caso": getattr(estudiante, "estado_caso", None) or "activo",
            },
            "aplicaciones": [
                {
                    "id": a.id,
                    "plantilla_id": a.plantilla_id,
                    "estado": a.estado,
                    "riesgo_global": a.riesgo_global,
                    "crisis_activada": bool(a.crisis_activada),
                    "asignada_at": a.asignada_at.isoformat() if a.asignada_at else None,
                    "completada_at": a.completada_at.isoformat() if a.completada_at else None,
                }
                for a in aplicaciones
            ],
        }
