"""
Dependencias FastAPI: extraer User del JWT y proteger por rol.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decodificar_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credenciales_excepcion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decodificar_token(token)
        user_id: str = payload.get("sub")
        if not user_id:
            raise credenciales_excepcion
    except JWTError:
        raise credenciales_excepcion

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.activo:
        raise credenciales_excepcion
    return user


def require_role(*roles_permitidos: str):
    """Factory de dependencia: exige que el user tenga uno de estos roles."""
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Rol requerido: {', '.join(roles_permitidos)}",
            )
        return user
    return _checker
