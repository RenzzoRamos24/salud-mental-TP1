"""
Schedulers automáticos del sistema.

- HU-23: backup diario de la BD a las 02:00 + purga de viejos.
- HU-41: cierre de ciclos cada noche a las 03:00 — marca las aplicaciones
  de cuestionario pendientes / en_progreso con más de 14 días como
  `expirada` para mantener el seguimiento longitudinal coherente.

Configurable vía settings:
  - BACKUP_HORA_DIARIA       (default 2)
  - BACKUP_RETENCION_DIAS    (default 14)
  - CICLO_HORA_DIARIA        (default 3)
  - CICLO_DIAS_VENTANA       (default 14)
"""
import logging
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models.bank import AplicacionCuestionario
from app.services.admin_service import AdminService, BACKUPS_DIR
from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _backup_job():
    """Tarea programada: crear backup + purgar viejos."""
    try:
        resultado = AdminService.crear_backup()
        logger.info(
            f"🗄️  [scheduler] Backup automático creado: {resultado['archivo']} "
            f"({resultado['tamanio_bytes']} bytes)"
        )
        _purgar_viejos()
    except Exception as e:
        logger.error(f"❌ [scheduler] Falló el backup automático: {e}")


def _purgar_viejos():
    """Elimina backups con más de RETENCION_DIAS días."""
    retencion = int(getattr(settings, "BACKUP_RETENCION_DIAS", 14))
    if not os.path.isdir(BACKUPS_DIR):
        return
    limite = datetime.utcnow() - timedelta(days=retencion)
    eliminados = 0
    for nombre in os.listdir(BACKUPS_DIR):
        if not nombre.endswith(".db"):
            continue
        ruta = os.path.join(BACKUPS_DIR, nombre)
        if datetime.utcfromtimestamp(os.path.getmtime(ruta)) < limite:
            try:
                os.remove(ruta)
                eliminados += 1
            except OSError:
                pass
    if eliminados:
        logger.info(f"🧹 [scheduler] Purgados {eliminados} backups > {retencion} días")


def _cierre_ciclos_job():
    """HU-41: marca como `expirada` cada aplicación pendiente/en_progreso
    cuyo plazo de 14 días (configurable) haya pasado desde la asignación.
    Esto cierra el ciclo del estudiante para que pueda abrirse uno nuevo.
    """
    ventana = int(getattr(settings, "CICLO_DIAS_VENTANA", 14))
    limite = datetime.utcnow() - timedelta(days=ventana)
    db = SessionLocal()
    try:
        q = (
            db.query(AplicacionCuestionario)
            .filter(
                AplicacionCuestionario.estado.in_(("pendiente", "en_progreso")),
                AplicacionCuestionario.asignada_at <= limite,
            )
        )
        afectadas = q.count()
        if afectadas:
            q.update({"estado": "expirada"}, synchronize_session=False)
            db.commit()
            logger.info(
                f"♻️  [scheduler] Cierre de ciclo: {afectadas} aplicaciones "
                f"marcadas como expiradas (> {ventana} días)."
            )
        else:
            logger.info("♻️  [scheduler] Cierre de ciclo: sin aplicaciones vencidas.")
    except Exception as e:
        logger.error(f"❌ [scheduler] Falló el cierre de ciclos: {e}")
        db.rollback()
    finally:
        db.close()


def iniciar_scheduler() -> AsyncIOScheduler:
    """Llamar UNA vez al startup de la app."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    hora_backup = int(getattr(settings, "BACKUP_HORA_DIARIA", 2))
    hora_ciclo = int(getattr(settings, "CICLO_HORA_DIARIA", 3))
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _backup_job,
        CronTrigger(hour=hora_backup, minute=0),
        id="backup_diario",
        replace_existing=True,
        name="Respaldo diario de la BD",
    )
    _scheduler.add_job(
        _cierre_ciclos_job,
        CronTrigger(hour=hora_ciclo, minute=0),
        id="cierre_ciclos",
        replace_existing=True,
        name="Cierre de ciclos > 14 días",
    )
    _scheduler.start()
    logger.info(
        f"⏰ Scheduler iniciado · backup {hora_backup:02d}:00 · "
        f"cierre de ciclos {hora_ciclo:02d}:00"
    )
    return _scheduler


def detener_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None


def info_scheduler() -> dict:
    """Para el panel admin: cuándo corre el próximo backup."""
    if not _scheduler:
        return {"activo": False, "jobs": []}
    jobs = []
    for j in _scheduler.get_jobs():
        jobs.append({
            "id": j.id,
            "name": j.name,
            "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
            "trigger": str(j.trigger),
        })
    return {
        "activo": True,
        "hora_diaria": int(getattr(settings, "BACKUP_HORA_DIARIA", 2)),
        "retencion_dias": int(getattr(settings, "BACKUP_RETENCION_DIAS", 14)),
        "jobs": jobs,
    }


def disparar_ahora() -> dict:
    """Ejecuta el job de backup manualmente (útil para probar)."""
    _backup_job()
    return info_scheduler()
