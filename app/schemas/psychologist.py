from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class EstudianteResumen(BaseModel):
    """Item de la lista de estudiantes para el dashboard del psicólogo."""
    id: str
    nombre: str
    apellido: str
    email: str
    total_sesiones: int
    sesiones_completadas: int
    total_entradas_diario: int = 0
    ultimo_riesgo: Optional[str] = None  # CRÍTICO/ALTO/MEDIO/BAJO o None
    ultimo_score: Optional[float] = None
    ultima_evaluacion: Optional[datetime] = None
    fuente_ultima: Optional[str] = None  # "chatbot" | "diario" | None


class IntercambioConversacion(BaseModel):
    numero: int
    pregunta: str
    respuesta: str


class SesionHistorial(BaseModel):
    """Una sesión de evaluación con su análisis y conversación."""
    session_id: str
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    estado: str
    nivel_riesgo: Optional[str] = None
    score: Optional[float] = None
    explicacion: Optional[str] = None
    conversacion: List[IntercambioConversacion]


class HistorialEstudiante(BaseModel):
    """Historial completo de un estudiante (HU-20)."""
    estudiante: EstudianteResumen
    sesiones: List[SesionHistorial]
    entradas_diario: List[Dict] = []  # [{id, fecha, texto, analisis}, ...]
    serie_temporal: List[Dict] = []  # [{fecha, nivel, score, fuente}, ...]
