"""
Servicio de aplicación de cuestionarios:
  * la psicóloga asigna una plantilla a un alumno;
  * el alumno ve sus cuestionarios pendientes y los responde;
  * al cerrar, se ejecuta el evaluator que produce el reporte.
"""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.bank import (
    AplicacionCuestionario,
    RespuestaAplicacion,
    PlantillaCuestionario,
    PlantillaBloque,
    BankInstrumento,
    BankItem,
    BankFraseIncompleta,
    BloqueCustom,
    BloqueCustomItem,
)


class CuestionarioService:

    # ── Asignación ──────────────────────────────────────────────────────────

    @staticmethod
    def asignar(
        db: Session, psicologo_id: str, plantilla_id: int, estudiante_id: str
    ) -> dict:
        plantilla = (
            db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.id == plantilla_id)
            .first()
        )
        if not plantilla or plantilla.psicologo_id != psicologo_id:
            raise ValueError("Plantilla no encontrada o no es tuya.")

        estudiante = (
            db.query(User)
            .filter(User.id == estudiante_id, User.role == "estudiante")
            .first()
        )
        if not estudiante:
            raise ValueError("Estudiante no encontrado.")

        app_ = AplicacionCuestionario(
            plantilla_id=plantilla_id,
            estudiante_id=estudiante_id,
            psicologo_id=psicologo_id,
        )
        db.add(app_)
        db.commit()
        db.refresh(app_)
        return {
            "id": app_.id,
            "plantilla_id": app_.plantilla_id,
            "estudiante_id": app_.estudiante_id,
            "estado": app_.estado,
            "asignada_at": app_.asignada_at.isoformat(),
        }

    # ── Listado para alumno ─────────────────────────────────────────────────

    @staticmethod
    def listar_para_estudiante(db: Session, estudiante_id: str) -> list[dict]:
        rows = (
            db.query(AplicacionCuestionario, PlantillaCuestionario)
            .join(
                PlantillaCuestionario,
                PlantillaCuestionario.id == AplicacionCuestionario.plantilla_id,
            )
            .filter(AplicacionCuestionario.estudiante_id == estudiante_id)
            .order_by(desc(AplicacionCuestionario.asignada_at))
            .all()
        )
        out = []
        for app_, plantilla in rows:
            preguntas = CuestionarioService.render_preguntas(db, plantilla)
            out.append({
                "id": app_.id,
                "plantilla_id": plantilla.id,
                "plantilla_nombre": plantilla.nombre,
                "estado": app_.estado,
                "asignada_at": app_.asignada_at,
                "completada_at": app_.completada_at,
                "n_preguntas": len(preguntas),
            })
        return out

    # ── Render de preguntas ─────────────────────────────────────────────────

    @staticmethod
    def render_preguntas(
        db: Session, plantilla: PlantillaCuestionario
    ) -> list[dict]:
        """
        Devuelve la lista de preguntas en el orden en que debe verlas el alumno.
        Cada pregunta es un dict {origen, bloque_codigo, bloque_nombre, tipo,
        likert_min, likert_max, texto}.
        """
        preguntas = []
        bloques = sorted(plantilla.bloques, key=lambda b: b.orden)
        for b in bloques:
            if b.tipo == "instrumento":
                instr = (
                    db.query(BankInstrumento)
                    .filter(BankInstrumento.id == b.instrumento_id)
                    .first()
                )
                if not instr:
                    continue
                items = sorted(instr.items, key=lambda x: x.numero)
                for it in items:
                    preguntas.append({
                        "origen": f"INSTR:{instr.codigo}:{it.numero}",
                        "bloque_codigo": instr.codigo,
                        "bloque_nombre": instr.nombre,
                        "tipo": "likert" if instr.tipo_escala == "likert" else "binaria",
                        "likert_min": instr.likert_min,
                        "likert_max": instr.likert_max,
                        "texto": it.texto,
                    })
            elif b.tipo == "custom":
                bc = (
                    db.query(BloqueCustom)
                    .filter(BloqueCustom.id == b.bloque_custom_id)
                    .first()
                )
                if not bc:
                    continue
                items = sorted(bc.items, key=lambda x: x.numero)
                for it in items:
                    preguntas.append({
                        "origen": f"CUSTOM:{bc.id}:{it.numero}",
                        "bloque_codigo": f"CUSTOM:{bc.id}",
                        "bloque_nombre": bc.nombre,
                        "tipo": "likert" if bc.tipo_escala == "likert" else "binaria",
                        "likert_min": bc.likert_min,
                        "likert_max": bc.likert_max,
                        "texto": it.texto,
                    })
            elif b.tipo == "frases":
                areas = (b.frases_areas or "").split(",")
                areas = [a.strip() for a in areas if a.strip()]
                rows = (
                    db.query(BankFraseIncompleta)
                    .filter(
                        BankFraseIncompleta.area.in_(areas),
                        BankFraseIncompleta.activo == 1,
                    )
                    .order_by(BankFraseIncompleta.numero)
                    .all()
                )
                for fr in rows:
                    preguntas.append({
                        "origen": f"FRASE:{fr.numero}",
                        "bloque_codigo": "FRASES",
                        "bloque_nombre": f"Frases incompletas — {fr.area}",
                        "tipo": "texto",
                        "likert_min": None,
                        "likert_max": None,
                        "texto": fr.texto,
                    })
        return preguntas

    # ── Detalle de aplicación para responder ────────────────────────────────

    @staticmethod
    def detalle_para_responder(
        db: Session, estudiante_id: str, aplicacion_id: int
    ) -> dict:
        app_ = (
            db.query(AplicacionCuestionario)
            .filter(
                AplicacionCuestionario.id == aplicacion_id,
                AplicacionCuestionario.estudiante_id == estudiante_id,
            )
            .first()
        )
        if not app_:
            raise ValueError("Aplicación no encontrada.")
        if app_.estado == "completado" or app_.estado == "revisado":
            raise ValueError("Este cuestionario ya fue completado.")

        plantilla = (
            db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.id == app_.plantilla_id)
            .first()
        )
        preguntas = CuestionarioService.render_preguntas(db, plantilla)

        if app_.iniciada_at is None:
            app_.iniciada_at = datetime.utcnow()
            app_.estado = "en_progreso"
            db.commit()

        return {
            "id": app_.id,
            "plantilla_id": plantilla.id,
            "plantilla_nombre": plantilla.nombre,
            "descripcion": plantilla.descripcion,
            "estado": app_.estado,
            "preguntas": preguntas,
        }

    # ── Envío de respuestas + cierre ────────────────────────────────────────

    @staticmethod
    def guardar_respuestas(
        db: Session, estudiante_id: str, aplicacion_id: int, respuestas: list[dict]
    ) -> AplicacionCuestionario:
        app_ = (
            db.query(AplicacionCuestionario)
            .filter(
                AplicacionCuestionario.id == aplicacion_id,
                AplicacionCuestionario.estudiante_id == estudiante_id,
            )
            .first()
        )
        if not app_:
            raise ValueError("Aplicación no encontrada.")
        if app_.estado in ("completado", "revisado"):
            raise ValueError("Este cuestionario ya fue completado.")

        # Reemplaza respuestas existentes (idempotente).
        db.query(RespuestaAplicacion).filter(
            RespuestaAplicacion.aplicacion_id == aplicacion_id
        ).delete()

        for r in respuestas:
            db.add(RespuestaAplicacion(
                aplicacion_id=aplicacion_id,
                origen=r["origen"],
                valor_num=r.get("valor_num"),
                valor_texto=r.get("valor_texto"),
            ))
        db.commit()
        db.refresh(app_)
        return app_

    @staticmethod
    def cerrar_y_evaluar(
        db: Session, estudiante_id: str, aplicacion_id: int
    ) -> dict:
        from app.services.evaluator_service import EvaluatorService
        app_ = (
            db.query(AplicacionCuestionario)
            .filter(
                AplicacionCuestionario.id == aplicacion_id,
                AplicacionCuestionario.estudiante_id == estudiante_id,
            )
            .first()
        )
        if not app_:
            raise ValueError("Aplicación no encontrada.")

        resultado = EvaluatorService.evaluar(db, app_)

        app_.estado = "completado"
        app_.completada_at = datetime.utcnow()
        app_.resultado_json = json.dumps(resultado, ensure_ascii=False)
        app_.riesgo_global = resultado.get("riesgo_global")
        app_.crisis_activada = bool(resultado.get("crisis_activada"))
        db.commit()
        db.refresh(app_)
        return resultado

    # ── Resultado para psicóloga ────────────────────────────────────────────

    @staticmethod
    def obtener_resultado(
        db: Session, psicologo_id: str, aplicacion_id: int, es_admin: bool = False
    ) -> dict:
        app_ = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.id == aplicacion_id)
            .first()
        )
        if not app_:
            raise ValueError("Aplicación no encontrada.")
        if not es_admin and app_.psicologo_id != psicologo_id:
            raise ValueError("No tienes acceso a este resultado.")

        resultado = json.loads(app_.resultado_json) if app_.resultado_json else None
        return {
            "id": app_.id,
            "estudiante_id": app_.estudiante_id,
            "psicologo_id": app_.psicologo_id,
            "plantilla_id": app_.plantilla_id,
            "estado": app_.estado,
            "asignada_at": app_.asignada_at.isoformat() if app_.asignada_at else None,
            "completada_at": app_.completada_at.isoformat() if app_.completada_at else None,
            "resultado": resultado,
        }

    @staticmethod
    def marcar_revisado(
        db: Session, psicologo_id: str, aplicacion_id: int
    ) -> AplicacionCuestionario:
        app_ = (
            db.query(AplicacionCuestionario)
            .filter(
                AplicacionCuestionario.id == aplicacion_id,
                AplicacionCuestionario.psicologo_id == psicologo_id,
            )
            .first()
        )
        if not app_:
            raise ValueError("Aplicación no encontrada o no es tuya.")
        app_.estado = "revisado"
        app_.revisada_at = datetime.utcnow()
        db.commit()
        db.refresh(app_)
        return app_
