"""
HU-23: scheduler de respaldos automáticos.

Usa APScheduler con un AsyncIOScheduler integrado al loop de FastAPI.
Hace backup diario a las 02:00 (servidor) y limpia respaldos viejos
para no llenar el disco.

Configurable vía settings:
  - BACKUP_HORA_DIARIA   (default 2)
  - BACKUP_RETENCION_DIAS (default 14)
"""
import logging
import os
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

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


def iniciar_scheduler() -> AsyncIOScheduler:
    """Llamar UNA vez al startup de la app."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    hora = int(getattr(settings, "BACKUP_HORA_DIARIA", 2))
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _backup_job,
        CronTrigger(hour=hora, minute=0),
        id="backup_diario",
        replace_existing=True,
        name="Respaldo diario de la BD",
    )
    _scheduler.start()
    logger.info(f"⏰ Scheduler iniciado · backup diario a las {hora:02d}:00")
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
