from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class UserSession(Base):
    """Sesión de usuario en el chatbot"""
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    nombre = Column(String(255), nullable=True)
    estado = Column(String(50), default="activa")
    pregunta_actual = Column(Integer, default=0)
    timestamp_inicio = Column(DateTime, default=datetime.utcnow)
    timestamp_fin = Column(DateTime, nullable=True)

    # ── Fase conversacional ──────────────────────────────────────────
    # "apertura"   → el bot saludó y espera la introducción libre del usuario.
    # "evaluacion" → ya hicimos triage, vamos por los 16 ítems en el orden de
    #                `modulos_orden`.
    # "completada" → equivalente a estado="completada" en la lectura, pero
    #                explícito para el flujo conversacional.
    fase = Column(String(20), default="apertura", nullable=False)
    # Orden en que se aplicarán los módulos clínicos, decidido por el AI
    # provider en el triage. Ej: "PHQ-9,GAD-7" o "GAD-7,PHQ-9".
    modulos_orden = Column(String(50), nullable=True)
    # Texto libre con el que el usuario inició la conversación.
    apertura_texto = Column(Text, nullable=True)

    responses = relationship("UserResponse", back_populates="session")
    risk_result = relationship("RiskResult", back_populates="session", uselist=False)

    def __repr__(self):
        return f"<UserSession {self.id}>"