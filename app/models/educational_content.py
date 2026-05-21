"""
HU-29 + HU-40: Contenido psicoeducativo (artículos, videos, infografías).
El admin lo gestiona (CRUD). El estudiante lo consume desde /recursos.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from datetime import datetime
from app.database import Base


class EducationalContent(Base):
    __tablename__ = "educational_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    # "articulo" | "video" | "infografia" | "audio"
    tipo = Column(String(20), nullable=False, index=True, default="articulo")
    # "ansiedad" | "depresion" | "estres" | "sueño" | "autocuidado" | "crisis"
    categoria = Column(String(30), nullable=True, index=True)
    url = Column(String(500), nullable=True)         # Link externo (YouTube, PDF…)
    contenido = Column(Text, nullable=True)          # Cuerpo si es artículo inline
    autor = Column(String(120), nullable=True)
    icono = Column(String(10), nullable=True, default="📄")
    activo = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EducationalContent {self.id} {self.titulo}>"
