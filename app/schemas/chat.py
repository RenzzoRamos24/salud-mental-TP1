from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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
    numero: int
    pregunta: str
    respuesta: str


class ConversationResponse(BaseModel):
    """Response de historial de conversación"""
    session_id: str
    usuario: str
    completado: bool
    conversacion: List[ConversacionItem]
    total_respuestas: int


# ═════════════════════════════════════════════════════════════════
# ANÁLISIS MULTI-CONDICIÓN
# ═════════════════════════════════════════════════════════════════

class CondicionDetectada(BaseModel):
    """Una condición clínica detectada con su nivel de confianza"""
    etiqueta: str = Field(..., description="Nombre legible de la condición")
    confianza: float = Field(..., description="Confianza del modelo (0-100)")


class AnalysisResultado(BaseModel):
    """Resultado detallado del análisis multi-condición"""
    nivel_riesgo: str = Field(..., description="CRÍTICO | ALTO | MEDIO | BAJO")
    condiciones_detectadas: Dict[str, CondicionDetectada] = Field(
        ..., description="Mapa clave→condición detectada con confianza"
    )
    scores_completos: Dict[str, float] = Field(
        ..., description="Scores (%) de TODAS las condiciones evaluadas"
    )
    explicacion: str = Field(..., description="Interpretación clínica en español")
    modelo: str = Field(..., description="Modelo BERT usado")


class AnalysisResponse(BaseModel):
    """Response completa del análisis"""
    session_id: str
    usuario: str
    fecha_analisis: str
    respuestas_analizadas: int
    resultado: AnalysisResultado
