"""
Entrenamiento del SVM de segunda opinión sobre PHQ-9 / PHQ-A con datos ENDES.

Por qué este modelo
-------------------
El SVM anterior (`train_svm_dass21.py`) solo opina si el cuestionario incluye
DASS-21, y el instrumento que se aplica en el colegio es PHQ-A + GAD-7. Por eso
la segunda opinión nunca aparecía sobre la cohorte real: no es que fallara, es
que nunca se la invocaba.

PHQ-9 y PHQ-A son el mismo instrumento —9 ítems, escala 0-3— con la redacción
adaptada a adolescentes, así que un modelo entrenado sobre PHQ-9 sí puede
opinar sobre las respuestas PHQ-A que el sistema ya recoge.

Entrada
-------
`estudiantes_phq9_endes2025.xlsx` — ENDES (INEI, Perú). Variables QS700A..QS700I
(los 9 ítems PHQ-9, escala 0-3, sin faltantes), QS23 (edad), phq9_total.

Mapeo ENDES → PHQ-A del sistema
-------------------------------
QS700A..QS700I son los ítems 1..9 en el orden estándar del PHQ-9, que es el
mismo del banco (`bank_item` del instrumento PHQ-A). Comprobado además por la
distribución: QS700H (ítem 8, enlentecimiento psicomotor) es el menos
endosado, como corresponde en población general.

ADVERTENCIA SOBRE LA ETIQUETA — leer antes de citar las métricas
----------------------------------------------------------------
El objetivo (`phq9_total >= 10`) es una **función aritmética de las mismas 9
features**: la suma de los ítems comparada con un corte. El modelo no aprende
a detectar depresión; aprende a sumar nueve números.

Las métricas van a salir muy altas y eso no es mérito del SVM. Por eso el
script entrena **también** una regla trivial (sumar y comparar con el corte) y
reporta las dos juntas: si el SVM no supera a la regla, queda a la vista que
no aporta nada por encima de la aritmética.

Esto es exactamente lo que ya pasaba con el modelo DASS-21 y conviene
declararlo en la tesis en vez de que lo encuentre el jurado.

Lo que volvería el modelo no circular es entrenar contra un objetivo que NO
sea función de los ítems — el juicio clínico de las psicólogas, que se está
recogiendo con el módulo de etiquetado.

Salidas
-------
    models/svm_endes_phq9.joblib
    reports/svm_endes.md
    reports/svm_endes.json

Uso
---
    venv/bin/python scripts/train_svm_endes.py
    venv/bin/python scripts/train_svm_endes.py --edad-max 16
    venv/bin/python scripts/train_svm_endes.py --corte 5 --kernel linear
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
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
DATA = ROOT / "estudiantes_phq9_endes2025.xlsx"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

# Los 9 ítems en el orden 1..9 del PHQ-9. Es el mismo orden en que el sistema
# guarda las respuestas (`INSTR:PHQ-A:1` .. `:9`), así que el vector se arma
# igual en entrenamiento y en inferencia. Si esto se tocara, hay que tocar
# también `SVMService.predecir_phq`.
ITEMS_ENDES = [f"QS700{c}" for c in "ABCDEFGHI"]

# Corte estándar del PHQ-9 para sospecha clínicamente significativa
# (Kroenke, Spitzer & Williams 2001). Coincide con el primer nivel de alerta
# que ya usa el sistema en `PHQA_CORTES`: "moderada" arranca en 10.
CORTE_RIESGO = 10


def cargar(edad_max: int) -> pd.DataFrame:
    if not DATA.exists():
        raise SystemExit(
            f"No encuentro {DATA}.\n"
            "Hace falta el Excel de ENDES con los ítems QS700A..QS700I."
        )
    df = pd.read_excel(DATA)
    faltan = [c for c in ITEMS_ENDES + ["QS23", "phq9_total"] if c not in df.columns]
    if faltan:
        raise SystemExit(f"Al Excel le faltan columnas: {faltan}")

    antes = len(df)
    df = df[df["QS23"] <= edad_max].copy()
    print(f"  edad <= {edad_max}: {len(df)} de {antes} registros")

    # Coherencia: el total tiene que ser la suma de los ítems. Si no lo fuera,
    # la etiqueta no describiría a estas features y todo lo demás sobra.
    suma = df[ITEMS_ENDES].sum(axis=1)
    if not (suma == df["phq9_total"]).all():
        n = int((suma != df["phq9_total"]).sum())
        raise SystemExit(
            f"{n} filas donde phq9_total no es la suma de los 9 ítems. "
            "Revisar el Excel antes de entrenar."
        )
    return df


def entrenar(df: pd.DataFrame, kernel: str, corte: int, test_size: float, semilla: int):
    X = df[ITEMS_ENDES].to_numpy(dtype=float)
    y = (df["phq9_total"] >= corte).astype(int).to_numpy()

    pos = int(y.sum())
    print(f"  en_riesgo (total >= {corte}): {pos} ({pos/len(y):.1%})  "
          f"· sin_riesgo: {len(y)-pos}")
    if pos < 30:
        print("  ! advertencia: muy pocos positivos, las métricas van a ser "
              "inestables")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_size, random_state=semilla, stratify=y
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        # class_weight balanceado: sin esto, con ~20% de positivos el modelo
        # gana accuracy diciendo "sin riesgo" a casi todo, y lo que importa en
        # tamizaje es justamente no perder los positivos.
        ("svc", SVC(kernel=kernel, probability=True, class_weight="balanced",
                    random_state=semilla)),
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=semilla)
    cv_scores = cross_val_score(pipeline, X_tr, y_tr, cv=cv, scoring="f1_macro")

    pipeline.fit(X_tr, y_tr)
    y_pred = pipeline.predict(X_te)
    y_proba = pipeline.predict_proba(X_te)[:, 1]

    # ── Línea base: la regla aritmética ───────────────────────────────────
    # Sumar los 9 ítems y comparar con el corte. Es lo que el SVM está
    # aprendiendo a imitar; sirve para ver cuánto aporta por encima de eso.
    base_pred = (X_te.sum(axis=1) >= corte).astype(int)

    return {
        "pipeline": pipeline,
        "y_te": y_te, "y_pred": y_pred, "y_proba": y_proba,
        "base_pred": base_pred,
        "cv_scores": cv_scores,
        "n_train": len(X_tr), "n_test": len(X_te),
        "n_total": len(X), "n_positivos": pos,
    }


def metricas(r: dict) -> dict:
    y, p, pr, b = r["y_te"], r["y_pred"], r["y_proba"], r["base_pred"]
    nombres = ["sin_riesgo", "en_riesgo"]
    cm = confusion_matrix(y, p).tolist()
    vn, fp, fn, vp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
    div = lambda a, b_: round(a / b_, 4) if b_ else None
    return {
        "cv_f1_macro_mean": round(float(r["cv_scores"].mean()), 4),
        "cv_f1_macro_std": round(float(r["cv_scores"].std()), 4),
        "test_accuracy": round(float(accuracy_score(y, p)), 4),
        "test_f1_macro": round(float(f1_score(y, p, average="macro")), 4),
        "test_f1_weighted": round(float(f1_score(y, p, average="weighted")), 4),
        "test_roc_auc": round(float(roc_auc_score(y, pr)), 4),
        "sensibilidad_en_riesgo": div(vp, vp + fn),
        "especificidad": div(vn, vn + fp),
        "precision_en_riesgo": div(vp, vp + fp),
        "vpn": div(vn, vn + fn),
        "matriz_confusion": cm,
        "classification_report": classification_report(
            y, p, target_names=nombres, digits=3, zero_division=0
        ),
        # La regla trivial, sobre el MISMO conjunto de prueba.
        "baseline_regla_suma": {
            "accuracy": round(float(accuracy_score(y, b)), 4),
            "f1_macro": round(float(f1_score(y, b, average="macro")), 4),
            "sensibilidad": div(
                int(((y == 1) & (b == 1)).sum()), int((y == 1).sum())
            ),
            "matriz_confusion": confusion_matrix(y, b).tolist(),
        },
    }


def escribir_reportes(m: dict, r: dict, cfg: dict) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    datos = {**cfg, **{k: v for k, v in m.items() if k != "classification_report"},
             "classification_report": m["classification_report"],
             "n_train": r["n_train"], "n_test": r["n_test"],
             "n_total": r["n_total"], "n_positivos": r["n_positivos"]}
    (REPORTS_DIR / "svm_endes.json").write_text(
        json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    b = m["baseline_regla_suma"]
    cm = m["matriz_confusion"]
    md = [
        "# SVM — segunda opinión sobre PHQ-9 / PHQ-A (ENDES)",
        "",
        "## Resumen",
        f"- **Fuente**: ENDES (INEI, Perú) — `estudiantes_phq9_endes2025.xlsx`",
        f"- **Población**: {cfg['edad_min']}–{cfg['edad_max']} años "
        f"(n = {r['n_total']}; {r['n_train']} entrenamiento / {r['n_test']} prueba)",
        f"- **Features**: los 9 ítems PHQ-9 (escala 0-3), sin el total",
        f"- **Etiqueta**: `en_riesgo` si la suma de los 9 ítems ≥ {cfg['corte']} "
        "(corte estándar PHQ-9, Kroenke 2001)",
        f"- **Positivos**: {r['n_positivos']} ({r['n_positivos']/r['n_total']:.1%})",
        f"- **Kernel**: `{cfg['kernel']}` · class_weight balanceado",
        f"- **Entrenado**: {cfg['fecha']}",
        "",
        "## Resultados",
        "| Métrica | Valor |",
        "| --- | --- |",
        f"| CV F1-macro (5-fold, train) | {m['cv_f1_macro_mean']} ± {m['cv_f1_macro_std']} |",
        f"| Accuracy (test) | {m['test_accuracy']} |",
        f"| F1-macro (test) | {m['test_f1_macro']} |",
        f"| F1-weighted (test) | {m['test_f1_weighted']} |",
        f"| ROC-AUC (test) | {m['test_roc_auc']} |",
        f"| **Sensibilidad en `en_riesgo`** | **{m['sensibilidad_en_riesgo']}** |",
        f"| Especificidad | {m['especificidad']} |",
        f"| Precisión en `en_riesgo` | {m['precision_en_riesgo']} |",
        f"| VPN | {m['vpn']} |",
        "",
        "## Reporte por clase",
        "```",
        m["classification_report"].rstrip(),
        "```",
        "",
        "## Matriz de confusión (test)",
        "| real \\ pred | sin_riesgo | en_riesgo |",
        "| --- | --- | --- |",
        f"| **sin_riesgo** | {cm[0][0]} | {cm[0][1]} |",
        f"| **en_riesgo**  | {cm[1][0]} | {cm[1][1]} |",
        "",
        "## Comparación con la regla aritmética",
        "",
        "La etiqueta es la suma de los 9 ítems comparada con un corte, y las",
        "features son esos mismos 9 ítems. Entonces el techo del problema lo",
        "marca una regla de una línea. Sobre el mismo conjunto de prueba:",
        "",
        "| | SVM | Regla `suma ≥ corte` |",
        "| --- | --- | --- |",
        f"| Accuracy | {m['test_accuracy']} | {b['accuracy']} |",
        f"| F1-macro | {m['test_f1_macro']} | {b['f1_macro']} |",
        f"| Sensibilidad | {m['sensibilidad_en_riesgo']} | {b['sensibilidad']} |",
        "",
        "**Cómo leerlo.** La regla acierta por construcción: la etiqueta se",
        "define con ella. Si el SVM no la supera, lo honesto es decir que no",
        "aporta nada por encima de sumar los ítems — que es lo que hace el",
        "sistema de reglas desde el principio.",
        "",
        "Para que el modelo aporte, el objetivo tiene que ser algo que NO sea",
        "función de los ítems: el juicio clínico de las psicólogas, que se está",
        "recogiendo con el módulo de etiquetado.",
        "",
        "## Fuente",
        "> Instituto Nacional de Estadística e Informática (INEI). Encuesta",
        "> Demográfica y de Salud Familiar (ENDES). Módulo de salud mental,",
        "> cuestionario PHQ-9 (variables QS700A–QS700I).",
    ]
    (REPORTS_DIR / "svm_endes.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edad-max", type=int, default=17,
                    help="edad máxima inclusive (default 17: 4to y 5to de secundaria)")
    ap.add_argument("--corte", type=int, default=CORTE_RIESGO)
    ap.add_argument("--kernel", default="rbf")
    ap.add_argument("--test-size", type=float, default=0.20)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--no-guardar", action="store_true",
                    help="entrena y reporta sin escribir el .joblib")
    args = ap.parse_args()

    print("Entrenando SVM PHQ-9 con datos ENDES")
    print("=" * 56)
    df = cargar(args.edad_max)
    r = entrenar(df, args.kernel, args.corte, args.test_size, args.semilla)
    m = metricas(r)

    print(f"\n  CV F1-macro : {m['cv_f1_macro_mean']} ± {m['cv_f1_macro_std']}")
    print(f"  Accuracy    : {m['test_accuracy']}")
    print(f"  F1-macro    : {m['test_f1_macro']}")
    print(f"  ROC-AUC     : {m['test_roc_auc']}")
    print(f"  Sensibilidad: {m['sensibilidad_en_riesgo']}")
    print(f"  Especificid.: {m['especificidad']}")
    print(f"\n  Regla trivial (suma >= {args.corte}) sobre el mismo test:")
    b = m["baseline_regla_suma"]
    print(f"    accuracy {b['accuracy']} · F1-macro {b['f1_macro']} · "
          f"sensibilidad {b['sensibilidad']}")

    cfg = {
        "dataset": "ENDES (INEI, Perú) — estudiantes_phq9_endes2025.xlsx",
        "instrumento": "PHQ-9 (aplicable a PHQ-A: mismos 9 ítems, escala 0-3)",
        "items": ITEMS_ENDES,
        "edad_min": int(df["QS23"].min()),
        "edad_max": int(df["QS23"].max()),
        "corte": args.corte,
        "kernel": args.kernel,
        "semilla": args.semilla,
        "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    escribir_reportes(m, r, cfg)
    print(f"\n  Reportes  → {REPORTS_DIR/'svm_endes.md'}")

    if args.no_guardar:
        print("  (--no-guardar: no se escribió el modelo)")
        return

    MODELS_DIR.mkdir(exist_ok=True)
    destino = MODELS_DIR / "svm_endes_phq9.joblib"
    joblib.dump({
        "pipeline": r["pipeline"],
        "items": ITEMS_ENDES,
        "n_items": 9,
        "kernel": args.kernel,
        "corte": args.corte,
        "n_train": r["n_train"],
        "cv_f1_macro_mean": m["cv_f1_macro_mean"],
        "test_roc_auc": m["test_roc_auc"],
        "test_accuracy": m["test_accuracy"],
        "sensibilidad": m["sensibilidad_en_riesgo"],
        # Trazabilidad: sin esto no se puede saber qué modelo está corriendo.
        "version": "endes-phq9-1.0",
        "entrenado_utc": datetime.now(timezone.utc).isoformat(),
        "dataset": cfg["dataset"],
        "edad_min": cfg["edad_min"],
        "edad_max": cfg["edad_max"],
    }, destino)
    print(f"  Modelo    → {destino}")


if __name__ == "__main__":
    main()
