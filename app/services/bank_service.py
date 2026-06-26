"""
Servicio que lee el banco fijo (instrumentos validados + frases incompletas)
y administra los bloques custom de cada psicóloga.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.bank import (
    BankInstrumento,
    BankItem,
    BankFraseIncompleta,
    BloqueCustom,
    BloqueCustomItem,
)


class BankService:

    # ── Lectura del banco fijo ─────────────────────────────────────────────

    @staticmethod
    def listar_instrumentos(db: Session) -> list[dict]:
        rows = (
            db.query(BankInstrumento)
            .filter(BankInstrumento.activo == 1)
            .order_by(BankInstrumento.id)
            .all()
        )
        return [BankService._serializar_instrumento(r) for r in rows]

    @staticmethod
    def obtener_instrumento(db: Session, codigo: str) -> Optional[dict]:
        instr = (
            db.query(BankInstrumento)
            .filter(BankInstrumento.codigo == codigo, BankInstrumento.activo == 1)
            .first()
        )
        if not instr:
            return None
        data = BankService._serializar_instrumento(instr)
        data["items"] = [
            {
                "numero": it.numero,
                "texto": it.texto,
                "inverso": int(it.inverso or 0),
                "criterio_dsm5": it.criterio_dsm5,
                "bandera_crisis": int(it.bandera_crisis or 0),
            }
            for it in sorted(instr.items, key=lambda x: x.numero)
        ]
        return data

    @staticmethod
    def listar_frases(db: Session) -> list[dict]:
        rows = (
            db.query(BankFraseIncompleta)
            .filter(BankFraseIncompleta.activo == 1)
            .order_by(BankFraseIncompleta.numero)
            .all()
        )
        return [{"numero": r.numero, "area": r.area, "texto": r.texto} for r in rows]

    @staticmethod
    def areas_frases(db: Session) -> list[dict]:
        from sqlalchemy import func
        rows = (
            db.query(
                BankFraseIncompleta.area,
                func.count(BankFraseIncompleta.id).label("n"),
            )
            .filter(BankFraseIncompleta.activo == 1)
            .group_by(BankFraseIncompleta.area)
            .all()
        )
        return [{"area": area, "n_frases": n} for area, n in rows]

    @staticmethod
    def _serializar_instrumento(instr: BankInstrumento) -> dict:
        return {
            "id": instr.id,
            "codigo": instr.codigo,
            "nombre": instr.nombre,
            "autor": instr.autor,
            "anio": instr.anio,
            "dominio": instr.dominio,
            "tipo_escala": instr.tipo_escala,
            "likert_min": instr.likert_min,
            "likert_max": instr.likert_max,
            "n_items": instr.n_items,
            "tiempo_min": instr.tiempo_min,
            "instruccion": instr.instruccion,
            "citacion": instr.citacion,
            "validacion_es": instr.validacion_es,
        }

    # ── Bloques custom ─────────────────────────────────────────────────────

    @staticmethod
    def crear_bloque_custom(db: Session, psicologo_id: str, payload: dict) -> dict:
        items = payload.get("items") or []
        n = len(items)
        if n == 0:
            raise ValueError("El bloque debe tener al menos un ítem.")

        # Valida cortes
        max_total = BankService._calcular_rango_total(
            payload["tipo_escala"], payload.get("likert_min", 0),
            payload.get("likert_max", 3), n,
        )
        cortes = (
            payload["corte_sin_alerta_max"],
            payload["corte_posible_max"],
            payload["corte_alto_max"],
        )
        if not (0 <= cortes[0] < cortes[1] < cortes[2] <= max_total):
            raise ValueError(
                f"Los cortes deben ser crecientes y estar dentro del rango "
                f"(0 — {max_total})."
            )

        bloque = BloqueCustom(
            psicologo_id=psicologo_id,
            nombre=payload["nombre"].strip(),
            dominio=(payload.get("dominio") or "").strip() or None,
            tipo_escala=payload["tipo_escala"],
            likert_min=payload.get("likert_min", 0),
            likert_max=payload.get("likert_max", 3),
            instruccion=payload.get("instruccion"),
            corte_sin_alerta_max=cortes[0],
            corte_posible_max=cortes[1],
            corte_alto_max=cortes[2],
        )
        db.add(bloque)
        db.flush()
        for it in items:
            db.add(BloqueCustomItem(
                bloque_id=bloque.id,
                numero=it["numero"],
                texto=it["texto"].strip(),
                inverso=int(it.get("inverso", 0)),
            ))
        db.commit()
        db.refresh(bloque)
        return BankService._serializar_bloque(bloque)

    @staticmethod
    def listar_bloques_custom(db: Session, psicologo_id: str) -> list[dict]:
        rows = (
            db.query(BloqueCustom)
            .filter(
                BloqueCustom.psicologo_id == psicologo_id,
                BloqueCustom.activo == 1,
            )
            .order_by(BloqueCustom.created_at.desc())
            .all()
        )
        return [BankService._serializar_bloque(b) for b in rows]

    @staticmethod
    def obtener_bloque_custom(db: Session, psicologo_id: str, bloque_id: int) -> Optional[dict]:
        b = (
            db.query(BloqueCustom)
            .filter(
                BloqueCustom.id == bloque_id,
                BloqueCustom.psicologo_id == psicologo_id,
            )
            .first()
        )
        return BankService._serializar_bloque(b) if b else None

    @staticmethod
    def borrar_bloque_custom(db: Session, psicologo_id: str, bloque_id: int) -> bool:
        b = (
            db.query(BloqueCustom)
            .filter(
                BloqueCustom.id == bloque_id,
                BloqueCustom.psicologo_id == psicologo_id,
            )
            .first()
        )
        if not b:
            return False
        b.activo = 0
        db.commit()
        return True

    @staticmethod
    def actualizar_bloque_custom(
        db: Session, psicologo_id: str, bloque_id: int, payload: dict
    ) -> dict:
        b = (
            db.query(BloqueCustom)
            .filter(
                BloqueCustom.id == bloque_id,
                BloqueCustom.psicologo_id == psicologo_id,
            )
            .first()
        )
        if not b:
            raise ValueError("Bloque no encontrado o no es tuyo.")

        items = payload.get("items") or []
        if not items:
            raise ValueError("El bloque debe tener al menos un ítem.")

        max_total = BankService._calcular_rango_total(
            payload["tipo_escala"], payload.get("likert_min", 0),
            payload.get("likert_max", 3), len(items),
        )
        cortes = (
            payload["corte_sin_alerta_max"],
            payload["corte_posible_max"],
            payload["corte_alto_max"],
        )
        if not (0 <= cortes[0] < cortes[1] < cortes[2] <= max_total):
            raise ValueError(
                f"Los cortes deben ser crecientes y estar dentro del rango "
                f"(0 — {max_total})."
            )

        b.nombre = payload["nombre"].strip()
        b.dominio = (payload.get("dominio") or "").strip() or None
        b.tipo_escala = payload["tipo_escala"]
        b.likert_min = payload.get("likert_min", 0)
        b.likert_max = payload.get("likert_max", 3)
        b.instruccion = payload.get("instruccion")
        b.corte_sin_alerta_max = cortes[0]
        b.corte_posible_max = cortes[1]
        b.corte_alto_max = cortes[2]

        # Reemplazo de items (orphan delete por cascade).
        b.items.clear()
        db.flush()
        for it in items:
            db.add(BloqueCustomItem(
                bloque_id=b.id,
                numero=it["numero"],
                texto=it["texto"].strip(),
                inverso=int(it.get("inverso", 0)),
            ))
        db.commit()
        db.refresh(b)
        return BankService._serializar_bloque(b)

    @staticmethod
    def _calcular_rango_total(tipo: str, lmin: int, lmax: int, n: int) -> int:
        if tipo == "binaria":
            return n * 1
        return n * lmax

    @staticmethod
    def _serializar_bloque(b: BloqueCustom) -> dict:
        items = sorted(b.items, key=lambda x: x.numero)
        return {
            "id": b.id,
            "psicologo_id": b.psicologo_id,
            "nombre": b.nombre,
            "dominio": b.dominio,
            "tipo_escala": b.tipo_escala,
            "likert_min": b.likert_min,
            "likert_max": b.likert_max,
            "instruccion": b.instruccion,
            "corte_sin_alerta_max": b.corte_sin_alerta_max,
            "corte_posible_max": b.corte_posible_max,
            "corte_alto_max": b.corte_alto_max,
            "n_items": len(items),
            "activo": int(b.activo or 0),
            "items": [
                {"numero": it.numero, "texto": it.texto, "inverso": int(it.inverso or 0)}
                for it in items
            ],
        }

    # ── Helpers para cortes por tercios ────────────────────────────────────

    @staticmethod
    def sugerir_cortes_tercios(rango_max: int) -> dict:
        a = rango_max // 3
        b = (2 * rango_max) // 3
        return {
            "corte_sin_alerta_max": a,
            "corte_posible_max": b,
            "corte_alto_max": rango_max,
        }
