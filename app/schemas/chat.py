from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ═════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═════════════════════════════════════════════════════════════════

class StartSessionRequest(BaseModel):
    """Request para iniciar sesión"""
    user_id: str = Field(..., description="ID único del usuario")
    nombre: str = Field(..., description="Nombre del usuario")


class AnswerRequest(BaseModel):
    """Request para enviar respuesta"""
    session_id: str = Field(..., description="ID de la sesión")
    respuesta: str = Field(..., description="Respuesta del usuario", min_length=1)


# ═════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═════════════════════════════════════════════════════════════════

class StartSessionResponse(BaseModel):
    """Response al iniciar sesión"""
    session_id: str
    pregunta_numero: int
    pregunta: str
    total_preguntas: int
    mensaje: str


class AnswerResponse(BaseModel):
    """Response al enviar respuesta"""
    completado: bool
    pregunta_numero: int
    pregunta: Optional[str] = None
    total_preguntas: int
    progreso: Optional[str] = None
    mensaje: Optional[str] = None
    siguiente_paso: Optional[str] = None


class ConversacionItem(BaseModel):
    """Item de conversación"""
    pregunta_numero: int
    pregunta: str
    respuesta: str


class ConversationResponse(BaseModel):
    """Response de historial de conversación"""
    session_id: str
    usuario: str
    completado: bool
    conversacion: List[ConversacionItem]
    total_respuestas: int


class AnalysisResultado(BaseModel):
    """Resultado del análisis"""
    nivel_riesgo: str
    confianza: str
    explicacion: str


class AnalysisResponse(BaseModel):
    """Response del análisis"""
    session_id: str
    usuario: str
    fecha_analisis: str
    respuestas_analizadas: int
    resultado: AnalysisResultado