"""
Endpoints exclusivos para rol admin.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import require_role
from app.schemas.admin import UsuarioResumen, StatsUsuarios
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/users", response_model=list[UsuarioResumen])
async def listar_usuarios(
    role: Optional[str] = Query(None, description="Filtra por rol: estudiante|psicologo|admin"),
    db: Session = Depends(get_db),
    _admin = Depends(require_role("admin")),
):
    return AdminService.listar_usuarios(db, role=role)


@router.get("/stats", response_model=StatsUsuarios)
async def stats_usuarios(
    db: Session = Depends(get_db),
    _admin = Depends(require_role("admin")),
):
    return AdminService.stats(db)
