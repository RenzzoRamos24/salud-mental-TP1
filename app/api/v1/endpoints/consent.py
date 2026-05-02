"""
Endpoints de consentimiento informado (HU-03).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.consent import AceptarConsentimientoRequest, ConsentimientoEstado
from app.services.consent_service import ConsentService
from app.core.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/aceptar", response_model=ConsentimientoEstado)
async def aceptar_consentimiento(
    req: AceptarConsentimientoRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        ip = request.client.host if request.client else None
        ConsentService.aceptar(
            db=db, user_id=current_user.id, version=req.version, ip_address=ip
        )
        return ConsentService.estado(db, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/estado", response_model=ConsentimientoEstado)
async def estado_consentimiento(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ConsentService.estado(db, current_user.id)
