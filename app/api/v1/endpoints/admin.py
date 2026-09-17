"""
Endpoints exclusivos para rol admin (Sprint 9 — cuestionarios).
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.core.deps import require_role
from app.schemas.admin import UsuarioResumen, StatsUsuarios
from app.services.admin_service import AdminService
from app.models.configuracion import Configuracion  # noqa: F401
from app.models.access_log import AccessLog         # noqa: F401
from app.models.user import User

router = APIRouter()


# ── Usuarios ────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UsuarioResumen])
async def listar_usuarios(
    role: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.listar_usuarios(db, role=role)


@router.get("/stats", response_model=StatsUsuarios)
async def stats_usuarios(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.stats(db)


# ── Auditoría ───────────────────────────────────────────────────────────────

@router.get("/audit-logs")
async def get_audit_logs(
    limit: int = Query(100, le=500),
    offset: int = 0,
    role: Optional[str] = None,
    endpoint: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.get_audit_logs(
        db, limit=limit, offset=offset, role=role, endpoint=endpoint
    )


# ── Respaldos ───────────────────────────────────────────────────────────────

@router.post("/backup")
async def crear_backup(_admin=Depends(require_role("admin"))):
    try:
        return AdminService.crear_backup()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def listar_backups(_admin=Depends(require_role("admin"))):
    return AdminService.listar_backups()


# ── Modelo NLP (BETO) ───────────────────────────────────────────────────────

@router.get("/nlp/modelo")
async def get_modelo(_admin=Depends(require_role("admin"))):
    return AdminService.get_modelo_info()


@router.post("/nlp/recargar")
async def recargar_modelo(_admin=Depends(require_role("admin"))):
    return AdminService.recargar_modelo()


# ── Asignación estudiante → psicólogo ───────────────────────────────────────

class AsignacionIn(BaseModel):
    psicologo_id: str | None = None


# HU-55: vinculación padre ↔ estudiante (un padre tutela N estudiantes) ───
class VincularPadreIn(BaseModel):
    padre_id: str
    estudiante_id: str


@router.post("/padres/vincular")
async def vincular_padre_estudiante(
    payload: VincularPadreIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    padre = db.query(User).filter(
        User.id == payload.padre_id, User.role == "padre"
    ).first()
    if not padre:
        raise HTTPException(404, "Padre no encontrado o rol incorrecto.")
    est = db.query(User).filter(
        User.id == payload.estudiante_id, User.role == "estudiante"
    ).first()
    if not est:
        raise HTTPException(404, "Estudiante no encontrado.")
    est.padre_id = padre.id
    db.commit()
    return {
        "ok": True,
        "padre": f"{padre.nombre} {padre.apellido}",
        "estudiante": f"{est.nombre} {est.apellido}",
    }


@router.post("/padres/desvincular")
async def desvincular_padre_estudiante(
    payload: VincularPadreIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    est = db.query(User).filter(
        User.id == payload.estudiante_id, User.role == "estudiante"
    ).first()
    if not est:
        raise HTTPException(404, "Estudiante no encontrado.")
    if est.padre_id != payload.padre_id:
        raise HTTPException(400, "Ese padre no estaba vinculado.")
    est.padre_id = None
    db.commit()
    return {"ok": True}


@router.post("/students/{student_id}/assign-psychologist")
async def asignar_psicologo(
    student_id: str,
    payload: AsignacionIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    try:
        return AdminService.asignar_psicologo(db, student_id, payload.psicologo_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Reasignación masiva del piloto ─────────────────────────────────────────
class ReasignacionMasivaIn(BaseModel):
    psicologo_email: str
    solo_piloto: bool = True  # si True, solo mueve alumnos del piloto colegio


class ReevaluarIn(BaseModel):
    filtro_plantilla_nombre: str = "%Pack C%"  # plantillas a re-evaluar


@router.post("/piloto/re-evaluar-beto")
async def re_evaluar_beto(
    payload: ReevaluarIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    """Re-evalúa aplicaciones ya cerradas con el modelo BETO actualizado.
    Reescribe `resultado_json`, `riesgo_global` y `crisis_activada`.
    """
    from app.models.bank import AplicacionCuestionario, PlantillaCuestionario
    from app.services.evaluator_service import EvaluatorService
    import json as _json

    apps = (
        db.query(AplicacionCuestionario)
        .join(PlantillaCuestionario)
        .filter(PlantillaCuestionario.nombre.like(payload.filtro_plantilla_nombre))
        .all()
    )
    ok, errores = 0, 0
    for a in apps:
        try:
            res = EvaluatorService.evaluar(db, a)
            a.resultado_json = _json.dumps(res, ensure_ascii=False)
            a.riesgo_global = res.get("riesgo_global")
            a.crisis_activada = bool(res.get("crisis_activada"))
            db.commit()
            ok += 1
        except Exception as e:
            db.rollback()
            errores += 1
            logger.warning(f"Re-eval error app_id={a.id}: {e}")
    return {"aplicaciones_encontradas": len(apps),
            "reevaluadas_ok": ok, "errores": errores}


@router.post("/piloto/reasignar-a-psicologo")
async def reasignar_piloto(
    payload: ReasignacionMasivaIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    """
    Mueve todos los alumnos del piloto colegio (los que tienen aplicaciones
    con plantilla 'Piloto Colegio%') a un psicólogo específico.

    Con `solo_piloto=False`, mueve todos los estudiantes del sistema — usar
    con cuidado.
    """
    from app.models.user import User
    from app.models.bank import AplicacionCuestionario, PlantillaCuestionario

    psi = db.query(User).filter(
        User.email == payload.psicologo_email.lower(),
        User.role == "psicologo",
    ).first()
    if not psi:
        raise HTTPException(404, f"No existe psicólogo con email {payload.psicologo_email}")

    # Encuentro los IDs de alumnos afectados usando subquery para portabilidad
    if payload.solo_piloto:
        plantilla_ids_sub = [
            p.id for p in db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.nombre.like("Piloto Colegio%")).all()
        ]
        est_ids = list({
            r[0] for r in
            db.query(AplicacionCuestionario.estudiante_id)
            .filter(AplicacionCuestionario.plantilla_id.in_(plantilla_ids_sub))
            .all()
        })
    else:
        est_ids = [
            u.id for u in db.query(User).filter(User.role == "estudiante").all()
        ]

    if not est_ids:
        return {"reasignados": 0, "aplicaciones_reasignadas": 0}

    # Actualizo el psicólogo responsable
    n_users = (
        db.query(User)
        .filter(User.id.in_(est_ids))
        .update({User.psicologo_id: psi.id}, synchronize_session=False)
    )

    # También actualizo el psicologo_id de las aplicaciones piloto.
    # Uso subquery en vez de JOIN porque UPDATE ... FROM JOIN se comporta
    # distinto en SQLite vs Postgres.
    if payload.solo_piloto:
        plantilla_ids = [
            p.id for p in db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.nombre.like("Piloto Colegio%")).all()
        ]
        n_apps = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.plantilla_id.in_(plantilla_ids))
            .update({AplicacionCuestionario.psicologo_id: psi.id},
                    synchronize_session=False)
        )
    else:
        n_apps = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.estudiante_id.in_(est_ids))
            .update({AplicacionCuestionario.psicologo_id: psi.id},
                    synchronize_session=False)
        )
    db.commit()

    return {
        "psicologo": {"id": psi.id, "email": psi.email,
                      "nombre": f"{psi.nombre} {psi.apellido}"},
        "estudiantes_reasignados": n_users,
        "aplicaciones_reasignadas": n_apps,
    }


# ── Estadísticas de cuestionarios ───────────────────────────────────────────

@router.get("/cuestionarios/stats")
async def cuestionarios_stats(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    return AdminService.stats_cuestionarios(db)


# ── Scheduler ───────────────────────────────────────────────────────────────

@router.get("/scheduler/info")
async def scheduler_info(_admin=Depends(require_role("admin"))):
    from app.services.scheduler_service import info_scheduler
    return info_scheduler()


@router.post("/scheduler/backup-ahora")
async def scheduler_backup_ahora(_admin=Depends(require_role("admin"))):
    from app.services.scheduler_service import disparar_ahora
    return disparar_ahora()
