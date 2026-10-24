"""
Equipo psicopedagógico: varias psicólogas que comparten la cartera de una
titular (`User.equipo_titular_id`).

Cada alumno sigue teniendo una sola psicóloga responsable (`psicologo_id`).
El equipo solo amplía quién puede VER y trabajar sobre esos alumnos: la
titular y todas las que apuntan a ella ven los mismos alumnos, resultados y
alertas. Las notas clínicas siguen siendo privadas de cada psicóloga.

El vínculo lo fija solo el admin (no hay endpoint para que una psicóloga se
una sola a un equipo), así que nadie puede ampliar su propio acceso.
"""
from sqlalchemy.orm import Session

from app.models.user import User


def ids_equipo(db: Session, psicologo_id: str | None) -> list[str]:
    """IDs de las psicólogas cuyo trabajo comparte esta: ella misma, la
    titular de su equipo y las demás integrantes. Sin equipo, solo ella."""
    if not psicologo_id:
        return []
    yo = db.query(User).filter(User.id == psicologo_id).first()
    if not yo:
        return [psicologo_id]
    titular = getattr(yo, "equipo_titular_id", None) or yo.id
    miembros = [
        r[0]
        for r in db.query(User.id)
        .filter(User.equipo_titular_id == titular, User.role == "psicologo")
        .all()
    ]
    return list({psicologo_id, titular, *miembros})
