from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router
from app.database import engine, Base
from app.utils.logger import get_logger
from app.services.nlp_service import NLPService
import logging

# Configura logging global (handler en el logger "app" — todos los hijos heredan)
get_logger("app")
logger = get_logger(__name__)

# Crea tablas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mental Health Chatbot API",
    description="API para evaluación de bienestar emocional",
    version="1.0.0"
)

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
    
    # Info del modelo
    info_modelo = NLPService.obtener_info_modelo()
    logger.info("   Información del modelo NLP:")
    logger.info(f"      Modelo: {info_modelo['modelo']}")
    logger.info(f"      Dispositivo: {info_modelo['dispositivo']}")
    logger.info(f"      Estado: {'🟢 Listo para cargar' if not info_modelo['cargado'] else '🔋 Ya cargado'}")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 80)
    logger.info("🛑 DETENIENDO APLICACIÓN")
    logger.info("=" * 80)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "mensaje": "Bienvenido a Mental Health Chatbot API",
        "documentación": "http://localhost:8000/docs",
        "version": "1.0.0"
    }