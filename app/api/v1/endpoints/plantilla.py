"""Endpoints de plantillas de cuestionario."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.services.plantilla_service import PlantillaService
from app.schemas.bank import PlantillaIn

router = APIRouter()


@router.get("")
async def listar_plantillas(
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return PlantillaService.listar(db, current_user.id)


@router.post("", status_code=201)
async def crear_plantilla(
    payload: PlantillaIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return PlantillaService.crear(db, current_user.id, payload.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{plantilla_id}")
async def obtener_plantilla(
    plantilla_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    p = PlantillaService.obtener(db, current_user.id, plantilla_id)
    if not p:
        raise HTTPException(404, "Plantilla no encontrada.")
    return p


@router.put("/{plantilla_id}")
async def actualizar_plantilla(
    plantilla_id: int,
    payload: PlantillaIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return PlantillaService.actualizar(
            db, current_user.id, plantilla_id, payload.model_dump()
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{plantilla_id}", status_code=204)
async def borrar_plantilla(
    plantilla_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    if not PlantillaService.borrar(db, current_user.id, plantilla_id):
        raise HTTPException(404, "Plantilla no encontrada.")
