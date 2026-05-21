"""
Backfill de score_riesgo / nivel_riesgo / condicion_dominante para
UserResponse existentes (sesiones completadas previas a HU-20 chart).

Uso:
    python -m scripts.backfill_response_scores
    python -m scripts.backfill_response_scores --force   # recalcula incluso si ya tiene score
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.response import UserResponse
from app.models.session import UserSession
from app.services.nlp_service import NLPService


def main():
    force = "--force" in sys.argv
    db = SessionLocal()
    try:
        sesiones_completadas = (
            db.query(UserSession)
            .filter(UserSession.estado == "completada")
            .all()
        )
        print(f"📦 Sesiones completadas a procesar: {len(sesiones_completadas)}")

        total_resp = 0
        total_actualizadas = 0
        for s in sesiones_completadas:
            respuestas = (
                db.query(UserResponse)
                .filter(UserResponse.session_id == s.id)
                .order_by(UserResponse.numero_pregunta)
                .all()
            )
            for r in respuestas:
                total_resp += 1
                if not force and r.score_riesgo is not None:
                    continue
                analisis = NLPService.analizar_respuesta_individual(r.respuesta or "")
                r.score_riesgo = analisis["score"]
                r.nivel_riesgo = analisis["nivel"]
                r.condicion_dominante = analisis["condicion"]
                total_actualizadas += 1
                print(
                    f"  · sesión {s.id[:8]}… P{r.numero_pregunta+1}: "
                    f"score={analisis['score']:.2f} nivel={analisis['nivel']} "
                    f"cond={analisis['condicion']}"
                )
            db.commit()

        print(f"✅ Backfill completado: {total_actualizadas}/{total_resp} respuestas actualizadas")
    finally:
        db.close()


if __name__ == "__main__":
    main()
