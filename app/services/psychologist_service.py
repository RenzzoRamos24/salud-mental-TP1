"""
Servicio del rol psicólogo (Sprint 9 — cuestionarios).

El modelo de "diario + ciclos" ya no aplica. Las métricas se calculan ahora
sobre AplicacionCuestionario (asignaciones a alumnos) y su evaluación.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user import User
from app.models.bank import AplicacionCuestionario

logger = logging.getLogger(__name__)


def _ultima_aplicacion_revisada(db: Session, user_id: str):
    return (
        db.query(AplicacionCuestionario)
        .filter(
            AplicacionCuestionario.estudiante_id == user_id,
            AplicacionCuestionario.completada_at.isnot(None),
        )
        .order_by(desc(AplicacionCuestionario.completada_at))
        .first()
    )


class PsychologistService:

    @staticmethod
    def stats_dashboard(db: Session, psicologo_id: str | None = None,
                        es_admin: bool = False) -> dict:
        """Métricas agregadas para el dashboard del psicólogo.

        - Si `es_admin=True`: ve todos los estudiantes activos.
        - Si no: ve solo los estudiantes cuyo `psicologo_id` coincide.
        """
        q = (
            db.query(User)
            .filter(User.role == "estudiante", User.activo == True)
        )
        if not es_admin and psicologo_id:
            q = q.filter(User.psicologo_id == psicologo_id)
        estudiantes = q.all()
        total = len(estudiantes)
        distribucion = {
            "CRITICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0,
            "SIN_RIESGO": 0, "sin_evaluacion": 0,
        }
        alertas = []

        for est in estudiantes:
            ultima = _ultima_aplicacion_revisada(db, est.id)
            if not ultima or not ultima.riesgo_global:
                distribucion["sin_evaluacion"] += 1
                continue
            clave = ultima.riesgo_global.upper().replace("Í", "I")
            if clave in distribucion:
                distribucion[clave] += 1
            if clave in ("CRITICO", "ALTO") or ultima.crisis_activada:
                alertas.append({
                    "id": est.id,
                    "nombre": est.nombre,
                    "apellido": est.apellido,
                    "email": est.email,
                    "riesgo_global": ultima.riesgo_global,
                    "crisis_activada": bool(ultima.crisis_activada),
                    "fecha_evaluacion": ultima.completada_at.isoformat() if ultima.completada_at else None,
                    "aplicacion_id": ultima.id,
                })

        alertas.sort(key=lambda x: (
            0 if (x["riesgo_global"] or "").upper().startswith("C") else 1,
            -(datetime.fromisoformat(x["fecha_evaluacion"]).timestamp() if x["fecha_evaluacion"] else 0),
        ))

        aplicaciones_q = db.query(AplicacionCuestionario)
        if not es_admin and psicologo_id:
            aplicaciones_q = aplicaciones_q.filter(
                AplicacionCuestionario.psicologo_id == psicologo_id
            )

        return {
            "total_estudiantes": total,
            "distribucion_riesgo": distribucion,
            "estudiantes_en_alerta": alertas,
            "total_cuestionarios_asignados": aplicaciones_q.count(),
            "total_cuestionarios_completados": aplicaciones_q
                .filter(AplicacionCuestionario.completada_at.isnot(None)).count(),
        }

    @staticmethod
    def listar_estudiantes(db: Session, psicologo_id: str | None = None,
                           es_admin: bool = False) -> list:
        """Lista estudiantes. Los psicólogos solo ven los suyos; admin ve todos."""
        q = (
            db.query(User)
            .filter(User.role == "estudiante", User.activo == True)
            .order_by(User.created_at.desc())
        )
        if not es_admin and psicologo_id:
            q = q.filter(User.psicologo_id == psicologo_id)
        estudiantes = q.all()
        out = []
        for est in estudiantes:
            ultima = _ultima_aplicacion_revisada(db, est.id)
            total_apps = (
                db.query(AplicacionCuestionario)
                .filter(AplicacionCuestionario.estudiante_id == est.id)
                .count()
            )
            out.append({
                "id": est.id,
                "nombre": est.nombre,
                "apellido": est.apellido,
                "email": est.email,
                "total_cuestionarios": total_apps,
                "ultimo_riesgo": ultima.riesgo_global if ultima else None,
                "ultima_evaluacion": ultima.completada_at.isoformat() if ultima and ultima.completada_at else None,
                "crisis_activada": bool(ultima.crisis_activada) if ultima else False,
                "estado_caso": getattr(est, "estado_caso", None) or "activo",
                "psicologo_id": getattr(est, "psicologo_id", None),
                "grado": getattr(est, "grado", None),
            })
        return out

    @staticmethod
    def cambiar_estado_caso(db: Session, student_id: str, nuevo_estado: str) -> dict:
        if nuevo_estado not in ("activo", "seguimiento", "cerrado"):
            raise ValueError("Estado inválido. Usa: activo | seguimiento | cerrado")
        est = (
            db.query(User)
            .filter(User.id == student_id, User.role == "estudiante")
            .first()
        )
        if not est:
            raise ValueError("Estudiante no encontrado")
        est.estado_caso = nuevo_estado
        db.commit()
        db.refresh(est)
        return {"id": est.id, "estado_caso": est.estado_caso}

    @staticmethod
    def historial_estudiante(db: Session, student_id: str,
                             psicologo_id: str | None = None,
                             es_admin: bool = False) -> dict:
        estudiante = (
            db.query(User)
            .filter(User.id == student_id, User.role == "estudiante")
            .first()
        )
        if not estudiante:
            raise ValueError("Estudiante no encontrado")
        # Un psicólogo solo puede ver el historial de sus propios estudiantes.
        if not es_admin and psicologo_id and estudiante.psicologo_id != psicologo_id:
            raise ValueError("No tienes acceso al historial de este estudiante.")

        aplicaciones = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.estudiante_id == student_id)
            .order_by(desc(AplicacionCuestionario.asignada_at))
            .all()
        )

        return {
            "estudiante": {
                "id": estudiante.id,
                "nombre": estudiante.nombre,
                "apellido": estudiante.apellido,
                "email": estudiante.email,
                "grado": getattr(estudiante, "grado", None),
                "estado_caso": getattr(estudiante, "estado_caso", None) or "activo",
            },
            "aplicaciones": [
                {
                    "id": a.id,
                    "plantilla_id": a.plantilla_id,
                    "estado": a.estado,
                    "riesgo_global": a.riesgo_global,
                    "crisis_activada": bool(a.crisis_activada),
                    "asignada_at": a.asignada_at.isoformat() if a.asignada_at else None,
                    "completada_at": a.completada_at.isoformat() if a.completada_at else None,
                }
                for a in aplicaciones
            ],
        }

    # ── Últimas evaluaciones (bandeja de revisión) ──────────────────────────

    @staticmethod
    def evaluaciones_recientes(
        db: Session,
        psicologo_id: str | None = None,
        es_admin: bool = False,
        limite: int = 100,
        solo_sin_revisar: bool = False,
    ) -> dict:
        """
        Una fila por aplicación ya evaluada, de la más reciente a la más
        antigua. Es la bandeja de trabajo del psicólogo: qué salió del
        sistema, qué dijo el SVM, qué dijo BETO y qué falta revisar.

        No es un listado de alumnos (eso es `listar_estudiantes`): acá puede
        haber varias filas del mismo alumno, una por cuestionario rendido.
        """
        import json

        from app.models.bank import PlantillaCuestionario, ResultadoFeedback

        q = (
            db.query(AplicacionCuestionario)
            .filter(AplicacionCuestionario.resultado_json.isnot(None))
            .order_by(
                desc(AplicacionCuestionario.completada_at),
                desc(AplicacionCuestionario.id),
            )
        )
        if not es_admin and psicologo_id:
            q = q.filter(AplicacionCuestionario.psicologo_id == psicologo_id)
        if solo_sin_revisar:
            q = q.filter(AplicacionCuestionario.revisada_at.is_(None))

        aplicaciones = q.limit(max(1, min(limite, 500))).all()
        if not aplicaciones:
            return {"total": 0, "resumen": _resumen_vacio(), "evaluaciones": []}

        # Tres queries en bloque en lugar de N por fila.
        ids_alumnos = {a.estudiante_id for a in aplicaciones}
        alumnos = {
            u.id: u for u in db.query(User).filter(User.id.in_(ids_alumnos)).all()
        }
        ids_plantillas = {a.plantilla_id for a in aplicaciones}
        plantillas = {
            p.id: p
            for p in db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.id.in_(ids_plantillas))
            .all()
        }
        ids_apl = [a.id for a in aplicaciones]
        veredictos = {
            f.aplicacion_id: f
            for f in db.query(ResultadoFeedback)
            .filter(ResultadoFeedback.aplicacion_id.in_(ids_apl))
            .all()
        }

        filas = []
        for a in aplicaciones:
            try:
                resultado = json.loads(a.resultado_json)
            except (ValueError, TypeError):
                logger.warning("resultado_json ilegible en aplicación %s", a.id)
                resultado = {}

            alumno = alumnos.get(a.estudiante_id)
            plantilla = plantillas.get(a.plantilla_id)
            fb = veredictos.get(a.id)
            frases = resultado.get("frases") or []
            svm = resultado.get("svm_segunda_opinion")

            filas.append({
                "aplicacion_id": a.id,
                "estudiante_id": a.estudiante_id,
                # El código de acceso es el identificador del piloto; si no
                # hay, cae al nombre. Permite trabajar pseudonimizado.
                "codigo_alumno": getattr(alumno, "codigo_acceso", None) if alumno else None,
                "nombre": alumno.nombre if alumno else "(alumno borrado)",
                "apellido": alumno.apellido if alumno else "",
                "grado": getattr(alumno, "grado", None) if alumno else None,
                "plantilla": plantilla.nombre if plantilla else f"#{a.plantilla_id}",
                "estado": a.estado,
                "completada_at": a.completada_at.isoformat() if a.completada_at else None,
                "revisada_at": a.revisada_at.isoformat() if a.revisada_at else None,
                "riesgo_global": resultado.get("riesgo_global") or a.riesgo_global,
                "crisis_activada": bool(
                    resultado.get("crisis_activada", a.crisis_activada)
                ),
                "n_senales": resultado.get("n_senales"),
                "bloques": [
                    {
                        "codigo": b.get("codigo"),
                        "nombre": b.get("nombre"),
                        "puntaje": b.get("puntaje"),
                        "rango_max": b.get("rango_max"),
                        "severidad": b.get("severidad"),
                        "severidad_alerta": bool(b.get("severidad_alerta")),
                        "bandera_crisis": bool(b.get("bandera_crisis")),
                    }
                    for b in (resultado.get("bloques") or [])
                ],
                "n_frases": len(frases),
                "n_frases_crisis": sum(1 for f in frases if f.get("crisis")),
                "svm": (
                    {
                        "clase": svm.get("clase"),
                        "probabilidad": svm.get("probabilidad"),
                        "confianza": svm.get("confianza"),
                        "discrepancia_con_reglas": bool(
                            svm.get("discrepancia_con_reglas")
                        ),
                    }
                    if svm
                    else None
                ),
                "veredicto_psicologo": fb.veredicto if fb else None,
            })

        return {
            "total": len(filas),
            "resumen": _resumen_evaluaciones(filas),
            "evaluaciones": filas,
        }


def _resumen_vacio() -> dict:
    return {
        "por_riesgo": {
            "CRITICO": 0, "ALTO": 0, "MEDIO": 0, "BAJO": 0, "SIN_RIESGO": 0,
        },
        "con_crisis": 0,
        "sin_revisar": 0,
        "con_svm": 0,
        "svm_discrepante": 0,
        "con_frases": 0,
        "juzgadas": 0,
    }


def _resumen_evaluaciones(filas: list) -> dict:
    out = _resumen_vacio()
    for f in filas:
        clave = (f["riesgo_global"] or "").upper().replace("Í", "I")
        if clave in out["por_riesgo"]:
            out["por_riesgo"][clave] += 1
        if f["crisis_activada"]:
            out["con_crisis"] += 1
        if not f["revisada_at"]:
            out["sin_revisar"] += 1
        if f["svm"]:
            out["con_svm"] += 1
            if f["svm"]["discrepancia_con_reglas"]:
                out["svm_discrepante"] += 1
        if f["n_frases"]:
            out["con_frases"] += 1
        if f["veredicto_psicologo"]:
            out["juzgadas"] += 1
    return out
