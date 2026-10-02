"""
Endpoints del etiquetado clínico ciego.

El psicólogo entra al sistema y etiqueta acá dentro. Nada de planillas
externas: las etiquetas quedan en la BD con su autor, su momento y lo que el
modelo había predicho, que es lo que las vuelve utilizables a la vez como
medición y como dataset de reentrenamiento.

La ceguedad se garantiza en los dos GET de cola: no serializan scores,
banderas ni riesgo calculado. Es deliberado — si el payload los trajera, se
verían abriendo el inspector del navegador y la concordancia dejaría de medir
concordancia.
"""
import csv
import io
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.models.user import User
from app.services.etiquetado_service import EtiquetadoService
from app.services.metricas_etiquetado_service import MetricasEtiquetadoService

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Progreso y plan de muestreo ─────────────────────────────────────────────


@router.get("/progreso")
async def progreso(
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    return EtiquetadoService.progreso(db, current_user.id)


class GenerarMuestraIn(BaseModel):
    n: int = Field(100, ge=10, le=600)
    semilla: int = 20260910
    reemplazar: bool = False


@router.post("/muestra/generar")
async def generar_muestra(
    payload: GenerarMuestraIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    """
    Sortea la muestra de medición, estratificada por el score del modelo.

    Hay que correrlo una vez antes de que el psicólogo empiece. Tiene que ser
    antes: si se regenera con etiquetas ya puestas, los pesos del estrato
    dejan de corresponder a lo etiquetado y las métricas proyectadas quedan
    inválidas. El servicio se niega a hacerlo en ese caso.
    """
    try:
        return EtiquetadoService.generar_muestra(
            db, n=payload.n, semilla=payload.semilla,
            reemplazar=payload.reemplazar,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Cola de frases ──────────────────────────────────────────────────────────


@router.get("/frases/siguiente")
async def siguiente_frase(
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """
    Próxima frase a etiquetar, ciega. Devuelve 204 cuando no queda ninguna.

    Primero sirve la muestra de medición; cuando se agota sigue con el resto
    del corpus, que ya no cuenta para las métricas pero sí engrosa el dataset.
    """
    frase = EtiquetadoService.siguiente_frase(db, current_user.id)
    if frase is None:
        return Response(status_code=204)
    return frase


class EtiquetaFraseIn(BaseModel):
    ref: str                        # "aplicacion_id:frase_numero"
    ideacion_presente: bool
    sufrimiento_grave: bool = False
    categoria: str | None = None    # depresion|ansiedad|adaptativo|neutral
    confianza: str = "alta"
    comentario: str | None = None
    segundos: int | None = None


@router.post("/frases", status_code=201)
async def guardar_frase(
    payload: EtiquetaFraseIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return EtiquetadoService.guardar_etiqueta_frase(
            db,
            evaluador_id=current_user.id,
            ref=payload.ref,
            ideacion_presente=payload.ideacion_presente,
            sufrimiento_grave=payload.sufrimiento_grave,
            categoria=payload.categoria,
            confianza=payload.confianza,
            comentario=payload.comentario,
            segundos=payload.segundos,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Cola de casos ───────────────────────────────────────────────────────────


@router.get("/casos/siguiente")
async def siguiente_caso(
    solo_con_svm: bool = Query(
        False,
        description="Solo aplicaciones donde el SVM opinó (las que tienen DASS-21)",
    ),
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """
    Próximo caso a etiquetar: las respuestas crudas, sin ninguna suma ni
    severidad. Devuelve 204 cuando no queda ninguno.
    """
    caso = EtiquetadoService.siguiente_caso(
        db, current_user.id, solo_con_svm=solo_con_svm
    )
    if caso is None:
        return Response(status_code=204)
    return caso


class EtiquetaCasoIn(BaseModel):
    aplicacion_id: int
    riesgo_clinico: str             # SIN_RIESGO|BAJO|MEDIO|ALTO|CRITICO
    requiere_derivacion: bool = False
    ideacion_presente: bool | None = None
    # depresion|ansiedad|estres|ninguno. Opcional: el SVM de hoy es binario y
    # no distingue, así que esto no se compara contra él — valida el desglose
    # por subescala del DASS-21 y queda como objetivo de un SVM de 3 salidas.
    predominante: str | None = None
    confianza: str = "alta"
    comentario: str | None = None
    segundos: int | None = None


@router.post("/casos", status_code=201)
async def guardar_caso(
    payload: EtiquetaCasoIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    try:
        return EtiquetadoService.guardar_etiqueta_caso(
            db,
            evaluador_id=current_user.id,
            aplicacion_id=payload.aplicacion_id,
            riesgo_clinico=payload.riesgo_clinico,
            requiere_derivacion=payload.requiere_derivacion,
            ideacion_presente=payload.ideacion_presente,
            predominante=payload.predominante,
            confianza=payload.confianza,
            comentario=payload.comentario,
            segundos=payload.segundos,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Salida de emergencia ────────────────────────────────────────────────────


class UrgenteIn(BaseModel):
    aplicacion_id: int
    motivo: str


@router.post("/urgente", status_code=201)
async def marcar_urgente(
    payload: UrgenteIn,
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """
    El evaluador vio algo que no puede esperar.

    Existe por obligación ética, no por completitud: si alguien lee una frase
    clínicamente urgente mientras etiqueta, no puede quedarse callado hasta
    que termine el estudio. Deja una nota clínica sobre el alumno para que la
    psicóloga a cargo la vea en su panel, y no revela nada del modelo al
    evaluador.
    """
    from app.models.bank import AplicacionCuestionario
    from app.services.notes_service import NotesService

    apl = (
        db.query(AplicacionCuestionario)
        .filter(AplicacionCuestionario.id == payload.aplicacion_id)
        .first()
    )
    if apl is None:
        raise HTTPException(404, f"No existe la aplicación #{payload.aplicacion_id}.")
    if not (payload.motivo or "").strip():
        raise HTTPException(400, "Hay que escribir el motivo.")

    nota = NotesService.crear(
        db,
        estudiante_id=apl.estudiante_id,
        psicologo_id=apl.psicologo_id,
        texto=(
            f"[URGENTE desde etiquetado ciego] Marcado por "
            f"{current_user.nombre} {current_user.apellido} sobre el "
            f"cuestionario #{apl.id}.\n\n{payload.motivo.strip()}"
        ),
        etiqueta="alerta",
    )
    logger.warning(
        "Caso marcado urgente durante el etiquetado: aplicación %s por %s",
        apl.id, current_user.email,
    )
    return {"nota_id": nota.id, "avisado": True}


# ── Métricas ────────────────────────────────────────────────────────────────


@router.get("/metricas")
async def metricas(
    solo_mias: bool = Query(
        False, description="Restringir a las etiquetas de este evaluador"
    ),
    current_user: User = Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """
    Cuánto se equivocó el modelo, contra las etiquetas humanas.

    Conviene mirarlo **después** de cerrar el etiquetado. Consultarlo a mitad
    de camino y seguir etiquetando es tocar el resultado: el criterio deja de
    ser independiente de lo que uno ya vio que le conviene.
    """
    return MetricasEtiquetadoService.metricas(
        db, evaluador_id=current_user.id if solo_mias else None
    )


# ── Dataset para reentrenar ─────────────────────────────────────────────────


def _csv(filas: list[dict], nombre: str) -> Response:
    if not filas:
        raise HTTPException(404, "Todavía no hay etiquetas para exportar.")
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(filas[0].keys()))
    w.writeheader()
    w.writerows(filas)
    return Response(
        # utf-8-sig para que Excel no destroce los acentos si alguien lo abre.
        content=buf.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get("/dataset/frases.csv")
async def dataset_frases(
    _psi=Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """Etiquetas de frases con el texto y los scores del modelo — dataset listo."""
    return _csv(EtiquetadoService.dataset_frases(db), "etiquetas_frases.csv")


@router.get("/dataset/casos.csv")
async def dataset_casos(
    _psi=Depends(require_role("psicologo", "admin")),
    db: Session = Depends(get_db),
):
    """
    Etiquetas de casos. `y_riesgo` es el objetivo de entrenamiento que no sale
    de los cortes de Lovibond — es lo que permite reentrenar el SVM contra
    criterio clínico en vez de contra la fórmula con la que ya se entrenó.
    """
    return _csv(EtiquetadoService.dataset_casos(db), "etiquetas_casos.csv")
