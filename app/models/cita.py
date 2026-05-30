from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Cita(Base):
    """Cita agendada entre psicólogo y estudiante (HU-19)."""
    __tablename__ = "citas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    psicologo_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    estudiante_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    fecha = Column(String(10), nullable=False)   # "YYYY-MM-DD"
    hora = Column(String(5), nullable=False)      # "HH:MM"
    # presencial | virtual
    modalidad = Column(String(20), nullable=False, default="presencial")
    # pendiente | confirmada | cancelada | completada
    estado = Column(String(20), nullable=False, default="pendiente")
    notas = Column(Text, nullable=True)
    # Resumen breve que el alumno SÍ ve en su panel "Mi proceso" tras
    # marcar la cita como completada. Distinto de las notas clínicas
    # privadas (clinical_notes) y de notas internas (notas).
    resumen_para_estudiante = Column(Text, nullable=True)
    completada_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # True si esta cita fue agendada como atención de crisis (escala suicida,
    # bullying, violencia familiar). Cuando se completa, ADELANTA el cierre
    # del ciclo en curso del estudiante. Las citas regulares (False) corren
    # en paralelo al ciclo sin afectarlo.
    es_crisis = Column(Boolean, nullable=False, default=False)

    psicologo = relationship("User", foreign_keys=[psicologo_id])
    estudiante = relationship("User", foreign_keys=[estudiante_id])

    def __repr__(self):
        return f"<Cita {self.id} {self.fecha} {self.hora}>"
