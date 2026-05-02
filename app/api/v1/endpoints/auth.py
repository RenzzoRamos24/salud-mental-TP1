"""
Endpoints de autenticación: registro, login, logout, recuperación de contraseña, /me.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserPublic,
    MensajeResponse,
)
from app.services.auth_service import AuthService
from app.core.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


def _user_a_publico(user: User, db: Session) -> dict:
    """Construye UserPublic incluyendo estado de consentimiento."""
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


# ─────────────────────────────────────────────────────────────────
# HU-01: REGISTRO
# ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def registrar(req: RegisterRequest, db: Session = Depends(get_db)):
    """Registra un nuevo usuario (estudiante o psicólogo) con correo institucional."""
    try:
        user = AuthService.registrar(
            db=db,
            email=req.email,
            password=req.password,
            nombre=req.nombre,
            apellido=req.apellido,
            role=req.role,
        )
        token_data = AuthService.emitir_token(user)
        return TokenResponse(
            **token_data,
            user=_user_a_publico(user, db),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# HU-02: LOGIN
# ─────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService.autenticar(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    token_data = AuthService.emitir_token(user)
    return TokenResponse(
        **token_data,
        user=_user_a_publico(user, db),
    )


# ─────────────────────────────────────────────────────────────────
# HU-26: LOGOUT
# ─────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=MensajeResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout stateless. El cliente descarta el token.
    Si el endpoint recibe el JWT y responde 200, es señal de logout exitoso.
    Para revocación dura (blacklist) habría que persistir tokens — fuera de alcance.
    """
    logger.info(f"👋 Logout: {current_user.email}")
    return MensajeResponse(mensaje="Sesión cerrada correctamente")


# ─────────────────────────────────────────────────────────────────
# HU-27: RECUPERAR / RESETEAR CONTRASEÑA
# ─────────────────────────────────────────────────────────────────

@router.post("/forgot-password", response_model=MensajeResponse)
async def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Genera un token de 6 dígitos y lo imprime en la consola del backend.
    Siempre responde 200 con el mismo mensaje (no filtra qué emails existen).
    """
    AuthService.crear_token_reset(db, req.email)
    return MensajeResponse(
        mensaje="Si el correo está registrado, recibirás un código de recuperación. "
                "Revisa la consola del backend (modo dev)."
    )


@router.post("/reset-password", response_model=MensajeResponse)
async def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        AuthService.resetear_password(
            db=db, email=req.email, token=req.token, nueva_password=req.nueva_password
        )
        return MensajeResponse(mensaje="Contraseña actualizada correctamente")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─────────────────────────────────────────────────────────────────
# /me — usuario autenticado actual
# ─────────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserPublic)
async def yo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _user_a_publico(current_user, db)
