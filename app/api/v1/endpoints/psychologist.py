"""
Endpoints del rol psicólogo (Sprint 5: HU-14, HU-15, HU-16, HU-17, HU-19 + HU-20).
Acceso restringido por require_role("psicologo", "admin").
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.psychologist import EstudianteResumen, HistorialEstudiante
from app.schemas.cita import CitaCreate, CitaUpdate, CitaOut
from app.services.psychologist_service import PsychologistService
from app.services.cita_service import CitaService
from app.services.notes_service import NotesService
from app.core.deps import require_role
from app.models.user import User
from app.models.cita import Cita   # necesario para que Base cree la tabla
from app.models.clinical_note import ClinicalNote  # noqa: F401  (Base.metadata)
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


# ── HU-15: Dashboard con métricas generales ──────────────────────────────────

@router.get("/dashboard-stats")
async def dashboard_stats(
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return PsychologistService.stats_dashboard(db)


# ── HU-17 / HU-20: Lista de estudiantes ──────────────────────────────────────

@router.get("/students", response_model=List[EstudianteResumen])
async def listar_estudiantes(
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return PsychologistService.listar_estudiantes(db)


# ── HU-17 / HU-20: Historial de un estudiante ────────────────────────────────

@router.get("/students/{student_id}/history", response_model=HistorialEstudiante)
async def historial_estudiante(
    student_id: str,
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return PsychologistService.historial_estudiante(db, student_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── HU-19: Agendar cita ───────────────────────────────────────────────────────

@router.post("/citas", response_model=CitaOut)
async def crear_cita(
    payload: CitaCreate,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return CitaService.crear(db, current_user.id, payload.model_dump())
    except Exception as e:
        logger.error(f"Error creando cita: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/citas", response_model=List[CitaOut])
async def listar_citas(
    estudiante_id: Optional[str] = None,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return CitaService.listar(db, current_user.id, estudiante_id)


@router.put("/citas/{cita_id}", response_model=CitaOut)
async def actualizar_cita(
    cita_id: int,
    payload: CitaUpdate,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return CitaService.actualizar(
            db, cita_id, current_user.id,
            {k: v for k, v in payload.model_dump().items() if v is not None},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/citas/{cita_id}", status_code=204)
async def cancelar_cita(
    cita_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        CitaService.cancelar(db, cita_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── HU-33: Notas clínicas privadas ──────────────────────────────────

class NotaIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=4000)
    etiqueta: Optional[str] = Field(None, max_length=50)


@router.get("/students/{student_id}/notes")
async def listar_notas(
    student_id: str,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    # Admin ve todas; psicólogo solo las suyas para preservar privacidad.
    psi_filter = None if current_user.role == "admin" else current_user.id
    return NotesService.listar(db, student_id, psicologo_id=psi_filter)


@router.post("/students/{student_id}/notes", status_code=201)
async def crear_nota(
    student_id: str,
    payload: NotaIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        nota = NotesService.crear(db, student_id, current_user.id, payload.texto, payload.etiqueta)
        return {"id": nota.id, "ok": True}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/students/{student_id}/notes/{nota_id}", status_code=204)
async def borrar_nota(
    student_id: str,
    nota_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    if not NotesService.eliminar(db, nota_id, current_user.id):
        raise HTTPException(404, "Nota no encontrada (o no es tuya).")


# ── HU-35: Estado del caso ──────────────────────────────────────────

class EstadoCasoIn(BaseModel):
    estado: str = Field(..., pattern="^(activo|seguimiento|cerrado)$")


@router.patch("/students/{student_id}/case-status")
async def cambiar_estado_caso(
    student_id: str,
    payload: EstadoCasoIn,
    _user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return PsychologistService.cambiar_estado_caso(db, student_id, payload.estado)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── HU-18: Reportes mensuales ───────────────────────────────────────

@router.get("/reports/monthly")
async def reporte_mensual(
    year: int,
    month: int,
    _user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    if not (1 <= month <= 12):
        raise HTTPException(400, "Mes inválido.")
    return PsychologistService.reporte_mensual(db, year, month)
