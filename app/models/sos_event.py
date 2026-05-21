"""
HU-31: Registro de pulsaciones del botón SOS por parte del estudiante.
Permite al psicólogo/admin auditar momentos de crisis.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.database import Base


class SosEvent(Base):
    __tablename__ = "sos_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    # Origen: "menu" | "chat" | "resultados" | "historial"
    origen = Column(String(20), nullable=True)
    # Mensaje opcional escrito por el estudiante al activar SOS
    mensaje = Column(Text, nullable=True)
    # "abierto" | "atendido" | "cerrado"
    estado = Column(String(20), nullable=False, default="abierto", index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    atendido_por = Column(String(36), nullable=True)
    atendido_en = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<SosEvent {self.id} user={self.user_id} estado={self.estado}>"
