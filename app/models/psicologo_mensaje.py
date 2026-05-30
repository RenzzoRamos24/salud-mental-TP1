"""
Mensaje breve del psicólogo dirigido a un estudiante específico.

Diferente de `clinical_notes` (que es privado del psicólogo). Este mensaje
sí lo lee el estudiante en su panel de apoyo: una frase / recomendación
puntual que el psicólogo quiere transmitirle entre cita y cita.
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from datetime import datetime
from app.database import Base


class PsicologoMensaje(Base):
    __tablename__ = "psicologo_mensajes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    psicologo_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    estudiante_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    mensaje = Column(Text, nullable=False)

    leido = Column(Boolean, nullable=False, default=False)
    leido_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return (
            f"<PsicologoMensaje {self.id} psi={self.psicologo_id} "
            f"est={self.estudiante_id} leido={self.leido}>"
        )
