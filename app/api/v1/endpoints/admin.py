"""
Endpoints exclusivos para rol admin (Sprint 6: HU-21, HU-22, HU-23, HU-24, HU-36).
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.core.deps import require_role
from app.schemas.admin import UsuarioResumen, StatsUsuarios
from app.services.admin_service import AdminService
# Importar modelos para que SQLAlchemy los registre al arrancar
from app.models.configuracion import Configuracion  # noqa: F401
from app.models.access_log import AccessLog         # noqa: F401

router = APIRouter()


# ── Usuarios (Sprint 1) ───────────────────────────────────────────────────────

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


# ── HU-21: Configuración de encuesta ─────────────────────────────────────────

class EncuestaUpdate(BaseModel):
    # PHQ-9 / GAD-7 son ítems clínicos fijos; el admin solo configura frecuencia.
    # `preguntas` se mantiene opcional por compatibilidad con el cliente, pero
    # el servicio la ignora.
    preguntas: list = None
    frecuencia_dias: int = 7


@router.get("/config/encuesta")
async def get_encuesta(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.get_encuesta(db)


@router.put("/config/encuesta")
async def update_encuesta(
    payload: EncuestaUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    try:
        return AdminService.update_encuesta(db, payload.preguntas, payload.frecuencia_dias)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── HU-22: Auditoría de accesos ───────────────────────────────────────────────

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(100, le=500),
    offset: int = 0,
    role: Optional[str] = None,
    endpoint: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.get_audit_logs(db, limit=limit, offset=offset, role=role, endpoint=endpoint)


# ── HU-23: Respaldos ─────────────────────────────────────────────────────────

@router.post("/backup")
async def crear_backup(_admin=Depends(require_role("admin"))):
    try:
        return AdminService.crear_backup()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def listar_backups(_admin=Depends(require_role("admin"))):
    return AdminService.listar_backups()


# ── HU-36: Umbrales BERT ──────────────────────────────────────────────────────

class UmbralItem(BaseModel):
    umbral: float
    etiqueta: str
    hipotesis: str


@router.get("/bert/umbrales")
async def get_umbrales(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.get_umbrales(db)


@router.put("/bert/umbrales")
async def update_umbrales(
    payload: dict,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.update_umbrales(db, payload)


# ── HU-24: Gestión del modelo BERT ────────────────────────────────────────────

@router.get("/bert/modelo")
async def get_modelo(_admin=Depends(require_role("admin"))):
    return AdminService.get_modelo_info()


@router.post("/bert/recargar")
async def recargar_modelo(_admin=Depends(require_role("admin"))):
    return AdminService.recargar_modelo()


# ─────────────────────────────────────────────────────────────────
# HU-38: Asignar estudiantes a psicólogos
# ─────────────────────────────────────────────────────────────────

class AsignacionIn(BaseModel):
    psicologo_id: str | None = None  # None = desasignar


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


# ─────────────────────────────────────────────────────────────────
# HU-39: Personalizar mensajes del chatbot
# ─────────────────────────────────────────────────────────────────

class ChatbotMessagesIn(BaseModel):
    # Cualquier subconjunto de las claves DEFAULT_CHATBOT_MSGS.
    mensajes: dict


@router.get("/chatbot-messages")
async def get_chatbot_messages(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.get_chatbot_messages(db)


@router.put("/chatbot-messages")
async def update_chatbot_messages(
    payload: ChatbotMessagesIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.update_chatbot_messages(db, payload.mensajes)


# ─────────────────────────────────────────────────────────────────
# HU-18 (admin lo expone aquí también): reportes mensuales agregados
# ─────────────────────────────────────────────────────────────────

@router.get("/reports/monthly")
async def reporte_mensual_admin(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    if not (1 <= month <= 12):
        raise HTTPException(400, "Mes inválido")
    from app.services.psychologist_service import PsychologistService
    return PsychologistService.reporte_mensual(db, year, month)


# ─────────────────────────────────────────────────────────────────
# HU-23: Scheduler de backups automáticos
# ─────────────────────────────────────────────────────────────────

@router.get("/scheduler/info")
async def scheduler_info(_admin=Depends(require_role("admin"))):
    from app.services.scheduler_service import info_scheduler
    return info_scheduler()


@router.post("/scheduler/backup-ahora")
async def scheduler_backup_ahora(_admin=Depends(require_role("admin"))):
    from app.services.scheduler_service import disparar_ahora
    return disparar_ahora()
