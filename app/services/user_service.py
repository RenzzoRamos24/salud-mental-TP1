"""
Servicio de gestión de cuenta del usuario: perfil, contraseña, eliminación.
"""
import logging
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.session import UserSession
from app.models.response import UserResponse
from app.models.risk import RiskResult
from app.core.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class UserService:

    @staticmethod
    def actualizar_perfil(
        db: Session, user: User, nombre: str, apellido: str
    ) -> User:
        user.nombre = nombre.strip()
        user.apellido = apellido.strip()
        db.commit()
        db.refresh(user)
        logger.info(f"✏️  Perfil actualizado: {user.email}")
        return user

    @staticmethod
    def cambiar_password(
        db: Session, user: User, password_actual: str, nueva_password: str
    ):
        if not verify_password(password_actual, user.hashed_password):
            raise ValueError("La contraseña actual es incorrecta")
        if password_actual == nueva_password:
            raise ValueError("La nueva contraseña debe ser diferente a la actual")
        user.hashed_password = hash_password(nueva_password)
        db.commit()
        logger.info(f"🔒 Contraseña cambiada: {user.email}")

    @staticmethod
    def eliminar_cuenta(db: Session, user: User, password: str):
        """
        Hard delete del usuario y todos sus datos: sesiones de chat,
        respuestas y resultados de riesgo. Cumple HU-05 (eliminación
        completa para que los datos sean removidos).
        """
        if not verify_password(password, user.hashed_password):
            raise ValueError("La contraseña es incorrecta")

        user_id = user.id
        email = user.email

        # 1. RiskResults asociados a sesiones del user
        sesiones = db.query(UserSession).filter(UserSession.user_id == user_id).all()
        session_ids = [s.id for s in sesiones]
        if session_ids:
            db.query(RiskResult).filter(
                RiskResult.session_id.in_(session_ids)
            ).delete(synchronize_session=False)
            db.query(UserResponse).filter(
                UserResponse.session_id.in_(session_ids)
            ).delete(synchronize_session=False)
            db.query(UserSession).filter(
                UserSession.user_id == user_id
            ).delete(synchronize_session=False)

        # 2. Cascade delete del User → Consent + PasswordResetToken
        db.delete(user)
        db.commit()

        logger.warning(f"🗑️  Cuenta eliminada: {email} (id={user_id})")
