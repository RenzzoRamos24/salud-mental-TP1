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
    # Sprint 8
    psicologo_id: Optional[str] = None
    estado_caso: Optional[str] = None
    grado: Optional[str] = None

    model_config = {"from_attributes": True}


class StatsUsuarios(BaseModel):
    total: int
    estudiantes: int
    psicologos: int
    admins: int
    activos: int
    inactivos: int
