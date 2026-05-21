from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CitaCreate(BaseModel):
    estudiante_id: str
    fecha: str        # YYYY-MM-DD
    hora: str         # HH:MM
    modalidad: str = "presencial"
    notas: Optional[str] = None


class CitaUpdate(BaseModel):
    estado: Optional[str] = None
    notas: Optional[str] = None
    fecha: Optional[str] = None
    hora: Optional[str] = None
    modalidad: Optional[str] = None


class CitaOut(BaseModel):
    id: int
    psicologo_id: str
    estudiante_id: str
    fecha: str
    hora: str
    modalidad: str
    estado: str
    notas: Optional[str] = None
    created_at: datetime
    # Datos del estudiante (se añaden en el servicio)
    estudiante_nombre: Optional[str] = None
    estudiante_apellido: Optional[str] = None
    estudiante_email: Optional[str] = None

    class Config:
        from_attributes = True
