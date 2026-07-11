"""
Evalúa BETO zero-shot con las hipótesis actuales del sistema contra un
dataset con etiquetas CLÍNICAS de depresión y/o ansiedad (no emociones
básicas como EmoEvent).

Datasets sugeridos:
    1. DEPSY-ES        → HuggingFace: ronaldahmed/depression_spanish
       Uso: python -m scripts.eval_beto_dataset_clinico --dataset depsy
    2. MentalRiskES    → https://sites.google.com/view/mentalriskes
       Uso: bajar TSV localmente y pasarlo con --dataset local --path TSV
    3. Cualquier CSV/TSV con columnas 'text' y 'label' (0/1)
       Uso: --dataset local --path RUTA.csv --label-col LABEL_COL

Uso:
    venv/bin/python -m scripts.eval_beto_dataset_clinico --dataset depsy
    venv/bin/python -m scripts.eval_beto_dataset_clinico --dataset local \\
        --path data/dataset_clinico.tsv --text-col texto --label-col es_depresion
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    confusion_matrix, roc_auc_score, classification_report,
)
from transformers import pipeline
from app.config import settings
from app.services.nlp_service import CATEGORIAS_EMOCIONALES

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"
REPORTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


def cargar_local(path, text_col, label_col, delim=None, limite=None):
    """Carga un CSV/TSV local con columnas de texto y etiqueta binaria."""
    p = Path(path)
    if delim is None:
        delim = "\t" if p.suffix.lower() in (".tsv", ".txt") else ","
    pares = []
    with p.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=delim):
            texto = (row.get(text_col) or "").strip()
            etiqueta = (row.get(label_col) or "").strip().lower()
            if not texto:
                continue
            gold = int(etiqueta in ("1", "true", "si", "sí", "positive",
                                    "depresion", "depression", "ansiedad",
                                    "anxiety"))
            pares.append((texto, gold))
            if limite and len(pares) >= limite:
                break
    return pares


def cargar_depsy(limite=None):
    """Carga DEPSY-ES desde HuggingFace (requiere internet)."""
    from datasets import load_dataset
    ds = load_dataset("ronaldahmed/depression_spanish", split="test")
    pares = []
    for row in ds:
        texto = row.get("text") or row.get("texto") or ""
        gold = int(row.get("label", 0))
        if texto:
            pares.append((texto.strip(), gold))
        if limite and len(pares) >= limite:
            break
    return pares


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["depsy", "local"], required=True)
    ap.add_argument("--path", help="Ruta al CSV/TSV local")
    ap.add_argument("--text-col", default="text")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--categoria", choices=["depresion", "ansiedad"],
                    default="depresion")
    ap.add_argument("--limite", type=int, default=None)
    ap.add_argument("--umbral", type=float, default=0.50)
    args = ap.parse_args()

    if args.dataset == "depsy":
        pares = cargar_depsy(args.limite)
    else:
        if not args.path:
            raise SystemExit("--path requerido para --dataset local")
        pares = cargar_local(args.path, args.text_col, args.label_col,
                             limite=args.limite)

    print(f"n={len(pares)} · positivos={sum(y for _, y in pares)}")

    # Hipótesis: la categoría clínica del sistema vs una hipótesis contraste
    hip_pos = CATEGORIAS_EMOCIONALES[args.categoria]
    hip_neg = (
        "Este texto no expresa síntomas clínicos de la categoría en cuestión; "
        "describe otra emoción, actividad cotidiana o contenido neutral."
    )

    print(f"\nHipótesis positiva ({args.categoria}):")
    print(f"  {hip_pos}")

    print(f"\nCargando BETO ({settings.MODEL_NAME})...")
    clf = pipeline("zero-shot-classification", model=settings.MODEL_NAME,
                   device=settings.DEVICE)

    print(f"Clasificando {len(pares)} textos...")
    y_true, y_pred, y_score = [], [], []
    for i, (texto, gold) in enumerate(pares):
        r = clf(texto, candidate_labels=[hip_pos, hip_neg], multi_label=False)
        idx = r["labels"].index(hip_pos)
        s = float(r["scores"][idx])
        y_true.append(gold)
        y_pred.append(int(s >= args.umbral))
        y_score.append(s)
        if (i + 1) % 100 == 0:
            print(f"  ... {i+1}/{len(pares)}")

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_score)
    except ValueError:
        auc = None
    cm = confusion_matrix(y_true, y_pred).tolist()
    report = classification_report(y_true, y_pred,
                                   target_names=[f"no_{args.categoria}",
                                                  args.categoria],
                                   digits=3, zero_division=0)

    print()
    print(f"=== BETO — {args.categoria} en {args.dataset} — n={len(pares)} ===")
    print(f"Accuracy:    {acc:.4f}")
    print(f"Precision:   {prec:.4f}")
    print(f"Recall:      {rec:.4f}")
    print(f"F1:          {f1:.4f}")
    print(f"F1-macro:    {f1_macro:.4f}")
    if auc:
        print(f"ROC-AUC:     {auc:.4f}")
    print()
    print(report)

    resumen = {
        "dataset": args.dataset,
        "categoria": args.categoria,
        "n": len(pares),
        "n_positivos": sum(y_true),
        "umbral": args.umbral,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "f1_macro": round(f1_macro, 4),
        "roc_auc": round(auc, 4) if auc is not None else None,
        "matriz_confusion": {"TN": cm[0][0], "FP": cm[0][1],
                             "FN": cm[1][0], "TP": cm[1][1]},
        "classification_report": report,
    }
    out = REPORTS_DIR / f"beto_{args.categoria}_{args.dataset}.json"
    out.write_text(json.dumps(resumen, indent=2, ensure_ascii=False))
    print(f"\nGuardado: {out}")


if __name__ == "__main__":
    main()
