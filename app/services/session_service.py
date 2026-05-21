import uuid
from sqlalchemy.orm import Session
from app.models.session import UserSession
from app.models.response import UserResponse
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionService:
    """
    Sesión de evaluación basada en escalas clínicas validadas:
      - PHQ-9 (9 ítems, depresión, DSM-5)
      - GAD-7 (7 ítems, ansiedad generalizada, DSM-5)

    Total: 16 ítems estructurados. Cada ítem se puntúa en escala Likert 0-3
    (frecuencia en las últimas 2 semanas). El usuario responde con texto libre
    y BERT propone el score; si la confianza es baja se muestra el selector
    de 4 botones en el frontend.
    """

    # Banco "canónico" de 16 ítems (PHQ-9 luego GAD-7). El orden REAL de cada
    # sesión se decide en el triage de apertura y se guarda en
    # `UserSession.modulos_orden`. `obtener_item_para_sesion` respeta ese orden.
    PREGUNTAS = settings.PHQ9_ITEMS + settings.GAD7_ITEMS

    MODULOS_DISPONIBLES = {
        "PHQ-9": settings.PHQ9_ITEMS,
        "GAD-7": settings.GAD7_ITEMS,
    }

    @staticmethod
    def crear_sesion(db: Session, user_id: str, nombre: str = None) -> UserSession:
        session_id = str(uuid.uuid4())

        nueva_sesion = UserSession(
            id=session_id,
            user_id=user_id,
            nombre=nombre,
            estado="activa",
            pregunta_actual=0,
            fase="apertura",
            modulos_orden=None,
        )

        db.add(nueva_sesion)
        db.commit()
        db.refresh(nueva_sesion)

        return nueva_sesion

    @staticmethod
    def items_en_orden(modulos_orden: str = None) -> list:
        """
        Devuelve la lista completa de ítems en el orden indicado.
        Si `modulos_orden` es None usa el orden canónico (PHQ-9 → GAD-7).
        """
        orden = (modulos_orden or "PHQ-9,GAD-7").split(",")
        items = []
        for mod in orden:
            mod = mod.strip()
            if mod in SessionService.MODULOS_DISPONIBLES:
                items.extend(SessionService.MODULOS_DISPONIBLES[mod])
        return items

    @staticmethod
    def obtener_item_para_sesion(session: UserSession, numero_pregunta: int) -> dict:
        """Devuelve el ítem en posición `numero_pregunta` respetando el orden de la sesión."""
        items = SessionService.items_en_orden(session.modulos_orden)
        if 0 <= numero_pregunta < len(items):
            return items[numero_pregunta]
        return None

    @staticmethod
    def actualizar_fase(db: Session, session_id: str, fase: str, modulos_orden: str = None,
                        apertura_texto: str = None) -> None:
        sesion = SessionService.obtener_sesion(db, session_id)
        if not sesion:
            return
        sesion.fase = fase
        if modulos_orden is not None:
            sesion.modulos_orden = modulos_orden
        if apertura_texto is not None:
            sesion.apertura_texto = apertura_texto
        db.commit()

    @staticmethod
    def obtener_sesion(db: Session, session_id: str) -> UserSession:
        return db.query(UserSession).filter(
            UserSession.id == session_id
        ).first()

    @staticmethod
    def obtener_item(numero_pregunta: int) -> dict:
        """Devuelve el dict completo del ítem clínico en esa posición."""
        if 0 <= numero_pregunta < len(SessionService.PREGUNTAS):
            return SessionService.PREGUNTAS[numero_pregunta]
        return None

    @staticmethod
    def obtener_pregunta_actual(numero_pregunta: int) -> str:
        """Compat: devuelve solo el texto de la pregunta."""
        item = SessionService.obtener_item(numero_pregunta)
        return item["texto"] if item else None

    @staticmethod
    def guardar_respuesta(
        db: Session,
        session_id: str,
        numero_pregunta: int,
        pregunta: str,
        respuesta: str,
        item: dict = None,
        score_likert: int = None,
        confianza_likert: float = None,
        score_origen: str = None,
    ) -> UserResponse:
        nueva_respuesta = UserResponse(
            session_id=session_id,
            numero_pregunta=numero_pregunta,
            pregunta=pregunta,
            respuesta=respuesta,
        )
        if item is not None:
            nueva_respuesta.item_codigo = item.get("id")
            nueva_respuesta.modulo = item.get("modulo")
            nueva_respuesta.criterio_dsm5 = item.get("criterio_dsm5")
        if score_likert is not None:
            nueva_respuesta.score_likert = score_likert
        if confianza_likert is not None:
            nueva_respuesta.confianza_likert = confianza_likert
        if score_origen is not None:
            nueva_respuesta.score_origen = score_origen

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
            "respuesta": r.respuesta,
            "item_codigo": r.item_codigo,
            "modulo": r.modulo,
            "criterio_dsm5": r.criterio_dsm5,
            "score_likert": r.score_likert,
            "score_origen": r.score_origen,
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
