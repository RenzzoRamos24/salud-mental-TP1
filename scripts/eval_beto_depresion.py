"""
Evaluación de BETO en modo binario: "depresión" vs "otra emoción".

Cambio metodológico respecto a `eval_beto_emoevent.py`:
en lugar de pedirle a BETO que distinga entre 5 emociones (tarea difícil para
zero-shot), lo restringimos a UNA sola decisión: "¿este texto habla de
tristeza / desesperanza / apatía?" — sí o no.

Mapeo EmoEvent → binario:
    sadness → 1 (depresión)
    resto   → 0 (no depresión)

Se espera un salto grande de F1 porque las tareas binarias zero-shot
son mucho más manejables que las multi-clase.

Uso:
    venv/bin/python -m scripts.eval_beto_depresion
    venv/bin/python -m scripts.eval_beto_depresion --limite 500
"""
from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from pathlib import Path

from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, roc_auc_score,
)

from app.services.nlp_service import NLPService

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"
REPORTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

SPLITS_URL = (
    "https://raw.githubusercontent.com/"
    "fmplaza/EmoEvent-multilingual-corpus/master/splits/es/{split}.tsv"
)

# Hipótesis binaria para el clasificador zero-shot.
HIP_DEPRESION = "Este texto expresa tristeza, desesperanza o vacío emocional."
HIP_OTRO      = "Este texto expresa otra emoción o es neutral."

# Umbral de decisión sobre el score de depresión (multi_label=False, así que
# la suma de ambas hipótesis = 1.0, un umbral de 0.5 es lo natural).
UMBRAL = 0.50


def cargar(limite: int | None = None):
    """EmoEvent test split → [(texto, es_depresion_bool), ...]."""
    destino = DATA_DIR / "emoevent_es_test.tsv"
    if not destino.exists():
        url = SPLITS_URL.format(split="test")
        urllib.request.urlretrieve(url, destino)
    pares = []
    with destino.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            emo = (row.get("emotion") or "").lower().strip()
            texto = (row.get("tweet") or "").strip()
            if not texto:
                continue
            es_depresion = int(emo == "sadness")
            pares.append((texto, es_depresion))
            if limite and len(pares) >= limite:
                break
    return pares


def predecir(pares):
    """Devuelve (y_true, y_pred_binary, y_score_depresion)."""
    print("Cargando modelo BETO...")
    classifier = NLPService.get_classifier()
    print(f"Clasificando {len(pares)} textos en modo binario depresión...")

    y_true, y_pred, y_score = [], [], []
    for i, (texto, real) in enumerate(pares, 1):
        try:
            resultado = classifier(
                texto,
                candidate_labels=[HIP_DEPRESION, HIP_OTRO],
                multi_label=False,   # exclusivo — suma 1
            )
            score_dep = 0.0
            for label, score in zip(resultado["labels"], resultado["scores"]):
                if label == HIP_DEPRESION:
                    score_dep = float(score)
                    break
        except Exception as e:
            print(f"  [{i}] error: {e}")
            continue
        y_true.append(real)
        y_pred.append(int(score_dep >= UMBRAL))
        y_score.append(score_dep)
        if i % 100 == 0:
            print(f"  {i}/{len(pares)} …")
    return y_true, y_pred, y_score


def reportar(y_true, y_pred, y_score):
    n = len(y_true)
    n_pos = sum(y_true)
    n_neg = n - n_pos
    acc = accuracy_score(y_true, y_pred)
    pre = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1  = f1_score(y_true, y_pred, zero_division=0)
    f1m = f1_score(y_true, y_pred, average="macro", zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_score)
    except Exception:
        auc = None
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()

    return {
        "modelo": "Recognai/bert-base-spanish-wwm-cased-xnli",
        "modo": "binario · depresión (tristeza) vs otra emoción",
        "hipotesis_positiva": HIP_DEPRESION,
        "hipotesis_negativa": HIP_OTRO,
        "umbral": UMBRAL,
        "dataset": "EmoEvent (Plaza-del-Arco et al., 2020) — split español test",
        "n_ejemplos": n,
        "n_positivos_depresion": n_pos,
        "n_negativos": n_neg,
        "accuracy": round(acc, 4),
        "precision_depresion": round(pre, 4),
        "recall_depresion": round(rec, 4),
        "f1_depresion": round(f1, 4),
        "f1_macro": round(f1m, 4),
        "roc_auc": round(auc, 4) if auc is not None else None,
        "matriz_confusion": {
            "TN": cm[0][0], "FP": cm[0][1],
            "FN": cm[1][0], "TP": cm[1][1],
        },
    }


def guardar_md(m: dict):
    json_path = REPORTS_DIR / "beto_depresion.json"
    md_path = REPORTS_DIR / "beto_depresion.md"
    json_path.write_text(json.dumps(m, indent=2, ensure_ascii=False))

    md = [
        "# Evaluación de BETO en modo binario · depresión",
        "",
        "## Resumen",
        f"- **Modelo:** `{m['modelo']}`",
        f"- **Modo:** {m['modo']}",
        f"- **Umbral:** {m['umbral']}",
        f"- **Dataset:** {m['dataset']}",
        f"- **N evaluado:** {m['n_ejemplos']} "
        f"({m['n_positivos_depresion']} positivos · {m['n_negativos']} negativos)",
        "",
        "## Métricas",
        "| Métrica | Valor |",
        "| --- | --- |",
        f"| Accuracy | {m['accuracy']} |",
        f"| **Precision (depresión)** | **{m['precision_depresion']}** |",
        f"| **Recall (depresión)** | **{m['recall_depresion']}** |",
        f"| **F1 (depresión)** | **{m['f1_depresion']}** |",
        f"| F1-macro | {m['f1_macro']} |",
        f"| ROC-AUC | {m['roc_auc']} |",
        "",
        "## Matriz de confusión",
        "| | Predicho: no depresión | Predicho: depresión |",
        "| --- | --- | --- |",
        f"| Real: no depresión | {m['matriz_confusion']['TN']} | {m['matriz_confusion']['FP']} |",
        f"| Real: depresión | {m['matriz_confusion']['FN']} | {m['matriz_confusion']['TP']} |",
    ]
    md_path.write_text("\n".join(md))
    print(f"\nReporte guardado en {md_path}")


def main(limite: int | None):
    pares = cargar(limite)
    y_true, y_pred, y_score = predecir(pares)
    m = reportar(y_true, y_pred, y_score)
    guardar_md(m)
    print("\n=== Métricas finales · binario depresión ===")
    print(f"  N            : {m['n_ejemplos']} "
          f"({m['n_positivos_depresion']} pos, {m['n_negativos']} neg)")
    print(f"  Accuracy     : {m['accuracy']}")
    print(f"  Precision    : {m['precision_depresion']}")
    print(f"  Recall       : {m['recall_depresion']}")
    print(f"  F1           : {m['f1_depresion']}")
    print(f"  F1-macro     : {m['f1_macro']}")
    print(f"  ROC-AUC      : {m['roc_auc']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=None)
    args = parser.parse_args()
    main(args.limite)
