from pydantic import BaseModel, Field, conint
from typing import Optional, List, Dict, Any
from datetime import datetime

# ═════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═════════════════════════════════════════════════════════════════

class StartSessionRequest(BaseModel):
    user_id: str = Field(..., description="ID único del usuario")
    nombre: str = Field(..., description="Nombre del usuario")


class AnswerRequest(BaseModel):
    """
    Request para enviar respuesta.
    - `respuesta`: texto libre del usuario (siempre requerido, aunque sea breve).
    - `score_likert`: 0-3 cuando el usuario eligió uno de los 4 botones.
      Si se provee, el backend lo guarda directamente con origen="manual".
      Si se omite, BERT propone el score y, si no tiene confianza, el
      backend devuelve `requiere_seleccion=true` con los botones.
    """
    session_id: str = Field(..., description="ID de la sesión")
    respuesta: str = Field(..., description="Respuesta del usuario", min_length=1)
    score_likert: Optional[conint(ge=0, le=3)] = Field(
        None, description="Puntaje Likert 0-3 si el usuario eligió un botón"
    )


# ═════════════════════════════════════════════════════════════════
# OPCIONES LIKERT (4 botones)
# ═════════════════════════════════════════════════════════════════

class OpcionLikert(BaseModel):
    valor: int = Field(..., ge=0, le=3)
    etiqueta: str
    descripcion: str


# ═════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═════════════════════════════════════════════════════════════════

class StartSessionResponse(BaseModel):
    session_id: str
    fase: str = "apertura"  # apertura | evaluacion | completada
    pregunta_numero: int
    pregunta: Optional[str] = None  # None mientras fase=apertura
    item_codigo: Optional[str] = None
    modulo: Optional[str] = None
    criterio_dsm5: Optional[str] = None
    opciones_likert: Optional[List[OpcionLikert]] = None
    total_preguntas: int
    mensaje: str


class AnswerResponse(BaseModel):
    """
    Rutas posibles según la fase:
      - fase=evaluacion + completado=true              → terminaron los 16 ítems
      - fase=evaluacion + requiere_seleccion=true      → confianza baja, botones
      - fase=evaluacion + ambos false                  → siguiente pregunta normal
      - Transición apertura→evaluacion: trae `modulos_orden`, `modulo_prioritario`,
        `crisis_inmediata`, etc.
    """
    completado: bool
    requiere_seleccion: bool = False
    fase: Optional[str] = None
    pregunta_numero: int
    pregunta: Optional[str] = None
    item_codigo: Optional[str] = None
    modulo: Optional[str] = None
    criterio_dsm5: Optional[str] = None
    opciones_likert: Optional[List[OpcionLikert]] = None
    score_propuesto: Optional[int] = Field(None, ge=0, le=3)
    confianza: Optional[float] = Field(None, ge=0.0, le=1.0)
    respuesta_usuario: Optional[str] = None
    total_preguntas: int
    progreso: Optional[str] = None
    mensaje: Optional[str] = None
    siguiente_paso: Optional[str] = None

    # ── Devueltos solo en la transición apertura → evaluación ───────
    modulos_orden: Optional[List[str]] = None
    modulo_prioritario: Optional[str] = None
    condiciones_detectadas: Optional[List[str]] = None
    crisis_inmediata: Optional[bool] = None


class ConversacionItem(BaseModel):
    numero: int
    pregunta: str
    respuesta: str
    item_codigo: Optional[str] = None
    modulo: Optional[str] = None
    criterio_dsm5: Optional[str] = None
    score_likert: Optional[int] = None
    score_origen: Optional[str] = None


class ConversationResponse(BaseModel):
    session_id: str
    usuario: str
    completado: bool
    conversacion: List[ConversacionItem]
    total_respuestas: int


# ═════════════════════════════════════════════════════════════════
# ANÁLISIS MULTI-CONDICIÓN + PHQ-9 + GAD-7
# ═════════════════════════════════════════════════════════════════

class CondicionDetectada(BaseModel):
    etiqueta: str
    confianza: float


class AnalysisResultado(BaseModel):
    nivel_riesgo: str
    condiciones_detectadas: Dict[str, CondicionDetectada]
    scores_completos: Dict[str, float]
    explicacion: str
    modelo: str


class EscalaItemDetalle(BaseModel):
    item: str
    criterio_dsm5: Optional[str] = None
    pregunta: str
    respuesta: str
    score: int = Field(..., ge=0, le=3)
    origen: Optional[str] = None


class EscalaResultado(BaseModel):
    total: int
    max: int
    severidad: str
    accion: str
    items: List[EscalaItemDetalle]


class AnalysisResponse(BaseModel):
    session_id: str
    usuario: str
    fecha_analisis: str
    respuestas_analizadas: int
    phq9: EscalaResultado
    gad7: EscalaResultado
    crisis_protocolo: bool = False
    resultado: AnalysisResultado
