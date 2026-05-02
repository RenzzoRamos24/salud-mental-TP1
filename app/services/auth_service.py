"""
Servicio de autenticación: registro, login, logout, recuperación de contraseña.
"""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.models.consent import Consent
from app.core.security import hash_password, verify_password, crear_access_token
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Lógica de auth pura. Los endpoints solo orquestan."""

    # ─────────────────────────────────────────────────────────────────
    # REGISTRO
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def registrar(
        db: Session,
        email: str,
        password: str,
        nombre: str,
        apellido: str,
        role: str,
    ) -> User:
        email_lower = email.lower()
        existente = db.query(User).filter(User.email == email_lower).first()
        if existente:
            raise ValueError("Ya existe una cuenta con este correo")

        if role not in ("estudiante", "psicologo"):
            raise ValueError("Rol inválido. Solo se permite estudiante o psicologo.")

        user = User(
            email=email_lower,
            hashed_password=hash_password(password),
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            role=role,
            activo=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"✅ Usuario registrado: {email_lower} ({role})")
        return user

    # ─────────────────────────────────────────────────────────────────
    # LOGIN
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def autenticar(db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.activo:
            return None
        return user

    @staticmethod
    def emitir_token(user: User) -> dict:
        token = crear_access_token(
            user_id=user.id, email=user.email, role=user.role
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MINUTES * 60,
        }

    # ─────────────────────────────────────────────────────────────────
    # RECUPERAR CONTRASEÑA
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def crear_token_reset(db: Session, email: str) -> Optional[PasswordResetToken]:
        """
        Crea un token de 6 dígitos. Devuelve None si el email no existe
        (para no filtrar qué emails están registrados).
        """
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not user.activo:
            logger.info(f"Reset solicitado para email no registrado: {email}")
            return None

        # Invalida tokens anteriores no usados
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.usado == False,
        ).update({"usado": True})

        token_str = f"{random.randint(0, 999999):06d}"
        reset = PasswordResetToken(
            user_id=user.id,
            token=token_str,
            expira_en=datetime.utcnow() + timedelta(
                minutes=settings.PASSWORD_RESET_TOKEN_MINUTOS
            ),
            usado=False,
        )
        db.add(reset)
        db.commit()
        db.refresh(reset)

        # 🔑 En modo dev, el token se imprime en consola.
        # En prod conectar con SendGrid/Mailtrap.
        logger.info("=" * 70)
        logger.info("🔑 TOKEN DE RECUPERACIÓN DE CONTRASEÑA")
        logger.info(f"   Email:   {user.email}")
        logger.info(f"   Token:   {token_str}")
        logger.info(f"   Expira:  {reset.expira_en.isoformat()} UTC "
                    f"({settings.PASSWORD_RESET_TOKEN_MINUTOS} min)")
        logger.info("=" * 70)

        return reset

    @staticmethod
    def resetear_password(
        db: Session, email: str, token: str, nueva_password: str
    ) -> bool:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user:
            raise ValueError("Token inválido o expirado")

        reset = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.token == token,
                PasswordResetToken.usado == False,
            )
            .order_by(PasswordResetToken.creado_en.desc())
            .first()
        )

        if not reset or reset.expira_en < datetime.utcnow():
            raise ValueError("Token inválido o expirado")

        user.hashed_password = hash_password(nueva_password)
        reset.usado = True
        db.commit()

        logger.info(f"🔒 Contraseña reseteada para: {user.email}")
        return True

    # ─────────────────────────────────────────────────────────────────
    # CONSENTIMIENTO (helper para enriquecer UserPublic)
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def obtener_consentimiento_actual(db: Session, user_id: str) -> Optional[Consent]:
        return (
            db.query(Consent)
            .filter(
                Consent.user_id == user_id,
                Consent.version == settings.CONSENT_VERSION_ACTUAL,
            )
            .order_by(Consent.aceptado_en.desc())
            .first()
        )
