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
from app.services.psychologist_service import (
    PsychologistService,
    resumen_diario_estudiante,
)
from app.services.cita_service import CitaService
from app.services.notes_service import NotesService
from app.core.deps import require_role
from app.models.user import User
from app.models.cita import Cita   # necesario para que Base cree la tabla
from app.models.clinical_note import ClinicalNote  # noqa: F401  (Base.metadata)
from app.models.psicologo_mensaje import PsicologoMensaje
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


# ── Resumen bisemanal del diario (panel psicólogo) ──────────────────────────

@router.get("/students/{student_id}/diario-resumen")
async def diario_resumen(
    student_id: str,
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """
    Resumen agregado del diario en una ventana de 14 días.

    Devuelve estado de evaluación (en_proceso/completo/sin_datos),
    porcentaje completado, alerta crítica si aplica y resumen de
    PHQ-9 / GAD-7 / condiciones BERT más recurrentes.
    """
    try:
        return resumen_diario_estudiante(db, student_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Reporte clínico por ciclo (días-con-síntoma → tabla Johnson 2002) ─────

@router.get("/students/{student_id}/reporte-ciclo")
async def reporte_ciclo_estudiante(
    student_id: str,
    ciclo: Optional[int] = None,
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """
    Reporte clínico de un ciclo de 14 días, calculado contando los DÍAS
    distintos en que apareció cada síntoma y mapeando con la tabla literal
    del PHQ-A (Johnson 2002):

        0 días     → 0 puntos ("Nunca")
        1–7 días   → 1 punto  ("Algunos días")
        8–11 días  → 2 puntos ("Más de la mitad de los días")
        12–14 días → 3 puntos ("Casi todos los días")

    Si `ciclo` no se pasa, devuelve el reporte del ciclo ACTUAL del alumno
    (basado en `info_ciclo_estudiante`). Si se pasa, devuelve el reporte
    del ciclo cerrado con ese número.
    """
    from app.services.ciclo_service import info_ciclo_estudiante
    from app.services.diario_analisis_service import DiarioAnalisisService
    from datetime import date

    try:
        info = info_ciclo_estudiante(db, student_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Determinar el rango de fechas del ciclo solicitado
    if ciclo is not None:
        cerrados = info.get("sesiones_cerradas", [])
        match = next((c for c in cerrados if c["numero"] == ciclo), None)
        if not match:
            actual = info.get("ciclo_actual") or {}
            if actual and actual.get("numero") == ciclo:
                ciclo_inicio = date.fromisoformat(actual["inicio"])
                ciclo_fin = date.fromisoformat(actual["fecha_limite"])
                cerrado = False
            else:
                raise HTTPException(
                    status_code=404, detail=f"Ciclo {ciclo} no encontrado"
                )
        else:
            ciclo_inicio = date.fromisoformat(match["inicio"])
            ciclo_fin = date.fromisoformat(match["cierre"])
            cerrado = True
    else:
        actual = info.get("ciclo_actual")
        if not actual:
            return {
                "estado": "sin_datos",
                "mensaje": "El estudiante aún no tiene ciclo en curso.",
            }
        ciclo_inicio = date.fromisoformat(actual["inicio"])
        ciclo_fin = date.fromisoformat(actual["fecha_limite"])
        cerrado = False

    reporte = DiarioAnalisisService.reporte_ciclo(
        db, student_id, ciclo_inicio, ciclo_fin
    )
    reporte["ciclo_cerrado"] = cerrado
    return reporte


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


# ── Mensajes del psicólogo al estudiante ────────────────────────────

class MensajeIn(BaseModel):
    mensaje: str = Field(..., min_length=1, max_length=1000)


@router.get("/students/{student_id}/mensajes")
async def listar_mensajes_estudiante(
    student_id: str,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(PsicologoMensaje)
        .filter(PsicologoMensaje.estudiante_id == student_id)
        .order_by(PsicologoMensaje.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": m.id,
            "psicologo_id": m.psicologo_id,
            "mensaje": m.mensaje,
            "leido": m.leido,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "leido_at": m.leido_at.isoformat() if m.leido_at else None,
        }
        for m in rows
    ]


@router.post("/students/{student_id}/mensajes", status_code=201)
async def crear_mensaje_estudiante(
    student_id: str,
    payload: MensajeIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    estudiante = (
        db.query(User)
        .filter(User.id == student_id, User.role == "estudiante")
        .first()
    )
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado.")

    m = PsicologoMensaje(
        psicologo_id=current_user.id,
        estudiante_id=student_id,
        mensaje=payload.mensaje.strip(),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "ok": True}


@router.delete("/students/{student_id}/mensajes/{mensaje_id}", status_code=204)
async def borrar_mensaje_estudiante(
    student_id: str,
    mensaje_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    m = (
        db.query(PsicologoMensaje)
        .filter(
            PsicologoMensaje.id == mensaje_id,
            PsicologoMensaje.estudiante_id == student_id,
            PsicologoMensaje.psicologo_id == current_user.id,
        )
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado.")
    db.delete(m)
    db.commit()


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
