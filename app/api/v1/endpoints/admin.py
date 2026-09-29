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


# ── Piloto: generación de códigos de acceso ─────────────────────────────────

class GenerarCodigosIn(BaseModel):
    psicologa_email: str
    n_4to: int = 52
    n_5to: int = 53


@router.post("/piloto/generar-codigos")
async def generar_codigos_piloto(
    payload: GenerarCodigosIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    """
    Crea (si no existe) la plantilla 'Re-encuesta colegio' con PHQ-A + GAD-7 +
    las 10 frases del piloto, y genera alumnos anónimos SAMI-{4TO,5TO}-NN con
    su AplicacionCuestionario pendiente. Idempotente: código ya existente se
    saltea. Ver scripts/generar_codigos_encuesta.py para la versión CLI
    (equivalente, para correr contra la BD local).
    """
    import uuid
    from datetime import datetime, timedelta
    from app.core.security import hash_password
    from app.models.bank import (
        AplicacionCuestionario, BankInstrumento, PlantillaBloque, PlantillaCuestionario,
    )

    PLANTILLA_NOMBRE = "Re-encuesta colegio · PHQ-A + GAD-7 + frases"
    FRASES_NUMEROS = "1,6,11,13,17,22,23,25,28,31"

    psi = db.query(User).filter(
        User.email == payload.psicologa_email.lower().strip(),
        User.role == "psicologo",
    ).first()
    if not psi:
        raise HTTPException(404, f"No existe psicólogo/a con email '{payload.psicologa_email}'.")

    pl = db.query(PlantillaCuestionario).filter_by(nombre=PLANTILLA_NOMBRE).first()
    if not pl:
        phqa = db.query(BankInstrumento).filter_by(codigo="PHQ-A").first()
        gad7 = db.query(BankInstrumento).filter_by(codigo="GAD-7").first()
        if not phqa or not gad7:
            raise HTTPException(500, "Falta PHQ-A o GAD-7 en el banco — correr seeds primero.")
        pl = PlantillaCuestionario(
            psicologo_id=psi.id, nombre=PLANTILLA_NOMBRE,
            descripcion="PHQ-A + GAD-7 + 10 frases seleccionadas — re-encuesta 4to/5to.",
            activa=1,
        )
        db.add(pl)
        db.flush()
        db.add(PlantillaBloque(plantilla_id=pl.id, orden=1, tipo="instrumento", instrumento_id=phqa.id))
        db.add(PlantillaBloque(plantilla_id=pl.id, orden=2, tipo="instrumento", instrumento_id=gad7.id))
        db.add(PlantillaBloque(plantilla_id=pl.id, orden=3, tipo="frases", frases_numeros=FRASES_NUMEROS))
        db.commit()
    else:
        bloque_frases = db.query(PlantillaBloque).filter_by(plantilla_id=pl.id, tipo="frases").first()
        if bloque_frases and bloque_frases.frases_numeros != FRASES_NUMEROS:
            bloque_frases.frases_numeros = FRASES_NUMEROS
            db.commit()

    filas = []
    for prefijo, grado, cantidad in (
        ("4TO", "4to secundaria", payload.n_4to),
        ("5TO", "5to secundaria", payload.n_5to),
    ):
        for i in range(1, cantidad + 1):
            codigo = f"SAMI-{prefijo}-{i:02d}"
            existente = db.query(User).filter_by(codigo_acceso=codigo).first()
            if existente:
                filas.append({"codigo": codigo, "grado": grado, "estado": "ya existía"})
                continue
            try:
                alumno = User(
                    id=str(uuid.uuid4()),
                    email=f"{codigo.lower()}@piloto.sami.local",
                    hashed_password=hash_password(str(uuid.uuid4())),
                    nombre=f"Alumno {prefijo}", apellido=f"#{i:02d}",
                    role="estudiante", activo=True,
                    psicologo_id=psi.id, grado=grado,
                    estado_caso="activo", codigo_acceso=codigo,
                )
                db.add(alumno)
                db.flush()
                # Sin Consent acá a propósito: el alumno tiene que aceptar
                # los términos él mismo en /consent antes de ver el
                # cuestionario, igual que cualquier otro usuario del sistema.
                db.add(AplicacionCuestionario(
                    plantilla_id=pl.id, estudiante_id=alumno.id, psicologo_id=psi.id,
                    estado="pendiente", asignada_at=datetime.utcnow() - timedelta(minutes=1),
                ))
                db.commit()
                filas.append({"codigo": codigo, "grado": grado, "estado": "nuevo"})
            except Exception as e:
                db.rollback()
                logger.warning(f"Error generando {codigo}: {e}")
                filas.append({"codigo": codigo, "grado": grado, "estado": f"error: {e}"})

    nuevos = sum(1 for f in filas if f["estado"] == "nuevo")
    return {"plantilla_id": pl.id, "total": len(filas), "nuevos": nuevos, "filas": filas}


class ResetPruebaIn(BaseModel):
    codigo_acceso: str


@router.post("/piloto/reset-aplicacion-prueba")
async def reset_aplicacion_prueba(
    payload: ResetPruebaIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    """
    Deshace una verificación de humo hecha sobre un código real del piloto:
    borra respuestas, resultado y encuesta de satisfacción, y vuelve la
    aplicación a 'pendiente' para que el alumno real la responda desde cero.
    """
    from app.models.bank import AplicacionCuestionario, RespuestaAplicacion, ResultadoFeedback
    from app.models.satisfaction_survey import SatisfactionSurvey

    codigo = payload.codigo_acceso.strip().upper()
    alumno = db.query(User).filter_by(codigo_acceso=codigo).first()
    if not alumno:
        raise HTTPException(404, f"No existe alumno con código '{codigo}'.")

    borradas_satisfaccion = (
        db.query(SatisfactionSurvey).filter_by(user_id=alumno.id)
        .delete(synchronize_session=False)
    )

    apps = db.query(AplicacionCuestionario).filter_by(estudiante_id=alumno.id).all()
    reseteadas = []
    for a in apps:
        db.query(ResultadoFeedback).filter_by(aplicacion_id=a.id).delete(synchronize_session=False)
        db.query(RespuestaAplicacion).filter_by(aplicacion_id=a.id).delete(synchronize_session=False)
        a.estado = "pendiente"
        a.iniciada_at = None
        a.completada_at = None
        a.resultado_json = None
        a.riesgo_global = None
        a.crisis_activada = False
        reseteadas.append(a.id)

    db.commit()
    return {
        "codigo": codigo,
        "satisfaction_surveys_borradas": borradas_satisfaccion,
        "aplicaciones_reseteadas": reseteadas,
    }


@router.post("/piloto/quitar-consentimiento-codigos")
async def quitar_consentimiento_codigos(
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    """
    Corrección puntual: los alumnos generados por /piloto/generar-codigos
    (antes de este cambio) quedaban con el consentimiento pre-aceptado por
    el propio script. Ahora el alumno debe aceptarlo él mismo en /consent
    antes de ver el cuestionario — esto borra el consentimiento ya puesto
    a esas cuentas para que la pantalla les aparezca mañana.
    """
    from app.models.consent import Consent

    ids_piloto = [u.id for u in db.query(User).filter(User.codigo_acceso.isnot(None)).all()]
    borrados = (
        db.query(Consent).filter(Consent.user_id.in_(ids_piloto))
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"alumnos_con_codigo": len(ids_piloto), "consentimientos_borrados": borrados}


class BorrarCodigoIn(BaseModel):
    codigo_acceso: str


@router.post("/piloto/borrar-codigo-prueba")
async def borrar_codigo_prueba(
    payload: BorrarCodigoIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_role("admin")),
):
    """
    Borra por completo una cuenta de prueba generada con codigo_acceso —
    usuario, aplicaciones, respuestas, feedback, consentimiento y encuesta
    de satisfacción. Solo actúa sobre cuentas CON codigo_acceso (nunca
    sobre una cuenta normal por accidente).
    """
    from app.models.consent import Consent
    from app.models.bank import AplicacionCuestionario, RespuestaAplicacion, ResultadoFeedback
    from app.models.satisfaction_survey import SatisfactionSurvey

    codigo = payload.codigo_acceso.strip().upper()
    alumno = db.query(User).filter(
        User.codigo_acceso == codigo,
    ).first()
    if not alumno:
        raise HTTPException(404, f"No existe alumno con código '{codigo}'.")

    db.query(SatisfactionSurvey).filter_by(user_id=alumno.id).delete(synchronize_session=False)
    db.query(Consent).filter_by(user_id=alumno.id).delete(synchronize_session=False)
    apps = db.query(AplicacionCuestionario).filter_by(estudiante_id=alumno.id).all()
    for a in apps:
        db.query(ResultadoFeedback).filter_by(aplicacion_id=a.id).delete(synchronize_session=False)
        db.query(RespuestaAplicacion).filter_by(aplicacion_id=a.id).delete(synchronize_session=False)
        db.delete(a)
    db.delete(alumno)
    db.commit()
    return {"codigo": codigo, "borrado": True, "aplicaciones_borradas": len(apps)}
