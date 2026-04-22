import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuración de la aplicación"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/mental_health"
    )
    
    # NLP
    MODEL_NAME: str = "joeddav/xlm-roberta-large-xnli"
    MAX_QUESTIONS: int = 10
    DEVICE: int = -1  # -1 = CPU, 0 = GPU
    
    # App
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Mental Health Chatbot"
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

settings = Settings()