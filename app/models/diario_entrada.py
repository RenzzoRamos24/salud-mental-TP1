"""
Entradas del diario digital del estudiante.

Reemplaza conceptualmente al chatbot: en lugar de 16 respuestas a preguntas
estructuradas (PHQ-9 + GAD-7), el estudiante escribe texto libre. El análisis
clínico con BETO se aplica sobre ese texto en una fase posterior.

Esta tabla coexiste con `user_sessions` y `user_responses`: el chatbot sigue
funcionando como respaldo y no comparte FKs con esta tabla.
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from datetime import datetime, date
from app.database import Base


class DiarioEntrada(Base):
    __tablename__ = "diario_entradas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(36),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # Texto narrativo libre del estudiante
    texto = Column(Text, nullable=False)

    # Mood elegido por el estudiante al guardar (NO clínico).
    # "soleado" | "mixto" | "nublado" | "lluvioso" | NULL
    estado_animo = Column(String(20), nullable=True)

    # Prompt suave que se le mostró ese día (para contexto del psicólogo).
    prompt_del_dia = Column(String(500), nullable=True)

    # Fecha "calendario" del día de la entrada (sin hora) — facilita filtros.
    fecha = Column(Date, nullable=False, default=date.today, index=True)

    # Momento exacto del guardado.
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Enlace al análisis BETO. Queda NULL hasta que el Paso 2 lo llene.
    # No se usa como FK estricta para no acoplar todavía.
    analisis_id = Column(Integer, nullable=True, index=True)

    def __repr__(self):
        return f"<DiarioEntrada {self.id} user={self.user_id} fecha={self.fecha}>"
