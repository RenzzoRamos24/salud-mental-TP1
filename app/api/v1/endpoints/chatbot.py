from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import (
    StartSessionRequest,
    StartSessionResponse,
    AnswerRequest,
    AnswerResponse,
    AnalysisResponse,
    ConversationResponse
)
from app.services.chat_service import ChatService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chatbot"])

# ─────────────────────────────────────────────────────────────────
# ENDPOINT 1: Iniciar sesión
# ─────────────────────────────────────────────────────────────────

@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Inicia una nueva sesión de evaluación de bienestar emocional.
    
    **Responsabilidad del endpoint:**
    - Validar entrada (FastAPI lo hace automáticamente)
    - Delegar a ChatService
    - Retornar respuesta formateada
    
    **Responsabilidad de ChatService:**
    - Crear sesión
    - Obtener primera pregunta
    - Guardar en BD
    """
    try:
        logger.info(f"POST /start - Usuario: {request.user_id}")
        
        resultado = ChatService.crear_sesion(
            db=db,
            user_id=request.user_id,
            nombre=request.nombre
        )
        
        return StartSessionResponse(**resultado)
    
    except Exception as e:
        logger.error(f"Error en /start: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# ENDPOINT 2: Enviar respuesta y avanzar
# ─────────────────────────────────────────────────────────────────

@router.post("/answer", response_model=AnswerResponse)
async def answer_question(
    request: AnswerRequest,
    db: Session = Depends(get_db)
):
    """
    Recibe respuesta del usuario y avanza a la siguiente pregunta.
    
    **Responsabilidad del endpoint:**
    - Validar entrada
    - Delegar a ChatService
    - Retornar siguiente pregunta o mensaje de finalización
    
    **Responsabilidad de ChatService:**
    - Guardar respuesta en BD
    - Determinar siguiente pregunta
    - Detectar si se completó la evaluación
    """
    try:
        logger.info(f"POST /answer - Session: {request.session_id}")
        
        resultado = ChatService.guardar_respuesta_y_avanzar(
            db=db,
            session_id=request.session_id,
            respuesta=request.respuesta
        )
        
        return AnswerResponse(**resultado)
    
    except ValueError as ve:
        logger.error(f"Validación error en /answer: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error en /answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# ENDPOINT 3: Analizar sesión completada
# ─────────────────────────────────────────────────────────────────

@router.post("/analizar", response_model=AnalysisResponse)
async def analizar_sesion(
    session_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Analiza una sesión completada y devuelve resultado de evaluación.
    
    **Responsabilidad del endpoint:**
    - Validar entrada
    - Delegar a ChatService
    - Retornar resultado
    
    **Responsabilidad de ChatService:**
    - Obtener respuestas de BD
    - Orquestar análisis NLP
    
    **Responsabilidad de NLPService:**
    - Análisis semántico con modelo XLM-RoBERTa
    - Clasificación de riesgo
    - Generación de explicación
    """
    try:
        logger.info(f"POST /analizar - Session: {session_id}")
        
        resultado = ChatService.analizar_sesion(
            db=db,
            session_id=session_id,
            user_id=user_id
        )
        
        return AnalysisResponse(**resultado)
    
    except ValueError as ve:
        logger.error(f"Validación error en /analizar: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error en /analizar: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# ENDPOINT 4: Obtener historial de conversación
# ─────────────────────────────────────────────────────────────────

@router.get("/conversacion/{session_id}", response_model=ConversationResponse)
async def obtener_conversacion(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial completo de una sesión.
    
    **Responsabilidad del endpoint:**
    - Validar entrada
    - Delegar a ChatService
    - Retornar historial
    
    **Responsabilidad de ChatService:**
    - Obtener respuestas de BD
    - Reconstruir conversación
    """
    try:
        logger.info(f"GET /conversacion - Session: {session_id}")
        
        resultado = ChatService.obtener_conversacion(
            db=db,
            session_id=session_id
        )
        
        return ConversationResponse(**resultado)
    
    except ValueError as ve:
        logger.error(f"Validación error en /conversacion: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error en /conversacion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# ENDPOINT 5: Health check
# ─────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """
    Verifica que el servicio está operacional.
    """
    return {
        "status": "healthy",
        "servicio": "chatbot",
        "version": "1.0.0"
    }