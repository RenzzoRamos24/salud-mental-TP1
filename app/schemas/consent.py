from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AceptarConsentimientoRequest(BaseModel):
    version: str


class ConsentimientoEstado(BaseModel):
    aceptado: bool
    version: Optional[str] = None
    aceptado_en: Optional[datetime] = None
    version_actual: str

    model_config = {"from_attributes": True}
