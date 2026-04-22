import uuid
from sqlalchemy.orm import Session
from app.models.session import UserSession
from app.models.response import UserResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionService:
    
    # ✅ PREGUNTAS DENTRO DE LA CLASE
    PREGUNTAS = [
        "¿Cómo te has sentido emocionalmente en los últimos días?",
        "¿Has experimentado cambios en tu sueño o apetito?",
        "¿Sientes dificultad para concentrarte en tareas cotidianas?",
        "¿Has tenido pensamientos negativos recurrentes?",
        "¿Cómo es tu relación con amigos y familia actualmente?",
        "¿Realizas actividades que te generan placer?",
        "¿Sientes ansiedad o preocupación excesiva?",
        "¿Has considerado hacerte daño a ti mismo o a otros?",
        "¿Tienes acceso a apoyo profesional o redes de contención?",
        "¿Hay algo más que quieras compartir sobre tu estado emocional?"
    ]
    
    @staticmethod
    def crear_sesion(db: Session, user_id: str, nombre: str = None) -> UserSession:
        session_id = str(uuid.uuid4())
        
        nueva_sesion = UserSession(
            id=session_id,
            user_id=user_id,
            nombre=nombre,
            estado="activa",
            pregunta_actual=0
        )
        
        db.add(nueva_sesion)
        db.commit()
        db.refresh(nueva_sesion)
        
        return nueva_sesion
    
    @staticmethod
    def obtener_sesion(db: Session, session_id: str) -> UserSession:
        return db.query(UserSession).filter(
            UserSession.id == session_id
        ).first()
    
    @staticmethod
    def obtener_pregunta_actual(numero_pregunta: int) -> str:
        if 0 <= numero_pregunta < len(SessionService.PREGUNTAS):
            return SessionService.PREGUNTAS[numero_pregunta]
        return None
    
    @staticmethod
    def guardar_respuesta(
        db: Session, 
        session_id: str, 
        numero_pregunta: int, 
        pregunta: str,
        respuesta: str
    ) -> UserResponse:
        nueva_respuesta = UserResponse(
            session_id=session_id,
            numero_pregunta=numero_pregunta,
            pregunta=pregunta,
            respuesta=respuesta
        )
        
        db.add(nueva_respuesta)
        db.commit()
        db.refresh(nueva_respuesta)
        
        return nueva_respuesta
    
    @staticmethod
    def actualizar_pregunta(db: Session, session_id: str, numero_pregunta: int):
        sesion = SessionService.obtener_sesion(db, session_id)
        if sesion:
            sesion.pregunta_actual = numero_pregunta
            db.commit()
    
    @staticmethod
    def obtener_todas_respuestas(db: Session, session_id: str) -> list:
        respuestas = db.query(UserResponse).filter(
            UserResponse.session_id == session_id
        ).order_by(UserResponse.numero_pregunta).all()
        
        return [{
            "numero": r.numero_pregunta,
            "pregunta": r.pregunta,
            "respuesta": r.respuesta
        } for r in respuestas]
    
    @staticmethod
    def finalizar_sesion(db: Session, session_id: str):
        sesion = SessionService.obtener_sesion(db, session_id)
        if sesion:
            sesion.estado = "completada"
            sesion.pregunta_actual = len(SessionService.PREGUNTAS)
            sesion.timestamp_fin = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def es_sesion_completa(numero_pregunta: int) -> bool:
        return numero_pregunta >= len(SessionService.PREGUNTAS)