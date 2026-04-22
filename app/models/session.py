from sqlalchemy import Column, String, Integer, DateTime
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
    
    responses = relationship("UserResponse", back_populates="session")
    risk_result = relationship("RiskResult", back_populates="session", uselist=False)
    
    def __repr__(self):
        return f"<UserSession {self.id}>"