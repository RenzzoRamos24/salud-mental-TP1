from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EstudianteResumen(BaseModel):
    id: str
    nombre: str
    apellido: str
    email: str
    total_cuestionarios: int = 0
    ultimo_riesgo: Optional[str] = None
    ultima_evaluacion: Optional[str] = None
    crisis_activada: bool = False
    estado_caso: Optional[str] = None
    psicologo_id: Optional[str] = None
    grado: Optional[str] = None


class AplicacionResumen(BaseModel):
    id: int
    plantilla_id: int
    estado: str
    riesgo_global: Optional[str] = None
    crisis_activada: bool = False
    asignada_at: Optional[str] = None
    completada_at: Optional[str] = None


class HistorialEstudiante(BaseModel):
    estudiante: dict
    aplicaciones: List[dict]
