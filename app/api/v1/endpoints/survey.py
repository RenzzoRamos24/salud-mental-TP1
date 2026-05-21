"""HU-25: encuesta de satisfacción del estudiante."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, conint
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.services.survey_service import SurveyService

router = APIRouter(tags=["survey"])


class SatisfactionIn(BaseModel):
    facilidad_uso: conint(ge=1, le=5)
    utilidad: conint(ge=1, le=5)
    confianza: conint(ge=1, le=5)
    recomendaria: conint(ge=1, le=5)
    nivel_animo_post: Optional[conint(ge=1, le=5)] = None
    comentario: Optional[str] = Field(None, max_length=2000)


@router.post("/satisfaction", status_code=201)
async def enviar_encuesta(
    payload: SatisfactionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        s = SurveyService.crear(db, user.id, payload.model_dump())
        return {"id": s.id, "mensaje": "¡Gracias por tu feedback!"}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/satisfaction/me")
async def mi_estado(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return {"ya_respondio": SurveyService.existe_para_usuario(db, user.id)}


@router.get("/admin/satisfaction/summary")
async def resumen_admin(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return SurveyService.resumen_admin(db)
