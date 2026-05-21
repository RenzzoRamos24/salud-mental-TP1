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
