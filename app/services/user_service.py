"""
Servicio de gestión de cuenta del usuario: perfil, contraseña, eliminación.
"""
import logging
from sqlalchemy.orm import Session
from app.models.user import User
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
        logger.info(f"Perfil actualizado: {user.email}")
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
        logger.info(f"Contraseña cambiada: {user.email}")

    @staticmethod
    def eliminar_cuenta(db: Session, user: User, password: str):
        if not verify_password(password, user.hashed_password):
            raise ValueError("La contraseña es incorrecta")

        email = user.email
        user_id = user.id
        db.delete(user)
        db.commit()
        logger.warning(f"Cuenta eliminada: {email} (id={user_id})")
