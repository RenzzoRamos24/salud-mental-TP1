"""
Análisis clínico (BETO) de una entrada del diario.

Vive en su propia tabla para no mezclarse con `risk_results` (que pertenece
al flujo del chatbot 1-1 con `user_sessions`). Reutiliza la misma semántica
de scoring (PHQ-9, GAD-7, nivel de riesgo, crisis) pero adaptada al texto
narrativo libre.

NUNCA se expone al estudiante. Solo el psicólogo y el admin lo ven.
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from datetime import datetime
from app.database import Base


class DiarioAnalisis(Base):
    __tablename__ = "diario_analisis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entrada_id = Column(
        Integer,
        ForeignKey("diario_entradas.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    user_id = Column(String(36), index=True, nullable=False)

    # ── Resultado global ────────────────────────────────────────────
    nivel_riesgo = Column(String(20), nullable=False)
    score = Column(Float, nullable=True)
    explicacion = Column(Text, nullable=True)

    # ── PHQ-9 / GAD-7 inferidos desde texto libre ───────────────────
    phq9_total = Column(Integer, nullable=True)        # 0-27
    gad7_total = Column(Integer, nullable=True)        # 0-21
    phq9_severidad = Column(String(30), nullable=True)
    gad7_severidad = Column(String(30), nullable=True)
    crisis_protocolo = Column(Boolean, nullable=False, default=False)

    # ── Estructuras detalladas (JSON serializado en Text) ───────────
    # condiciones_detectadas: {"depresion": {"etiqueta": "...", "confianza": 78.3}, ...}
    condiciones_detectadas_json = Column(Text, nullable=True)
    # scores_completos: {"depresion": 78.3, "ansiedad": 45.2, ...}
    scores_completos_json = Column(Text, nullable=True)
    # items_detectados: [{"item": "phq9_3", "modulo": "PHQ-9",
    #                     "criterio_dsm5": "...", "score": 2,
    #                     "confianza": 0.62, "keywords": ["no puedo dormir"]}, ...]
    items_detectados_json = Column(Text, nullable=True)

    # ── Metadata del modelo ─────────────────────────────────────────
    modelo = Column(String(120), nullable=True)
    tiempo_inferencia = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return (
            f"<DiarioAnalisis {self.id} entrada={self.entrada_id} "
            f"nivel={self.nivel_riesgo}>"
        )
