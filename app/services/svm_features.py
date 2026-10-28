"""Construcción de features del SVM clínico (PHQ-A + GAD-7 → riesgo MEDIO+).

Vive en `app/services/` y no en `scripts/` a propósito: el pipeline guardado en
`models/svm_clinico.joblib` contiene un `FunctionTransformer` que referencia a
`construir_features` por ruta de módulo. Si la función se mueve, el joblib no
se puede cargar. Cualquier cambio acá invalida el modelo entrenado.

Las 13 derivadas no son automáticas: cada una traduce una regla publicada
(suma total de cada instrumento, recuento de síntomas del DSM-5, subescalas
somática y cognitivo-afectiva del PHQ-9, bandera de ideación del ítem 9).
Con n=102 el modelo no puede redescubrir esas reglas solo, así que se le dan
calculadas. Todas se obtienen **únicamente** de las respuestas del estudiante:
ninguna usa la etiqueta de la psicóloga.
"""
from __future__ import annotations

import numpy as np

# Orden canónico de la entrada. El modelo espera exactamente estas 16 columnas,
# en este orden. Coinciden con el campo `origen` de `respuesta_aplicacion`.
ITEMS_PHQ: list[str] = [f"INSTR:PHQ-A:{i}" for i in range(1, 10)]
ITEMS_GAD: list[str] = [f"INSTR:GAD-7:{i}" for i in range(1, 8)]
ITEMS: list[str] = ITEMS_PHQ + ITEMS_GAD

# Subescalas del PHQ-9 (índices 0-based sobre los 9 ítems del PHQ-A).
# Somática: sueño, fatiga, apetito, psicomotor (ítems 3, 4, 5, 8).
# Cognitivo-afectiva: anhedonia, ánimo, autoimagen, concentración, ideación
# (ítems 1, 2, 6, 7, 9).
IDX_SOMATICA: list[int] = [2, 3, 4, 7]
IDX_COGNITIVA: list[int] = [0, 1, 5, 6, 8]
IDX_IDEACION: int = 8  # PHQ-A #9

NOMBRES_DERIVADAS: list[str] = [
    "phq_total",      # suma PHQ-A (0-27), procedimiento publicado
    "gad_total",      # suma GAD-7 (0-21), procedimiento publicado
    "total",          # carga sintomática global
    "phq_n_ge2",      # ítems PHQ-A >= 2: recuento tipo DSM-5 (>= mitad de días)
    "gad_n_ge2",      # ítems GAD-7 >= 2
    "phq_n_ge1",      # amplitud: cuántos dominios toca, sin importar intensidad
    "gad_n_ge1",
    "phq_max",        # intensidad del síntoma peor
    "gad_max",
    "item9",          # ideación, valor crudo 0-3
    "crisis",         # bandera: PHQ-A #9 >= 1 (misma regla del EvaluatorService)
    "phq_somatica",   # subescala somática
    "phq_cognitiva",  # subescala cognitivo-afectiva
]

NOMBRES_FEATURES: list[str] = ITEMS + NOMBRES_DERIVADAS


def derivar(X: np.ndarray) -> np.ndarray:
    """Las 13 derivadas. Fila por fila: ningún estadístico de la muestra.

    Esto importa para la validación — una feature que use medias o
    desviaciones del conjunto filtraría información entre folds.
    """
    X = np.asarray(X, dtype=float)
    phq, gad = X[:, :9], X[:, 9:16]
    return np.column_stack([
        phq.sum(1),
        gad.sum(1),
        phq.sum(1) + gad.sum(1),
        (phq >= 2).sum(1),
        (gad >= 2).sum(1),
        (phq >= 1).sum(1),
        (gad >= 1).sum(1),
        phq.max(1),
        gad.max(1),
        phq[:, IDX_IDEACION],
        (phq[:, IDX_IDEACION] >= 1).astype(float),
        phq[:, IDX_SOMATICA].sum(1),
        phq[:, IDX_COGNITIVA].sum(1),
    ])


def construir_features(X: np.ndarray) -> np.ndarray:
    """29 columnas: los 16 ítems crudos + las 13 derivadas.

    Es la entrada del pipeline guardado. `SelectKBest` decide adentro cuáles
    de las 29 sobreviven, así que acá no se poda nada.
    """
    X = np.asarray(X, dtype=float)
    return np.hstack([X, derivar(X)])
