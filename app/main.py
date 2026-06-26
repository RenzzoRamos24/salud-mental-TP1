"""Sami — FastAPI app entrypoint. Sirve la API y, en producción, el bundle
estático de Vue desde /project/dist."""
import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.database import engine, Base, SessionLocal
from app.middleware.access_log import AccessLogMiddleware
from app.services.nlp_service import NLPService
from app.utils.logger import get_logger

get_logger("app")
logger = get_logger(__name__)

# Crear tablas (incluyendo configuraciones, access_logs y citas).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sami — Salud Mental",
    description="API para evaluación de bienestar emocional",
    version="1.0.0",
)

# Middleware de auditoría (HU-22) — antes de CORS para capturar todos los accesos.
app.add_middleware(AccessLogMiddleware)

# CORS — en producción se sirve todo desde el mismo origen, así que basta con un
# allow_origins amplio. Para dev (Vite en 5173) seguimos abriendo todo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router de la API.
app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("=" * 80)
    logger.info("INICIANDO SAMI")
    logger.info("=" * 80)
    logger.info("   API: Sami — Salud Mental")
    logger.info("   Version: 1.0.0")
    logger.info("   Documentación: /docs")

    try:
        from app.services.admin_service import AdminService

        db = SessionLocal()
        AdminService.aplicar_config_inicio(db)
        db.close()
        logger.info("   Configuración cargada desde BD")
    except Exception as e:
        logger.warning(f"   No se pudo cargar config desde BD: {e}")

    info_modelo = NLPService.obtener_info_modelo()
    logger.info("   Modelo NLP:")
    logger.info(f"      Modelo: {info_modelo['modelo']}")
    logger.info(f"      Dispositivo: {info_modelo['dispositivo']}")
    logger.info(
        f"      Estado: {'cargado' if info_modelo['cargado'] else 'listo para cargar'}"
    )
    logger.info("=" * 80)

    try:
        from app.services.scheduler_service import iniciar_scheduler

        iniciar_scheduler()
    except Exception as e:
        logger.warning(f"   Scheduler no iniciado: {e}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("=" * 80)
    logger.info("DETENIENDO SAMI")
    logger.info("=" * 80)
    try:
        from app.services.scheduler_service import detener_scheduler

        detener_scheduler()
    except Exception:
        pass


# ─── Servir el frontend Vue compilado (en producción) ────────────────────────
# El build de Vite queda en project/dist. En dev, vite sirve en :5173 por
# separado y este bloque no existe (no hay dist).
DIST = Path(__file__).resolve().parent.parent / "project" / "dist"
DIST_ASSETS = DIST / "assets"

if DIST.exists():
    logger.info(f"Sirviendo frontend desde {DIST}")
    app.mount("/assets", StaticFiles(directory=str(DIST_ASSETS)), name="assets")

    @app.get("/", include_in_schema=False)
    async def root_spa() -> FileResponse:
        return FileResponse(str(DIST / "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        # Catch-all: cualquier ruta que no sea /api/v1 ni /assets devuelve el
        # index.html para que Vue Router maneje la navegación.
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            return FileResponse(
                str(DIST / "index.html"), status_code=404
            )
        # Sirve archivos estáticos sueltos (favicon, .svg, etc.) si existen.
        candidato = DIST / full_path
        if candidato.is_file():
            return FileResponse(str(candidato))
        return FileResponse(str(DIST / "index.html"))

else:
    logger.info(
        "Frontend Vue no encontrado en project/dist — modo dev (Vite separado)."
    )

    @app.get("/")
    async def root():
        return {
            "mensaje": "Sami API",
            "documentación": "/docs",
            "version": "1.0.0",
        }
