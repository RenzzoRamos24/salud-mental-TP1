"""
Servicio del Diario digital.

Responsabilidad única: CRUD de `diario_entradas` para el estudiante autenticado.
El análisis clínico (BETO) NO vive aquí — se enchufa en el Paso 2 y solo
escribe `analisis_id` en cada entrada.
"""
import logging
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.diario_entrada import DiarioEntrada

logger = logging.getLogger(__name__)


# Recorte para el preview en el listado (la UI ya lo corta también, pero
# evitamos enviar 20k caracteres al pintar la lista).
PREVIEW_CHARS = 200


class DiarioService:

    # ─────────────────────────────────────────────────────────────────
    # CREAR
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def crear(
        db: Session,
        user_id: str,
        texto: str,
        estado_animo: str = None,
        prompt_del_dia: str = None,
    ) -> DiarioEntrada:
        texto_limpio = (texto or "").strip()
        if not texto_limpio:
            raise ValueError("La entrada está vacía.")

        entrada = DiarioEntrada(
            user_id=user_id,
            texto=texto_limpio,
            estado_animo=estado_animo,
            prompt_del_dia=(prompt_del_dia or None),
            fecha=date.today(),
            timestamp=datetime.utcnow(),
        )
        db.add(entrada)
        db.commit()
        db.refresh(entrada)
        logger.info(
            f"📓 Entrada diario creada: id={entrada.id} user={user_id} "
            f"len={len(texto_limpio)}c mood={estado_animo or '-'}"
        )
        return entrada

    # ─────────────────────────────────────────────────────────────────
    # LISTAR (propias del estudiante, más reciente primero)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def listar_propias(db: Session, user_id: str) -> list[dict]:
        entradas = (
            db.query(DiarioEntrada)
            .filter(DiarioEntrada.user_id == user_id)
            .order_by(desc(DiarioEntrada.timestamp))
            .all()
        )
        return [
            {
                "id": e.id,
                "fecha": e.fecha,
                "timestamp": e.timestamp,
                "estado_animo": e.estado_animo,
                "preview": DiarioService._preview(e.texto),
            }
            for e in entradas
        ]

    # ─────────────────────────────────────────────────────────────────
    # OBTENER (propia, con validación de dueño)
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def obtener_propia(db: Session, entrada_id: int, user_id: str) -> DiarioEntrada:
        e = (
            db.query(DiarioEntrada)
            .filter(
                DiarioEntrada.id == entrada_id,
                DiarioEntrada.user_id == user_id,
            )
            .first()
        )
        if not e:
            raise ValueError("Entrada no encontrada.")
        return e

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _preview(texto: str) -> str:
        if not texto:
            return ""
        t = texto.strip()
        if len(t) <= PREVIEW_CHARS:
            return t
        return t[:PREVIEW_CHARS].rstrip() + "…"
