from sqlalchemy.orm import Session
from app.models.session import UserSession
from app.models.response import UserResponse
from app.services.session_service import SessionService
from app.services.nlp_service import NLPService
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class ChatService:
    """
    Servicio de chat que orquesta el flujo de conversación.
    
    Responsabilidades:
    ✓ Crear sesiones
    ✓ Guardar respuestas
    ✓ Avanzar a la siguiente pregunta
    ✓ Orquestar análisis NLP
    
    NO hace:
    ✗ Lógica NLP (eso es nlp_service.py)
    ✗ Validación de entrada (eso es schemas)
    """
    
    @staticmethod
    def crear_sesion(
        db: Session,
        user_id: str,
        nombre: str
    ) -> dict:
        """
        Crea una nueva sesión de chat.
        """
        try:
            logger.info(f"📋 Creando sesión para usuario: {user_id}")
            
            # Usa SessionService para crear la sesión
            user_session = SessionService.crear_sesion(
                db=db,
                user_id=user_id,
                nombre=nombre
            )
            
            # Obtiene primera pregunta
            pregunta_actual = SessionService.obtener_pregunta_actual(0)
            total_preguntas = len(SessionService.PREGUNTAS)
            
            logger.info(f"✅ Sesión creada: {user_session.id}")
            
            return {
                "session_id": user_session.id,
                "pregunta_numero": 1,
                "pregunta": pregunta_actual,
                "total_preguntas": total_preguntas,
                "mensaje": f"¡Bienvenido/a {nombre}! Vamos a evaluar tu bienestar emocional."
            }
            
        except Exception as e:
            logger.error(f"❌ Error creando sesión: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def guardar_respuesta_y_avanzar(
        db: Session,
        session_id: str,
        respuesta: str
    ) -> dict:
        """
        Guarda respuesta del usuario y avanza a la siguiente pregunta.
        """
        try:
            logger.info(f"💬 Procesando respuesta para sesión: {session_id}")
            
            # Obtiene la sesión actual
            user_session = SessionService.obtener_sesion(db, session_id)
            
            if not user_session:
                logger.warning(f"⚠️ Sesión no encontrada: {session_id}")
                raise ValueError(f"Sesión no encontrada: {session_id}")
            
            # Verifica si ya está completada
            if SessionService.es_sesion_completa(user_session.pregunta_actual):
                logger.warning(f"⚠️ Sesión ya completada: {session_id}")
                raise ValueError("Esta sesión ya ha sido completada")
            
            # Obtiene pregunta actual
            pregunta_actual = SessionService.obtener_pregunta_actual(user_session.pregunta_actual)
            
            # Guarda la respuesta
            SessionService.guardar_respuesta(
                db=db,
                session_id=session_id,
                numero_pregunta=user_session.pregunta_actual,
                pregunta=pregunta_actual,
                respuesta=respuesta
            )
            
            # Avanza a la siguiente pregunta
            siguiente_pregunta = user_session.pregunta_actual + 1
            SessionService.actualizar_pregunta(db, session_id, siguiente_pregunta)
            
            # Verifica si ya respondió todas las preguntas
            total_preguntas = len(SessionService.PREGUNTAS)
            
            if SessionService.es_sesion_completa(siguiente_pregunta):
                # Marca como completada
                SessionService.finalizar_sesion(db, session_id)
                
                logger.info(f"✅ Sesión completada: {session_id}")
                
                return {
                    "completado": True,
                    "pregunta_numero": siguiente_pregunta,
                    "total_preguntas": total_preguntas,
                    "mensaje": "¡Evaluación completada! Procesando análisis...",
                    "siguiente_paso": "Llamar a /api/v1/chatbot/analizar para obtener resultado"
                }
            else:
                # Obtiene siguiente pregunta
                siguiente_pregunta_texto = SessionService.obtener_pregunta_actual(siguiente_pregunta)
                
                logger.info(
                    f"✅ Respuesta guardada. Pregunta {siguiente_pregunta + 1}"
                    f" de {total_preguntas}"
                )
                
                return {
                    "completado": False,
                    "pregunta_numero": siguiente_pregunta + 1,
                    "pregunta": siguiente_pregunta_texto,
                    "total_preguntas": total_preguntas,
                    "progreso": f"{siguiente_pregunta}/{total_preguntas}"
                }
        
        except Exception as e:
            logger.error(f"❌ Error guardando respuesta: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def analizar_sesion(
        db: Session,
        session_id: str,
        user_id: str
    ) -> dict:
        """
        Orquesta el análisis de una sesión completada.
        """
        try:
            logger.info(f"🔍 Iniciando análisis de sesión: {session_id}")
            
            # Obtiene la sesión
            user_session = SessionService.obtener_sesion(db, session_id)
            
            if not user_session:
                logger.warning(f"⚠️ Sesión no encontrada: {session_id}")
                raise ValueError(f"Sesión no encontrada: {session_id}")
            
            # Verifica que esté completada
            if not SessionService.es_sesion_completa(user_session.pregunta_actual):
                logger.warning(f"⚠️ Sesión no completada: {session_id}")
                raise ValueError("La sesión debe estar completada para analizar")
            
            # Obtiene todas las respuestas
            respuestas_lista = SessionService.obtener_todas_respuestas(db, session_id)
            
            if not respuestas_lista:
                logger.warning(f"⚠️ No hay respuestas para sesión: {session_id}")
                raise ValueError("No hay respuestas para analizar")
            
            # Convierte al formato esperado por NLPService
            respuestas_dict = [
                {"respuesta": r["respuesta"]} for r in respuestas_lista
            ]
            
            logger.info(f"📊 Enviando {len(respuestas_dict)} respuestas al NLPService")
            
            # 🎯 Llama al NLPService
            resultado_nlp = NLPService.analizar_respuestas(respuestas_dict)
            
            logger.info(f"✅ Análisis NLP completado")
            
            # Guarda resultado en BD
            resultado_guardado = NLPService.guardar_resultado(
                db=db,
                session_id=session_id,
                user_id=user_id,
                resultado=resultado_nlp
            )
            
            logger.info(f"💾 Resultado guardado en BD")
            
            return {
                "session_id": session_id,
                "usuario": user_session.nombre,
                "fecha_analisis": datetime.utcnow().isoformat(),
                "respuestas_analizadas": len(respuestas_dict),
                "resultado": {
                    "nivel_riesgo": resultado_nlp["nivel_riesgo"],
                    "condiciones_detectadas": resultado_nlp["condiciones_detectadas"],
                    "scores_completos": resultado_nlp["scores_completos"],
                    "explicacion": resultado_nlp["explicacion"],
                    "modelo": resultado_nlp["modelo"],
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Error en análisis: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def obtener_conversacion(
        db: Session,
        session_id: str
    ) -> dict:
        """
        Obtiene el historial completo de una sesión.
        """
        try:
            logger.info(f"📖 Obteniendo conversación: {session_id}")
            
            # Obtiene la sesión
            user_session = SessionService.obtener_sesion(db, session_id)
            
            if not user_session:
                logger.warning(f"⚠️ Sesión no encontrada: {session_id}")
                raise ValueError(f"Sesión no encontrada: {session_id}")
            
            # Obtiene todas las respuestas
            conversacion = SessionService.obtener_todas_respuestas(db, session_id)
            
            logger.info(f"✅ Conversación obtenida: {len(conversacion)} intercambios")
            
            return {
                "session_id": session_id,
                "usuario": user_session.nombre,
                "completado": user_session.estado == "completada",
                "conversacion": conversacion,
                "total_respuestas": len(conversacion)
            }
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo conversación: {str(e)}")
            raise