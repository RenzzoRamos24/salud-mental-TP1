"""
HU-33: Notas clínicas privadas del psicólogo sobre un estudiante.
Solo el psicólogo autor puede leerlas/editarlas. Nunca son visibles para el estudiante.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.database import Base


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    estudiante_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    psicologo_id  = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    texto = Column(Text, nullable=False)
    # Etiqueta libre (opcional): "primera sesión", "seguimiento", "alerta", etc.
    etiqueta = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ClinicalNote {self.id} est={self.estudiante_id}>"
