"""
Endpoints del rol PADRE (Sprint 11).
HU-55: el padre ve a sus hijos, qué cuestionarios completaron y descarga
        un informe NO clínico firmado por la psicóloga responsable.

Las puntuaciones, banderas de crisis y notas internas NO se exponen al padre.
Solo: nombre del hijo, grado, número de cuestionarios, mensaje de la psicóloga.
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.models.bank import AplicacionCuestionario
from app.models.cita import Cita
from app.services import report_service, word_service

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────────────────
class HijoResumen(BaseModel):
    id: str
    nombre: str
    apellido: str
    grado: Optional[str] = None
    estado_caso: Optional[str] = None
    cuestionarios_completados: int
    ultima_actividad: Optional[datetime] = None
    psicologo_nombre: Optional[str] = None


class HijoDetalle(BaseModel):
    id: str
    nombre: str
    apellido: str
    grado: Optional[str] = None
    estado_caso: Optional[str] = None
    cuestionarios_completados: int
    mensaje_psicologa: Optional[str] = None
    psicologo_nombre: Optional[str] = None


# ── Helpers ─────────────────────────────────────────────────────────────
def _hijos_del_padre(db: Session, padre_id: str) -> List[User]:
    return (
        db.query(User)
        .filter(User.role == "estudiante", User.padre_id == padre_id)
        .order_by(User.nombre)
        .all()
    )


def _validar_acceso(db: Session, padre_id: str, hijo_id: str) -> User:
    hijo = db.query(User).filter(
        User.id == hijo_id,
        User.role == "estudiante",
        User.padre_id == padre_id,
    ).first()
    if not hijo:
        raise HTTPException(404, "No tiene acceso a este estudiante.")
    return hijo


# ── HU-55: listado de hijos ─────────────────────────────────────────────
@router.get("/hijos", response_model=List[HijoResumen])
async def listar_hijos(
    me: User = Depends(require_role("padre")),
    db: Session = Depends(get_db),
):
    hijos = _hijos_del_padre(db, me.id)
    out: List[HijoResumen] = []
    for h in hijos:
        completados = (
            db.query(AplicacionCuestionario)
            .filter(
                AplicacionCuestionario.estudiante_id == h.id,
                AplicacionCuestionario.estado.in_(["completado", "revisado"]),
            )
            .count()
        )
        ult = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.estudiante_id == h.id)
            .order_by(AplicacionCuestionario.asignada_at.desc())
            .first()
        )
        psi = (
            db.query(User).filter(User.id == h.psicologo_id).first()
            if h.psicologo_id else None
        )
        out.append(HijoResumen(
            id=h.id, nombre=h.nombre, apellido=h.apellido,
            grado=h.grado, estado_caso=h.estado_caso,
            cuestionarios_completados=completados,
            ultima_actividad=ult.asignada_at if ult else None,
            psicologo_nombre=f"{psi.nombre} {psi.apellido}" if psi else None,
        ))
    return out


# ── Detalle de un hijo ──────────────────────────────────────────────────
@router.get("/hijos/{hijo_id}", response_model=HijoDetalle)
async def detalle_hijo(
    hijo_id: str,
    me: User = Depends(require_role("padre")),
    db: Session = Depends(get_db),
):
    hijo = _validar_acceso(db, me.id, hijo_id)
    completados = (
        db.query(AplicacionCuestionario)
        .filter(
            AplicacionCuestionario.estudiante_id == hijo.id,
            AplicacionCuestionario.estado.in_(["completado", "revisado"]),
        )
        .count()
    )
    ultima_cita = (
        db.query(Cita)
        .filter(
            Cita.estudiante_id == hijo.id,
            Cita.resumen_para_estudiante.isnot(None),
        )
        .order_by(Cita.fecha.desc(), Cita.hora.desc())
        .first()
    )
    psi = (
        db.query(User).filter(User.id == hijo.psicologo_id).first()
        if hijo.psicologo_id else None
    )
    return HijoDetalle(
        id=hijo.id, nombre=hijo.nombre, apellido=hijo.apellido,
        grado=hijo.grado, estado_caso=hijo.estado_caso,
        cuestionarios_completados=completados,
        mensaje_psicologa=ultima_cita.resumen_para_estudiante if ultima_cita else None,
        psicologo_nombre=f"{psi.nombre} {psi.apellido}" if psi else None,
    )


# ── HU-58: descarga del informe firmado ─────────────────────────────────
@router.get("/hijos/{hijo_id}/informe.pdf")
async def descargar_informe_padre_pdf(
    hijo_id: str,
    me: User = Depends(require_role("padre")),
    db: Session = Depends(get_db),
):
    hijo = _validar_acceso(db, me.id, hijo_id)
    try:
        pdf = report_service.informe_para_padre_pdf(db, hijo.id)
    except Exception as e:
        logger.exception("Falló informe padre PDF")
        raise HTTPException(500, f"Error generando PDF: {e}")
    headers = {
        "Content-Disposition": f'attachment; filename="informe_{hijo.nombre}.pdf"'
    }
    return Response(content=pdf, media_type="application/pdf", headers=headers)


@router.get("/hijos/{hijo_id}/informe.docx")
async def descargar_informe_padre_word(
    hijo_id: str,
    me: User = Depends(require_role("padre")),
    db: Session = Depends(get_db),
):
    hijo = _validar_acceso(db, me.id, hijo_id)
    try:
        docx = word_service.informe_para_padre_docx(db, hijo.id)
    except Exception as e:
        logger.exception("Falló informe padre Word")
        raise HTTPException(500, f"Error generando Word: {e}")
    headers = {
        "Content-Disposition": f'attachment; filename="informe_{hijo.nombre}.docx"'
    }
    return Response(
        content=docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )
