"""
Servicio admin: visibilidad de cuentas (estudiantes, psicólogos, admins).
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User


class AdminService:

    @staticmethod
    def listar_usuarios(db: Session, role: Optional[str] = None) -> list[User]:
        q = db.query(User)
        if role:
            q = q.filter(User.role == role)
        return q.order_by(User.created_at.desc()).all()

    @staticmethod
    def stats(db: Session) -> dict:
        usuarios = db.query(User).all()
        return {
            "total": len(usuarios),
            "estudiantes": sum(1 for u in usuarios if u.role == "estudiante"),
            "psicologos": sum(1 for u in usuarios if u.role == "psicologo"),
            "admins": sum(1 for u in usuarios if u.role == "admin"),
            "activos": sum(1 for u in usuarios if u.activo),
            "inactivos": sum(1 for u in usuarios if not u.activo),
        }
