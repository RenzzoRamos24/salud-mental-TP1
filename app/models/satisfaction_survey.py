"""
HU-25: Encuesta de satisfacción del estudiante tras responder un cuestionario.

Las 5 dimensiones siguen el instrumento de validación de usabilidad/UX
(escala Likert 1-5): facilidad de uso, claridad de la comunicación, utilidad
y pertinencia de las preguntas, fluidez sin dificultades, satisfacción general.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.database import Base


class SatisfactionSurvey(Base):
    __tablename__ = "satisfaction_surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)

    # 1-5 en cada dimensión
    facilidad_uso         = Column(Integer, nullable=False)  # ¿fue fácil usar y entender el cuestionario?
    claridad               = Column(Integer, nullable=False)  # ¿fueron claras las preguntas?
    utilidad               = Column(Integer, nullable=False)  # ¿consideras pertinentes las preguntas?
    fluidez                = Column(Integer, nullable=False)  # ¿pudiste responder sin dificultades?
    satisfaccion_general   = Column(Integer, nullable=False)  # ¿satisfecho con la experiencia?

    comentario = Column(Text, nullable=True)
    timestamp  = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SatisfactionSurvey {self.id} user={self.user_id}>"
