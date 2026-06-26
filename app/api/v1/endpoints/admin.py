"""
Endpoints exclusivos para rol admin (Sprint 9 — cuestionarios).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.core.deps import require_role
from app.schemas.admin import UsuarioResumen, StatsUsuarios
from app.services.admin_service import AdminService
from app.models.configuracion import Configuracion  # noqa: F401
from app.models.access_log import AccessLog         # noqa: F401

router = APIRouter()


# ── Usuarios ────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UsuarioResumen])
async def listar_usuarios(
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.listar_usuarios(db, role=role)


@router.get("/stats", response_model=StatsUsuarios)
async def stats_usuarios(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.stats(db)


# ── Auditoría ───────────────────────────────────────────────────────────────

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(100, le=500),
    offset: int = 0,
    role: Optional[str] = None,
    endpoint: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.get_audit_logs(
        db, limit=limit, offset=offset, role=role, endpoint=endpoint
    )


# ── Respaldos ───────────────────────────────────────────────────────────────

@router.post("/backup")
async def crear_backup(_admin=Depends(require_role("admin"))):
    try:
        return AdminService.crear_backup()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def listar_backups(_admin=Depends(require_role("admin"))):
    return AdminService.listar_backups()


# ── Modelo NLP (BETO) ───────────────────────────────────────────────────────

@router.get("/nlp/modelo")
async def get_modelo(_admin=Depends(require_role("admin"))):
    return AdminService.get_modelo_info()


@router.post("/nlp/recargar")
async def recargar_modelo(_admin=Depends(require_role("admin"))):
    return AdminService.recargar_modelo()


# ── Asignación estudiante → psicólogo ───────────────────────────────────────

class AsignacionIn(BaseModel):
    psicologo_id: str | None = None


@router.post("/students/{student_id}/assign-psychologist")
async def asignar_psicologo(
    student_id: str,
    payload: AsignacionIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    try:
        return AdminService.asignar_psicologo(db, student_id, payload.psicologo_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Estadísticas de cuestionarios ───────────────────────────────────────────

@router.get("/cuestionarios/stats")
async def cuestionarios_stats(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.stats_cuestionarios(db)


# ── Scheduler ───────────────────────────────────────────────────────────────

@router.get("/scheduler/info")
async def scheduler_info(_admin=Depends(require_role("admin"))):
    from app.services.scheduler_service import info_scheduler
    return info_scheduler()


@router.post("/scheduler/backup-ahora")
async def scheduler_backup_ahora(_admin=Depends(require_role("admin"))):
    from app.services.scheduler_service import disparar_ahora
    return disparar_ahora()
