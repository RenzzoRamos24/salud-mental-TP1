from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class RiskResult(Base):
    """Resultado del análisis de riesgo"""
    __tablename__ = "risk_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("user_sessions.id"), unique=True, index=True)
    user_id = Column(String(100), index=True, nullable=False)
    nivel_riesgo = Column(String(50))
    score = Column(Float)
    explicacion = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("UserSession", back_populates="risk_result")
    
    def __repr__(self):
        return f"<RiskResult {self.id}>"