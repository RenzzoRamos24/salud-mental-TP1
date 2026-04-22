class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    user_id = Column(String)
    nivel_riesgo = Column(String)  # bajo/medio/alto
    confianza = Column(Float)  # 83.6
    fecha_analisis = Column(DateTime)
    timestamp_creacion = Column(DateTime, default=datetime.utcnow)