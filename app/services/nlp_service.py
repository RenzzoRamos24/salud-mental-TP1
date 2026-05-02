"""
NLPService — Clasificación multi-condición de salud mental con BERT español.

Modelo: Recognai/bert-base-spanish-wwm-cased-xnli (BETO + XNLI)
Técnica: Zero-shot multi-label con hipótesis en español + boost de keywords clínicos.

Optimizado para PRECISIÓN:
  1. Zero-shot multi-label (cada condición evaluada independientemente).
  2. Hypothesis templating ("Este texto expresa {}.") - más natural que etiquetas planas.
  3. Keyword boost - refuerza score cuando hay términos diagnósticos explícitos.
  4. Umbrales calibrados por condición (riesgo suicida con sensibilidad alta: 0.40).

Optimizado para VELOCIDAD:
  1. Singleton del modelo (carga única en memoria, ~400MB vs 2.2GB del anterior).
  2. Un solo forward pass sobre texto concatenado (no por pregunta).
  3. Thread-safe con double-check locking.
"""
from transformers import pipeline
from sqlalchemy.orm import Session
from app.models.risk import RiskResult
from app.config import settings
import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class NLPService:
    """Servicio NLP con patrón Singleton para carga única del modelo BERT."""

    _classifier = None
    _lock = threading.Lock()
    _is_loading = False
    _load_time = None
    _load_timestamp = None

    # ═══════════════════════════════════════════════════════════════════
    # CARGA DEL MODELO (Singleton thread-safe)
    # ═══════════════════════════════════════════════════════════════════

    @classmethod
    def get_classifier(cls):
        """
        Carga el pipeline BERT zero-shot en la primera llamada.
        Posteriores llamadas retornan el modelo cacheado en memoria.
        """
        if cls._classifier is None:
            with cls._lock:
                if cls._classifier is None:
                    cls._is_loading = True
                    tiempo_inicio = time.time()
                    cls._load_timestamp = datetime.utcnow().isoformat()

                    logger.info("=" * 80)
                    logger.info("🤖 CARGANDO MODELO BERT (BETO + XNLI)")
                    logger.info(f"   Modelo: {settings.MODEL_NAME}")
                    logger.info(f"   Dispositivo: {'CPU' if settings.DEVICE == -1 else f'GPU:{settings.DEVICE}'}")
                    logger.info("   ⏳ Primera carga puede tardar 1-3 min (descarga ~400MB)...")
                    logger.info("=" * 80)

                    try:
                        cls._classifier = pipeline(
                            "zero-shot-classification",
                            model=settings.MODEL_NAME,
                            device=settings.DEVICE,
                        )
                        cls._load_time = time.time() - tiempo_inicio
                        cls._is_loading = False

                        logger.info("=" * 80)
                        logger.info("✅ MODELO BERT CARGADO")
                        logger.info(f"   ⏱️  Tiempo de carga: {cls._formatear_tiempo(cls._load_time)}")
                        logger.info("   Próximas inferencias serán instantáneas ⚡")
                        logger.info("=" * 80)

                    except Exception as e:
                        cls._is_loading = False
                        logger.error(f"❌ Error cargando modelo BERT: {e}")
                        raise

        return cls._classifier

    @staticmethod
    def _formatear_tiempo(segundos: float) -> str:
        if segundos < 1:
            return f"{segundos*1000:.2f}ms"
        if segundos < 60:
            return f"{segundos:.2f}s"
        if segundos < 3600:
            return f"{segundos/60:.2f}m"
        return f"{segundos/3600:.2f}h"

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
        }

    # ═══════════════════════════════════════════════════════════════════
    # ANÁLISIS MULTI-CONDICIÓN
    # ═══════════════════════════════════════════════════════════════════

    @classmethod
    def analizar_respuestas(cls, respuestas_dict: list) -> dict:
        """
        Analiza las respuestas del usuario y devuelve scores por condición clínica.

        Proceso:
            1. Concatena respuestas preservando español (sin traducir).
            2. Ejecuta zero-shot multi-label sobre todas las hipótesis clínicas.
            3. Aplica keyword boost por condición.
            4. Decide qué condiciones superan su umbral.
            5. Calcula nivel de riesgo global.

        Args:
            respuestas_dict: lista de dicts con clave "respuesta".

        Returns:
            dict con nivel_riesgo, condiciones_detectadas, scores, explicación.
        """
        tiempo_inicio = time.time()
        logger.info("=" * 80)
        logger.info("🔍 INICIANDO ANÁLISIS MULTI-CONDICIÓN")
        logger.info("=" * 80)

        if not respuestas_dict:
            raise ValueError("Se requiere al menos una respuesta para analizar")

        # 1️⃣ Concatenar respuestas
        respuestas_lista = [
            r["respuesta"].strip()
            for r in respuestas_dict
            if isinstance(r, dict) and r.get("respuesta", "").strip()
        ]
        if not respuestas_lista:
            raise ValueError("Se requiere al menos una respuesta válida")

        texto_completo = " ".join(respuestas_lista)
        logger.info(f"   📋 Respuestas procesadas: {len(respuestas_lista)}")
        logger.info(f"   📝 Caracteres totales: {len(texto_completo)}")

        # 2️⃣ Construir hipótesis multi-label
        claves = list(settings.CONDICIONES.keys())
        hipotesis = [settings.CONDICIONES[k]["hipotesis"] for k in claves]
        hipotesis_a_clave = dict(zip(hipotesis, claves))

        # 3️⃣ Inferencia zero-shot multi-label (un solo forward pass)
        classifier = cls.get_classifier()
        t_infer = time.time()

        resultado = classifier(
            texto_completo,
            candidate_labels=hipotesis,
            multi_label=True,
            hypothesis_template=settings.HYPOTHESIS_TEMPLATE,
        )

        tiempo_inferencia = time.time() - t_infer
        logger.info(f"   ⚡ Inferencia BERT: {cls._formatear_tiempo(tiempo_inferencia)}")

        # 4️⃣ Mapear scores base a cada condición
        scores = {}
        for hip, score in zip(resultado["labels"], resultado["scores"]):
            scores[hipotesis_a_clave[hip]] = float(score)

        # 5️⃣ Keyword boost — refuerza cuando hay términos clínicos explícitos
        texto_lower = texto_completo.lower()
        boost_info = {}
        for clave, keywords in settings.KEYWORDS.items():
            matches = [kw for kw in keywords if kw in texto_lower]
            if matches:
                boost = min(
                    settings.KEYWORD_BOOST_PER_MATCH * len(matches),
                    settings.KEYWORD_BOOST_MAX,
                )
                score_previo = scores.get(clave, 0.0)
                scores[clave] = min(score_previo + boost, 1.0)
                boost_info[clave] = {
                    "matches": matches,
                    "boost_aplicado": boost,
                    "score_antes": score_previo,
                    "score_despues": scores[clave],
                }

        # 6️⃣ Log detallado de scores
        logger.info("   " + "─" * 76)
        logger.info("   📊 SCORES POR CONDICIÓN (modelo + keyword boost):")
        for clave in claves:
            cfg = settings.CONDICIONES[clave]
            score = scores.get(clave, 0.0)
            umbral = cfg["umbral"]
            detectado = "🔴 DETECTADO" if score >= umbral else "⚪ descartado"
            barra = "█" * int(score * 20)
            logger.info(
                f"   {cfg['etiqueta']:<42} {score*100:5.1f}% "
                f"(umbral {umbral*100:.0f}%) {detectado} {barra}"
            )

        # 7️⃣ Determinar condiciones detectadas (≠ estabilidad)
        condiciones_detectadas = {}
        for clave in claves:
            if clave == "estabilidad":
                continue
            if scores[clave] >= settings.CONDICIONES[clave]["umbral"]:
                condiciones_detectadas[clave] = {
                    "etiqueta": settings.CONDICIONES[clave]["etiqueta"],
                    "confianza": round(scores[clave] * 100, 1),
                }

        # 8️⃣ Nivel de riesgo global (jerárquico, prioriza seguridad)
        nivel_riesgo = cls._calcular_nivel_riesgo(scores, condiciones_detectadas)

        # 9️⃣ Explicación
        explicacion = cls._generar_explicacion(
            nivel_riesgo, condiciones_detectadas, scores, len(respuestas_lista)
        )

        tiempo_total = time.time() - tiempo_inicio
        logger.info("   " + "─" * 76)
        logger.info(f"   🎯 Nivel de riesgo global: {nivel_riesgo}")
        logger.info(f"   🩺 Condiciones detectadas: {len(condiciones_detectadas)}")
        logger.info(f"   ⏱️  Tiempo total del análisis: {cls._formatear_tiempo(tiempo_total)}")
        logger.info("=" * 80)

        return {
            "nivel_riesgo": nivel_riesgo,
            "condiciones_detectadas": condiciones_detectadas,
            "scores_completos": {k: round(v * 100, 1) for k, v in scores.items()},
            "boost_aplicado": boost_info,
            "explicacion": explicacion,
            "respuestas_analizadas": len(respuestas_lista),
            "caracteres_totales": len(texto_completo),
            "tiempo_inferencia": tiempo_inferencia,
            "tiempo_total": tiempo_total,
            "modelo": settings.MODEL_NAME,
        }

    # ═══════════════════════════════════════════════════════════════════
    # NIVEL DE RIESGO GLOBAL
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _calcular_nivel_riesgo(scores: dict, detectadas: dict) -> str:
        """
        Jerarquía de riesgo (prioriza seguridad clínica):
          CRÍTICO   — riesgo suicida detectado (cualquier score ≥ umbral)
          ALTO      — ≥2 condiciones detectadas, o alguna con confianza ≥ 75%
          MEDIO     — 1 condición detectada con confianza moderada
          BAJO      — ninguna condición detectada y estabilidad alta
        """
        if "riesgo_suicida" in detectadas:
            return "CRÍTICO"

        confianzas = [d["confianza"] for d in detectadas.values()]
        if len(detectadas) >= 2 or any(c >= 75.0 for c in confianzas):
            return "ALTO"

        if len(detectadas) == 1:
            return "MEDIO"

        if scores.get("estabilidad", 0) >= settings.CONDICIONES["estabilidad"]["umbral"]:
            return "BAJO"

        return "MEDIO"

    # ═══════════════════════════════════════════════════════════════════
    # EXPLICACIÓN CLÍNICA EN ESPAÑOL
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _generar_explicacion(
        nivel: str, detectadas: dict, scores: dict, num_respuestas: int
    ) -> str:
        disclaimer = (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️  ACLARACIÓN IMPORTANTE\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Este análisis es INFORMATIVO, basado en procesamiento de texto con IA.\n"
            "NO constituye un diagnóstico clínico ni sustituye la evaluación de\n"
            "un profesional de salud mental calificado.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

        # Encabezado según nivel
        encabezados = {
            "CRÍTICO": (
                "🔴🔴🔴 NIVEL CRÍTICO — ATENCIÓN URGENTE 🔴🔴🔴\n"
                "Se detectaron indicadores de ideación suicida o autolesión.\n"
                "Por favor, busca ayuda profesional INMEDIATAMENTE.\n"
            ),
            "ALTO": (
                "🔴 NIVEL ALTO — Afectación emocional significativa\n"
                "Se detectaron múltiples indicadores clínicos relevantes.\n"
                "Se recomienda encarecidamente evaluación profesional.\n"
            ),
            "MEDIO": (
                "🟡 NIVEL MEDIO — Indicadores moderados\n"
                "Se detectaron señales que merecen seguimiento.\n"
                "Considera conversar con un profesional de salud mental.\n"
            ),
            "BAJO": (
                "🟢 NIVEL BAJO — Estabilidad emocional\n"
                "No se detectaron indicadores clínicos significativos.\n"
                "Mantén tus hábitos de autocuidado.\n"
            ),
        }

        bloque_condiciones = ""
        if detectadas:
            bloque_condiciones = "\n📋 CONDICIONES DETECTADAS:\n─────────────────────────────\n"
            for clave, info in detectadas.items():
                bloque_condiciones += f"  • {info['etiqueta']}: {info['confianza']}% de confianza\n"
        else:
            bloque_condiciones = (
                "\n📋 CONDICIONES DETECTADAS:\n─────────────────────────────\n"
                "  • Ninguna condición supera el umbral de detección.\n"
            )

        # Recomendaciones por condición detectada
        recomendaciones = NLPService._recomendaciones_por_condiciones(detectadas)

        return (
            f"{encabezados.get(nivel, encabezados['MEDIO'])}"
            f"\nBasado en {num_respuestas} respuestas analizadas.\n"
            f"{bloque_condiciones}"
            f"{recomendaciones}"
            f"{disclaimer}"
        )

    @staticmethod
    def _recomendaciones_por_condiciones(detectadas: dict) -> str:
        """Genera recomendaciones específicas por cada condición detectada."""
        if not detectadas:
            return (
                "\n💡 RECOMENDACIONES PARA MANTENER BIENESTAR:\n"
                "─────────────────────────────────────────\n"
                "  • Mantén rutina de sueño (7-8h), actividad física y vínculos sociales.\n"
                "  • Si en algún momento notas cambios, busca orientación profesional.\n"
            )

        recs = {
            "depresion": (
                "  🔹 Depresión: considera consulta psicológica; activa rutinas de\n"
                "     higiene del sueño, actividad física y contacto social."
            ),
            "ansiedad": (
                "  🔹 Ansiedad: practica técnicas de respiración diafragmática y\n"
                "     mindfulness; reduce cafeína; consulta con psicólogo si persiste."
            ),
            "tdah": (
                "  🔹 TDAH: una evaluación neuropsicológica puede confirmar el\n"
                "     diagnóstico. Estrategias: técnica Pomodoro, listas, entornos\n"
                "     libres de distracciones."
            ),
            "estres_academico": (
                "  🔹 Estrés académico: usa los servicios de bienestar estudiantil\n"
                "     UPC; planifica con bloques realistas; no sacrifiques el sueño."
            ),
            "soledad": (
                "  🔹 Soledad: construye vínculos en grupos de la UPC (clubs,\n"
                "     voluntariados); mantén contacto regular con tu familia en provincia."
            ),
            "riesgo_suicida": (
                "  🆘 RIESGO SUICIDA — ACCIÓN INMEDIATA:\n"
                "     • Línea 113 (MINSA Perú), opción 5 — salud mental 24/7.\n"
                "     • Bienestar Estudiantil UPC — atención psicológica gratuita.\n"
                "     • No te quedes solo/a: contacta a alguien de confianza AHORA.\n"
                "     • Si hay peligro inmediato: emergencias 106 o acude al hospital."
            ),
        }

        salida = "\n💡 RECOMENDACIONES POR CONDICIÓN:\n─────────────────────────────\n"
        for clave in detectadas.keys():
            if clave in recs:
                salida += recs[clave] + "\n"
        return salida

    # ═══════════════════════════════════════════════════════════════════
    # PERSISTENCIA
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def guardar_resultado(db: Session, session_id: str, user_id: str, resultado: dict) -> RiskResult:
        """Persiste el resultado en la tabla risk_results."""
        # Score principal: score de la condición dominante (o estabilidad si no hay detectadas)
        if resultado["condiciones_detectadas"]:
            score_principal = max(
                d["confianza"] for d in resultado["condiciones_detectadas"].values()
            ) / 100.0
        else:
            score_principal = resultado["scores_completos"].get("estabilidad", 0.0) / 100.0

        risk = RiskResult(
            session_id=session_id,
            user_id=user_id,
            nivel_riesgo=resultado["nivel_riesgo"],
            score=score_principal,
            explicacion=resultado["explicacion"],
        )
        db.add(risk)
        db.commit()
        db.refresh(risk)
        return risk
