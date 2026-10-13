"""
SVMService — segunda opinión sobre PHQ-A (9 ítems).

Carga `models/svm_phq9.joblib` una sola vez (singleton) y expone
`predecir(respuestas_phq)` → dict con clase + probabilidad.

Por qué cambió respecto al SVM de DASS-21
-----------------------------------------
El modelo anterior esperaba los 21 ítems del DASS-21. Sami aplica PHQ-A (9)
+ GAD-7 (7), así que esas features no existían en los datos reales y el SVM
nunca emitió una predicción: `etiqueta_caso.modelo_svm_clase` está NULL en
los 102 casos que la psicóloga etiquetó. Este modelo consume los 9 ítems del
PHQ-A, que sí se recolectan siempre.

Qué mide y qué NO mide
----------------------
Se entrenó sobre ENDES 2025 (INEI), 1,370 adolescentes de 15-17 años, con
etiqueta `phq9_total >= 10`. Esa etiqueta es la suma de las propias features,
así que el modelo aprendió a reproducir el corte publicado — y lo hace de
forma exacta: en la validación externa contra el juicio de la psicóloga da
métricas **idénticas** a aplicar `PHQ-A total >= 10` directamente, y permutar
el orden de los 9 ítems no cambia el resultado (sd = 0.0000 sobre 200
permutaciones).

O sea: hoy este artefacto es, matemáticamente, la regla de corte. No agrega
información sobre las reglas del `EvaluatorService`, que en los mismos 102
casos dan F1-macro 0.853 / κ 0.708 contra 0.784 / 0.571 de este modelo.

Se mantiene en el pipeline porque el slot de "segunda opinión" se va a
reentrenar con las etiquetas clínicas de la psicóloga, que sí son un objetivo
independiente. Ver `reports/svm_phq9_endes.md`.

Métricas (validación externa, n=102, etiqueta clínica humana):
    - F1-macro:  0.7843
    - Kappa:     0.5713
    - ROC-AUC:   0.8634
    - Sens/Esp:  0.727 / 0.851
"""
from __future__ import annotations

import logging
from pathlib import Path
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)

# Orden de los ítems PHQ-A esperado por el modelo: 1..9, el orden estándar
# del PHQ-9. DEBE coincidir con scripts/train_svm_phq9_endes.py.
#
# El orden es irrelevante en la práctica —el modelo se apoya en la suma, y
# permutar las features no mueve ninguna métrica— pero se mantiene explícito
# para que el contrato no dependa de esa coincidencia.
ITEMS_ORDEN = list(range(1, 10))

RUTA_MODELO = "svm_phq9.joblib"


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
                / "models" / RUTA_MODELO
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
                    "SVM PHQ-9 cargado (n_train=%s, CV F1=%.3f).",
                    cls._modelo.get("n_train"),
                    cls._modelo.get("cv_f1_macro_mean", 0.0),
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
        externo = m.get("validacion_externa_piloto") or {}
        return {
            "cargado": True,
            "instrumento": m.get("instrumento"),
            "dataset": m.get("dataset"),
            "kernel": m.get("kernel"),
            "n_train": m.get("n_train"),
            "cv_f1_macro_mean": m.get("cv_f1_macro_mean"),
            # La métrica que vale: contra criterio clínico, no contra la
            # fórmula con la que se entrenó.
            "externo_f1_macro": externo.get("f1_macro"),
            "externo_kappa": externo.get("kappa"),
            "externo_roc_auc": externo.get("roc_auc"),
            "ruta": str(cls._ruta) if cls._ruta else None,
        }

    @classmethod
    def predecir(cls, respuestas_phq: dict[int, int]) -> Optional[dict]:
        """
        respuestas_phq: { numero_phq (1..9): valor (0..3) }
                        — vienen del PHQ-A que el alumno respondió.

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
            x = [int(respuestas_phq[i]) for i in ITEMS_ORDEN]
        except (KeyError, TypeError, ValueError):
            logger.warning(
                "SVM PHQ-9: faltan respuestas o tipos inválidos; "
                "respuestas recibidas=%s", respuestas_phq,
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
