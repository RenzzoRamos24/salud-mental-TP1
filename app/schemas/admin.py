from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UsuarioResumen(BaseModel):
    id: str
    email: str
    nombre: str
    apellido: str
    role: str
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StatsUsuarios(BaseModel):
    total: int
    estudiantes: int
    psicologos: int
    admins: int
    activos: int
    inactivos: int
