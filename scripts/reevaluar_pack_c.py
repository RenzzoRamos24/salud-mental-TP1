"""
Re-evalúa las aplicaciones del Pack C con el modelo BETO actualizado
(2 categorías: depresión + ansiedad). Reescribe el `resultado_json` de
cada AplicacionCuestionario.

Uso local (SQLite):
    venv/bin/python -m scripts.reevaluar_pack_c

Uso contra Azure Postgres:
    DATABASE_URL='postgresql+psycopg2://user:pass@host:5432/db?sslmode=require' \\
      venv/bin/python -m scripts.reevaluar_pack_c
"""
from __future__ import annotations
import json
from app.database import SessionLocal
from app.models.bank import AplicacionCuestionario, PlantillaCuestionario
from app.services.evaluator_service import EvaluatorService


def main():
    db = SessionLocal()
    try:
        apps = (
            db.query(AplicacionCuestionario)
            .join(PlantillaCuestionario)
            .filter(PlantillaCuestionario.nombre.like("%Pack C%"))
            .all()
        )
        print(f"Re-evaluando {len(apps)} aplicaciones del Pack C...")
        for i, a in enumerate(apps, 1):
            try:
                res = EvaluatorService.evaluar(db, a)
                a.resultado_json = json.dumps(res, ensure_ascii=False)
                a.riesgo_global = res.get("riesgo_global")
                a.crisis_activada = bool(res.get("crisis_activada"))
                db.commit()
                n_frases = len(res.get("frases", []))
                print(f"  [{i:>3}/{len(apps)}] app_id={a.id}  "
                      f"riesgo={a.riesgo_global}  crisis={a.crisis_activada}  "
                      f"n_frases={n_frases}")
            except Exception as e:
                db.rollback()
                print(f"  ⚠ app_id={a.id}: {e}")
        print("OK.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
