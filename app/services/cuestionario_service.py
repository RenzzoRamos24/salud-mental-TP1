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
from app.services.feedback_service import FeedbackService


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
        from app.services.plantilla_service import validar_maximo
        validar_maximo(db, plantilla.bloques)

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
    def asignar_por_grado(
        db: Session, psicologo_id: str, plantilla_id: int, grado: str
    ) -> dict:
        """Asigna la plantilla a todo un salón (grado) de una vez.

        Alcance: los alumnos activos de ese grado que tienen a esta psicóloga
        como responsable — los mismos que ve en su lista. Salta a quien ya
        tiene esa misma plantilla pendiente o en curso, para no duplicar.
        Todo en una sola transacción: o se asignan todos, o ninguno.
        """
        from app.services.plantilla_service import validar_maximo

        plantilla = (
            db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.id == plantilla_id)
            .first()
        )
        if not plantilla or plantilla.psicologo_id != psicologo_id:
            raise ValueError("Plantilla no encontrada o no es tuya.")
        n_preguntas = validar_maximo(db, plantilla.bloques)

        grado = (grado or "").strip()
        if not grado:
            raise ValueError("Elige un salón.")

        alumnos = (
            db.query(User)
            .filter(
                User.role == "estudiante",
                User.activo == True,  # noqa: E712
                User.grado == grado,
                User.psicologo_id == psicologo_id,
            )
            .all()
        )
        if not alumnos:
            raise ValueError(f"No tienes alumnos de {grado} a tu cargo.")

        ya_activos = {
            a.estudiante_id
            for a in db.query(AplicacionCuestionario)
            .filter(
                AplicacionCuestionario.plantilla_id == plantilla_id,
                AplicacionCuestionario.estudiante_id.in_([u.id for u in alumnos]),
                AplicacionCuestionario.estado.in_(["pendiente", "en_progreso"]),
            )
            .all()
        }
        nuevos = [u for u in alumnos if u.id not in ya_activos]
        for u in nuevos:
            db.add(AplicacionCuestionario(
                plantilla_id=plantilla_id,
                estudiante_id=u.id,
                psicologo_id=psicologo_id,
            ))
        db.commit()
        return {
            "grado": grado,
            "plantilla": plantilla.nombre,
            "n_preguntas": n_preguntas,
            "alumnos_en_grado": len(alumnos),
            "asignados": len(nuevos),
            "omitidos_ya_tenian": len(ya_activos),
        }

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
                numeros = [n.strip() for n in (b.frases_numeros or "").split(",") if n.strip()]
                if numeros:
                    filtro = BankFraseIncompleta.numero.in_([int(n) for n in numeros])
                else:
                    areas = [a.strip() for a in (b.frases_areas or "").split(",") if a.strip()]
                    filtro = BankFraseIncompleta.area.in_(areas)
                rows = (
                    db.query(BankFraseIncompleta)
                    .filter(filtro, BankFraseIncompleta.activo == 1)
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

        est = db.query(User).filter(User.id == app_.estudiante_id).first()
        estudiante = {
            "id": app_.estudiante_id,
            "nombre": est.nombre if est else None,
            "apellido": est.apellido if est else None,
            "codigo_acceso": getattr(est, "codigo_acceso", None) if est else None,
            "grado": getattr(est, "grado", None) if est else None,
        }

        return {
            "id": app_.id,
            "estudiante_id": app_.estudiante_id,
            "estudiante": estudiante,
            "psicologo_id": app_.psicologo_id,
            "plantilla_id": app_.plantilla_id,
            "estado": app_.estado,
            "asignada_at": app_.asignada_at.isoformat() if app_.asignada_at else None,
            "completada_at": app_.completada_at.isoformat() if app_.completada_at else None,
            "resultado": resultado,
            # Respuestas ítem por ítem de TODOS los instrumentos del cuestionario
            # (PHQ-A, GAD-7, etc.), para que la psicóloga pueda señalar el ítem
            # exacto que levantó una bandera. Antes solo existía para DASS-21.
            "instrumentos_detalle": CuestionarioService._instrumentos_detalle(
                db, aplicacion_id
            ),
            # Detalle DASS-21 para que la psicóloga pueda validar la opinión
            # del SVM viendo exactamente qué respondió el alumno.
            "dass21_detalle": CuestionarioService._dass21_detalle(db, aplicacion_id),
            # Veredicto ya emitido sobre el análisis del modelo, para que la
            # vista pinte los botones en el estado en que quedaron.
            "feedback": FeedbackService.por_aplicacion(db, aplicacion_id),
        }

    # ── Respuestas ítem por ítem de cada instrumento del cuestionario ──────
    @staticmethod
    def _instrumentos_detalle(db: Session, aplicacion_id: int) -> list[dict]:
        """Para cada bloque de instrumento respondido, los ítems con su valor,
        el texto del ítem y si es un ítem con bandera de crisis (p. ej. PHQ-A
        #9). Ordenado por código de instrumento y número de ítem."""
        from app.models.bank import RespuestaAplicacion, BankInstrumento

        rows = (
            db.query(RespuestaAplicacion)
            .filter(RespuestaAplicacion.aplicacion_id == aplicacion_id)
            .filter(RespuestaAplicacion.origen.like("INSTR:%"))
            .filter(RespuestaAplicacion.valor_num.isnot(None))
            .all()
        )
        if not rows:
            return []

        # origen = "INSTR:<codigo>:<numero>" → agrupar por código.
        por_codigo: dict[str, dict[int, int]] = {}
        for r in rows:
            partes = r.origen.split(":")
            if len(partes) != 3:
                continue
            codigo, numero = partes[1], partes[2]
            try:
                por_codigo.setdefault(codigo, {})[int(numero)] = int(r.valor_num)
            except (ValueError, TypeError):
                continue

        salida = []
        for codigo, valores in por_codigo.items():
            instr = (
                db.query(BankInstrumento)
                .filter(BankInstrumento.codigo == codigo)
                .first()
            )
            if not instr:
                continue
            items = []
            for it in sorted(instr.items, key=lambda x: x.numero):
                if it.numero not in valores:
                    continue
                items.append({
                    "numero": it.numero,
                    "texto": it.texto,
                    "valor": valores[it.numero],
                    "es_crisis": bool(it.bandera_crisis),
                })
            if items:
                salida.append({
                    "codigo": instr.codigo,
                    "nombre": instr.nombre,
                    "likert_min": instr.likert_min,
                    "likert_max": instr.likert_max,
                    "items": items,
                })
        salida.sort(key=lambda b: b["codigo"])
        return salida

    # ── Detalle DASS-21 (respuestas item-a-item por subescala) ─────────────
    @staticmethod
    def _dass21_detalle(db: Session, aplicacion_id: int) -> dict | None:
        from app.models.bank import RespuestaAplicacion, BankInstrumento

        dass = db.query(BankInstrumento).filter_by(codigo="DASS-21").first()
        if not dass:
            return None

        rows = (
            db.query(RespuestaAplicacion)
            .filter(RespuestaAplicacion.aplicacion_id == aplicacion_id)
            .filter(RespuestaAplicacion.origen.like("INSTR:DASS-21:%"))
            .all()
        )
        if not rows:
            return None
        resps = {r.origen: r for r in rows}

        # Índices de subescala (item numero 1-21 → 'D'|'A'|'S')
        DEP = {3, 5, 10, 13, 16, 17, 21}
        ANS = {2, 4, 7, 9, 15, 19, 20}
        LABELS = ["No me aplicó", "Un poco", "Bastante", "Mucho"]

        items_out = []
        for it in sorted(dass.items, key=lambda x: x.numero):
            r = resps.get(f"INSTR:DASS-21:{it.numero}")
            val = int(r.valor_num) if r and r.valor_num is not None else None
            sub = "D" if it.numero in DEP else "A" if it.numero in ANS else "S"
            items_out.append({
                "numero": it.numero,
                "texto": it.texto,
                "valor": val,
                "etiqueta": LABELS[val] if val is not None and 0 <= val <= 3 else None,
                "subescala": sub,
            })

        def _sub_total(nums):
            total = 0
            for n in nums:
                r = resps.get(f"INSTR:DASS-21:{n}")
                if r and r.valor_num is not None:
                    total += int(r.valor_num)
            return total * 2  # DASS-21 × 2 = escala DASS-42

        return {
            "items": items_out,
            "subtotales": {
                "depresion": _sub_total(DEP),
                "ansiedad": _sub_total(ANS),
                "estres": _sub_total({1, 6, 8, 11, 12, 14, 18}),
            },
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
