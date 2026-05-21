from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import (
    AnswerRequest,
    AnswerResponse,
    AnalysisResponse,
    ConversationResponse,
    StartSessionResponse,
)
from app.services.chat_service import ChatService
from app.services.consent_service import ConsentService
from app.core.deps import get_current_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chatbot"])


def _exigir_consentimiento(db: Session, user_id: str):
    estado = ConsentService.estado(db, user_id)
    if not estado["aceptado"]:
        raise HTTPException(
            status_code=403,
            detail="Debes aceptar el consentimiento informado antes de iniciar.",
        )


# ─────────────────────────────────────────────────────────────────
# ENDPOINT 1: Iniciar sesión de evaluación
# ─────────────────────────────────────────────────────────────────

@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Inicia una nueva sesión de evaluación.
    El user_id y nombre se toman del JWT (no del body).
    """
    _exigir_consentimiento(db, current_user.id)
    try:
        logger.info(f"POST /start - Usuario: {current_user.email}")
        resultado = ChatService.crear_sesion(
            db=db,
            user_id=current_user.id,
            nombre=current_user.nombre,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        logger.info(
            f"POST /answer - Session: {request.session_id} "
            f"(score_likert={request.score_likert})"
        )
        resultado = ChatService.guardar_respuesta_y_avanzar(
            db=db,
            session_id=request.session_id,
            respuesta=request.respuesta,
            score_likert=request.score_likert,
        )
        return AnswerResponse(**resultado)
    except ValueError as ve:
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"POST /analizar - Session: {session_id}")
        resultado = ChatService.analizar_sesion(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
        )
        return AnalysisResponse(**resultado)
    except ValueError as ve:
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        logger.info(f"GET /conversacion - Session: {session_id}")
        resultado = ChatService.obtener_conversacion(db=db, session_id=session_id)
        return ConversationResponse(**resultado)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error en /conversacion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# ENDPOINT 5: Historial emocional propio del estudiante (HU-12)
# ─────────────────────────────────────────────────────────────────

@router.get("/mi-historial")
async def mi_historial(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Devuelve el historial emocional completo del estudiante autenticado.
    Incluye serie temporal, sesiones con conversación y análisis de riesgo.
    """
    from app.services.psychologist_service import PsychologistService
    try:
        return PsychologistService.historial_estudiante(db, str(current_user.id))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error en /mi-historial: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# ENDPOINT 6: Health check (público)
# ─────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "servicio": "chatbot",
        "version": "1.0.0",
    }


# ─────────────────────────────────────────────────────────────────
# HU-30: el ESTUDIANTE agenda cita desde el chatbot
# ─────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field  # noqa: E402
from typing import Optional  # noqa: E402
from app.services.cita_service import CitaService  # noqa: E402


class CitaEstudianteIn(BaseModel):
    fecha: str = Field(..., description="YYYY-MM-DD")
    hora: str = Field(..., description="HH:MM")
    modalidad: str = Field("presencial", pattern="^(presencial|virtual)$")
    motivo: Optional[str] = Field(None, max_length=500)


@router.post("/cita", status_code=201)
async def solicitar_cita_estudiante(
    payload: CitaEstudianteIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        cita = CitaService.solicitar_desde_estudiante(db, current_user.id, payload.model_dump())
        return {
            "ok": True,
            "cita_id": cita["id"],
            "estado": cita["estado"],
            "mensaje": (
                "Solicitud enviada. El psicólogo/a del colegio la confirmará pronto. "
                "Te avisaremos por correo."
            ),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/citas/mias")
async def listar_mis_citas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CitaService.listar_estudiante(db, current_user.id)
