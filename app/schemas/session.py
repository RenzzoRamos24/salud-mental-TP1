from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "bajo"
    MEDIUM = "medio"
    HIGH = "alto"

# ===== START SESSION =====
class StartSessionRequest(BaseModel):
    user_id: str
    nombre: Optional[str] = None

class StartSessionResponse(BaseModel):
    session_id: str
    user_id: str
    pregunta_actual: str
    numero_pregunta: int
    total_preguntas: int

# ===== ANSWER =====
class AnswerRequest(BaseModel):
    session_id: str
    respuesta: str

class AnswerResponse(BaseModel):
    session_id: str
    numero_pregunta: int
    total_preguntas: int
    pregunta_siguiente: Optional[str] = None
    completado: bool

# ===== ANALYZE =====
class AnalizeRequest(BaseModel):
    session_id: str

class RiskAnalysisResult(BaseModel):
    session_id: str
    user_id: str
    nivel_riesgo: RiskLevel
    score: float
    explicacion: str
    timestamp: datetime

# ===== HISTORY =====
class PreguntaRespuesta(BaseModel):
    numero: int
    pregunta: str
    respuesta: str

class ConversationHistory(BaseModel):
    session_id: str
    preguntas_respuestas: List[PreguntaRespuesta]
    timestamp: datetime