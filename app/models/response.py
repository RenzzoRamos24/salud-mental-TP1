from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
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
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("UserSession", back_populates="responses")
    
    def __repr__(self):
        return f"<UserResponse {self.id}>"