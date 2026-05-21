from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router
from app.database import engine, Base, SessionLocal
from app.utils.logger import get_logger
from app.services.nlp_service import NLPService
from app.middleware.access_log import AccessLogMiddleware
import logging

# Configura logging global
get_logger("app")
logger = get_logger(__name__)

# Crea tablas (incluyendo configuraciones, access_logs y citas)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mental Health Chatbot API",
    description="API para evaluación de bienestar emocional",
    version="1.0.0"
)

# Middleware de auditoría (HU-22) — antes de CORS para capturar todos los accesos
app.add_middleware(AccessLogMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluye routers
app.include_router(api_router, prefix="/api/v1")

# Evento de startup
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 INICIANDO APLICACIÓN")
    logger.info("=" * 80)
    logger.info("   API: Mental Health Chatbot")
    logger.info("   Version: 1.0.0")
    logger.info("   Documentación: http://localhost:8000/docs")
    logger.info("")

    # Aplicar configuración dinámica guardada en BD (umbrales BERT + preguntas)
    try:
        from app.services.admin_service import AdminService
        db = SessionLocal()
        AdminService.aplicar_config_inicio(db)
        db.close()
        logger.info("   Configuración dinámica cargada desde BD")
    except Exception as e:
        logger.warning(f"   No se pudo cargar config desde BD: {e}")

    # Info del modelo
    info_modelo = NLPService.obtener_info_modelo()
    logger.info("   Información del modelo NLP:")
    logger.info(f"      Modelo: {info_modelo['modelo']}")
    logger.info(f"      Dispositivo: {info_modelo['dispositivo']}")
    logger.info(f"      Estado: {'🟢 Listo para cargar' if not info_modelo['cargado'] else '🔋 Ya cargado'}")
    logger.info("=" * 80)

    # HU-23: scheduler de backups automáticos diarios
    try:
        from app.services.scheduler_service import iniciar_scheduler
        iniciar_scheduler()
    except Exception as e:
        logger.warning(f"   No se pudo iniciar el scheduler de backups: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 80)
    logger.info("🛑 DETENIENDO APLICACIÓN")
    logger.info("=" * 80)
    try:
        from app.services.scheduler_service import detener_scheduler
        detener_scheduler()
    except Exception:
        pass

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "mensaje": "Bienvenido a Mental Health Chatbot API",
        "documentación": "http://localhost:8000/docs",
        "version": "1.0.0"
    }