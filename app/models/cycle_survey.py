"""
Encuesta clínica de cierre de ciclo (PHQ-A + GAD-7).

Al cumplirse el día 14 del ciclo del diario, el estudiante debe responder
las 16 preguntas (9 del PHQ-A para depresión adolescente + 7 del GAD-7 para
ansiedad) en escala Likert 0–3. El resultado se guarda como reporte clínico
del ciclo y queda disponible para la psicóloga.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Boolean, ForeignKey
from datetime import datetime
from app.database import Base


class CycleSurvey(Base):
    __tablename__ = "cycle_surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Ciclo al que pertenece (cerrado o el actual ya vencido).
    ciclo_numero = Column(Integer, nullable=False)
    ciclo_inicio = Column(Date, nullable=False)
    ciclo_fin = Column(Date, nullable=False)

    # Ventana de respuesta
    iniciada_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completada_at = Column(DateTime, nullable=True)

    # Respuestas crudas: { "phq9_1": 2, "phq9_2": 1, ... } como JSON.
    respuestas_json = Column(Text, nullable=True)

    # Totales calculados al cerrar.
    phq9_total = Column(Integer, nullable=True)   # 0-27
    gad7_total = Column(Integer, nullable=True)   # 0-21
    phq9_severidad = Column(String(30), nullable=True)
    gad7_severidad = Column(String(30), nullable=True)
    # PHQ-9 ítem 9 ≥ 1 → protocolo de crisis activado.
    crisis_protocolo = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        estado = "completada" if self.completada_at else "pendiente"
        return f"<CycleSurvey user={self.user_id} ciclo={self.ciclo_numero} {estado}>"
