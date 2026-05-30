"""
Endpoints del Diario digital del estudiante.

Convive con `/chatbot/*` (no lo reemplaza todavía). Solo estudiantes
autenticados pueden crear y leer sus propias entradas. El psicólogo verá
estas entradas desde sus propios endpoints en el Paso 3.
"""
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.diario_entrada import DiarioEntrada  # noqa: F401  (Base.metadata)
from app.models.diario_analisis import DiarioAnalisis  # noqa: F401  (Base.metadata)
from app.models.psicologo_mensaje import PsicologoMensaje
from app.schemas.diario import (
    DiarioEntradaIn,
    DiarioEntradaOut,
    DiarioEntradaResumen,
)
from app.services.diario_service import DiarioService
from app.services.diario_analisis_service import analizar_en_background
from app.services.recomendaciones_service import recomendaciones_para_estudiante
from app.services.cita_service import CitaService
from app.services.ciclo_service import info_ciclo_estudiante

logger = logging.getLogger(__name__)

router = APIRouter(tags=["diario"])


def _exigir_estudiante(user: User) -> None:
    if user.role != "estudiante":
        raise HTTPException(
            status_code=403,
            detail="Solo los estudiantes pueden escribir en el diario.",
        )


# ─────────────────────────────────────────────────────────────────────────
# POST /diario/entrada  — guardar una entrada
# ─────────────────────────────────────────────────────────────────────────

@router.post("/entrada", response_model=DiarioEntradaOut, status_code=201)
async def crear_entrada(
    payload: DiarioEntradaIn,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _exigir_estudiante(user)
    try:
        entrada = DiarioService.crear(
            db=db,
            user_id=user.id,
            texto=payload.texto,
            estado_animo=payload.estado_animo,
            prompt_del_dia=payload.prompt_del_dia,
        )
        # El análisis BETO corre detrás para no bloquear el POST. El estudiante
        # recibe respuesta inmediata; el resultado queda disponible para el
        # psicólogo unos segundos después.
        background_tasks.add_task(analizar_en_background, entrada.id)
        return entrada
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error creando entrada de diario: {e}")
        raise HTTPException(status_code=500, detail="Error guardando la entrada.")


# ─────────────────────────────────────────────────────────────────────────
# GET /diario/mis-entradas  — listar las del propio estudiante
# ─────────────────────────────────────────────────────────────────────────

@router.get("/mis-entradas", response_model=List[DiarioEntradaResumen])
async def listar_mis_entradas(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _exigir_estudiante(user)
    return DiarioService.listar_propias(db, user.id)


# ─────────────────────────────────────────────────────────────────────────
# GET /diario/entrada/{id}  — detalle de una entrada propia
# ─────────────────────────────────────────────────────────────────────────

@router.get("/entrada/{entrada_id}", response_model=DiarioEntradaOut)
async def obtener_entrada(
    entrada_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _exigir_estudiante(user)
    try:
        return DiarioService.obtener_propia(db, entrada_id, user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Entrada no encontrada.")


# ─────────────────────────────────────────────────────────────────────────
# GET /diario/recomendaciones  — consejos según lo que escribió
# ─────────────────────────────────────────────────────────────────────────

@router.get("/recomendaciones")
async def mis_recomendaciones(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _exigir_estudiante(user)
    return recomendaciones_para_estudiante(db, user.id)


# ─────────────────────────────────────────────────────────────────────────
# Mensajes del psicólogo dirigidos al estudiante
# ─────────────────────────────────────────────────────────────────────────

@router.get("/mensajes-psicologo")
async def listar_mensajes_psicologo(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _exigir_estudiante(user)
    rows = (
        db.query(PsicologoMensaje)
        .filter(PsicologoMensaje.estudiante_id == user.id)
        .order_by(PsicologoMensaje.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": m.id,
            "mensaje": m.mensaje,
            "leido": m.leido,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "leido_at": m.leido_at.isoformat() if m.leido_at else None,
        }
        for m in rows
    ]


@router.post("/mensajes-psicologo/{mensaje_id}/leido")
async def marcar_mensaje_leido(
    mensaje_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _exigir_estudiante(user)
    m = (
        db.query(PsicologoMensaje)
        .filter(
            PsicologoMensaje.id == mensaje_id,
            PsicologoMensaje.estudiante_id == user.id,
        )
        .first()
    )
    if not m:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado.")
    if not m.leido:
        m.leido = True
        m.leido_at = datetime.utcnow()
        db.commit()
    return {"ok": True, "leido": m.leido}


# ─────────────────────────────────────────────────────────────────────────
# GET /diario/mis-citas — próximas citas con el psicólogo
# ─────────────────────────────────────────────────────────────────────────

@router.get("/mis-citas")
async def mis_citas(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _exigir_estudiante(user)
    return CitaService.listar_estudiante(db, user.id)


# ─────────────────────────────────────────────────────────────────────────
# GET /diario/mi-ciclo — día actual del ciclo + sesiones cerradas
# ─────────────────────────────────────────────────────────────────────────

@router.get("/mi-ciclo")
async def mi_ciclo(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _exigir_estudiante(user)
    try:
        return info_ciclo_estudiante(db, user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ─────────────────────────────────────────────────────────────────────────
# GET /diario/consejo-del-dia
# ─────────────────────────────────────────────────────────────────────────
# Frase corta para mostrar al alumno tras guardar una entrada. Rotación
# determinista por día del año (no aleatoria) para que sea consistente:
# todos los alumnos ven el mismo consejo el mismo día, y mañana es otro.

_CONSEJOS_DEL_DIA = [
    "Escribir lo que sientes es uno de los actos más cuidadosos que podés hacer por vos.",
    "Lo que registres hoy es información valiosa para tu yo de mañana.",
    "No tenés que entenderlo todo. Solo nombrarlo ya cambia algo por dentro.",
    "Cuidarte no es egoísmo — es lo que te permite estar disponible para los demás.",
    "Las emociones son datos, no enemigas. Hoy registraste un dato más.",
    "El hábito de escribir vale más que cualquier entrada perfecta.",
    "Cada vez que escribís, le das forma a algo que antes era niebla.",
    "No estás solo/a en esto. El psicólogo UPC está para acompañarte cuando lo necesites.",
    "Lo que hoy te cuesta nombrar, mañana puede tener otro tamaño.",
    "Dormir bien, moverte y hablar con alguien hacen más por tu ánimo que cualquier consejo.",
    "No tenés que esperar a estar mal para pedir ayuda.",
    "Volver a este espacio mañana ya es suficiente plan.",
]


@router.get("/consejo-del-dia")
async def consejo_del_dia(
    user: User = Depends(get_current_user),
):
    _exigir_estudiante(user)
    from datetime import date

    indice = date.today().timetuple().tm_yday % len(_CONSEJOS_DEL_DIA)
    return {"consejo": _CONSEJOS_DEL_DIA[indice]}
