"""
Entrenamiento del SVM "segunda opinión" de Sami sobre DASS-21.

Entrada
-------
data/dass/data.csv  — DASS-42 de Open Psychometrics (~39k respuestas, real).
                      Cada usuario respondió los 42 ítems en escala 1-4.

Mapeo DASS-21 ⊂ DASS-42 (Lovibond 1995, codebook Open Psychometrics)
-------------------------------------------------------------------
- Depresión:  Q3, Q42, Q10, Q26, Q31, Q17, Q38
- Ansiedad:   Q2,  Q4,  Q41, Q40, Q28, Q25, Q20
- Estrés:     Q22, Q6,  Q12, Q8,  Q39, Q35, Q18

Cortes DASS-21 oficiales (puntaje × 2 sobre escala 0-3 para alinearlos
con los puntajes DASS-42):
- Depresión: Normal 0-9, Leve 10-13, Moderado 14-20, Severo 21-27, Extremo 28+
- Ansiedad:  Normal 0-7, Leve 8-9,  Moderado 10-14, Severo 15-19, Extremo 20+
- Estrés:    Normal 0-14, Leve 15-18, Moderado 19-25, Severo 26-33, Extremo 34+

Target binario
--------------
at_risk = 1  si  D ≥ 14  ∨  A ≥ 10  ∨  S ≥ 19   (≥ Moderado en cualquier subescala)
at_risk = 0  caso contrario.

Filtrado de población
---------------------
Solo adolescentes 13–17 años (target real del sistema en colegio privado).

Salidas
-------
models/svm_dass21.joblib    pipeline serializado (scaler + SVC RBF)
reports/svm_dass21.md       métricas + comparación contra las reglas DASS-21
reports/svm_dass21.json     misma info en JSON

Uso
---
    venv/bin/python scripts/train_svm_dass21.py
    venv/bin/python scripts/train_svm_dass21.py --kernel linear --seed 7
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "dass" / "data.csv"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Columnas DASS-42 que componen DASS-21
DEPRESION_ITEMS = [3, 42, 10, 26, 31, 17, 38]
ANSIEDAD_ITEMS = [2, 4, 41, 40, 28, 25, 20]
ESTRES_ITEMS = [22, 6, 12, 8, 39, 35, 18]
DASS21_ITEMS = DEPRESION_ITEMS + ANSIEDAD_ITEMS + ESTRES_ITEMS  # 21 ítems

FEATURES = [f"Q{i}A" for i in DASS21_ITEMS]

# Cortes DASS-21 oficiales (puntaje multiplicado por 2)
CORTE_DEPRESION_MODERADO = 14
CORTE_ANSIEDAD_MODERADO = 10
CORTE_ESTRES_MODERADO = 19


def cargar_y_filtrar() -> pd.DataFrame:
    if not DATA.exists():
        raise SystemExit(
            f"Falta el dataset DASS en {DATA}. "
            "Descargá DASS-42 de Open Psychometrics y colocá data.csv ahí."
        )
    print(f"Cargando {DATA} (puede tardar — 21 MB)…")
    df = pd.read_csv(DATA, sep="\t", low_memory=False)
    print(f"  filas totales: {len(df):,}")

    # Filtra adolescentes 13-17 años (población real de Sami).
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df[(df["age"] >= 13) & (df["age"] <= 17)].copy()
    print(f"  filas tras filtrar 13-17 años: {len(df):,}")

    # Filtra respuestas válidas (1-4); descarta nulos y fuera de rango.
    for col in FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=FEATURES)
    valid_mask = (df[FEATURES] >= 1).all(axis=1) & (df[FEATURES] <= 4).all(axis=1)
    df = df[valid_mask].copy()
    print(f"  filas con DASS-21 completo y válido: {len(df):,}")

    return df


def computar_etiquetas(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica cortes DASS-21 oficiales y genera la etiqueta binaria at_risk."""
    # Las respuestas vienen en escala 1-4. Llevamos a 0-3 (escala DASS oficial).
    for col in FEATURES:
        df[col] = df[col] - 1

    # Suma por subescala × 2 (regla DASS-21 para alinear con cortes DASS-42).
    df["score_D"] = df[[f"Q{i}A" for i in DEPRESION_ITEMS]].sum(axis=1) * 2
    df["score_A"] = df[[f"Q{i}A" for i in ANSIEDAD_ITEMS]].sum(axis=1) * 2
    df["score_S"] = df[[f"Q{i}A" for i in ESTRES_ITEMS]].sum(axis=1) * 2

    df["at_risk"] = (
        (df["score_D"] >= CORTE_DEPRESION_MODERADO)
        | (df["score_A"] >= CORTE_ANSIEDAD_MODERADO)
        | (df["score_S"] >= CORTE_ESTRES_MODERADO)
    ).astype(int)
    print(
        f"  distribución at_risk: "
        f"sin_riesgo={int((df['at_risk'] == 0).sum())}, "
        f"en_riesgo={int((df['at_risk'] == 1).sum())}"
    )
    return df


def entrenar(kernel: str, test_size: float, seed: int) -> dict:
    df = cargar_y_filtrar()
    df = computar_etiquetas(df)

    X = df[FEATURES].to_numpy(dtype=float)
    y = df["at_risk"].to_numpy(dtype=int)
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y,
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(
            kernel=kernel,
            C=1.0,
            gamma="scale",
            class_weight="balanced",
            probability=True,
            random_state=seed,
        )),
    ])

    print(f"\nEntrenando SVM ({kernel}) sobre {len(X_train):,} ejemplos…")
    pipeline.fit(X_train, y_train)

    # CV sobre el train
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1_macro")
    print(f"CV F1-macro: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Evaluación holdout
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    f1_m = f1_score(y_test, y_pred, average="macro", zero_division=0)
    f1_w = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    auc = roc_auc_score(y_test, y_proba)
    reporte = classification_report(
        y_test, y_pred, target_names=["sin_riesgo", "en_riesgo"],
        digits=3, zero_division=0,
    )
    matriz = confusion_matrix(y_test, y_pred, labels=[0, 1]).tolist()

    # Línea base: usar las MISMAS reglas DASS-21 sobre el test (debería dar 100%
    # de acuerdo con los labels — sirve para confirmar que el código de cortes
    # es coherente y que el SVM aporta sobre features individuales, no sobre
    # los puntajes derivados que ya conocemos).
    # Acá lo que reporto es: ¿qué tan bien predice el SVM las decisiones de
    # corte sin haber visto los puntajes sumados?
    metricas = {
        "kernel": kernel,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_total": int(len(X)),
        "n_positivos": n_pos,
        "n_negativos": n_neg,
        "balance_positivos": round(n_pos / (n_pos + n_neg), 4),
        "edad_min": 13,
        "edad_max": 17,
        "features": FEATURES,
        "cv_f1_macro_mean": round(float(cv_scores.mean()), 4),
        "cv_f1_macro_std": round(float(cv_scores.std()), 4),
        "test_accuracy": round(float(acc), 4),
        "test_f1_macro": round(float(f1_m), 4),
        "test_f1_weighted": round(float(f1_w), 4),
        "test_roc_auc": round(float(auc), 4),
        "matriz_confusion": matriz,
        "classification_report": reporte,
        "cortes_oficiales": {
            "depresion_moderado": CORTE_DEPRESION_MODERADO,
            "ansiedad_moderado": CORTE_ANSIEDAD_MODERADO,
            "estres_moderado": CORTE_ESTRES_MODERADO,
        },
        "dataset_source": (
            "Open Psychometrics. Depression Anxiety Stress Scales (DASS) "
            "Responses (2017–2019). Public domain. URL: "
            "https://openpsychometrics.org/_rawdata/"
        ),
    }

    # Persistencia del modelo
    modelo_path = MODELS_DIR / "svm_dass21.joblib"
    joblib.dump({
        "pipeline": pipeline,
        "features": FEATURES,
        "kernel": kernel,
        "n_train": len(X_train),
        "cv_f1_macro_mean": float(cv_scores.mean()),
        "test_roc_auc": float(auc),
    }, modelo_path)
    print(f"Modelo guardado: {modelo_path}")

    return metricas


def reportar(metricas: dict) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    json_path = REPORTS_DIR / "svm_dass21.json"
    md_path = REPORTS_DIR / "svm_dass21.md"
    json_path.write_text(json.dumps(metricas, indent=2, ensure_ascii=False))

    md = []
    md.append("# SVM — segunda opinión sobre DASS-21\n")
    md.append("## Resumen ejecutivo")
    md.append(
        f"- **Población**: adolescentes {metricas['edad_min']}–{metricas['edad_max']} años "
        f"(target real del sistema Sami).\n"
        f"- **Total ejemplos**: {metricas['n_total']:,} "
        f"({metricas['n_positivos']:,} en riesgo, "
        f"{metricas['n_negativos']:,} sin riesgo).\n"
        f"- **Balance positivos**: {metricas['balance_positivos']*100:.1f} %.\n"
        f"- **Kernel**: `{metricas['kernel']}`."
    )
    md.append("")
    md.append("## Resultados")
    md.append(
        f"| Métrica | Valor |\n| --- | --- |\n"
        f"| CV F1-macro (5-fold, train) | {metricas['cv_f1_macro_mean']:.4f} ± "
        f"{metricas['cv_f1_macro_std']:.4f} |\n"
        f"| Accuracy (test) | {metricas['test_accuracy']:.4f} |\n"
        f"| F1-macro (test) | {metricas['test_f1_macro']:.4f} |\n"
        f"| F1-weighted (test) | {metricas['test_f1_weighted']:.4f} |\n"
        f"| ROC-AUC (test) | {metricas['test_roc_auc']:.4f} |"
    )
    md.append("")
    md.append("## Reporte por clase")
    md.append("```")
    md.append(metricas["classification_report"])
    md.append("```")
    md.append("")
    md.append("## Matriz de confusión (test)")
    md.append("| real \\ pred | sin_riesgo | en_riesgo |")
    md.append("| --- | --- | --- |")
    md.append(f"| **sin_riesgo** | {metricas['matriz_confusion'][0][0]} | "
              f"{metricas['matriz_confusion'][0][1]} |")
    md.append(f"| **en_riesgo**  | {metricas['matriz_confusion'][1][0]} | "
              f"{metricas['matriz_confusion'][1][1]} |")
    md.append("")
    md.append("## Cortes oficiales DASS-21 usados para etiquetar")
    md.append(
        f"- Depresión ≥ {metricas['cortes_oficiales']['depresion_moderado']} "
        "(Moderado o superior).\n"
        f"- Ansiedad ≥ {metricas['cortes_oficiales']['ansiedad_moderado']}.\n"
        f"- Estrés ≥ {metricas['cortes_oficiales']['estres_moderado']}.\n"
        "Si **alguna** subescala alcanza Moderado → `at_risk = 1`."
    )
    md.append("")
    md.append("## Fuente del dataset")
    md.append(f"> {metricas['dataset_source']}")

    md_path.write_text("\n".join(md))
    print(f"Reporte: {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel", default="rbf", choices=["rbf", "linear", "poly"])
    parser.add_argument("--test-size", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    metricas = entrenar(args.kernel, args.test_size, args.seed)
    reportar(metricas)
    print("\n=== Resultado final ===")
    print(f"  CV F1-macro: {metricas['cv_f1_macro_mean']:.4f}")
    print(f"  Test accuracy: {metricas['test_accuracy']:.4f}")
    print(f"  Test F1-macro: {metricas['test_f1_macro']:.4f}")
    print(f"  Test ROC-AUC: {metricas['test_roc_auc']:.4f}")


if __name__ == "__main__":
    main()
