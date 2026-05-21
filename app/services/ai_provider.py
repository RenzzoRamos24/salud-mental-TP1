"""
AIProvider — Capa de abstracción para la IA conversacional del chatbot.

Permite enchufar distintos motores (BERT local, Claude API, OpenAI, …) sin
tocar `ChatService`. El provider activo se selecciona vía `settings.AI_PROVIDER`.

Métodos del contrato:
  - triage_apertura(texto)       → decide orden PHQ-9 / GAD-7 según el relato libre
  - score_likert(texto, item)    → propone score 0-3 para un ítem clínico
  - acuse_continuar(contexto)    → frase corta para encadenar respuestas
  - acuse_aclaracion(contexto)   → frase para pedir frecuencia (los 4 botones)

Hoy: BertAIProvider envuelve la lógica BERT/keywords existente.
Mañana: ClaudeAIProvider (o equivalente) sobrescribe estos métodos para
respuestas dinámicas y conversacionales, sin tocar el resto del sistema.
"""
from abc import ABC, abstractmethod
import random
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CONTRATO
# ═══════════════════════════════════════════════════════════════════════════

class AIProvider(ABC):
    """Interfaz que debe implementar cualquier motor conversacional."""

    name: str = "abstract"

    @abstractmethod
    def triage_apertura(self, texto: str, nombre: Optional[str] = None) -> dict:
        """
        Analiza el relato libre del usuario al inicio de la sesión y decide
        con qué módulo clínico empezar.

        Returns:
            {
              "modulos_orden":          list[str]  # ej. ["PHQ-9", "GAD-7"]
              "modulo_prioritario":     str        # primero de la lista
              "condiciones_detectadas": list[str]  # claves NLP
              "crisis_inmediata":       bool       # señales suicidas/autolesión
              "acuse":                  str        # respuesta empática al usuario
              "razonamiento":           str        # explicación corta para logs
            }
        """
        ...

    @abstractmethod
    def score_likert(self, texto: str, item: dict) -> dict:
        """Propone score Likert 0-3 para un ítem PHQ-9/GAD-7."""
        ...

    @abstractmethod
    def acuse_continuar(self) -> str:
        """Frase corta para encadenar antes de la siguiente pregunta."""
        ...

    @abstractmethod
    def acuse_aclaracion(self) -> str:
        """Frase para pedir la frecuencia con los 4 botones."""
        ...


# ═══════════════════════════════════════════════════════════════════════════
# IMPLEMENTACIÓN ACTUAL: BERT + KEYWORDS
# ═══════════════════════════════════════════════════════════════════════════

class BertAIProvider(AIProvider):
    """
    Motor por defecto. Reutiliza NLPService (BETO + XNLI zero-shot) para
    triage y scoring. Las frases empáticas vienen del pool de `settings`.
    """

    name = "bert"

    def triage_apertura(self, texto: str, nombre: Optional[str] = None) -> dict:
        from app.services.nlp_service import NLPService

        texto_limpio = (texto or "").strip()
        if not texto_limpio:
            # Sin información: orden por defecto, sin crisis.
            return {
                "modulos_orden": ["PHQ-9", "GAD-7"],
                "modulo_prioritario": "PHQ-9",
                "condiciones_detectadas": [],
                "crisis_inmediata": False,
                "acuse": (
                    f"Gracias por estar aquí{', ' + nombre if nombre else ''}. "
                    "Empezamos con unas preguntas para conocerte mejor."
                ),
                "razonamiento": "texto vacío → orden por defecto",
            }

        # 1) Análisis multi-condición a nivel respuesta individual
        analisis = NLPService.analizar_respuesta_individual(texto_limpio)

        # 2) Detalle: corremos el clasificador para obtener TODOS los scores
        #    y decidir por dominancia, no solo por la "condición ganadora".
        classifier = NLPService.get_classifier()
        claves = list(settings.CONDICIONES.keys())
        hipotesis = [settings.CONDICIONES[k]["hipotesis"] for k in claves]
        hipotesis_a_clave = dict(zip(hipotesis, claves))

        try:
            resultado = classifier(
                texto_limpio,
                candidate_labels=hipotesis,
                multi_label=True,
                hypothesis_template=settings.HYPOTHESIS_TEMPLATE,
            )
            scores = {
                hipotesis_a_clave[lab]: float(s)
                for lab, s in zip(resultado["labels"], resultado["scores"])
            }
        except Exception as e:
            logger.warning(f"⚠️ triage BERT falló, usando fallback simple: {e}")
            scores = {k: 0.0 for k in claves}
            if analisis.get("condicion"):
                scores[analisis["condicion"]] = analisis.get("score", 0.5)

        # 3) Keyword boost (texto plano, español)
        texto_lower = texto_limpio.lower()
        for clave, keywords in settings.KEYWORDS.items():
            matches = [kw for kw in keywords if kw in texto_lower]
            if matches:
                boost = min(
                    settings.KEYWORD_BOOST_PER_MATCH * len(matches),
                    settings.KEYWORD_BOOST_MAX,
                )
                scores[clave] = min(scores.get(clave, 0.0) + boost, 1.0)

        score_dep = scores.get("depresion", 0.0)
        score_ans = scores.get("ansiedad", 0.0)
        score_suicida = scores.get("riesgo_suicida", 0.0)
        umbral_suicida = settings.CONDICIONES["riesgo_suicida"]["umbral"]

        # 4) Decisión de orden
        crisis = score_suicida >= umbral_suicida
        if crisis:
            # Señales de autolesión: PHQ-9 va primero (incluye el ítem 9).
            modulos_orden = ["PHQ-9", "GAD-7"]
            razon = (
                f"crisis: riesgo_suicida={score_suicida*100:.1f}% "
                f"(≥ {umbral_suicida*100:.0f}%) → PHQ-9 primero"
            )
        elif score_ans > score_dep + 0.05:
            modulos_orden = ["GAD-7", "PHQ-9"]
            razon = (
                f"ansiedad ({score_ans*100:.1f}%) > depresión "
                f"({score_dep*100:.1f}%) → GAD-7 primero"
            )
        else:
            modulos_orden = ["PHQ-9", "GAD-7"]
            razon = (
                f"depresión ({score_dep*100:.1f}%) ≥ ansiedad "
                f"({score_ans*100:.1f}%) → PHQ-9 primero"
            )

        # 5) Condiciones detectadas (las que superan su umbral)
        condiciones_detectadas = [
            k for k in claves
            if k != "estabilidad"
            and scores.get(k, 0.0) >= settings.CONDICIONES[k]["umbral"]
        ]

        # 6) Acuse empático contextualizado
        acuse = self._construir_acuse_apertura(
            modulo_prioritario=modulos_orden[0],
            crisis=crisis,
            nombre=nombre,
        )

        logger.info(
            f"   🧭 Triage apertura → {modulos_orden[0]} primero. "
            f"Crisis={crisis}. Condiciones={condiciones_detectadas}. "
            f"Razón: {razon}"
        )

        return {
            "modulos_orden": modulos_orden,
            "modulo_prioritario": modulos_orden[0],
            "condiciones_detectadas": condiciones_detectadas,
            "crisis_inmediata": crisis,
            "acuse": acuse,
            "razonamiento": razon,
        }

    def score_likert(self, texto: str, item: dict) -> dict:
        from app.services.nlp_service import NLPService
        return NLPService.proponer_score_likert(texto, item)

    def acuse_continuar(self) -> str:
        return random.choice(settings.ACKS_CONTINUAR)

    def acuse_aclaracion(self) -> str:
        return random.choice(settings.ACKS_PEDIR_FRECUENCIA)

    # ─────────────────────────────────────────────────────────────────
    # Helpers internos
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _construir_acuse_apertura(modulo_prioritario: str, crisis: bool, nombre: Optional[str]) -> str:
        primer = (nombre or "").split(" ")[0] if nombre else ""
        saludo = f"Gracias por contarme{', ' + primer if primer else ''}."
        if crisis:
            return (
                f"{saludo} Que me cuentes esto es importante y te lo agradezco. "
                "Vamos a ir paso a paso, sin presión. Si en algún momento "
                "sientes que te supera, recuerda: la Línea 113 (opción 5) "
                "atiende gratis las 24h, y siempre puedes hablar con un "
                "adulto de confianza, un profe o el psicólogo del cole. "
                "No estás solo/a. Te voy a hacer algunas preguntas con cuidado."
            )
        if modulo_prioritario == "GAD-7":
            tema = "los nervios y la ansiedad"
        else:
            tema = "cómo te has sentido de ánimo"
        cierres = [
            f"{saludo} Te haré algunas preguntas cortas para entender mejor "
            f"{tema} estos días.",
            f"{saludo} Vamos a explorar un poco {tema} con preguntas rápidas. "
            f"No hay respuestas buenas o malas, solo sé sincero/a contigo.",
            f"{saludo} Te entiendo. Te haré unas preguntas sobre {tema}. "
            f"Si algo no te aplica, está bien decirlo también.",
        ]
        return random.choice(cierres)


# ═══════════════════════════════════════════════════════════════════════════
# PROVIDER FACTORY
# ═══════════════════════════════════════════════════════════════════════════

_INSTANCE: Optional[AIProvider] = None


def get_ai_provider() -> AIProvider:
    """
    Devuelve la instancia activa según `settings.AI_PROVIDER`.
    Cachea la instancia (singleton ligero).
    """
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE

    nombre = getattr(settings, "AI_PROVIDER", "bert").lower()
    if nombre == "bert":
        _INSTANCE = BertAIProvider()
    # elif nombre == "claude":
    #     from app.services.ai_providers.claude_provider import ClaudeAIProvider
    #     _INSTANCE = ClaudeAIProvider()
    # elif nombre == "openai":
    #     from app.services.ai_providers.openai_provider import OpenAIProvider
    #     _INSTANCE = OpenAIProvider()
    else:
        logger.warning(f"AI_PROVIDER='{nombre}' desconocido; usando BERT por defecto.")
        _INSTANCE = BertAIProvider()

    logger.info(f"🤖 AIProvider activo: {_INSTANCE.name}")
    return _INSTANCE


def reset_ai_provider() -> None:
    """Útil para tests o tras cambiar settings.AI_PROVIDER en caliente."""
    global _INSTANCE
    _INSTANCE = None
