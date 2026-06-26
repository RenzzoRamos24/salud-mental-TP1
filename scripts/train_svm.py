"""
Entrenamiento del SVM clasificador de riesgo de Sami.

Entrada: `data/phq9_prepared.csv` (lo genera `prepare_phq9_dataset.py`).
Modelo:  SVC con kernel RBF + StandardScaler. Pipeline serializado.
Salida:
    models/svm_riesgo.joblib   modelo + scaler + label encoder
    reports/svm_training.md    métricas para pegar en la tesis

Métricas: 5-fold CV sobre el train + evaluación final sobre held-out 20%.

Uso:
    venv/bin/python scripts/train_svm.py
    venv/bin/python scripts/train_svm.py --kernel linear --test-size 0.25
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
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "phq9_prepared.csv"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
MODELS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

CLASES = ["SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "CRITICO"]

# Features que usa el sistema en producción. Estas son las mismas variables
# que el EvaluatorService puede entregarle al SVM cuando un alumno termina
# un cuestionario (puntajes de los 9 ítems + total + contexto demográfico).
FEATURES = [
    "phq_1", "phq_2", "phq_3", "phq_4", "phq_5",
    "phq_6", "phq_7", "phq_8", "phq_9", "phq_total",
    "sleep_quality", "study_pressure", "financial_pressure",
]


def cargar() -> pd.DataFrame:
    if not DATA.exists():
        raise SystemExit(
            f"Falta {DATA}. Corre primero: "
            "venv/bin/python scripts/prepare_phq9_dataset.py"
        )
    return pd.read_csv(DATA)


def entrenar(kernel: str, test_size: float, seed: int) -> dict:
    df = cargar()
    X = np.asarray(df[FEATURES].to_numpy(), dtype=float)
    y = np.asarray(df["riesgo"].to_numpy(), dtype=object)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y,
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svm", SVC(
            kernel=kernel,
            C=1.0,
            gamma="scale",
            class_weight="balanced",  # compensa el desbalance entre clases
            probability=True,
            random_state=seed,
        )),
    ])

    print(f"Entrenando SVM ({kernel}) sobre {len(X_train)} ejemplos...")
    pipeline.fit(X_train, y_train)

    # Validación cruzada sobre el TRAIN
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring="f1_macro")
    print(f"CV F1-macro: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Evaluación sobre el TEST (held-out)
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro", labels=CLASES, zero_division=0)
    f1_weighted = f1_score(y_test, y_pred, average="weighted", labels=CLASES, zero_division=0)
    reporte = classification_report(
        y_test, y_pred, labels=CLASES, digits=3, zero_division=0,
    )
    matriz = confusion_matrix(y_test, y_pred, labels=CLASES).tolist()

    metricas = {
        "kernel": kernel,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "features": FEATURES,
        "clases": CLASES,
        "cv_f1_macro_mean": round(float(cv_scores.mean()), 4),
        "cv_f1_macro_std": round(float(cv_scores.std()), 4),
        "test_accuracy": round(float(acc), 4),
        "test_f1_macro": round(float(f1_macro), 4),
        "test_f1_weighted": round(float(f1_weighted), 4),
        "matriz_confusion": matriz,
        "classification_report": reporte,
        "dataset_source": (
            "Miraz, M.A.I.A. (2025). PHQ-9 Student Depression Dataset. "
            "Mendeley Data. DOI: 10.17632/kkzjk253cy.1. CC BY 4.0."
        ),
    }

    # Persistir modelo + metadatos
    modelo_path = MODELS_DIR / "svm_riesgo.joblib"
    joblib.dump({
        "pipeline": pipeline,
        "features": FEATURES,
        "clases": CLASES,
        "kernel": kernel,
        "n_train": len(X_train),
        "cv_f1_macro_mean": float(cv_scores.mean()),
    }, modelo_path)
    print(f"Modelo guardado: {modelo_path}")

    return metricas


def reportar(metricas: dict) -> None:
    json_path = REPORTS_DIR / "svm_training.json"
    md_path = REPORTS_DIR / "svm_training.md"
    json_path.write_text(json.dumps(metricas, indent=2, ensure_ascii=False))

    md = []
    md.append("# Entrenamiento del SVM de riesgo\n")
    md.append("## Resumen")
    md.append(f"- **Kernel:** `{metricas['kernel']}`")
    md.append(f"- **N entrenamiento:** {metricas['n_train']}")
    md.append(f"- **N test (held-out):** {metricas['n_test']}")
    md.append(f"- **Features ({len(metricas['features'])}):** "
              f"{', '.join(metricas['features'])}")
    md.append(f"- **Clases:** {', '.join(metricas['clases'])}\n")

    md.append("## Métricas")
    md.append(f"- **CV F1-macro (5-fold sobre train):** "
              f"{metricas['cv_f1_macro_mean']} ± {metricas['cv_f1_macro_std']}")
    md.append(f"- **Test accuracy:** {metricas['test_accuracy']}")
    md.append(f"- **Test F1-macro:** {metricas['test_f1_macro']}")
    md.append(f"- **Test F1-weighted:** {metricas['test_f1_weighted']}\n")

    md.append("## Reporte por clase")
    md.append("```")
    md.append(metricas["classification_report"])
    md.append("```\n")

    md.append("## Matriz de confusión")
    cats = metricas["clases"]
    md.append("| real \\ pred | " + " | ".join(cats) + " |")
    md.append("| --- | " + " | ".join(["---"] * len(cats)) + " |")
    for i, fila in enumerate(metricas["matriz_confusion"]):
        md.append(f"| **{cats[i]}** | " + " | ".join(str(x) for x in fila) + " |")
    md.append("")

    md.append("## Fuente del dataset")
    md.append(f"> {metricas['dataset_source']}\n")

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
    print(f"  CV F1-macro: {metricas['cv_f1_macro_mean']}")
    print(f"  Test accuracy: {metricas['test_accuracy']}")
    print(f"  Test F1-macro: {metricas['test_f1_macro']}")


if __name__ == "__main__":
    main()
