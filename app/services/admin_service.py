"""
Servicio admin: usuarios, auditoría, backups y métricas de cuestionarios.
"""
import json
import shutil
import os
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.user import User
from app.models.configuracion import Configuracion
from app.models.access_log import AccessLog
from app.models.bank import AplicacionCuestionario, PlantillaCuestionario, BloqueCustom


# `BACKUP_DIR` permite sacar los respaldos de `wwwroot`, que cada despliegue pisa
# (en Azure App Service conviene `/home/backups`, que sí persiste).
BACKUPS_DIR = os.environ.get("BACKUP_DIR") or os.path.join(
    os.path.dirname(__file__), "..", "..", "backups"
)
EXTENSIONES_BACKUP = (".db", ".json.gz")


def _es_postgres() -> bool:
    from app.config import settings
    return settings.DATABASE_URL.startswith(("postgres://", "postgresql"))


def _volcar_logico(destino: str) -> None:
    """Volcado lógico de todas las tablas a JSON comprimido (QA CP066/CP073).

    Con PostgreSQL no hay archivo de base que copiar. Es un respaldo de
    datos (tabla → filas), útil para auditar y reconstruir; no reemplaza un
    `pg_dump` ni los respaldos administrados del servidor. Contiene respuestas
    de menores: el archivo se crea con permisos 0600.
    """
    import gzip
    from sqlalchemy import MetaData, select
    from app.database import engine

    md = MetaData()
    md.reflect(bind=engine)
    fd = os.open(destino, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with gzip.GzipFile(fileobj=os.fdopen(fd, "wb"), mode="wb") as gz:
        volcado = {}
        with engine.connect() as conn:
            for t in sorted(md.tables.values(), key=lambda t: t.name):
                volcado[t.name] = [dict(r._mapping) for r in conn.execute(select(t))]
        gz.write(json.dumps(
            {"generado_utc": datetime.utcnow().isoformat(), "tablas": volcado},
            default=str, ensure_ascii=False,
        ).encode("utf-8"))


def _get_config(db: Session, clave: str, default=None):
    row = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    return json.loads(row.valor) if row else default


def _set_config(db: Session, clave: str, valor):
    row = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if row:
        row.valor = json.dumps(valor, ensure_ascii=False)
        row.updated_at = datetime.utcnow()
    else:
        db.add(Configuracion(clave=clave, valor=json.dumps(valor, ensure_ascii=False)))
    db.commit()


class AdminService:

    # ── Usuarios ────────────────────────────────────────────────────────────

    @staticmethod
    def listar_usuarios(db: Session, role: Optional[str] = None) -> list[User]:
        q = db.query(User)
        if role:
            q = q.filter(User.role == role)
        return q.order_by(User.created_at.desc()).all()

    @staticmethod
    def stats(db: Session) -> dict:
        usuarios = db.query(User).all()
        return {
            "total": len(usuarios),
            "estudiantes": sum(1 for u in usuarios if u.role == "estudiante"),
            "psicologos": sum(1 for u in usuarios if u.role == "psicologo"),
            "admins": sum(1 for u in usuarios if u.role == "admin"),
            "activos": sum(1 for u in usuarios if u.activo),
            "inactivos": sum(1 for u in usuarios if not u.activo),
        }

    # ── Auditoría ───────────────────────────────────────────────────────────

    @staticmethod
    def get_audit_logs(
        db: Session,
        limit: int = 100,
        offset: int = 0,
        role: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> dict:
        q = db.query(AccessLog).order_by(desc(AccessLog.timestamp))
        if role:
            q = q.filter(AccessLog.role == role)
        if endpoint:
            q = q.filter(AccessLog.endpoint.contains(endpoint))
        total = q.count()
        logs = q.offset(offset).limit(limit).all()
        return {
            "total": total,
            "logs": [
                {
                    "id": l.id,
                    "user_id": l.user_id,
                    "email": l.email,
                    "role": l.role,
                    "method": l.method,
                    "endpoint": l.endpoint,
                    "status_code": l.status_code,
                    "ip": l.ip,
                    "timestamp": l.timestamp,
                }
                for l in logs
            ],
        }

    # ── Respaldos ───────────────────────────────────────────────────────────

    @staticmethod
    def crear_backup() -> dict:
        from app.config import settings
        if _es_postgres():
            os.makedirs(BACKUPS_DIR, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            dest = os.path.join(BACKUPS_DIR, f"backup_{ts}.json.gz")
            _volcar_logico(dest)
            return {"archivo": os.path.basename(dest),
                    "tamanio_bytes": os.path.getsize(dest), "timestamp": ts}
        db_path = settings.DATABASE_URL.replace("sqlite:///./", "").replace("sqlite:///", "")
        if not os.path.isabs(db_path):
            db_path = os.path.join(os.path.dirname(__file__), "..", "..", db_path)
        db_path = os.path.normpath(db_path)

        os.makedirs(BACKUPS_DIR, exist_ok=True)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(BACKUPS_DIR, f"backup_{ts}.db")
        shutil.copy2(db_path, dest)
        size = os.path.getsize(dest)
        return {"archivo": os.path.basename(dest), "tamanio_bytes": size, "timestamp": ts}

    @staticmethod
    def listar_backups() -> list[dict]:
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        archivos = sorted(
            [f for f in os.listdir(BACKUPS_DIR) if f.endswith(EXTENSIONES_BACKUP)],
            reverse=True,
        )
        return [
            {
                "archivo": nombre,
                "tamanio_bytes": os.path.getsize(os.path.join(BACKUPS_DIR, nombre)),
                "fecha": datetime.utcfromtimestamp(
                    os.path.getmtime(os.path.join(BACKUPS_DIR, nombre))
                ).isoformat(),
            }
            for nombre in archivos
        ]

    # ── Modelo NLP ──────────────────────────────────────────────────────────

    @staticmethod
    def get_modelo_info() -> dict:
        from app.services.nlp_service import NLPService
        return NLPService.obtener_info_modelo()

    @staticmethod
    def recargar_modelo() -> dict:
        from app.services.nlp_service import NLPService
        with NLPService._lock:
            NLPService._classifier = None
            NLPService._is_loading = False
            NLPService._load_time = None
            NLPService._load_timestamp = None
        return {"mensaje": "Modelo descargado. Se recargará en la próxima inferencia."}

    # ── Asignación ─────────────────────────────────────────────────────────

    @staticmethod
    def asignar_psicologo(db: Session, estudiante_id: str, psicologo_id: str | None) -> dict:
        est = (
            db.query(User)
            .filter(User.id == estudiante_id, User.role == "estudiante")
            .first()
        )
        if not est:
            raise ValueError("Estudiante no encontrado")
        if psicologo_id:
            psi = (
                db.query(User)
                .filter(User.id == psicologo_id, User.role == "psicologo")
                .first()
            )
            if not psi:
                raise ValueError("Psicólogo no encontrado o sin ese rol")
        est.psicologo_id = psicologo_id
        db.commit()
        db.refresh(est)
        return {"id": est.id, "psicologo_id": est.psicologo_id}

    # ── Estadísticas de cuestionarios ──────────────────────────────────────

    @staticmethod
    def stats_cuestionarios(db: Session) -> dict:
        total_asignados = db.query(AplicacionCuestionario).count()
        total_completados = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.completada_at.isnot(None))
            .count()
        )
        total_plantillas = db.query(PlantillaCuestionario).count()
        total_bloques_custom = db.query(BloqueCustom).count()

        distribucion = {
            "CRITICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0, "SIN_RIESGO": 0,
        }
        rows = (
            db.query(AplicacionCuestionario.riesgo_global, func.count(AplicacionCuestionario.id))
            .filter(AplicacionCuestionario.riesgo_global.isnot(None))
            .group_by(AplicacionCuestionario.riesgo_global)
            .all()
        )
        for nivel, n in rows:
            clave = (nivel or "").upper().replace("Í", "I")
            if clave in distribucion:
                distribucion[clave] = int(n)

        return {
            "total_asignados": total_asignados,
            "total_completados": total_completados,
            # QA CP102: lo que falta por responder (asignados sin resultado)
            "total_pendientes": max(total_asignados - total_completados, 0),
            "tasa_completitud_pct": round(
                100 * total_completados / total_asignados, 1
            ) if total_asignados else 0,
            "total_plantillas": total_plantillas,
            "total_bloques_custom": total_bloques_custom,
            "distribucion_riesgo": distribucion,
        }

    # ── Compatibilidad ──────────────────────────────────────────────────────

    @staticmethod
    def aplicar_config_inicio(db: Session):
        """Hook de startup: re-aplica los parámetros generales guardados (HU0021)."""
        from app.services import config_service
        return config_service.cargar_en_settings(db)
