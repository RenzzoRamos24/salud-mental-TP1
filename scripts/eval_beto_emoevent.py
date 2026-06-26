"""
Evaluación de BETO sobre EmoEvent (Plaza-del-Arco et al., 2020).

Demuestra que el clasificador zero-shot de Sami funciona sobre texto emocional
en español, contra un benchmark público con etiquetas ya hechas.

Mapeo de etiquetas: EmoEvent usa 7 emociones básicas (Ekman + neutral). Las
mapeamos a 5 de las 8 categorías de Sami; `disgust` y `surprise` se descartan
porque no aparecen en las categorías clínicas que mide el sistema.

    EmoEvent       →   Sami
    ----------         ----------
    anger          →   ira
    fear           →   miedo
    sadness        →   tristeza
    joy            →   esperanza
    others         →   neutral
    disgust        →   (descartado)
    surprise       →   (descartado)

Salida:
    reports/beto_emoevent.json   métricas crudas
    reports/beto_emoevent.md     reporte para pegar en la tesis

Cita:
    Plaza-del-Arco, F. M., Strapparava, C., Ureña-López, L. A., & Martín-Valdivia,
    M. T. (2020). EmoEvent: A Multilingual Emotion Corpus based on different
    Events. Proceedings of LREC 2020, 1492–1498.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import csv
import urllib.request

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from app.services.nlp_service import NLPService

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DATA_DIR = ROOT / "data"
REPORTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# TSVs públicos del repositorio oficial (Apache-2.0). No requieren login.
SPLITS_URL = (
    "https://raw.githubusercontent.com/"
    "fmplaza/EmoEvent-multilingual-corpus/master/splits/es/{split}.tsv"
)

EMOEVENT_TO_SAMI = {
    "anger": "ira",
    "fear": "miedo",
    "sadness": "tristeza",
    "joy": "esperanza",
    "others": "neutral",
}
CATEGORIAS_EVAL = ["ira", "miedo", "tristeza", "esperanza", "neutral"]


def descargar_split(split: str) -> Path:
    """Descarga y cachea el TSV correspondiente al split."""
    destino = DATA_DIR / f"emoevent_es_{split}.tsv"
    if destino.exists():
        return destino
    url = SPLITS_URL.format(split=split)
    print(f"Descargando {url} ...")
    urllib.request.urlretrieve(url, destino)
    print(f"  → {destino} ({destino.stat().st_size // 1024} KB)")
    return destino


def cargar_split(split: str = "test", limite: int | None = None):
    """Devuelve [(texto, etiqueta_sami), ...] desde el TSV oficial."""
    archivo = descargar_split(split)
    pares = []
    with archivo.open(encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            emo = (row.get("emotion") or "").lower().strip()
            sami = EMOEVENT_TO_SAMI.get(emo)
            if sami is None:
                continue  # descartamos disgust / surprise
            texto = (row.get("tweet") or "").strip()
            if not texto:
                continue
            pares.append((texto, sami))
            if limite and len(pares) >= limite:
                break
    print(f"EmoEvent_es ({split}): {len(pares)} ejemplos utilizables "
          f"(categorías {CATEGORIAS_EVAL})")
    return pares


def predecir(pares):
    """Corre BETO sobre cada texto y devuelve la categoría dominante."""
    print("Cargando modelo BETO (primera vez puede tardar 2–5 min)...")
    NLPService.get_classifier()
    print("Modelo cargado. Clasificando...")

    y_true, y_pred = [], []
    for i, (texto, etiqueta_real) in enumerate(pares, 1):
        try:
            resultado = NLPService.clasificar_frase(texto)
            # La categoría dominante entre las que evaluamos (no contamos las
            # que no están en CATEGORIAS_EVAL — para no penalizar al modelo por
            # predecir, p. ej., `soledad` cuando la real es `tristeza`).
            scores = resultado.get("scores") or {}
            filtrados = {k: v for k, v in scores.items() if k in CATEGORIAS_EVAL}
            if not filtrados:
                continue
            dominante = max(filtrados, key=filtrados.get)
        except Exception as e:
            print(f"  [{i}] error: {e}")
            continue
        y_true.append(etiqueta_real)
        y_pred.append(dominante)
        if i % 50 == 0:
            print(f"  {i}/{len(pares)} procesados")
    return y_true, y_pred


def reportar(y_true, y_pred) -> dict:
    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, labels=CATEGORIAS_EVAL, average="macro", zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, labels=CATEGORIAS_EVAL, average="weighted", zero_division=0)
    reporte = classification_report(
        y_true, y_pred, labels=CATEGORIAS_EVAL, digits=3, zero_division=0,
    )
    matriz = confusion_matrix(y_true, y_pred, labels=CATEGORIAS_EVAL).tolist()

    metricas = {
        "modelo": "Recognai/bert-base-spanish-wwm-cased-xnli",
        "dataset": "EmoEvent (Plaza-del-Arco et al., 2020) — split español test",
        "n_ejemplos": len(y_true),
        "accuracy": round(acc, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_weighted": round(f1_weighted, 4),
        "categorias": CATEGORIAS_EVAL,
        "matriz_confusion": matriz,
        "classification_report": reporte,
    }
    return metricas


def guardar(metricas):
    json_path = REPORTS_DIR / "beto_emoevent.json"
    md_path = REPORTS_DIR / "beto_emoevent.md"
    json_path.write_text(json.dumps(metricas, indent=2, ensure_ascii=False))

    md = []
    md.append("# Evaluación de BETO sobre EmoEvent\n")
    md.append("## Resumen")
    md.append(f"- **Modelo:** `{metricas['modelo']}`")
    md.append(f"- **Dataset:** {metricas['dataset']}")
    md.append(f"- **N evaluado:** {metricas['n_ejemplos']}")
    md.append(f"- **Accuracy:** {metricas['accuracy']}")
    md.append(f"- **F1-macro:** {metricas['f1_macro']}")
    md.append(f"- **F1-weighted:** {metricas['f1_weighted']}\n")

    md.append("## Reporte por clase\n")
    md.append("```")
    md.append(metricas["classification_report"])
    md.append("```\n")

    md.append("## Matriz de confusión")
    cats = metricas["categorias"]
    header = "| real \\ pred | " + " | ".join(cats) + " |"
    sep = "| --- | " + " | ".join(["---"] * len(cats)) + " |"
    md.append(header)
    md.append(sep)
    for i, fila in enumerate(metricas["matriz_confusion"]):
        md.append(f"| **{cats[i]}** | " + " | ".join(str(x) for x in fila) + " |")
    md.append("")

    md.append("## Cita")
    md.append("> Plaza-del-Arco, F. M., Strapparava, C., Ureña-López, L. A., "
              "& Martín-Valdivia, M. T. (2020). EmoEvent: A Multilingual "
              "Emotion Corpus based on different Events. *Proceedings of LREC "
              "2020*, 1492–1498.\n")

    md_path.write_text("\n".join(md))
    print(f"Reporte guardado en:\n  {json_path}\n  {md_path}")


def main(limite: int | None = None):
    pares = cargar_split(split="test", limite=limite)
    y_true, y_pred = predecir(pares)
    metricas = reportar(y_true, y_pred)
    guardar(metricas)
    print("\n=== Métricas finales ===")
    print(f"  N           : {metricas['n_ejemplos']}")
    print(f"  Accuracy    : {metricas['accuracy']}")
    print(f"  F1-macro    : {metricas['f1_macro']}")
    print(f"  F1-weighted : {metricas['f1_weighted']}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evalúa BETO sobre EmoEvent_es")
    parser.add_argument(
        "--limite", type=int, default=None,
        help="Tope de ejemplos a evaluar (útil para pruebas rápidas)",
    )
    args = parser.parse_args()
    main(limite=args.limite)
