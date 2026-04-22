from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False)
    nivel_riesgo = Column(String, nullable=False)  # bajo, medio, alto
    confianza = Column(Float, nullable=False)  # 83.6
    fecha_analisis = Column(DateTime, default=datetime.utcnow)