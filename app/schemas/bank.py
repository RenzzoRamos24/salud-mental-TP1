"""Pydantic schemas para el banco de instrumentos, bloques custom, plantillas
y aplicaciones."""
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ── Banco fijo ──────────────────────────────────────────────────────────────


class BankItemOut(BaseModel):
    numero: int
    texto: str
    inverso: int = 0
    criterio_dsm5: Optional[str] = None
    bandera_crisis: int = 0


class BankInstrumentoOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    autor: str
    anio: int
    dominio: str
    tipo_escala: str
    likert_min: Optional[int] = None
    likert_max: Optional[int] = None
    n_items: int
    tiempo_min: Optional[int] = None
    instruccion: Optional[str] = None
    citacion: str
    validacion_es: Optional[str] = None
    items: Optional[List[BankItemOut]] = None


class BankFraseOut(BaseModel):
    numero: int
    area: str
    texto: str


# ── Bloque custom ───────────────────────────────────────────────────────────


class BloqueCustomItemIn(BaseModel):
    numero: int = Field(..., ge=1)
    texto: str = Field(..., min_length=1, max_length=500)
    inverso: int = 0


class BloqueCustomIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    dominio: Optional[str] = Field(None, max_length=80)
    tipo_escala: str = Field(..., pattern="^(likert|binaria)$")
    likert_min: int = 0
    likert_max: int = 3
    instruccion: Optional[str] = None
    corte_sin_alerta_max: int
    corte_posible_max: int
    corte_alto_max: int
    items: List[BloqueCustomItemIn] = Field(..., min_length=1)


class BloqueCustomItemOut(BaseModel):
    numero: int
    texto: str
    inverso: int


class BloqueCustomOut(BaseModel):
    id: int
    psicologo_id: str
    nombre: str
    dominio: Optional[str]
    tipo_escala: str
    likert_min: int
    likert_max: int
    instruccion: Optional[str]
    corte_sin_alerta_max: int
    corte_posible_max: int
    corte_alto_max: int
    n_items: int
    activo: int
    items: List[BloqueCustomItemOut] = []


# ── Plantilla ───────────────────────────────────────────────────────────────


class PlantillaBloqueIn(BaseModel):
    orden: int = 0
    tipo: str = Field(..., pattern="^(instrumento|custom|frases)$")
    instrumento_id: Optional[int] = None
    bloque_custom_id: Optional[int] = None
    frases_areas: Optional[List[str]] = None


class PlantillaIn(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = None
    bloques: List[PlantillaBloqueIn] = Field(..., min_length=1)


class PlantillaBloqueOut(BaseModel):
    id: int
    orden: int
    tipo: str
    instrumento_id: Optional[int] = None
    bloque_custom_id: Optional[int] = None
    frases_areas: Optional[List[str]] = None


class PlantillaOut(BaseModel):
    id: int
    psicologo_id: str
    nombre: str
    descripcion: Optional[str]
    activa: int
    created_at: datetime
    bloques: List[PlantillaBloqueOut] = []


# ── Asignación / respuesta ──────────────────────────────────────────────────


class AsignarCuestionarioIn(BaseModel):
    plantilla_id: int
    estudiante_id: str


class PreguntaRender(BaseModel):
    """Una pregunta tal como la ve el alumno."""
    origen: str
    bloque_codigo: str  # ej. "PHQ-A", "CUSTOM:5", "FRASES"
    bloque_nombre: str
    tipo: str           # 'likert' | 'binaria' | 'texto'
    likert_min: Optional[int] = None
    likert_max: Optional[int] = None
    texto: str


class AplicacionEstudianteOut(BaseModel):
    id: int
    plantilla_id: int
    plantilla_nombre: str
    estado: str
    asignada_at: datetime
    completada_at: Optional[datetime]
    n_preguntas: int


class RespuestaIn(BaseModel):
    origen: str
    valor_num: Optional[int] = None
    valor_texto: Optional[str] = None


class EnviarRespuestasIn(BaseModel):
    respuestas: List[RespuestaIn]


class BloqueResultado(BaseModel):
    codigo: str
    nombre: str
    dominio: str
    puntaje: int
    rango_max: int
    severidad: str
    bandera_crisis: bool = False


class FraseAnalisis(BaseModel):
    area: str
    pregunta: str
    respuesta: str
    dominante: Optional[str]
    detectadas: List[str]
    crisis: bool


class ResultadoAplicacionOut(BaseModel):
    id: int
    estudiante_id: str
    plantilla_id: int
    estado: str
    completada_at: Optional[datetime]
    riesgo_global: str
    crisis_activada: bool
    bloques: List[BloqueResultado] = []
    frases: List[FraseAnalisis] = []
    n_señales: int = 0
