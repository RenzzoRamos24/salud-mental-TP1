"""
Endpoints del rol psicólogo (Sprint 9 — cuestionarios).
Acceso restringido por require_role("psicologo", "admin").
"""
import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database import get_db
from app.schemas.psychologist import EstudianteResumen
from app.schemas.cita import CitaCreate, CitaUpdate, CitaOut
from app.services.psychologist_service import PsychologistService
from app.services.cita_service import CitaService
from app.services import report_service, word_service
from fastapi.responses import Response
from app.services.notes_service import NotesService
from app.core.deps import require_role
from app.models.user import User
from app.models.cita import Cita  # noqa: F401 (Base.metadata)
from app.models.clinical_note import ClinicalNote  # noqa: F401 (Base.metadata)

UPLOAD_FIRMAS_DIR = Path("uploads/firmas")
UPLOAD_FIRMAS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Dashboard del psicólogo ─────────────────────────────────────────────────

@router.get("/dashboard-stats")
async def dashboard_stats(
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return PsychologistService.stats_dashboard(
        db,
        psicologo_id=current_user.id,
        es_admin=(current_user.role == "admin"),
    )


# ── Listado de estudiantes ──────────────────────────────────────────────────

@router.get("/students", response_model=List[EstudianteResumen])
async def listar_estudiantes(
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return PsychologistService.listar_estudiantes(
        db,
        psicologo_id=current_user.id,
        es_admin=(current_user.role == "admin"),
    )


@router.get("/students/{student_id}/history")
async def historial_estudiante(
    student_id: str,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return PsychologistService.historial_estudiante(
            db, student_id,
            psicologo_id=current_user.id,
            es_admin=(current_user.role == "admin"),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Citas ───────────────────────────────────────────────────────────────────

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


# ── Notas clínicas privadas ─────────────────────────────────────────────────

class NotaIn(BaseModel):
    texto: str = Field(..., min_length=1, max_length=4000)
    etiqueta: Optional[str] = Field(None, max_length=50)


@router.get("/students/{student_id}/notes")
async def listar_notas(
    student_id: str,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    psi_filter = None if current_user.role == "admin" else current_user.id
    return NotesService.listar(db, student_id, psicologo_id=psi_filter)


@router.post("/students/{student_id}/notes", status_code=201)
async def crear_nota(
    student_id: str,
    payload: NotaIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    _validar_acceso_psi_a_alumno(db, current_user, student_id)
    try:
        nota = NotesService.crear(
            db, student_id, current_user.id, payload.texto, payload.etiqueta
        )
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


# ── Estado del caso ─────────────────────────────────────────────────────────

class EstadoCasoIn(BaseModel):
    estado: str = Field(..., pattern="^(activo|seguimiento|cerrado)$")


@router.patch("/students/{student_id}/case-status")
async def cambiar_estado_caso(
    student_id: str,
    payload: EstadoCasoIn,
    me: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    _validar_acceso_psi_a_alumno(db, me, student_id)
    try:
        return PsychologistService.cambiar_estado_caso(db, student_id, payload.estado)
    except ValueError as e:
        raise HTTPException(400, str(e))



# ── HU-34 / HU-18: reportes en PDF ─────────────────────────────────────────

@router.get("/students/{student_id}/report.pdf")
async def descargar_reporte_individual(
    student_id: str,
    me: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """HU-34: descarga el reporte clínico individual del estudiante en PDF."""
    _validar_acceso_psi_a_alumno(db, me, student_id)
    try:
        pdf = report_service.reporte_individual_pdf(db, student_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.exception("Falló reporte individual PDF")
        raise HTTPException(500, f"Error generando PDF: {e}")
    headers = {
        "Content-Disposition": f'attachment; filename="reporte_{student_id[:8]}.pdf"'
    }
    return Response(content=pdf, media_type="application/pdf", headers=headers)


# HU-60: psicóloga vincula/desvincula al padre de un estudiante ─────────
class AsignarPadreIn(BaseModel):
    padre_id: str


@router.get("/padres")
async def listar_padres_disponibles(
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """Lista todos los padres registrados — para que la psicóloga elija."""
    padres = (
        db.query(User)
        .filter(User.role == "padre", User.activo == True)  # noqa: E712
        .order_by(User.nombre)
        .all()
    )
    return [
        {"id": p.id, "nombre": p.nombre, "apellido": p.apellido, "email": p.email}
        for p in padres
    ]


def _validar_acceso_psi_a_alumno(db: Session, psi: User, student_id: str) -> User:
    """El psicólogo solo puede tocar alumnos que tiene asignados (admin todo)."""
    est = db.query(User).filter(User.id == student_id, User.role == "estudiante").first()
    if not est:
        raise HTTPException(404, "Estudiante no encontrado.")
    if psi.role == "psicologo" and est.psicologo_id != psi.id:
        raise HTTPException(403, "El estudiante no está asignado a ti.")
    return est


@router.post("/students/{student_id}/assign-padre")
async def asignar_padre(
    student_id: str,
    payload: AsignarPadreIn,
    me: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    est = _validar_acceso_psi_a_alumno(db, me, student_id)
    padre = db.query(User).filter(
        User.id == payload.padre_id, User.role == "padre"
    ).first()
    if not padre:
        raise HTTPException(404, "Padre no encontrado o rol incorrecto.")
    est.padre_id = padre.id
    db.commit()
    return {
        "ok": True,
        "padre": f"{padre.nombre} {padre.apellido}",
        "padre_email": padre.email,
        "estudiante": f"{est.nombre} {est.apellido}",
    }


@router.delete("/students/{student_id}/assign-padre", status_code=204)
async def desasignar_padre(
    student_id: str,
    me: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    est = _validar_acceso_psi_a_alumno(db, me, student_id)
    est.padre_id = None
    db.commit()


@router.get("/students/{student_id}/padre")
async def padre_del_estudiante(
    student_id: str,
    me: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    est = _validar_acceso_psi_a_alumno(db, me, student_id)
    if not est.padre_id:
        return {"tiene_padre": False}
    padre = db.query(User).filter(User.id == est.padre_id).first()
    if not padre:
        return {"tiene_padre": False}
    return {
        "tiene_padre": True,
        "id": padre.id,
        "nombre": padre.nombre,
        "apellido": padre.apellido,
        "email": padre.email,
    }


# HU-57: descarga del reporte clínico individual en Word ─────────────────
@router.get("/students/{student_id}/report.docx")
async def descargar_reporte_individual_word(
    student_id: str,
    me: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    _validar_acceso_psi_a_alumno(db, me, student_id)
    try:
        docx = word_service.reporte_individual_docx(db, student_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.exception("Falló reporte individual Word")
        raise HTTPException(500, f"Error generando Word: {e}")
    headers = {
        "Content-Disposition": f'attachment; filename="reporte_{student_id[:8]}.docx"'
    }
    return Response(
        content=docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


# HU-56: subir / consultar firma de la psicóloga ─────────────────────────
class FirmaInfo(BaseModel):
    tiene_firma: bool
    url: Optional[str] = None


@router.get("/firma", response_model=FirmaInfo)
async def info_firma(
    me: User = Depends(require_role("psicologo")),
):
    if me.firma_path and os.path.exists(me.firma_path):
        return FirmaInfo(tiene_firma=True, url=f"/api/v1/psychologist/firma/img?t={me.updated_at.timestamp()}")
    return FirmaInfo(tiene_firma=False)


@router.get("/firma/img")
async def firma_imagen(
    me: User = Depends(require_role("psicologo", "admin")),
):
    if not me.firma_path or not os.path.exists(me.firma_path):
        raise HTTPException(404, "Sin firma cargada")
    ext = Path(me.firma_path).suffix.lower().lstrip(".")
    mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
    with open(me.firma_path, "rb") as f:
        return Response(content=f.read(), media_type=mime)


@router.post("/firma")
async def subir_firma(
    archivo: UploadFile = File(...),
    me: User = Depends(require_role("psicologo")),
    db: Session = Depends(get_db),
):
    """Sube la imagen PNG/JPG de la firma de la psicóloga."""
    ext = Path(archivo.filename or "").suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(400, "Solo se aceptan PNG o JPG.")
    contenido = await archivo.read()
    if len(contenido) > 2 * 1024 * 1024:
        raise HTTPException(400, "La firma no puede pesar más de 2 MB.")

    # Borra firma anterior si existía
    if me.firma_path and os.path.exists(me.firma_path):
        try:
            os.remove(me.firma_path)
        except OSError:
            pass

    nombre = f"{me.id}_{uuid.uuid4().hex[:8]}{ext}"
    destino = UPLOAD_FIRMAS_DIR / nombre
    destino.write_bytes(contenido)

    me.firma_path = str(destino)
    db.add(me)
    db.commit()
    return {"ok": True, "url": f"/api/v1/psychologist/firma/img?t={me.updated_at.timestamp()}"}


@router.delete("/firma", status_code=204)
async def eliminar_firma(
    me: User = Depends(require_role("psicologo")),
    db: Session = Depends(get_db),
):
    if me.firma_path and os.path.exists(me.firma_path):
        try:
            os.remove(me.firma_path)
        except OSError:
            pass
    me.firma_path = None
    db.add(me)
    db.commit()


@router.get("/reports/monthly.pdf")
async def descargar_reporte_mensual(
    anio: int,
    mes: int,
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """HU-18: reporte mensual agregado para autoridades del colegio."""
    if not (1 <= mes <= 12):
        raise HTTPException(400, "Mes inválido (1-12).")
    try:
        pdf = report_service.reporte_mensual_pdf(db, anio, mes)
    except Exception as e:
        logger.exception("Falló reporte mensual PDF")
        raise HTTPException(500, f"Error generando PDF: {e}")
    headers = {
        "Content-Disposition": f'attachment; filename="reporte_{anio}_{mes:02d}.pdf"'
    }
    return Response(content=pdf, media_type="application/pdf", headers=headers)
