"""HU-25: encuesta de satisfacción del estudiante."""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.models.satisfaction_survey import SatisfactionSurvey


class SurveyService:

    @staticmethod
    def crear(db: Session, user_id: str, data: dict) -> SatisfactionSurvey:
        def _validar(v):
            v = int(v)
            if not (1 <= v <= 5):
                raise ValueError("Las puntuaciones deben estar entre 1 y 5.")
            return v
        s = SatisfactionSurvey(
            user_id=user_id,
            facilidad_uso=_validar(data["facilidad_uso"]),
            claridad=_validar(data["claridad"]),
            utilidad=_validar(data["utilidad"]),
            fluidez=_validar(data["fluidez"]),
            satisfaccion_general=_validar(data["satisfaccion_general"]),
            comentario=(data.get("comentario") or "").strip() or None,
        )
        db.add(s)
        db.commit()
        db.refresh(s)
        return s

    @staticmethod
    def existe_para_usuario(db: Session, user_id: str) -> bool:
        return db.query(SatisfactionSurvey.id).filter(SatisfactionSurvey.user_id == user_id).first() is not None

    @staticmethod
    def resumen_admin(db: Session) -> dict:
        """Para HU-18 / panel admin: agregados de la encuesta."""
        total = db.query(func.count(SatisfactionSurvey.id)).scalar() or 0
        if not total:
            return {"total": 0}
        promedios = db.query(
            func.avg(SatisfactionSurvey.facilidad_uso),
            func.avg(SatisfactionSurvey.claridad),
            func.avg(SatisfactionSurvey.utilidad),
            func.avg(SatisfactionSurvey.fluidez),
            func.avg(SatisfactionSurvey.satisfaccion_general),
        ).first()
        ultimos = (db.query(SatisfactionSurvey)
                     .filter(SatisfactionSurvey.comentario.isnot(None))
                     .order_by(desc(SatisfactionSurvey.timestamp))
                     .limit(5).all())
        return {
            "total": total,
            "promedios": {
                "facilidad_uso": round(promedios[0] or 0, 2),
                "claridad": round(promedios[1] or 0, 2),
                "utilidad": round(promedios[2] or 0, 2),
                "fluidez": round(promedios[3] or 0, 2),
                "satisfaccion_general": round(promedios[4] or 0, 2),
            },
            "ultimos_comentarios": [
                {"comentario": s.comentario, "timestamp": s.timestamp.isoformat()}
                for s in ultimos
            ],
        }

    # ── Vista para la psicóloga ────────────────────────────────────────────

    @staticmethod
    def resumen_para_psicologo(
        db: Session, psicologo_id: str | None = None, es_admin: bool = False
    ) -> dict:
        """
        Cómo vivieron los alumnos la aplicación del cuestionario.

        El resumen del admin da promedios y cinco comentarios. Acá hace falta
        algo distinto: la psicóloga necesita ver la **distribución** —un 3.8
        de promedio puede ser todos en 4, o la mitad en 5 y la mitad en 2, y
        eso cambia qué hacer— y **todos** los comentarios, que es donde los
        chicos dicen lo que ninguna escala captura.

        Se incluye la tasa de respuesta: si contestó la encuesta un tercio,
        los promedios describen a ese tercio y no a la clase.
        """
        from app.models.user import User
        from app.models.bank import AplicacionCuestionario

        DIMENSIONES = [
            ("facilidad_uso", "¿Fue fácil de usar y entender?"),
            ("claridad", "¿Las preguntas eran claras?"),
            ("utilidad", "¿Te parecieron pertinentes?"),
            ("fluidez", "¿Pudiste responder sin dificultades?"),
            ("satisfaccion_general", "¿Quedaste conforme con la experiencia?"),
        ]

        # Alumnos en vista: los del psicólogo, o todos si es admin.
        q_al = db.query(User.id).filter(User.role == "estudiante", User.activo == True)
        if not es_admin and psicologo_id:
            q_al = q_al.filter(User.psicologo_id == psicologo_id)
        ids_alumnos = {r[0] for r in q_al.all()}

        # Cuántos de ellos llegaron a cerrar un cuestionario: es contra ese
        # número que la tasa de respuesta significa algo. A quien no lo rindió
        # nunca se le ofreció la encuesta.
        con_cuestionario = {
            r[0] for r in db.query(AplicacionCuestionario.estudiante_id)
            .filter(
                AplicacionCuestionario.estudiante_id.in_(ids_alumnos or {""}),
                AplicacionCuestionario.completada_at.isnot(None),
            ).distinct().all()
        } if ids_alumnos else set()

        filas = (
            db.query(SatisfactionSurvey)
            .filter(SatisfactionSurvey.user_id.in_(ids_alumnos or {""}))
            .order_by(desc(SatisfactionSurvey.timestamp))
            .all()
        ) if ids_alumnos else []

        if not filas:
            return {
                "total": 0,
                "alumnos_con_cuestionario": len(con_cuestionario),
                "tasa_respuesta": None,
                "dimensiones": [
                    {"clave": k, "pregunta": t, "promedio": None,
                     "distribucion": {str(i): 0 for i in range(1, 6)}}
                    for k, t in DIMENSIONES
                ],
                "comentarios": [],
            }

        dimensiones = []
        for clave, pregunta in DIMENSIONES:
            valores = [getattr(f, clave) for f in filas if getattr(f, clave)]
            dist = {str(i): 0 for i in range(1, 6)}
            for v in valores:
                dist[str(int(v))] = dist.get(str(int(v)), 0) + 1
            dimensiones.append({
                "clave": clave,
                "pregunta": pregunta,
                "promedio": round(sum(valores) / len(valores), 2) if valores else None,
                "distribucion": dist,
                # Cuántos respondieron 1 o 2: son los que la pasaron mal y los
                # que hay que mirar, no el promedio.
                "n_bajos": dist["1"] + dist["2"],
            })

        comentarios = [
            {
                "comentario": f.comentario.strip(),
                "timestamp": f.timestamp.isoformat() if f.timestamp else None,
                "satisfaccion_general": f.satisfaccion_general,
            }
            for f in filas
            if (f.comentario or "").strip()
        ]

        return {
            "total": len(filas),
            "alumnos_con_cuestionario": len(con_cuestionario),
            "tasa_respuesta": (
                round(len(filas) / len(con_cuestionario), 4)
                if con_cuestionario else None
            ),
            "dimensiones": dimensiones,
            "promedio_global": round(
                sum(d["promedio"] or 0 for d in dimensiones) / len(dimensiones), 2
            ),
            "comentarios": comentarios,
        }
