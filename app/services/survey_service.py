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
            utilidad=_validar(data["utilidad"]),
            confianza=_validar(data["confianza"]),
            recomendaria=_validar(data["recomendaria"]),
            nivel_animo_post=int(data["nivel_animo_post"]) if data.get("nivel_animo_post") is not None else None,
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
            func.avg(SatisfactionSurvey.utilidad),
            func.avg(SatisfactionSurvey.confianza),
            func.avg(SatisfactionSurvey.recomendaria),
        ).first()
        ultimos = (db.query(SatisfactionSurvey)
                     .filter(SatisfactionSurvey.comentario.isnot(None))
                     .order_by(desc(SatisfactionSurvey.timestamp))
                     .limit(5).all())
        return {
            "total": total,
            "promedios": {
                "facilidad_uso": round(promedios[0] or 0, 2),
                "utilidad": round(promedios[1] or 0, 2),
                "confianza": round(promedios[2] or 0, 2),
                "recomendaria": round(promedios[3] or 0, 2),
            },
            "ultimos_comentarios": [
                {"comentario": s.comentario, "timestamp": s.timestamp.isoformat()}
                for s in ultimos
            ],
        }
