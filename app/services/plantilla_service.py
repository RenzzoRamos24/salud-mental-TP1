"""
Servicio de plantillas: la psicóloga arma cuestionarios combinando bloques
del banco fijo, bloques custom y áreas de frases incompletas.
"""
from typing import Optional
from sqlalchemy.orm import Session, object_session
from app.models.bank import (
    PlantillaCuestionario,
    PlantillaBloque,
    BankInstrumento,
    BankFraseIncompleta,
    BloqueCustom,
    BloqueCustomItem,
)

# Tope de preguntas por cuestionario (ítems de instrumentos + ítems custom +
# frases). El cuestionario del piloto —PHQ-A 9 + GAD-7 7 + 10 frases— queda
# justo en 26. El frontend repite este número para avisar antes de guardar;
# el que manda es este.
MAX_PREGUNTAS = 26


def _campo(b, nombre):
    """Lee un campo de un bloque venga como dict (payload) o como fila ORM."""
    return b.get(nombre) if isinstance(b, dict) else getattr(b, nombre, None)


def contar_preguntas(db: Session, bloques) -> int:
    """Cuenta las preguntas que verá el alumno con estos bloques."""
    total = 0
    for b in bloques:
        tipo = _campo(b, "tipo")
        if tipo == "instrumento":
            ins = db.query(BankInstrumento).filter(
                BankInstrumento.id == _campo(b, "instrumento_id")
            ).first()
            total += ins.n_items if ins else 0
        elif tipo == "custom":
            total += db.query(BloqueCustomItem).filter(
                BloqueCustomItem.bloque_id == _campo(b, "bloque_custom_id")
            ).count()
        elif tipo == "frases":
            numeros = _campo(b, "frases_numeros")
            if isinstance(numeros, str):
                numeros = [n for n in numeros.split(",") if n.strip()]
            if numeros:
                total += len(numeros)
                continue
            areas = _campo(b, "frases_areas")
            if isinstance(areas, str):
                areas = [a.strip() for a in areas.split(",") if a.strip()]
            if areas:
                total += db.query(BankFraseIncompleta).filter(
                    BankFraseIncompleta.area.in_(areas),
                    BankFraseIncompleta.activo == 1,
                ).count()
    return total


def validar_maximo(db: Session, bloques) -> int:
    n = contar_preguntas(db, bloques)
    if n > MAX_PREGUNTAS:
        raise ValueError(
            f"El cuestionario tiene {n} preguntas y el máximo permitido es "
            f"{MAX_PREGUNTAS}. Quita bloques o frases hasta llegar a "
            f"{MAX_PREGUNTAS} o menos."
        )
    return n


class PlantillaService:

    @staticmethod
    def crear(db: Session, psicologo_id: str, payload: dict) -> dict:
        bloques = payload.get("bloques") or []
        if not bloques:
            raise ValueError("La plantilla debe tener al menos un bloque.")
        validar_maximo(db, bloques)

        plantilla = PlantillaCuestionario(
            psicologo_id=psicologo_id,
            nombre=payload["nombre"].strip(),
            descripcion=(payload.get("descripcion") or "").strip() or None,
        )
        db.add(plantilla)
        db.flush()

        for idx, b in enumerate(bloques):
            tipo = b["tipo"]
            instrumento_id = b.get("instrumento_id")
            bloque_custom_id = b.get("bloque_custom_id")
            frases_areas = b.get("frases_areas")
            frases_numeros = b.get("frases_numeros")

            if tipo == "instrumento":
                if not instrumento_id or not db.query(BankInstrumento).filter(
                    BankInstrumento.id == instrumento_id
                ).first():
                    raise ValueError(f"Instrumento {instrumento_id} inválido.")
            elif tipo == "custom":
                bc = db.query(BloqueCustom).filter(
                    BloqueCustom.id == bloque_custom_id,
                    BloqueCustom.psicologo_id == psicologo_id,
                ).first()
                if not bc:
                    raise ValueError(
                        f"Bloque custom {bloque_custom_id} inválido o no es tuyo."
                    )
            elif tipo == "frases":
                tiene_numeros = isinstance(frases_numeros, list) and frases_numeros
                tiene_areas = isinstance(frases_areas, list) and frases_areas
                if not tiene_numeros and not tiene_areas:
                    raise ValueError(
                        "Debes elegir al menos un área o unas frases puntuales."
                    )
            else:
                raise ValueError(f"Tipo de bloque desconocido: {tipo}")

            db.add(PlantillaBloque(
                plantilla_id=plantilla.id,
                orden=b.get("orden", idx),
                tipo=tipo,
                instrumento_id=instrumento_id if tipo == "instrumento" else None,
                bloque_custom_id=bloque_custom_id if tipo == "custom" else None,
                frases_areas=(
                    ",".join(frases_areas)
                    if tipo == "frases" and frases_areas else None
                ),
                frases_numeros=(
                    ",".join(str(n) for n in frases_numeros)
                    if tipo == "frases" and frases_numeros else None
                ),
            ))

        db.commit()
        db.refresh(plantilla)
        return PlantillaService._serializar(plantilla)

    @staticmethod
    def listar(db: Session, psicologo_id: str) -> list[dict]:
        rows = (
            db.query(PlantillaCuestionario)
            .filter(
                PlantillaCuestionario.psicologo_id == psicologo_id,
                PlantillaCuestionario.activa == 1,
            )
            .order_by(PlantillaCuestionario.created_at.desc())
            .all()
        )
        return [PlantillaService._serializar(p) for p in rows]

    @staticmethod
    def obtener(db: Session, psicologo_id: str, plantilla_id: int) -> Optional[dict]:
        p = (
            db.query(PlantillaCuestionario)
            .filter(
                PlantillaCuestionario.id == plantilla_id,
                PlantillaCuestionario.psicologo_id == psicologo_id,
            )
            .first()
        )
        return PlantillaService._serializar(p) if p else None

    @staticmethod
    def obtener_libre(db: Session, plantilla_id: int) -> Optional[PlantillaCuestionario]:
        return (
            db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.id == plantilla_id)
            .first()
        )

    @staticmethod
    def actualizar(
        db: Session, psicologo_id: str, plantilla_id: int, payload: dict
    ) -> dict:
        p = (
            db.query(PlantillaCuestionario)
            .filter(
                PlantillaCuestionario.id == plantilla_id,
                PlantillaCuestionario.psicologo_id == psicologo_id,
            )
            .first()
        )
        if not p:
            raise ValueError("Plantilla no encontrada o no es tuya.")

        bloques = payload.get("bloques") or []
        if not bloques:
            raise ValueError("La plantilla debe tener al menos un bloque.")
        validar_maximo(db, bloques)

        p.nombre = payload["nombre"].strip()
        p.descripcion = (payload.get("descripcion") or "").strip() or None

        # Validar referencias antes de reemplazar
        for b in bloques:
            tipo = b["tipo"]
            if tipo == "instrumento":
                if not b.get("instrumento_id") or not db.query(BankInstrumento).filter(
                    BankInstrumento.id == b["instrumento_id"]
                ).first():
                    raise ValueError(f"Instrumento {b.get('instrumento_id')} inválido.")
            elif tipo == "custom":
                bc = db.query(BloqueCustom).filter(
                    BloqueCustom.id == b.get("bloque_custom_id"),
                    BloqueCustom.psicologo_id == psicologo_id,
                ).first()
                if not bc:
                    raise ValueError(
                        f"Bloque custom {b.get('bloque_custom_id')} inválido o no es tuyo."
                    )
            elif tipo == "frases":
                if not b.get("frases_areas") and not b.get("frases_numeros"):
                    raise ValueError(
                        "Debes elegir al menos un área o unas frases puntuales."
                    )
            else:
                raise ValueError(f"Tipo de bloque desconocido: {tipo}")

        # Reemplazar bloques
        p.bloques.clear()
        db.flush()
        for idx, b in enumerate(bloques):
            es_frases = b["tipo"] == "frases"
            db.add(PlantillaBloque(
                plantilla_id=p.id,
                orden=b.get("orden", idx),
                tipo=b["tipo"],
                instrumento_id=b.get("instrumento_id") if b["tipo"] == "instrumento" else None,
                bloque_custom_id=b.get("bloque_custom_id") if b["tipo"] == "custom" else None,
                frases_areas=(
                    ",".join(b["frases_areas"])
                    if es_frases and b.get("frases_areas") else None
                ),
                frases_numeros=(
                    ",".join(str(n) for n in b["frases_numeros"])
                    if es_frases and b.get("frases_numeros") else None
                ),
            ))
        db.commit()
        db.refresh(p)
        return PlantillaService._serializar(p)

    @staticmethod
    def borrar(db: Session, psicologo_id: str, plantilla_id: int) -> bool:
        p = (
            db.query(PlantillaCuestionario)
            .filter(
                PlantillaCuestionario.id == plantilla_id,
                PlantillaCuestionario.psicologo_id == psicologo_id,
            )
            .first()
        )
        if not p:
            return False
        p.activa = 0
        db.commit()
        return True

    @staticmethod
    def _serializar(p: PlantillaCuestionario) -> dict:
        bloques = sorted(p.bloques, key=lambda x: x.orden)
        db = object_session(p)
        return {
            "n_preguntas": contar_preguntas(db, bloques) if db else None,
            "max_preguntas": MAX_PREGUNTAS,
            "id": p.id,
            "psicologo_id": p.psicologo_id,
            "nombre": p.nombre,
            "descripcion": p.descripcion,
            "activa": int(p.activa or 0),
            "created_at": p.created_at,
            "bloques": [
                {
                    "id": b.id,
                    "orden": b.orden,
                    "tipo": b.tipo,
                    "instrumento_id": b.instrumento_id,
                    "bloque_custom_id": b.bloque_custom_id,
                    "frases_areas": (
                        b.frases_areas.split(",") if b.frases_areas else None
                    ),
                    "frases_numeros": (
                        [int(n) for n in b.frases_numeros.split(",") if n.strip()]
                        if getattr(b, "frases_numeros", None) else None
                    ),
                }
                for b in bloques
            ],
        }
