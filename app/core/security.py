"""
Hash de contraseñas (bcrypt) y emisión/verificación de JWT.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def crear_access_token(*, user_id: str, email: str, role: str,
                       expira_minutos: Optional[int] = None) -> str:
    """Genera un JWT con sub=user_id, email y role."""
    expira = datetime.utcnow() + timedelta(
        minutes=expira_minutos or settings.JWT_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expira,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decodificar_token(token: str) -> dict:
    """Decodifica el JWT. Lanza JWTError si es inválido o expiró."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
