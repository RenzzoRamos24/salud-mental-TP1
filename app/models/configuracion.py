from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base


class Configuracion(Base):
    """Almacén clave-valor JSON para configuración dinámica del sistema (Sprint 6)."""
    __tablename__ = "configuraciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(Text, nullable=False)   # JSON serializado
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Configuracion {self.clave}>"


class ConfiguracionCambio(Base):
    """Auditoría de cambios de parámetros generales (QA CP063, HU0021).

    Una fila por cambio efectivo: qué clave, valor anterior y nuevo, quién y cuándo.
    Nunca se edita ni se borra desde la aplicación.
    """
    __tablename__ = "configuracion_cambios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    clave = Column(String(100), nullable=False, index=True)
    valor_anterior = Column(Text, nullable=False)
    valor_nuevo = Column(Text, nullable=False)
    usuario_id = Column(String(36), nullable=True)
    usuario_email = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
