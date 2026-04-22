from transformers import pipeline
from sqlalchemy.orm import Session
from app.models.risk import RiskResult
from app.schemas.session import RiskLevel
from app.config import settings
import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class NLPService:
    """
    Servicio NLP con patrón Singleton para carga única del modelo.
    El modelo se carga una sola vez en memoria y se reutiliza en todas las solicitudes.
    """
    
    _classifier = None  # ← Variable estática (Singleton)
    _lock = threading.Lock()  # ← Lock para thread-safety
    _is_loading = False  # ← Flag para tracking de carga
    _load_time = None  # ← Tiempo que tardó cargando
    _load_timestamp = None  # ← Cuándo se cargó
    
    @classmethod
    def get_classifier(cls):
        """
        Obtiene el clasificador NLP con patrón Singleton.
        
        Primera llamada: Carga el modelo desde HuggingFace (5-10 min)
        Llamadas posteriores: Retorna el modelo en memoria (instantáneo)
        
        Thread-safe: Usa double-check locking para evitar race conditions
        """
        
        # Primer check sin lock (rápido)
        if cls._classifier is None:
            with cls._lock:
                # Double-check dentro del lock
                if cls._classifier is None:
                    cls._is_loading = True
                    tiempo_inicio = time.time()
                    cls._load_timestamp = datetime.utcnow().isoformat()
                    
                    logger.info("=" * 80)
                    logger.info("🤖 INICIANDO CARGA DEL MODELO NLP")
                    logger.info(f"   Modelo: {settings.MODEL_NAME}")
                    logger.info(f"   Dispositivo: {settings.DEVICE}")
                    logger.info(f"   Timestamp: {cls._load_timestamp}")
                    logger.info("   ⏳ Esto puede tomar 5-10 minutos en la primera solicitud...")
                    logger.info("=" * 80)
                    
                    try:
                        # Carga el pipeline de zero-shot-classification
                        cls._classifier = pipeline(
                            "zero-shot-classification",
                            model=settings.MODEL_NAME,
                            device=settings.DEVICE
                        )
                        
                        # Calcula tiempo de carga
                        cls._load_time = time.time() - tiempo_inicio
                        tiempo_formateado = cls._formatear_tiempo(cls._load_time)
                        
                        logger.info("=" * 80)
                        logger.info("✅ MODELO NLP CARGADO EXITOSAMENTE")
                        logger.info(f"   ⏱️  Tiempo de carga: {tiempo_formateado}")
                        logger.info(f"   Timestamp: {cls._load_timestamp}")
                        logger.info("   El modelo está en memoria y listo para usar")
                        logger.info("   Próximas solicitudes serán instantáneas ⚡")
                        logger.info("=" * 80)
                        
                        cls._is_loading = False
                        
                    except Exception as e:
                        cls._is_loading = False
                        logger.error("=" * 80)
                        logger.error("❌ ERROR CARGANDO EL MODELO NLP")
                        logger.error(f"   Error: {str(e)}")
                        logger.error("=" * 80)
                        raise
        else:
            logger.debug(f"♻️ Reutilizando modelo NLP ya cargado en memoria")
            logger.debug(f"   Cargado hace: {cls._obtener_tiempo_desde_carga()}")
        
        return cls._classifier
    
    @classmethod
    def _obtener_tiempo_desde_carga(cls) -> str:
        """Calcula tiempo transcurrido desde que se cargó el modelo"""
        if cls._load_timestamp is None:
            return "desconocido"
        
        tiempo_transcurrido = time.time() - float(datetime.fromisoformat(cls._load_timestamp).timestamp())
        return cls._formatear_tiempo(tiempo_transcurrido)
    
    @staticmethod
    def _formatear_tiempo(segundos: float) -> str:
        """Formatea segundos a un formato legible"""
        if segundos < 1:
            return f"{segundos*1000:.2f}ms"
        elif segundos < 60:
            return f"{segundos:.2f}s"
        elif segundos < 3600:
            minutos = segundos / 60
            return f"{minutos:.2f}m"
        else:
            horas = segundos / 3600
            return f"{horas:.2f}h"
    
    @classmethod
    def modelo_cargado(cls) -> bool:
        """Retorna True si el modelo está cargado en memoria"""
        return cls._classifier is not None
    
    @classmethod
    def esta_cargando(cls) -> bool:
        """Retorna True si el modelo se está cargando en este momento"""
        return cls._is_loading
    
    @classmethod
    def obtener_info_modelo(cls) -> dict:
        """Retorna información del estado del modelo"""
        return {
            "cargado": cls.modelo_cargado(),
            "cargando": cls.esta_cargando(),
            "modelo": settings.MODEL_NAME,
            "dispositivo": settings.DEVICE,
            "timestamp_carga": cls._load_timestamp,
            "tiempo_carga": cls._load_time,
            "tiempo_desde_carga": cls._obtener_tiempo_desde_carga() if cls.modelo_cargado() else None
        }
    
    @staticmethod
    def analizar_respuestas(respuestas_dict: list) -> dict:
        """
        Analiza respuestas en español y clasifica nivel de riesgo emocional.
        Usa XLM-RoBERTa para mejor comprensión del contexto en español.
        
        ✅ NO traduce el texto
        ✅ Envía directamente al modelo multilenguaje
        ✅ Maneja caracteres especiales correctamente
        ✅ Registra tiempo de ejecución
        
        Args:
            respuestas_dict: Lista de diccionarios con las respuestas del usuario
            
        Returns:
            Dict con nivel_riesgo, score y explicación
        """
        tiempo_inicio_total = time.time()
        logger.info("=" * 80)
        logger.info("🔍 INICIANDO ANÁLISIS DE RESPUESTAS")
        logger.info(f"   Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)
        
        try:
            # Validación de entrada
            if not respuestas_dict:
                logger.warning("⚠️ Lista de respuestas vacía")
                raise ValueError("Se requiere al menos una respuesta para analizar")
            
            if len(respuestas_dict) < 1:
                logger.warning("⚠️ Número insuficiente de respuestas")
                raise ValueError("Se requieren al menos 1 respuesta para analizar")
            
            # 1️⃣ Concatena todas las respuestas EN ESPAÑOL (sin traducción)
            tiempo_inicio_paso = time.time()
            logger.info("📋 PASO 1: Procesando respuestas del usuario")
            logger.info("─" * 80)
            
            respuestas_lista = []
            for i, respuesta_dict in enumerate(respuestas_dict, 1):
                if isinstance(respuesta_dict, dict) and "respuesta" in respuesta_dict:
                    respuesta_texto = respuesta_dict["respuesta"].strip()
                    if respuesta_texto:
                        respuestas_lista.append(respuesta_texto)
                        logger.debug(f"   Respuesta {i}: {respuesta_texto[:60]}...")
            
            if not respuestas_lista:
                logger.warning("⚠️ No hay respuestas válidas para analizar")
                raise ValueError("Se requiere al menos una respuesta válida")
            
            # Junta todas las respuestas con espacio
            texto_completo = " ".join(respuestas_lista)
            tiempo_paso_1 = time.time() - tiempo_inicio_paso
            
            logger.info(f"   ✅ Respuestas procesadas: {len(respuestas_lista)}")
            logger.info(f"   Total de caracteres: {len(texto_completo)}")
            logger.info(f"   ⏱️  Tiempo de este paso: {NLPService._formatear_tiempo(tiempo_paso_1)}")
            
            # Verifica caracteres especiales españoles
            caracteres_especiales = ['á', 'é', 'í', 'ó', 'ú', 'ñ', 'ü', '¿', '¡']
            caracteres_encontrados = [c for c in caracteres_especiales if c in texto_completo]
            if caracteres_encontrados:
                logger.info(f"   ✓ Caracteres españoles: {set(caracteres_encontrados)}")
            
            # 2️⃣ Define las etiquetas de clasificación EN ESPAÑOL
            tiempo_inicio_paso = time.time()
            logger.info("")
            logger.info("📋 PASO 2: Configurando etiquetas de clasificación")
            logger.info("─" * 80)
            
            categorias = [
                "estabilidad emocional y bienestar psicológico",
                "estrés moderado con ansiedad y dificultad de concentración",
                "crisis emocional con alto riesgo y necesidad urgente de apoyo"
            ]
            
            for i, cat in enumerate(categorias, 1):
                logger.debug(f"   {i}. {cat[:70]}")
            
            tiempo_paso_2 = time.time() - tiempo_inicio_paso
            logger.info(f"   ✅ Etiquetas configuradas: {len(categorias)}")
            logger.info(f"   ⏱️  Tiempo de este paso: {NLPService._formatear_tiempo(tiempo_paso_2)}")
            
            # 3️⃣ Obtiene el clasificador (cargado una sola vez en memoria)
            tiempo_inicio_paso = time.time()
            logger.info("")
            logger.info("🤖 PASO 3: Cargando modelo XLM-RoBERTa")
            logger.info("─" * 80)
            
            classifier = NLPService.get_classifier()
            
            tiempo_paso_3 = time.time() - tiempo_inicio_paso
            logger.info(f"   ✅ Modelo listo para usar")
            logger.info(f"   ⏱️  Tiempo de este paso: {NLPService._formatear_tiempo(tiempo_paso_3)}")
            
            # 4️⃣ Clasifica el texto DIRECTAMENTE EN ESPAÑOL (sin traducción)
            tiempo_inicio_paso = time.time()
            logger.info("")
            logger.info("🔬 PASO 4: Clasificando con zero-shot-classification")
            logger.info("─" * 80)
            logger.info("   Modelo: joeddav/xlm-roberta-large-xnli")
            logger.info("   Lenguaje: ESPAÑOL (sin traducción)")
            
            resultado = classifier(texto_completo, categorias)
            
            tiempo_paso_4 = time.time() - tiempo_inicio_paso
            logger.info(f"   ✅ Clasificación completada")
            logger.info(f"   ⏱️  Tiempo de este paso: {NLPService._formatear_tiempo(tiempo_paso_4)}")
            
            # 5️⃣ Extrae etiqueta principal y score de confianza
            tiempo_inicio_paso = time.time()
            logger.info("")
            logger.info("📊 PASO 5: Procesando resultados")
            logger.info("─" * 80)
            
            etiqueta_principal = resultado["labels"][0]
            score = resultado["scores"][0]
            
            # Muestra todas las clasificaciones
            logger.info("   Todas las clasificaciones:")
            for etiqueta, puntuacion in zip(resultado["labels"], resultado["scores"]):
                porcentaje = f"{puntuacion*100:.1f}%"
                barra = "█" * int(puntuacion * 15)
                logger.info(f"   {etiqueta[:45]:<45} {porcentaje:>6} {barra}")
            
            tiempo_paso_5 = time.time() - tiempo_inicio_paso
            logger.info(f"   ⏱️  Tiempo de este paso: {NLPService._formatear_tiempo(tiempo_paso_5)}")
            
            # 6️⃣ Mapea a nivel de riesgo
            tiempo_inicio_paso = time.time()
            logger.info("")
            logger.info("🎯 PASO 6: Mapeando a nivel de riesgo")
            logger.info("─" * 80)
            
            if "estabilidad" in etiqueta_principal.lower():
                nivel_riesgo = RiskLevel.LOW
                emoji_riesgo = "🟢"
            elif "moderado" in etiqueta_principal.lower():
                nivel_riesgo = RiskLevel.MEDIUM
                emoji_riesgo = "🟡"
            else:
                nivel_riesgo = RiskLevel.HIGH
                emoji_riesgo = "🔴"
            
            tiempo_paso_6 = time.time() - tiempo_inicio_paso
            logger.info(f"   {emoji_riesgo} Nivel de riesgo: {nivel_riesgo.value.upper()}")
            logger.info(f"   Confianza: {score*100:.1f}%")
            logger.info(f"   ⏱️  Tiempo de este paso: {NLPService._formatear_tiempo(tiempo_paso_6)}")
            
            # 7️⃣ Genera explicación personalizada
            tiempo_inicio_paso = time.time()
            logger.info("")
            logger.info("📝 PASO 7: Generando explicación")
            logger.info("─" * 80)
            
            explicacion = NLPService._generar_explicacion(
                nivel_riesgo,
                score,
                len(respuestas_lista)
            )
            
            tiempo_paso_7 = time.time() - tiempo_inicio_paso
            logger.info(f"   ✅ Explicación generada")
            logger.info(f"   ⏱️  Tiempo de este paso: {NLPService._formatear_tiempo(tiempo_paso_7)}")
            
            # Resumen final
            tiempo_total = time.time() - tiempo_inicio_total
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
            logger.info("=" * 80)
            logger.info(f"   Respuestas analizadas: {len(respuestas_lista)}")
            logger.info(f"   Caracteres procesados: {len(texto_completo)}")
            logger.info(f"   Nivel de riesgo: {emoji_riesgo} {nivel_riesgo.value}")
            logger.info(f"   Confianza: {score*100:.1f}%")
            logger.info("")
            logger.info("   ⏱️  TIEMPOS POR PASO:")
            logger.info(f"      Paso 1 (Procesar): {NLPService._formatear_tiempo(tiempo_paso_1)}")
            logger.info(f"      Paso 2 (Etiquetas): {NLPService._formatear_tiempo(tiempo_paso_2)}")
            logger.info(f"      Paso 3 (Modelo): {NLPService._formatear_tiempo(tiempo_paso_3)}")
            logger.info(f"      Paso 4 (Clasificación): {NLPService._formatear_tiempo(tiempo_paso_4)}")
            logger.info(f"      Paso 5 (Resultados): {NLPService._formatear_tiempo(tiempo_paso_5)}")
            logger.info(f"      Paso 6 (Mapeo): {NLPService._formatear_tiempo(tiempo_paso_6)}")
            logger.info(f"      Paso 7 (Explicación): {NLPService._formatear_tiempo(tiempo_paso_7)}")
            logger.info(f"      ────────────────────────────")
            logger.info(f"      ⏱️  TIEMPO TOTAL: {NLPService._formatear_tiempo(tiempo_total)}")
            logger.info("=" * 80)
            
            return {
                "nivel_riesgo": nivel_riesgo,
                "score": float(score),
                "explicacion": explicacion,
                "respuestas_analizadas": len(respuestas_lista),
                "caracteres_totales": len(texto_completo),
                "tiempo_ejecucion": tiempo_total
            }
        
        except ValueError as ve:
            tiempo_total = time.time() - tiempo_inicio_total
            logger.error("=" * 80)
            logger.error(f"❌ ERROR DE VALIDACIÓN")
            logger.error(f"   Mensaje: {str(ve)}")
            logger.error(f"   ⏱️  Tiempo hasta error: {NLPService._formatear_tiempo(tiempo_total)}")
            logger.error("=" * 80)
            raise
        except Exception as e:
            tiempo_total = time.time() - tiempo_inicio_total
            logger.error("=" * 80)
            logger.error(f"❌ ERROR EN ANÁLISIS")
            logger.error(f"   Tipo: {type(e).__name__}")
            logger.error(f"   Mensaje: {str(e)}")
            logger.error(f"   ⏱️  Tiempo hasta error: {NLPService._formatear_tiempo(tiempo_total)}")
            logger.error("=" * 80)
            import traceback
            logger.error(f"   Traceback: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def _generar_explicacion(nivel_riesgo: RiskLevel, score: float, num_respuestas: int) -> str:
        """Genera explicación personalizada del resultado en español"""
        # ... (el código anterior sin cambios)
        confianza = f"{score*100:.1f}%"
        
        disclaimer = (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ ACLARACIÓN IMPORTANTE\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Este análisis es INFORMATIVO y está basado en análisis de texto con IA.\n"
            "NO constituye un diagnóstico clínico ni evaluación psicológica formal.\n"
            "Solo un profesional de salud mental calificado puede realizar diagnósticos.\n"
            "Si tienes dudas sobre tu salud mental, consulta con un especialista.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        explicaciones = {
            RiskLevel.LOW: (
                f"✅ INTERPRETACIÓN: ESTADO EMOCIONAL ESTABLE\n\n"
                f"Confianza del análisis: {confianza}\n"
                f"Basado en: {num_respuestas} respuestas\n\n"
                "📊 INTERPRETACIÓN DE RESULTADOS:\n"
                "─────────────────────────────────\n"
                "Tu respuesta al cuestionario sugiere que:\n\n"
                "✓ Tienes un equilibrio emocional adecuado\n"
                "✓ Manejas de forma satisfactoria el estrés cotidiano\n"
                "✓ Mantienes relaciones sociales positivas\n"
                "✓ Disfrutas de actividades que te generan bienestar\n"
                "✓ No se detectan indicadores de malestar emocional significativo\n\n"
                "💡 RECOMENDACIONES INFORMATIVAS:\n"
                "─────────────────────────────────\n"
                "Para mantener tu bienestar emocional:\n\n"
                "• Continúa con tus hábitos saludables\n"
                "• Mantén una rutina regular de sueño (7-8 horas)\n"
                "• Realiza actividad física con regularidad\n"
                "• Cultiva conexiones sociales significativas\n"
                "• Practica actividades que te generen satisfacción\n"
                "• Si experimentas cambios, busca orientación profesional\n"
                f"{disclaimer}"
            ),
            RiskLevel.MEDIUM: (
                f"⚠️ INTERPRETACIÓN: POSIBLES INDICADORES DE ESTRÉS O ANSIEDAD\n\n"
                f"Confianza del análisis: {confianza}\n"
                f"Basado en: {num_respuestas} respuestas\n\n"
                "📊 INTERPRETACIÓN DE RESULTADOS:\n"
                "─────────────────────────────────\n"
                "Tu respuesta al cuestionario sugiere que:\n\n"
                "⚠ Posiblemente experimentas estrés o ansiedad moderada\n"
                "⚠ Podrías tener dificultad para concentrarte en algunas tareas\n"
                "⚠ Posibles cambios en patrones de sueño o apetito\n"
                "⚠ Algunos momentos de preocupación o tensión\n"
                "⚠ Necesidad de estrategias para mejorar bienestar emocional\n\n"
                "💡 RECOMENDACIONES INFORMATIVAS:\n"
                "─────────────────────────────────\n"
                "Para mejorar tu bienestar emocional:\n\n"
                "• 👨‍⚕️ Busca orientación con un psicólogo o consejero\n"
                "• 🧘 Practica técnicas de relajación:\n"
                "    - Meditación (10-15 min diarios)\n"
                "    - Respiración profunda\n"
                "    - Progressive muscle relaxation\n"
                "• 😴 Establece una rutina regular de sueño\n"
                "• ☕ Reduce consumo de cafeína y estimulantes\n"
                "• 🤝 Habla con amigos o familia de confianza\n"
                "• 📚 Accede a recursos de autocuidado\n"
                "• 🏫 Utiliza servicios de consejería universitaria si estudias\n\n"
                "🔔 CUÁNDO BUSCAR AYUDA PROFESIONAL:\n"
                "────────────────────────────────────\n"
                "Considera consultar con un profesional si:\n"
                "• Los síntomas persisten más de 2 semanas\n"
                "• Interfieren con tu desempeño académico o laboral\n"
                "• Afectan tus relaciones personales\n"
                "• Experimentes empeoramiento progresivo\n"
                f"{disclaimer}"
            ),
            RiskLevel.HIGH: (
                f"🔴 INTERPRETACIÓN: POSIBLES INDICADORES DE AFECTACIÓN EMOCIONAL SIGNIFICATIVA\n\n"
                f"Confianza del análisis: {confianza}\n"
                f"Basado en: {num_respuestas} respuestas\n\n"
                "📊 INTERPRETACIÓN DE RESULTADOS:\n"
                "─────────────────────────────────\n"
                "Tu respuesta al cuestionario sugiere que:\n\n"
                "🔴 Experimentas malestar emocional significativo\n"
                "🔴 Posibles indicadores de depresión o ansiedad severa\n"
                "🔴 Cambios notables en comportamiento, sueño o apetito\n"
                "🔴 Dificultad importante para realizar actividades cotidianas\n"
                "🔴 Posible riesgo para tu bienestar emocional y físico\n\n"
                "🆘 RECOMENDACIÓN IMPORTANTE:\n"
                "─────────────────────────────────\n"
                "⚠️ BUSCA AYUDA PROFESIONAL DE INMEDIATO ⚠️\n\n"
                "Tu situación requiere evaluación y apoyo profesional.\n"
                "Esto NO es una emergencia médica, pero SÍ requiere atención urgente.\n\n"
                "📞 OPCIONES DE APOYO INMEDIATO:\n"
                "────────────────────────────────\n"
                "1. 👨‍⚕️ PSICÓLOGO O PSIQUIATRA\n"
                "   • Busca un profesional en tu área\n"
                "   • Solicita cita de urgencia\n"
                "   • Algunos ofrecen telesalud\n\n"
                "2. 🏥 CENTROS DE SALUD MENTAL\n"
                "   • Hospital o clínica más cercana\n"
                "   • Centro de salud mental comunitario\n"
                "   • Servicios de emergencia psiquiátrica\n\n"
                "3. 🏫 SERVICIOS UNIVERSITARIOS (si aplica)\n"
                "   • Consejería o bienestar estudiantil\n"
                "   • Servicios de salud del campus\n"
                "   • Programas de apoyo emocional\n\n"
                "4. 📱 LÍNEAS DE CRISIS\n"
                "   • Líneas de emergencia 24/7\n"
                "   • Chatbots de crisis (Crisis Text Line, etc.)\n"
                "   • Aplicaciones de apoyo emocional\n\n"
                "5. 🤝 RED DE APOYO\n"
                "   • Familia o amigos cercanos\n"
                "   • Mentor o profesor de confianza\n"
                "   • Comunidades de apoyo\n\n"
                "💪 RECUERDA:\n"
                "────────────\n"
                "✓ No estás solo/a\n"
                "✓ Pedir ayuda es un SIGNO DE FORTALEZA, no de debilidad\n"
                "✓ Hay profesionales capacitados para ayudarte\n"
                "✓ El apoyo psicológico funciona\n"
                "✓ Las cosas pueden mejorar\n"
                "✓ Tu vida y bienestar SON IMPORTANTES\n"
                f"{disclaimer}"
            )
        }
        
        return explicaciones.get(nivel_riesgo, "Análisis no disponible")
    
    @staticmethod
    def guardar_resultado(db: Session, session_id: str, user_id: str, resultado):
        analysis = AnalysisResult(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            nivel_riesgo=resultado["nivel_riesgo"].value,
            confianza=resultado["score"] * 100,
            fecha_analisis=datetime.utcnow()
        )
        db.add(analysis)
        db.commit()
        return analysis