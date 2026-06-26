import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuración de la aplicación."""

    # ── Base de datos ────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mental_health.db")

    # ── Modelo NLP ───────────────────────────────────────────────────────
    # BETO + XNLI (Recognai/bert-base-spanish-wwm-cased-xnli) usado en
    # `NLPService` para clasificar respuestas a frases incompletas (zero-shot
    # multi-label sobre 8 categorías emocionales).
    MODEL_NAME: str = os.getenv(
        "MODEL_NAME",
        "Recognai/bert-base-spanish-wwm-cased-xnli",
    )
    DEVICE: int = int(os.getenv("DEVICE", "-1"))  # -1 = CPU, 0+ = GPU

    # ── App ──────────────────────────────────────────────────────────────
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Sami — Salud Mental"

    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]

    # ── Autenticación ────────────────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production-please")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    PASSWORD_RESET_TOKEN_MINUTOS: int = 15
    CONSENT_VERSION_ACTUAL: str = "1.0"

    # ── Backups automáticos ─────────────────────────────────────────────
    BACKUP_HORA_DIARIA: int = int(os.getenv("BACKUP_HORA_DIARIA", "2"))
    BACKUP_RETENCION_DIAS: int = int(os.getenv("BACKUP_RETENCION_DIAS", "14"))

    # ── OAuth (Google / Microsoft) ──────────────────────────────────────
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")
    MICROSOFT_TENANT: str = os.getenv("MICROSOFT_TENANT", "common")
    OAUTH_REDIRECT_URI: str = os.getenv(
        "OAUTH_REDIRECT_URI", "http://localhost:5173/oauth-callback"
    )


settings = Settings()
