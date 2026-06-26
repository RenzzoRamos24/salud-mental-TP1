"""
Endpoints de gestión de cuenta del usuario (HU-04, HU-05).
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UpdateProfileRequest, ChangePasswordRequest, DeleteAccountRequest
from app.schemas.auth import UserPublic, MensajeResponse
from app.schemas.cita import CitaOut, CitaSolicitudEstudiante
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.cita_service import CitaService
from app.core.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


def _user_a_publico(user: User, db: Session) -> dict:
    consent = AuthService.obtener_consentimiento_actual(db, user.id)
    return {
        "id": user.id,
        "email": user.email,
        "nombre": user.nombre,
        "apellido": user.apellido,
        "role": user.role,
        "activo": user.activo,
        "created_at": user.created_at,
        "consentimiento_aceptado": consent is not None,
        "consentimiento_version": consent.version if consent else None,
    }


# HU-04: actualizar datos personales
@router.put("/me", response_model=UserPublic)
async def actualizar_perfil(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = UserService.actualizar_perfil(
        db=db, user=current_user, nombre=req.nombre, apellido=req.apellido
    )
    return _user_a_publico(user, db)


# HU-04: cambiar contraseña (gestión de cuenta)
@router.put("/me/password", response_model=MensajeResponse)
async def cambiar_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        UserService.cambiar_password(
            db=db, user=current_user,
            password_actual=req.password_actual,
            nueva_password=req.nueva_password,
        )
        return MensajeResponse(mensaje="Contraseña actualizada correctamente")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Citas del estudiante ─────────────────────────────────────────
@router.get("/me/citas", response_model=List[CitaOut])
async def mis_citas(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return CitaService.listar_estudiante(db, current_user.id)


@router.post("/me/citas", response_model=CitaOut, status_code=201)
async def solicitar_cita(
    payload: CitaSolicitudEstudiante,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return CitaService.solicitar_desde_estudiante(
            db, current_user.id, payload.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/me/slots-sugeridos")
async def slots_sugeridos(
    cantidad: int = 4,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Horarios sugeridos para agendar (descarta los que el psicólogo ya tiene ocupados)."""
    return CitaService.slots_sugeridos(db, current_user.id, cantidad=cantidad)


@router.get("/me/psicologo")
async def mi_psicologo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Datos básicos del psicólogo asignado al estudiante."""
    if not current_user.psicologo_id:
        return {"asignado": False}
    p = db.query(User).filter(User.id == current_user.psicologo_id).first()
    if not p:
        return {"asignado": False}
    return {
        "asignado": True,
        "id": p.id,
        "nombre": p.nombre,
        "apellido": p.apellido,
        "email": p.email,
    }


# HU-05: eliminar cuenta
@router.delete("/me", response_model=MensajeResponse)
async def eliminar_cuenta(
    req: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.confirmacion.strip().upper() != "ELIMINAR":
        raise HTTPException(
            status_code=400,
            detail='Debes escribir "ELIMINAR" en mayúsculas para confirmar',
        )
    try:
        UserService.eliminar_cuenta(db=db, user=current_user, password=req.password)
        return MensajeResponse(
            mensaje="Tu cuenta y todos tus datos han sido eliminados correctamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
