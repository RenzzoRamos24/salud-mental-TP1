"""Servicio CRUD para citas psicólogo–estudiante (HU-19)."""
import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.cita import Cita
from app.models.user import User

logger = logging.getLogger(__name__)


def _enriquecer(cita: Cita, db: Session) -> dict:
    """Agrega nombre/apellido/email del estudiante al dict de salida."""
    est = db.query(User).filter(User.id == cita.estudiante_id).first()
    return {
        "id": cita.id,
        "psicologo_id": cita.psicologo_id,
        "estudiante_id": cita.estudiante_id,
        "fecha": cita.fecha,
        "hora": cita.hora,
        "modalidad": cita.modalidad,
        "estado": cita.estado,
        "notas": cita.notas,
        "created_at": cita.created_at,
        "estudiante_nombre": est.nombre if est else None,
        "estudiante_apellido": est.apellido if est else None,
        "estudiante_email": est.email if est else None,
    }


class CitaService:

    @staticmethod
    def crear(db: Session, psicologo_id: str, datos: dict) -> dict:
        cita = Cita(
            psicologo_id=psicologo_id,
            estudiante_id=datos["estudiante_id"],
            fecha=datos["fecha"],
            hora=datos["hora"],
            modalidad=datos.get("modalidad", "presencial"),
            notas=datos.get("notas"),
        )
        db.add(cita)
        db.commit()
        db.refresh(cita)
        logger.info(f"Cita {cita.id} creada para estudiante {cita.estudiante_id}")
        return _enriquecer(cita, db)

    @staticmethod
    def listar(db: Session, psicologo_id: str, estudiante_id: str | None = None) -> list:
        q = db.query(Cita).filter(Cita.psicologo_id == psicologo_id)
        if estudiante_id:
            q = q.filter(Cita.estudiante_id == estudiante_id)
        citas = q.order_by(Cita.fecha.asc(), Cita.hora.asc()).all()
        return [_enriquecer(c, db) for c in citas]

    @staticmethod
    def actualizar(db: Session, cita_id: int, psicologo_id: str, cambios: dict) -> dict:
        cita = db.query(Cita).filter(
            Cita.id == cita_id,
            Cita.psicologo_id == psicologo_id,
        ).first()
        if not cita:
            raise ValueError("Cita no encontrada")
        for campo, valor in cambios.items():
            if valor is not None:
                setattr(cita, campo, valor)
        db.commit()
        db.refresh(cita)
        return _enriquecer(cita, db)

    @staticmethod
    def cancelar(db: Session, cita_id: int, psicologo_id: str) -> None:
        cita = db.query(Cita).filter(
            Cita.id == cita_id,
            Cita.psicologo_id == psicologo_id,
        ).first()
        if not cita:
            raise ValueError("Cita no encontrada")
        cita.estado = "cancelada"
        db.commit()

    # ── HU-30: agendamiento iniciado por el ESTUDIANTE ───────────────
    @staticmethod
    def solicitar_desde_estudiante(db: Session, estudiante_id: str, datos: dict) -> dict:
        """
        El estudiante propone una cita. Si tiene psicólogo asignado
        (`User.psicologo_id`), va a él; si no, queda con `psicologo_id=NULL`
        para que el psicólogo de guardia la tome.
        """
        estudiante = db.query(User).filter(User.id == estudiante_id).first()
        if not estudiante:
            raise ValueError("Estudiante no encontrado")

        cita = Cita(
            psicologo_id=getattr(estudiante, "psicologo_id", None) or None,
            estudiante_id=estudiante_id,
            fecha=datos["fecha"],
            hora=datos["hora"],
            modalidad=datos.get("modalidad", "presencial"),
            notas=datos.get("motivo") or datos.get("notas"),
            estado="pendiente",
        )
        db.add(cita)
        db.commit()
        db.refresh(cita)
        logger.info(f"Estudiante {estudiante_id} solicitó cita {cita.id}")
        return _enriquecer(cita, db)

    @staticmethod
    def listar_estudiante(db: Session, estudiante_id: str) -> list:
        citas = (db.query(Cita)
                   .filter(Cita.estudiante_id == estudiante_id)
                   .order_by(Cita.fecha.asc(), Cita.hora.asc())
                   .all())
        return [_enriquecer(c, db) for c in citas]
