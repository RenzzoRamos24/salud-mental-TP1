"""Schemas Pydantic del Diario digital."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────
# REQUEST
# ─────────────────────────────────────────────────────────────────────────

class DiarioEntradaIn(BaseModel):
    """Lo que envía el estudiante al guardar una entrada."""
    texto: str = Field(..., min_length=1, max_length=20000)
    estado_animo: Optional[str] = Field(
        None,
        pattern="^(soleado|mixto|nublado|lluvioso)$",
        description="Mood elegido por el estudiante. NO es clínico.",
    )
    prompt_del_dia: Optional[str] = Field(None, max_length=500)


# ─────────────────────────────────────────────────────────────────────────
# RESPONSE
# ─────────────────────────────────────────────────────────────────────────

class DiarioEntradaResumen(BaseModel):
    """Para el listado del propio estudiante (sin texto completo)."""
    id: int
    fecha: date
    timestamp: datetime
    estado_animo: Optional[str] = None
    preview: str

    class Config:
        from_attributes = True


class DiarioEntradaOut(BaseModel):
    """Detalle completo de una entrada."""
    id: int
    fecha: date
    timestamp: datetime
    estado_animo: Optional[str] = None
    prompt_del_dia: Optional[str] = None
    texto: str

    class Config:
        from_attributes = True
