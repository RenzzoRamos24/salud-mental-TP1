"""
NLPService — Clasificación zero-shot multi-label con BETO / XLM-RoBERTa.

Modelo: Recognai/bert-base-spanish-wwm-cased-xnli (BETO + XNLI).
Uso en Sami: clasificar respuestas abiertas (frases incompletas) en categorías
emocionales (tristeza, ansiedad, soledad, ira, miedo, ideación, esperanza,
neutral). El servicio mantiene una única instancia del pipeline en memoria
(singleton thread-safe) para que la inferencia sea instantánea tras la primera
carga.
"""
import logging
import threading
import time
from datetime import datetime
from transformers import pipeline
from app.config import settings

logger = logging.getLogger(__name__)


# Categorías emocionales que clasificamos sobre las frases incompletas.
# Una respuesta puede tener varias etiquetas (multi-label).
CATEGORIAS_EMOCIONALES = {
    "tristeza":         "Este texto expresa tristeza o desánimo.",
    "ansiedad":         "Este texto expresa ansiedad o preocupación.",
    "soledad":          "Este texto expresa soledad o aislamiento.",
    "ira":              "Este texto expresa enojo o frustración.",
    "miedo":            "Este texto expresa miedo o temor.",
    "ideacion_suicida": "Este texto expresa deseos de hacerse daño o pensamientos sobre la muerte.",
    "esperanza":        "Este texto expresa esperanza o motivación.",
    "neutral":          "Este texto es neutro y no expresa una emoción intensa.",
}

# Umbral por defecto para considerar una etiqueta "detectada".
UMBRAL_DETECCION = 0.50
# La ideación suicida activa la bandera de crisis con un umbral más bajo
# (preferimos un falso positivo a perder un caso real).
UMBRAL_CRISIS = 0.40


class NLPService:
    """Singleton thread-safe para el pipeline BETO zero-shot."""

    _classifier = None
    _lock = threading.Lock()
    _is_loading = False
    _load_time = None
    _load_timestamp = None

    # ── Carga del modelo ───────────────────────────────────────────────

    @classmethod
    def get_classifier(cls):
        if cls._classifier is None:
            with cls._lock:
                if cls._classifier is None:
                    cls._is_loading = True
                    tiempo_inicio = time.time()
                    cls._load_timestamp = datetime.utcnow().isoformat()

                    logger.info("Cargando modelo NLP: %s", settings.MODEL_NAME)
                    try:
                        cls._classifier = pipeline(
                            "zero-shot-classification",
                            model=settings.MODEL_NAME,
                            device=settings.DEVICE,
                        )
                        cls._load_time = time.time() - tiempo_inicio
                        logger.info("Modelo cargado en %.2fs", cls._load_time)
                    except Exception as e:
                        logger.error("Error cargando modelo NLP: %s", e)
                        raise
                    finally:
                        cls._is_loading = False
        return cls._classifier

    @classmethod
    def modelo_cargado(cls) -> bool:
        return cls._classifier is not None

    @classmethod
    def esta_cargando(cls) -> bool:
        return cls._is_loading

    @classmethod
    def obtener_info_modelo(cls) -> dict:
        return {
            "cargado": cls.modelo_cargado(),
            "cargando": cls.esta_cargando(),
            "modelo": settings.MODEL_NAME,
            "dispositivo": settings.DEVICE,
            "timestamp_carga": cls._load_timestamp,
            "tiempo_carga_segundos": cls._load_time,
            "categorias": list(CATEGORIAS_EMOCIONALES.keys()),
        }

    # ── Clasificación de una frase ─────────────────────────────────────

    @classmethod
    def clasificar_frase(cls, texto: str) -> dict:
        """
        Clasifica una respuesta a frase incompleta en las 8 categorías
        emocionales. Devuelve:
            {
              "scores": {categoria: prob_float, ...},  # todas las categorías
              "detectadas": [categoria, ...],          # las que superan umbral
              "crisis": bool,                          # ideación >= UMBRAL_CRISIS
              "dominante": categoria_con_max_score,
            }
        """
        if not texto or not texto.strip():
            return {
                "scores": {k: 0.0 for k in CATEGORIAS_EMOCIONALES},
                "detectadas": [],
                "crisis": False,
                "dominante": None,
            }

        classifier = cls.get_classifier()
        claves = list(CATEGORIAS_EMOCIONALES.keys())
        hipotesis = [CATEGORIAS_EMOCIONALES[k] for k in claves]
        hipotesis_a_clave = dict(zip(hipotesis, claves))

        resultado = classifier(
            texto.strip(),
            candidate_labels=hipotesis,
            multi_label=True,
        )

        scores = {}
        for hip, score in zip(resultado["labels"], resultado["scores"]):
            scores[hipotesis_a_clave[hip]] = float(score)

        detectadas = [k for k, v in scores.items() if v >= UMBRAL_DETECCION and k != "neutral"]
        crisis = scores.get("ideacion_suicida", 0.0) >= UMBRAL_CRISIS
        dominante = max(scores, key=scores.get) if scores else None

        return {
            "scores": {k: round(v, 4) for k, v in scores.items()},
            "detectadas": detectadas,
            "crisis": crisis,
            "dominante": dominante,
        }

    @classmethod
    def clasificar_frases(cls, textos: list[str]) -> list[dict]:
        """Aplica `clasificar_frase` a una lista. Devuelve la lista de resultados."""
        return [cls.clasificar_frase(t) for t in textos]
