import uuid
from sqlalchemy.orm import Session
from app.models.session import UserSession
from app.models.response import UserResponse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionService:

    # 10 preguntas alineadas a escalas clínicas validadas.
    # Cada una apunta a detectar una condición específica pero está redactada
    # de forma conversacional y abierta para que el modelo BERT capture matices.
    #
    # Mapeo diagnóstico:
    #   1 → Depresión (PHQ-9 ítem 2: anhedonia)
    #   2 → Depresión (PHQ-9 ítems 1, 6: ánimo, autoestima)
    #   3 → Ansiedad (GAD-7 ítems 1-3)
    #   4 → TDAH - inatención (ASRS-v1.1 ítems 1-4)
    #   5 → TDAH - hiperactividad/impulsividad (ASRS-v1.1 ítems 5-6)
    #   6 → Estrés académico y adaptación provincia→Lima
    #   7 → Soledad (UCLA-3 Loneliness Scale)
    #   8 → Sueño y somatización (PHQ-9 ítem 3)
    #   9 → Ideación suicida / autolesión (PHQ-9 ítem 9, C-SSRS screening)
    #  10 → Red de apoyo y búsqueda de ayuda profesional
    PREGUNTAS = [
        # 1. Depresión — anhedonia
        "En las últimas dos semanas, ¿has sentido poco interés o placer al hacer "
        "cosas que antes disfrutabas (música, salir, estudiar, hobbies)? "
        "Cuéntame con tus palabras.",

        # 2. Depresión — ánimo y autoestima
        "¿Has experimentado sentimientos de tristeza profunda, desesperanza, "
        "vacío o la sensación de ser un fracaso últimamente? Descríbeme cómo te has sentido.",

        # 3. Ansiedad — preocupación y tensión
        "¿Cómo manejas las situaciones que te generan nervios o preocupación? "
        "¿Sientes que la ansiedad se te vuelve difícil de controlar, o tienes "
        "episodios de pánico, taquicardia o sensación de ahogo?",

        # 4. TDAH — inatención
        "¿Te cuesta concentrarte en clases o al leer, terminas las tareas que "
        "empiezas, o sueles postergar mucho aunque sepas que es importante? "
        "Descríbeme cómo te va con eso.",

        # 5. TDAH — hiperactividad/impulsividad
        "¿Sueles sentirte inquieto/a, con la mente acelerada, interrumpes a "
        "otros o actúas sin pensar? ¿Te cuesta quedarte quieto/a o esperar tu turno?",

        # 6. Estrés académico y migración provincia→Lima
        "Como estudiante en UPC San Isidro (y si vienes de provincia, tomándolo "
        "en cuenta): ¿cómo has sentido la carga académica, los exámenes y la "
        "adaptación a Lima? ¿Te sientes sobrepasado/a?",

        # 7. Soledad (UCLA-3)
        "¿Con qué frecuencia te sientes solo/a, aislado/a o sientes que te "
        "falta compañía real con quien hablar de lo que te pasa? ¿Sientes que "
        "estás lejos de tu familia o de tu red de siempre?",

        # 8. Sueño y somatización
        "¿Cómo está tu sueño y tu apetito? ¿Duermes bien, te cuesta conciliar "
        "el sueño, te despiertas muy cansado/a, o has notado cambios fuertes "
        "en cuánto comes?",

        # 9. Ideación suicida / autolesión (pregunta sensible pero directa)
        "Esta pregunta es importante y sensible: ¿en las últimas semanas has "
        "tenido pensamientos de hacerte daño, de que sería mejor no estar, "
        "de desaparecer, o pensamientos que te asustan? Responde con confianza.",

        # 10. Red de apoyo y búsqueda de ayuda
        "¿Cuentas con una red de apoyo (familia, amigos cercanos, pareja, un "
        "psicólogo o consejero)? ¿Has considerado buscar ayuda profesional, "
        "o ya lo estás haciendo?",
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
