"""
Endpoints del banco de instrumentos y bloques custom (Sprint 9.2 + 9.3).
Acceso restringido a psicóloga / admin.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.services.bank_service import BankService
from app.schemas.bank import BloqueCustomIn

router = APIRouter()


# ── Instrumentos validados (lectura) ────────────────────────────────────────

@router.get("/instrumentos")
async def listar_instrumentos(
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return BankService.listar_instrumentos(db)


@router.get("/instrumentos/{codigo}")
async def obtener_instrumento(
    codigo: str,
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    data = BankService.obtener_instrumento(db, codigo)
    if not data:
        raise HTTPException(404, "Instrumento no encontrado.")
    return data


# ── Frases incompletas ──────────────────────────────────────────────────────

@router.get("/frases")
async def listar_frases(
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return BankService.listar_frases(db)


@router.get("/frases/areas")
async def listar_areas_frases(
    _: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return BankService.areas_frases(db)


# ── Bloques custom (psicóloga arma sus propios) ─────────────────────────────

@router.get("/bloques-custom")
async def listar_bloques_custom(
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return BankService.listar_bloques_custom(db, current_user.id)


@router.post("/bloques-custom", status_code=201)
async def crear_bloque_custom(
    payload: BloqueCustomIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return BankService.crear_bloque_custom(
            db, current_user.id, payload.model_dump()
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/bloques-custom/{bloque_id}")
async def obtener_bloque_custom(
    bloque_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    data = BankService.obtener_bloque_custom(db, current_user.id, bloque_id)
    if not data:
        raise HTTPException(404, "Bloque no encontrado.")
    return data


@router.put("/bloques-custom/{bloque_id}")
async def actualizar_bloque_custom(
    bloque_id: int,
    payload: BloqueCustomIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return BankService.actualizar_bloque_custom(
            db, current_user.id, bloque_id, payload.model_dump()
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/bloques-custom/{bloque_id}", status_code=204)
async def borrar_bloque_custom(
    bloque_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    if not BankService.borrar_bloque_custom(db, current_user.id, bloque_id):
        raise HTTPException(404, "Bloque no encontrado.")


# ── Sugerir cortes por tercios ──────────────────────────────────────────────

@router.get("/sugerir-cortes")
async def sugerir_cortes(
    rango_max: int,
    _: User = Depends(require_role("psicologo", "admin")),
):
    if rango_max < 3:
        raise HTTPException(400, "El rango máximo debe ser ≥ 3.")
    return BankService.sugerir_cortes_tercios(rango_max)
