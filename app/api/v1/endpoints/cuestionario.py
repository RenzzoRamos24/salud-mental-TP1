"""
Endpoints de aplicación de cuestionarios.

  * Psicóloga: asignar, listar asignaciones, ver resultado, marcar revisado.
  * Estudiante: listar propios, ver detalle para responder, enviar respuestas, cerrar.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.services.cuestionario_service import CuestionarioService
from app.services.feedback_service import FeedbackService
from app.schemas.bank import AsignarCuestionarioIn, EnviarRespuestasIn

router = APIRouter()


# ── Psicóloga ───────────────────────────────────────────────────────────────

@router.post("/asignar", status_code=201)
async def asignar(
    payload: AsignarCuestionarioIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return CuestionarioService.asignar(
            db, current_user.id, payload.plantilla_id, payload.estudiante_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/aplicacion/{aplicacion_id}/resultado")
async def obtener_resultado(
    aplicacion_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return CuestionarioService.obtener_resultado(
            db, current_user.id, aplicacion_id, es_admin=(current_user.role == "admin"),
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/aplicacion/{aplicacion_id}/marcar-revisado")
async def marcar_revisado(
    aplicacion_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        a = CuestionarioService.marcar_revisado(db, current_user.id, aplicacion_id)
        return {"id": a.id, "estado": a.estado, "revisada_at": a.revisada_at.isoformat()}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Feedback de la psicóloga sobre el análisis de BETO ──────────────────────


class FeedbackResultadoIn(BaseModel):
    veredicto: str = Field(
        ...,
        description="'aceptado' si el análisis del modelo es correcto, "
                    "'rechazado' si se descarta por incorrecto.",
    )
    comentario: Optional[str] = Field(None, max_length=500)


@router.post("/aplicacion/{aplicacion_id}/feedback")
async def registrar_feedback_resultado(
    aplicacion_id: int,
    payload: FeedbackResultadoIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """Acepta o descarta el análisis que el modelo hizo de este cuestionario."""
    try:
        fb = FeedbackService.registrar(
            db,
            psicologo_id=current_user.id,
            aplicacion_id=aplicacion_id,
            veredicto=payload.veredicto,
            comentario=payload.comentario,
            es_admin=(current_user.role == "admin"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return {
        "aplicacion_id": fb.aplicacion_id,
        "veredicto": fb.veredicto,
        "comentario": fb.comentario,
        "metricas": FeedbackService.metricas_globales(
            db, current_user.id, es_admin=(current_user.role == "admin"),
        ),
    }


@router.delete("/aplicacion/{aplicacion_id}/feedback")
async def quitar_feedback_resultado(
    aplicacion_id: int,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """Deshace el veredicto: el resultado vuelve a quedar sin juzgar."""
    try:
        quitado = FeedbackService.quitar(
            db,
            psicologo_id=current_user.id,
            aplicacion_id=aplicacion_id,
            es_admin=(current_user.role == "admin"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {
        "quitado": quitado,
        "metricas": FeedbackService.metricas_globales(
            db, current_user.id, es_admin=(current_user.role == "admin"),
        ),
    }


# ── Estudiante ──────────────────────────────────────────────────────────────

@router.get("/mis-cuestionarios")
async def mis_cuestionarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "estudiante":
        raise HTTPException(403, "Solo el alumno ve esta vista.")
    return CuestionarioService.listar_para_estudiante(db, current_user.id)


@router.get("/responder/{aplicacion_id}")
async def detalle_para_responder(
    aplicacion_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "estudiante":
        raise HTTPException(403, "Solo el alumno ve esta vista.")
    try:
        return CuestionarioService.detalle_para_responder(
            db, current_user.id, aplicacion_id
        )
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/responder/{aplicacion_id}/guardar")
async def guardar_respuestas(
    aplicacion_id: int,
    payload: EnviarRespuestasIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "estudiante":
        raise HTTPException(403, "Solo el alumno responde.")
    try:
        app_ = CuestionarioService.guardar_respuestas(
            db, current_user.id, aplicacion_id,
            [r.model_dump() for r in payload.respuestas],
        )
        return {"id": app_.id, "estado": app_.estado, "n": len(payload.respuestas)}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/responder/{aplicacion_id}/cerrar")
async def cerrar(
    aplicacion_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "estudiante":
        raise HTTPException(403, "Solo el alumno cierra el cuestionario.")
    try:
        resultado = CuestionarioService.cerrar_y_evaluar(
            db, current_user.id, aplicacion_id
        )
        # El alumno solo ve confirmación, no el reporte clínico.
        return {
            "ok": True,
            "crisis_activada": bool(resultado.get("crisis_activada")),
            "mensaje": (
                "Gracias por completar el cuestionario. La psicóloga revisará tus respuestas."
            ),
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
