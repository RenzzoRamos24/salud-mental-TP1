"""
NLPService — Clasificación zero-shot multi-label con BETO / XLM-RoBERTa.

Modelo: Recognai/bert-base-spanish-wwm-cased-xnli (BETO + XNLI).
Uso en Sami: clasificar respuestas abiertas (frases incompletas) en dos
dimensiones clínicamente alineadas con los instrumentos cuantitativos del
sistema — **depresión** (paralelo a PHQ-A) y **ansiedad** (paralelo a GAD-7).

Se descartaron intencionalmente las otras categorías (ira, miedo, soledad,
esperanza, neutral) para concentrar la señal semántica en las dos dimensiones
que el sistema efectivamente utiliza como criterio de tamizaje. Esto también
alinea el clasificador con las escalas validadas y mejora la precisión en
zero-shot (menos categorías = menos dilución de la probabilidad).
"""
import logging
import threading
import time
from datetime import datetime
from transformers import pipeline
from app.config import settings

logger = logging.getLogger(__name__)


# Categorías clínicamente alineadas con los instrumentos del sistema.
# Se agrega una categoría 'neutral' explícita para forzar competencia
# semántica (softmax) — sin ella, cualquier texto con mínima carga
# negativa disparaba las dos categorías patológicas al mismo tiempo,
# incluyendo respuestas positivas o cotidianas.
CATEGORIAS_EMOCIONALES = {
    "depresion": (
        "Este texto expresa ideas de muerte, ideación suicida, deseo de "
        "desaparecer, desesperanza total sobre el futuro, o sentimientos "
        "profundos e incapacitantes de inutilidad, fracaso o vacío emocional "
        "que impiden funcionar en la vida cotidiana."
    ),
    "ansiedad": (
        "Este texto expresa preocupación persistente e incontrolable, "
        "nerviosismo intenso, tensión física paralizante, miedo severo, "
        "o síntomas de pánico o crisis de angustia."
    ),
    "adaptativo": (
        "Este texto describe afrontamiento saludable, resiliencia, metas "
        "personales, sueños, aspiraciones, esfuerzo para superar "
        "dificultades, crecimiento personal, autoconocimiento, o "
        "estrategias positivas para manejar emociones."
    ),
    "neutral": (
        "Este texto describe actividades cotidianas, hobbies, deportes, "
        "videojuegos, descanso, estudios, personalidad, rasgos de carácter, "
        "relaciones sociales, familia, amistad, agradecimiento, alegría, "
        "aburrimiento leve o cansancio normal, sin sufrimiento clínico."
    ),
}

# Umbrales calibrados para softmax con 4 categorías. Con esta
# configuración la masa se divide entre depresion/ansiedad/adaptativo/
# neutral, así que scores medios son suficientes para ser señal fiable.
# El requisito extra en `clasificar_frase` es que la categoría clínica
# también domine — así una nota positiva con 0.40 de depresion no
# dispara nada porque adaptativo suele ganar por más.
UMBRAL_DETECCION = 0.40
# Bandera de crisis: depresión domina Y supera este umbral. Calibrado
# para atrapar ideación clara sin marcar contenido semánticamente dudoso.
UMBRAL_CRISIS = 0.55


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
            # multi_label=False → softmax competitivo entre las 3 categorías.
            # Fuerza que sumen 1.0 y compitan entre sí. Sin esto, cualquier
            # texto con carga negativa activaba tanto 'depresion' como
            # 'ansiedad' al mismo tiempo por overlap semántico.
            multi_label=False,
        )

        scores = {}
        for hip, score in zip(resultado["labels"], resultado["scores"]):
            scores[hipotesis_a_clave[hip]] = float(score)

        # Filtro 'detectadas' → una categoría clínica solo se lista si
        # domina Y supera el umbral. Si 'adaptativo' o 'neutral' dominan,
        # la respuesta no es preocupante aunque una clínica pase el umbral.
        NO_CLINICAS = {"neutral", "adaptativo"}
        dominante = max(scores, key=scores.get) if scores else None
        detectadas = []
        if dominante and dominante not in NO_CLINICAS:
            if scores.get(dominante, 0.0) >= UMBRAL_DETECCION:
                detectadas.append(dominante)
        # Crisis: depresión domina Y supera el umbral de crisis.
        crisis = (
            dominante == "depresion"
            and scores.get("depresion", 0.0) >= UMBRAL_CRISIS
        )

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
