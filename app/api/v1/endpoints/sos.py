"""HU-31: botón de emergencia SOS."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.services.sos_service import SosService

router = APIRouter(tags=["sos"])


class SosIn(BaseModel):
    origen: Optional[str] = Field(None, description="menu | chat | resultados | historial")
    mensaje: Optional[str] = Field(None, max_length=1000)


@router.post("/", status_code=201)
async def activar_sos(
    payload: SosIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ev = SosService.registrar(db, user.id, origen=payload.origen, mensaje=payload.mensaje)
    return {
        "id": ev.id,
        "estado": ev.estado,
        "mensaje": (
            "Estamos contigo. Ya registramos tu solicitud y "
            "alertamos al psicólogo/a del colegio. Por favor llama AHORA a la "
            "Línea 113, opción 5. No estás solo/a."
        ),
        "linea_emergencia": "113 (opción 5) — MINSA, 24/7",
    }


@router.get("/abiertos")
async def listar_abiertos(
    db: Session = Depends(get_db),
    _admin_o_psi=Depends(require_role("psicologo", "admin")),
):
    return SosService.listar_abiertos(db)


@router.patch("/{event_id}/atender")
async def marcar_atendido(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("psicologo", "admin")),
):
    ok = SosService.marcar_atendido(db, event_id, user.id)
    return {"ok": ok}
