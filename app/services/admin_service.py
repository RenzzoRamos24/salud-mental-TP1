"""
Servicio admin: usuarios, configuración, auditoría, backups y modelo BERT.
Sprint 6: HU-21, HU-22, HU-23, HU-24, HU-36.
"""
import json
import shutil
import os
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.configuracion import Configuracion
from app.models.access_log import AccessLog

# ── Claves de configuración ───────────────────────────────────────────────────
_KEY_PREGUNTAS = "preguntas_encuesta"
_KEY_FRECUENCIA = "frecuencia_evaluacion_dias"
_KEY_UMBRALES = "bert_umbrales"
# HU-39: mensajes del chatbot editables por el admin (saludo, cierre, acuses, etc.)
_KEY_CHATBOT_MSGS = "chatbot_messages"

BACKUPS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backups")


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

    # ── Usuarios ──────────────────────────────────────────────────────────────

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

    # ── HU-21: Configuración de encuesta ─────────────────────────────────────
    #
    # NOTA CLÍNICA: las preguntas son ahora ítems validados PHQ-9 + GAD-7
    # (con criterio DSM-5 mapeado). No se permite que el admin las edite,
    # porque alterar la redacción rompe la validez psicométrica de la escala.
    # El admin sí puede ajustar la frecuencia de evaluación.

    @staticmethod
    def get_encuesta(db: Session) -> dict:
        from app.services.session_service import SessionService
        frecuencia = _get_config(db, _KEY_FRECUENCIA, 7)
        return {
            "preguntas": SessionService.PREGUNTAS,
            "frecuencia_dias": frecuencia,
            "escala": "PHQ-9 + GAD-7",
            "editable": False,
            "nota": (
                "Las preguntas son ítems clínicos validados (PHQ-9 / GAD-7) "
                "y no son editables. Solo la frecuencia es configurable."
            ),
        }

    @staticmethod
    def update_encuesta(db: Session, preguntas=None, frecuencia_dias: int = None) -> dict:
        if frecuencia_dias is not None:
            _set_config(db, _KEY_FRECUENCIA, frecuencia_dias)
        from app.services.session_service import SessionService
        return {
            "preguntas": SessionService.PREGUNTAS,
            "frecuencia_dias": _get_config(db, _KEY_FRECUENCIA, 7),
            "nota": (
                "Las preguntas PHQ-9 / GAD-7 están bloqueadas por integridad clínica. "
                "Solo se actualizó la frecuencia."
            ),
        }

    # ── HU-22: Auditoría de accesos ───────────────────────────────────────────

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

    # ── HU-23: Respaldos de la BD ─────────────────────────────────────────────

    @staticmethod
    def crear_backup() -> dict:
        from app.config import settings
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
            [f for f in os.listdir(BACKUPS_DIR) if f.endswith(".db")],
            reverse=True,
        )
        resultado = []
        for nombre in archivos:
            ruta = os.path.join(BACKUPS_DIR, nombre)
            resultado.append({
                "archivo": nombre,
                "tamanio_bytes": os.path.getsize(ruta),
                "fecha": datetime.utcfromtimestamp(os.path.getmtime(ruta)).isoformat(),
            })
        return resultado

    # ── HU-36: Umbrales del modelo BERT ──────────────────────────────────────

    @staticmethod
    def get_umbrales(db: Session) -> dict:
        from app.config import settings
        umbrales_db = _get_config(db, _KEY_UMBRALES, None)
        if umbrales_db:
            return umbrales_db
        # Fallback: leer de settings
        return {
            clave: {
                "umbral": cfg["umbral"],
                "etiqueta": cfg["etiqueta"],
                "hipotesis": cfg["hipotesis"],
            }
            for clave, cfg in settings.CONDICIONES.items()
        }

    @staticmethod
    def update_umbrales(db: Session, umbrales: dict) -> dict:
        from app.config import settings
        # Persistir en BD
        _set_config(db, _KEY_UMBRALES, umbrales)
        # Aplicar en caliente
        for clave, vals in umbrales.items():
            if clave in settings.CONDICIONES and "umbral" in vals:
                settings.CONDICIONES[clave]["umbral"] = float(vals["umbral"])
        return umbrales

    # ── HU-24: Gestión del modelo BERT ────────────────────────────────────────

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
        return {"mensaje": "Modelo descargado de memoria. Se recargará en la próxima inferencia."}

    # ── HU-38: Asignar estudiante a psicólogo ────────────────────────────────

    @staticmethod
    def asignar_psicologo(db: Session, estudiante_id: str, psicologo_id: str | None) -> dict:
        from app.models.user import User
        est = db.query(User).filter(User.id == estudiante_id, User.role == "estudiante").first()
        if not est:
            raise ValueError("Estudiante no encontrado")
        if psicologo_id:
            psi = db.query(User).filter(User.id == psicologo_id, User.role == "psicologo").first()
            if not psi:
                raise ValueError("Psicólogo no encontrado o sin ese rol")
        est.psicologo_id = psicologo_id
        db.commit()
        db.refresh(est)
        return {"id": est.id, "psicologo_id": est.psicologo_id}

    # ── HU-39: Mensajes del chatbot personalizables por el admin ─────────────

    DEFAULT_CHATBOT_MSGS = {
        "saludo_inicial": (
            "¡Hola{nombre_coma_espacio}! ¿Cómo puedo ayudarte? Cuéntame con tus palabras "
            "qué te trae por aquí — cómo te has estado sintiendo en el cole, en casa, "
            "con tus amigos o con cualquier otra cosa. Lo que escribas queda entre nosotros."
        ),
        "bot_nombre": "Sami",
        "tagline": "En línea · Opinion-BERT activo",
        "cierre_resultados": "¿Estás listo para ver tus resultados?",
        "footer_chat": "🔒 Tus respuestas son confidenciales · Procesado con Opinion-BERT · Mapeado a DSM-5",
    }

    @staticmethod
    def get_chatbot_messages(db: Session) -> dict:
        custom = _get_config(db, _KEY_CHATBOT_MSGS, {}) or {}
        return {**AdminService.DEFAULT_CHATBOT_MSGS, **custom}

    @staticmethod
    def update_chatbot_messages(db: Session, mensajes: dict) -> dict:
        # Validamos las claves para no aceptar basura.
        valid_keys = set(AdminService.DEFAULT_CHATBOT_MSGS.keys())
        clean = {k: v for k, v in (mensajes or {}).items() if k in valid_keys and isinstance(v, str)}
        existente = _get_config(db, _KEY_CHATBOT_MSGS, {}) or {}
        nuevo = {**existente, **clean}
        _set_config(db, _KEY_CHATBOT_MSGS, nuevo)
        return AdminService.get_chatbot_messages(db)

    # ── Carga de config al arrancar ───────────────────────────────────────────

    @staticmethod
    def aplicar_config_inicio(db: Session):
        """
        Aplica umbrales y preguntas guardados en BD al arrancar la app.
        Garantiza que cambios del admin persistan entre reinicios.
        """
        from app.config import settings
        umbrales = _get_config(db, _KEY_UMBRALES, None)
        if umbrales:
            for clave, vals in umbrales.items():
                if clave in settings.CONDICIONES and "umbral" in vals:
                    settings.CONDICIONES[clave]["umbral"] = float(vals["umbral"])

        # Las preguntas PHQ-9/GAD-7 son fijas. Ignoramos cualquier override
        # legado (list[str]) que haya quedado en config para no corromper
        # el banco clínico estructurado.
