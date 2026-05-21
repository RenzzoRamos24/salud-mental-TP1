"""
HU-25: Encuesta de satisfacción del estudiante tras usar el sistema.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.database import Base


class SatisfactionSurvey(Base):
    __tablename__ = "satisfaction_surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)

    # 1-5 estrellas en cada dimensión
    facilidad_uso     = Column(Integer, nullable=False)   # facilidad de la conversación
    utilidad          = Column(Integer, nullable=False)   # cuán útil le fue
    confianza         = Column(Integer, nullable=False)   # privacidad / seguridad
    recomendaria      = Column(Integer, nullable=False)   # NPS-like 1-5
    nivel_animo_post  = Column(Integer, nullable=True)    # cómo se siente DESPUÉS (1-5)

    comentario = Column(Text, nullable=True)
    timestamp  = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SatisfactionSurvey {self.id} user={self.user_id}>"
