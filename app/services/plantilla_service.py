"""
Servicio de plantillas: la psicóloga arma cuestionarios combinando bloques
del banco fijo, bloques custom y áreas de frases incompletas.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.bank import (
    PlantillaCuestionario,
    PlantillaBloque,
    BankInstrumento,
    BloqueCustom,
)


class PlantillaService:

    @staticmethod
    def crear(db: Session, psicologo_id: str, payload: dict) -> dict:
        bloques = payload.get("bloques") or []
        if not bloques:
            raise ValueError("La plantilla debe tener al menos un bloque.")

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
                if not frases_areas or not isinstance(frases_areas, list):
                    raise ValueError("Debes elegir al menos un área de frases.")
            else:
                raise ValueError(f"Tipo de bloque desconocido: {tipo}")

            db.add(PlantillaBloque(
                plantilla_id=plantilla.id,
                orden=b.get("orden", idx),
                tipo=tipo,
                instrumento_id=instrumento_id if tipo == "instrumento" else None,
                bloque_custom_id=bloque_custom_id if tipo == "custom" else None,
                frases_areas=",".join(frases_areas) if tipo == "frases" else None,
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
                if not b.get("frases_areas"):
                    raise ValueError("Debes elegir al menos un área de frases.")
            else:
                raise ValueError(f"Tipo de bloque desconocido: {tipo}")

        # Reemplazar bloques
        p.bloques.clear()
        db.flush()
        for idx, b in enumerate(bloques):
            db.add(PlantillaBloque(
                plantilla_id=p.id,
                orden=b.get("orden", idx),
                tipo=b["tipo"],
                instrumento_id=b.get("instrumento_id") if b["tipo"] == "instrumento" else None,
                bloque_custom_id=b.get("bloque_custom_id") if b["tipo"] == "custom" else None,
                frases_areas=",".join(b["frases_areas"]) if b["tipo"] == "frases" else None,
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
        return {
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
                }
                for b in bloques
            ],
        }
