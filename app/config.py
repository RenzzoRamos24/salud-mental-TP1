import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuración de la aplicación"""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./mental_health.db"
    )

    # NLP — BERT multilingüe fine-tuned en XNLI para zero-shot en español
    # BETO (BERT en español) + XNLI permite clasificación multi-etiqueta sin traducción.
    MODEL_NAME: str = os.getenv(
        "MODEL_NAME",
        "Recognai/bert-base-spanish-wwm-cased-xnli"
    )
    MAX_QUESTIONS: int = 10
    DEVICE: int = -1  # -1 = CPU, 0 = GPU

    # Plantilla de hipótesis en español (crítica para precisión del zero-shot)
    HYPOTHESIS_TEMPLATE: str = "Este texto expresa {}."

    # Condiciones clínicas a detectar.
    # Cada clave interna tiene (a) la hipótesis para el modelo y (b) un umbral calibrado.
    # Umbrales más bajos = mayor sensibilidad (importante en riesgo suicida).
    CONDICIONES: dict = {
        "depresion": {
            "hipotesis": "síntomas de depresión, tristeza profunda y desesperanza",
            "umbral": 0.55,
            "etiqueta": "Depresión",
        },
        "ansiedad": {
            "hipotesis": "síntomas de ansiedad, preocupación excesiva y nerviosismo",
            "umbral": 0.55,
            "etiqueta": "Ansiedad",
        },
        "tdah": {
            "hipotesis": "dificultad de atención, concentración, impulsividad o hiperactividad propia del TDAH",
            "umbral": 0.50,
            "etiqueta": "TDAH (déficit de atención / hiperactividad)",
        },
        "estres_academico": {
            "hipotesis": "estrés académico, sobrecarga universitaria y agotamiento por estudios",
            "umbral": 0.55,
            "etiqueta": "Estrés académico",
        },
        "soledad": {
            "hipotesis": "sentimientos de soledad, aislamiento social y falta de apoyo",
            "umbral": 0.55,
            "etiqueta": "Soledad / aislamiento",
        },
        "riesgo_suicida": {
            "hipotesis": "ideación suicida, pensamientos de autolesión o de no querer seguir viviendo",
            "umbral": 0.40,  # sensibilidad alta por seguridad clínica
            "etiqueta": "Riesgo suicida / autolesión",
        },
        "estabilidad": {
            "hipotesis": "bienestar emocional, estabilidad psicológica y equilibrio mental",
            "umbral": 0.60,
            "etiqueta": "Estabilidad emocional",
        },
    }

    # Keywords clínicos en español (booster de precisión).
    # Refuerzan el score del modelo cuando aparecen términos diagnósticos explícitos.
    KEYWORDS: dict = {
        "depresion": [
            "triste", "vacío", "vacia", "deprim", "sin ganas", "desesperanza",
            "no disfruto", "sin sentido", "llor", "inútil", "cansad", "agotad",
            "nada me importa", "no tengo ánimo", "sin motivación",
        ],
        "ansiedad": [
            "ansi", "nervios", "preocup", "miedo", "pánico", "panico",
            "taquicardia", "agobi", "respirar", "tenso", "tensa", "inquiet",
            "no puedo parar de pensar", "sobrepensar",
        ],
        "tdah": [
            "concentr", "distra", "impulsiv", "inquiet", "disper",
            "me olvido", "no termino", "me aburro rápido", "mente acelerada",
            "no puedo quedarme quiet", "hiperactiv", "postergar",
        ],
        "estres_academico": [
            "estres", "estrés", "carga", "exámen", "examen", "agobiad",
            "saturad", "no me alcanza el tiempo", "presión", "presion",
            "trabajos", "entregas", "parcial",
        ],
        "soledad": [
            "solo", "sola", "aislad", "nadie", "extraño a", "lejos de",
            "sin amigos", "no tengo con quien", "provincia", "familia lejos",
        ],
        "riesgo_suicida": [
            "morir", "no estar", "hacerme daño", "suicid", "no quiero vivir",
            "terminar con todo", "desaparecer", "no despertar",
            "mejor no estar", "cortar", "autolesion", "autolesión",
        ],
    }

    # Boost de keywords: cada match suma este valor (capeado en MAX_BOOST)
    KEYWORD_BOOST_PER_MATCH: float = 0.05
    KEYWORD_BOOST_MAX: float = 0.25

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

    # ─────────────────────────────────────────────────────────────────
    # AUTENTICACIÓN
    # ─────────────────────────────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production-please")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h

    # Recuperación de contraseña
    PASSWORD_RESET_TOKEN_MINUTOS: int = 15

    # Consentimiento informado
    CONSENT_VERSION_ACTUAL: str = "1.0"

settings = Settings()
