from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class UserResponse(Base):
    """Respuesta del usuario a una pregunta"""
    __tablename__ = "user_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("user_sessions.id"), index=True)
    numero_pregunta = Column(Integer, nullable=False)
    pregunta = Column(Text, nullable=False)
    respuesta = Column(Text, nullable=False)
    # Score de criticidad de la respuesta individual (0..1).
    # Calculado por NLPService.analizar_respuesta_individual al cerrar la sesión.
    score_riesgo = Column(Float, nullable=True)
    # Nivel cualitativo derivado del score (BAJO / MEDIO / ALTO / CRÍTICO).
    nivel_riesgo = Column(String(20), nullable=True)
    # Condición clínica con mayor score en esa respuesta (depresion, ansiedad, ...).
    condicion_dominante = Column(String(50), nullable=True)

    # ── PHQ-9 / GAD-7 (escala clínica estructurada) ─────────────────
    # Código del ítem clínico (ej. "phq9_1", "gad7_3").
    item_codigo = Column(String(20), nullable=True, index=True)
    # Módulo al que pertenece el ítem ("PHQ-9" o "GAD-7").
    modulo = Column(String(10), nullable=True, index=True)
    # Criterio DSM-5 que mide este ítem (legible, para reportes al psicólogo).
    criterio_dsm5 = Column(String(200), nullable=True)
    # Puntaje Likert 0-3 (0=nunca, 1=algunos días, 2=más de la mitad, 3=casi todos).
    score_likert = Column(Integer, nullable=True)
    # Confianza del modelo BERT al proponer el score (0..1). NULL si fue manual.
    confianza_likert = Column(Float, nullable=True)
    # Origen del score: "nlp" (propuesto por BERT) | "manual" (botón) | "corregido".
    score_origen = Column(String(20), nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("UserSession", back_populates="responses")

    def __repr__(self):
        return f"<UserResponse {self.id}>"