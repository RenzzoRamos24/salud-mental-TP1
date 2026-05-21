"""HU-31: botón SOS — registra el evento para que el psicólogo lo audite."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from app.models.sos_event import SosEvent


class SosService:

    @staticmethod
    def registrar(db: Session, user_id: str, origen: str = None, mensaje: str = None) -> SosEvent:
        ev = SosEvent(
            user_id=user_id,
            origen=origen,
            mensaje=(mensaje or "").strip() or None,
        )
        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev

    @staticmethod
    def listar_abiertos(db: Session, limit: int = 50) -> list[dict]:
        eventos = (db.query(SosEvent)
                     .filter(SosEvent.estado == "abierto")
                     .order_by(desc(SosEvent.timestamp))
                     .limit(limit)
                     .all())
        return [SosService._serializar(e) for e in eventos]

    @staticmethod
    def marcar_atendido(db: Session, event_id: int, atendido_por: str) -> bool:
        ev = db.query(SosEvent).filter(SosEvent.id == event_id).first()
        if not ev:
            return False
        ev.estado = "atendido"
        ev.atendido_por = atendido_por
        ev.atendido_en = datetime.utcnow()
        db.commit()
        return True

    @staticmethod
    def _serializar(e: SosEvent) -> dict:
        return {
            "id": e.id,
            "user_id": e.user_id,
            "origen": e.origen,
            "mensaje": e.mensaje,
            "estado": e.estado,
            "timestamp": e.timestamp.isoformat(),
            "atendido_por": e.atendido_por,
            "atendido_en": e.atendido_en.isoformat() if e.atendido_en else None,
        }
