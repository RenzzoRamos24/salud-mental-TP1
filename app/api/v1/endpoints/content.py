"""HU-29 (alumno consume) + HU-40 (admin gestiona)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.services.content_service import ContentService

router = APIRouter(tags=["content"])


class ContentIn(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=200)
    descripcion: str = Field(..., min_length=3)
    tipo: str = Field("articulo")
    categoria: Optional[str] = None
    url: Optional[str] = None
    contenido: Optional[str] = None
    autor: Optional[str] = None
    icono: Optional[str] = "📄"
    activo: bool = True


# ── Estudiante / cualquier autenticado: listar y leer ───────────────
@router.get("/")
async def listar(
    categoria: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return ContentService.listar(db, solo_activos=True, categoria=categoria)


@router.get("/{content_id}")
async def obtener(
    content_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    item = ContentService.obtener(db, content_id)
    if not item or not item["activo"]:
        raise HTTPException(404, "Contenido no encontrado")
    return item


# ── Admin: CRUD ─────────────────────────────────────────────────────
@router.get("/admin/all")
async def admin_listar_todos(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return ContentService.listar(db, solo_activos=False)


@router.post("/admin", status_code=201)
async def admin_crear(
    payload: ContentIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    try:
        return ContentService.crear(db, payload.model_dump())
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/admin/{content_id}")
async def admin_actualizar(
    content_id: int,
    payload: ContentIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    item = ContentService.actualizar(db, content_id, payload.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(404, "Contenido no encontrado")
    return item


@router.delete("/admin/{content_id}", status_code=204)
async def admin_eliminar(
    content_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    if not ContentService.eliminar(db, content_id):
        raise HTTPException(404, "Contenido no encontrado")
