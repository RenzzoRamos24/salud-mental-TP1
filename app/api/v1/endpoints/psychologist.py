"""
Endpoints del rol psicólogo (HU-20).
Acceso restringido por require_role("psicologo", "admin").
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.psychologist import EstudianteResumen, HistorialEstudiante
from app.services.psychologist_service import PsychologistService
from app.core.deps import require_role
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/students", response_model=List[EstudianteResumen])
async def listar_estudiantes(
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return PsychologistService.listar_estudiantes(db)


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
