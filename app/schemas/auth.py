from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════
# REGISTRO
# ═══════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Correo institucional del estudiante o psicólogo")
    password: str = Field(..., min_length=8, max_length=72,
                          description="Mínimo 8 caracteres")
    nombre: str = Field(..., min_length=1, max_length=100)
    apellido: str = Field(..., min_length=1, max_length=100)
    role: Literal["estudiante", "psicologo"] = Field(
        ..., description="Rol del usuario. 'admin' solo se crea vía script."
    )

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, v: str) -> str:
        return v.lower().strip()


# ═══════════════════════════════════════════════════════════════════
# LOGIN
# ═══════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos
    user: "UserPublic"


# ═══════════════════════════════════════════════════════════════════
# OAUTH (Google / Microsoft)
# ═══════════════════════════════════════════════════════════════════

class OAuthGoogleRequest(BaseModel):
    id_token: str = Field(..., description="JWT id_token de Google Identity Services.")


class OAuthMicrosoftRequest(BaseModel):
    access_token: str = Field(..., description="Access token devuelto por Microsoft Identity.")


class OAuthProviderConfig(BaseModel):
    configurado: bool
    client_id: str = ""
    tenant: Optional[str] = None


class OAuthConfigResponse(BaseModel):
    google: OAuthProviderConfig
    microsoft: OAuthProviderConfig
    redirect_uri: str


# ═══════════════════════════════════════════════════════════════════
# RECUPERAR / RESETEAR CONTRASEÑA
# ═══════════════════════════════════════════════════════════════════

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str = Field(..., min_length=6, max_length=10)
    nueva_password: str = Field(..., min_length=8, max_length=72)


# ═══════════════════════════════════════════════════════════════════
# USER PÚBLICO (sin password)
# ═══════════════════════════════════════════════════════════════════

class UserPublic(BaseModel):
    id: str
    email: str
    nombre: str
    apellido: str
    role: str
    activo: bool
    created_at: datetime
    consentimiento_aceptado: bool = False
    consentimiento_version: Optional[str] = None

    model_config = {"from_attributes": True}


class MensajeResponse(BaseModel):
    mensaje: str


TokenResponse.model_rebuild()
