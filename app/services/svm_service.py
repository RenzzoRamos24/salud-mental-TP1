"""
SVMService — segunda opinión sobre DASS-21.

Carga `models/svm_dass21.joblib` una sola vez (singleton) y expone
`predecir(respuestas_dass21)` → dict con clase + probabilidad.

El modelo fue entrenado con datos reales de Open Psychometrics, filtrado a
adolescentes 13–17 años (n = 7,269). Features = 21 respuestas DASS-21
(escala 0–3). Target = at_risk binario según cortes oficiales DASS-21.

Métricas (test held-out 20 %):
    - Accuracy:   0.9711
    - F1-macro:   0.9215
    - ROC-AUC:    0.9977
    - CV F1-mac:  0.9287 ± 0.0066

Ver `reports/svm_dass21.md` para detalle.
"""
from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)

# Orden de los ítems DASS-21 esperado por el modelo. DEBE coincidir con
# scripts/train_svm_dass21.py — primero Depresión, luego Ansiedad, luego Estrés.
ITEMS_ORDEN = [
    # Depresión (7)
    3, 5, 10, 13, 16, 17, 21,
    # Ansiedad (7)
    2, 4, 7, 9, 15, 19, 20,
    # Estrés (7)
    1, 6, 8, 11, 12, 14, 18,
]


class SVMService:
    """Singleton perezoso. El modelo se carga en el primer uso."""

    _modelo = None
    _lock = Lock()
    _ruta: Optional[Path] = None

    @classmethod
    def _cargar(cls) -> Optional[dict]:
        if cls._modelo is not None:
            return cls._modelo
        with cls._lock:
            if cls._modelo is not None:
                return cls._modelo
            cls._ruta = (
                Path(__file__).resolve().parent.parent.parent
                / "models" / "svm_dass21.joblib"
            )
            if not cls._ruta.exists():
                logger.warning(
                    "SVM no disponible: falta %s. El sistema sigue funcionando "
                    "con reglas + BETO.",
                    cls._ruta,
                )
                return None
            try:
                import joblib  # import perezoso para no obligar a sklearn en cold start.
                cls._modelo = joblib.load(cls._ruta)
                logger.info(
                    "SVM DASS-21 cargado (CV F1=%.3f, AUC=%.3f).",
                    cls._modelo.get("cv_f1_macro_mean", 0.0),
                    cls._modelo.get("test_roc_auc", 0.0),
                )
            except Exception as e:
                logger.exception("Falló la carga del SVM: %s", e)
                cls._modelo = None
        return cls._modelo

    @classmethod
    def disponible(cls) -> bool:
        return cls._cargar() is not None

    @classmethod
    def info(cls) -> dict:
        m = cls._cargar()
        if not m:
            return {"cargado": False}
        return {
            "cargado": True,
            "kernel": m.get("kernel"),
            "n_train": m.get("n_train"),
            "cv_f1_macro_mean": m.get("cv_f1_macro_mean"),
            "test_roc_auc": m.get("test_roc_auc"),
            "ruta": str(cls._ruta) if cls._ruta else None,
        }

    @classmethod
    def predecir(cls, respuestas_dass21: dict[int, int]) -> Optional[dict]:
        """
        respuestas_dass21: { numero_dass21 (1..21): valor (0..3) }
                            — vienen del cuestionario que el alumno respondió.

        Devuelve None si el modelo no está cargado o faltan respuestas.
        Caso normal: { 'clase': 'en_riesgo'|'sin_riesgo',
                       'probabilidad': float (0..1),
                       'confianza': 'alta'|'media'|'baja' }
        """
        m = cls._cargar()
        if not m:
            return None

        # Construye el vector en el ORDEN exacto que vio el entrenamiento.
        try:
            x = [int(respuestas_dass21[i]) for i in ITEMS_ORDEN]
        except (KeyError, TypeError, ValueError):
            logger.warning(
                "SVM DASS-21: faltan respuestas o tipos inválidos; "
                "respuestas recibidas=%s", respuestas_dass21,
            )
            return None

        # Saneamiento: valores fuera de 0..3 se recortan.
        x = [max(0, min(3, v)) for v in x]
        proba = float(m["pipeline"].predict_proba([x])[0][1])  # prob de en_riesgo
        clase = "en_riesgo" if proba >= 0.5 else "sin_riesgo"

        # Confianza relativa al umbral 0.5.
        margen = abs(proba - 0.5)
        if margen >= 0.35:
            confianza = "alta"
        elif margen >= 0.15:
            confianza = "media"
        else:
            confianza = "baja"

        return {
            "clase": clase,
            "probabilidad": round(proba, 4),
            "confianza": confianza,
        }
