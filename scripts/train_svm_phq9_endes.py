"""
Entrenamiento del SVM de Sami sobre PHQ-9 (ENDES 2025, adolescentes 15-17).

Por qué reemplaza al SVM de DASS-21
-----------------------------------
El modelo anterior (`train_svm_dass21.py`) pedía como entrada los 21 ítems
del DASS-21. Sami aplica PHQ-A (9 ítems) + GAD-7 (7 ítems), así que esas
features no existen en producción: el SVM nunca emitió una sola predicción
—verificado, `etiqueta_caso.modelo_svm_clase` está NULL en los 102 casos
etiquetados. Este modelo usa los 9 ítems del PHQ-9, que **sí** coinciden
1:1 con los del PHQ-A que el sistema recolecta.

Datos
-----
`data/endes/estudiantes_phq9_endes2025.xlsx` — microdatos públicos de ENDES
(INEI, Perú). 2,238 filas, edades 15-24. Se filtra a **15-17 años → n=1,370**,
que es la población objetivo (secundaria). No hay casos de 13-14: el módulo
de salud mental de ENDES (QS700) se aplica desde los 15 años.

Honestidad sobre la etiqueta
----------------------------
ENDES **no tiene criterio clínico**: nadie evaluó a esos 1,370 adolescentes.
La única etiqueta posible es el corte del propio PHQ-9 (`phq9_total >= 10`),
y `phq9_total` es la suma exacta de las 9 features. O sea: la etiqueta es
función determinista de la entrada, igual que en el modelo de DASS-21.

Por eso las métricas internas de este script (CV, test held-out) **no miden
capacidad clínica** — miden qué tan bien el SVM aproxima una suma con umbral.
Se reportan porque hacen falta para verificar que el entrenamiento funcionó,
y van marcadas como circulares.

**La métrica que vale es la validación externa**: aplicar este modelo a los
102 casos del piloto y comparar contra el juicio ciego de la psicóloga. Esas
etiquetas son independientes de las de entrenamiento (criterio humano sobre
otros sujetos), así que esa comparación no es circular.

Supuesto a verificar
--------------------
Se asume que las columnas `QS700A..QS700I` corresponden a los ítems 1..9 del
PHQ-9 en orden estándar, y que el ítem 9 (QS700I) es el de ideación. Evidencia
a favor: QS700H es el menos endosado (7.1 %), y el ítem 8 del PHQ-9
(agitación/retardo psicomotor) es típicamente el menos endosado. Hay que
confirmarlo con el codebook de INEI. El script corre una prueba de
sensibilidad a permutaciones para cuantificar cuánto importaría equivocarse.

Uso
---
    venv/bin/python scripts/train_svm_phq9_endes.py

    # Con validación externa contra el piloto etiquetado
    venv/bin/python scripts/train_svm_phq9_endes.py --piloto ruta/casos.csv

Salidas
-------
    models/svm_phq9.joblib        modelo + metadatos
    reports/svm_phq9_endes.md     reporte de métricas
"""
from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import (
    GridSearchCV,
    LeaveOneOut,
    StratifiedKFold,
    cross_val_predict,
    cross_val_score,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

# sklearn 1.9 deprecó SVC(probability=True) a favor de CalibratedClassifierCV.
# Se mantiene probability=True por ahora (cambiarlo altera la calibración y
# habría que revalidar); migrar antes de sklearn 1.11.
warnings.filterwarnings("ignore", category=FutureWarning)

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
SEMILLA = 20261013

# Los 9 ítems del PHQ-9 en ENDES, en orden estándar 1..9.
ITEMS_ENDES = [f"QS700{c}" for c in "ABCDEFGHI"]
# Los mismos 9 ítems como los guarda Sami (`respuesta_aplicacion.origen`).
ITEMS_SAMI = [f"INSTR:PHQ-A:{i}" for i in range(1, 10)]

EDAD_MIN, EDAD_MAX = 15, 17
CORTE_MODERADO = 10          # PHQ-9 >= 10 → depresión moderada o superior
ORDEN_RIESGO = {"SIN_RIESGO": 0, "BAJO": 1, "MEDIO": 2, "ALTO": 3, "CRITICO": 4}
CORTE_ALERTA = ORDEN_RIESGO["MEDIO"]

GRID = {
    "svc__C": [0.1, 0.3, 1, 3, 10, 30],
    "svc__gamma": ["scale", 0.01, 0.03, 0.1],
    "svc__kernel": ["rbf", "linear"],
}


def pipeline() -> Pipeline:
    return Pipeline([
        ("sc", StandardScaler()),
        # class_weight balanceado: la prevalencia de PHQ-9 >= 10 en ENDES
        # 15-17 es 8 %. Sin esto el modelo aprende a decir siempre "no".
        ("svc", SVC(probability=True, class_weight="balanced",
                    random_state=SEMILLA)),
    ])


def buscador(cv=5) -> GridSearchCV:
    return GridSearchCV(pipeline(), GRID, scoring="f1_macro", cv=cv, n_jobs=-1)


# ════════════════════════════════════════════════════════════════════════════
# Datos
# ════════════════════════════════════════════════════════════════════════════


def cargar_endes(ruta: Path | None = None) -> pd.DataFrame:
    candidatos = [
        ruta,
        ROOT / "data" / "endes" / "estudiantes_phq9_endes2025.xlsx",
        ROOT / "estudiantes_phq9_endes2025.xlsx",
    ]
    for c in candidatos:
        if c and Path(c).exists():
            archivo = Path(c)
            break
    else:
        raise SystemExit(
            "Falta el xlsx de ENDES. Esperado en "
            "data/endes/estudiantes_phq9_endes2025.xlsx"
        )

    print(f"Cargando {archivo.relative_to(ROOT)}…")
    df = pd.read_excel(archivo)
    print(f"  filas totales: {len(df):,} | edades {df.QS23.min()}-{df.QS23.max()}")

    faltan = [c for c in ITEMS_ENDES + ["QS23", "phq9_total"] if c not in df]
    if faltan:
        raise SystemExit(f"Columnas ausentes en el xlsx: {faltan}")

    df = df[df.QS23.between(EDAD_MIN, EDAD_MAX)].copy()
    print(f"  tras filtrar {EDAD_MIN}-{EDAD_MAX} años: {len(df):,}")

    for c in ITEMS_ENDES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=ITEMS_ENDES)
    valido = (df[ITEMS_ENDES] >= 0).all(axis=1) & (df[ITEMS_ENDES] <= 3).all(axis=1)
    df = df[valido].copy()
    print(f"  con los 9 ítems válidos (0-3): {len(df):,}")

    # Chequeo de integridad: phq9_total debe ser la suma de los 9 ítems.
    suma = df[ITEMS_ENDES].sum(axis=1)
    coincide = int((suma == df.phq9_total).sum())
    print(f"  phq9_total == suma de ítems en {coincide:,}/{len(df):,} filas")
    if coincide != len(df):
        print("  ⚠ hay filas donde no coincide; se recalcula desde los ítems")
    df["phq9_total"] = suma

    df["at_risk"] = (df.phq9_total >= CORTE_MODERADO).astype(int)
    print(f"  at_risk (PHQ-9 >= {CORTE_MODERADO}): "
          f"{int(df.at_risk.sum())} de {len(df)} "
          f"({100 * df.at_risk.mean():.1f} %)")
    return df


def cargar_piloto(ruta: Path) -> pd.DataFrame | None:
    """Casos del piloto con la etiqueta ciega de la psicóloga."""
    if not ruta or not Path(ruta).exists():
        return None
    df = pd.read_csv(ruta)
    faltan = [c for c in ITEMS_SAMI + ["riesgo_clinico"] if c not in df]
    if faltan:
        print(f"  ⚠ el CSV del piloto no tiene {faltan}; se omite la "
              "validación externa")
        return None
    df = df.dropna(subset=ITEMS_SAMI + ["riesgo_clinico"]).copy()
    print(f"\nPiloto cargado: {len(df)} casos con etiqueta clínica")
    return df


# ════════════════════════════════════════════════════════════════════════════
# Métricas
# ════════════════════════════════════════════════════════════════════════════


def metricas(y, pred, proba=None) -> dict:
    P, R, F, _ = precision_recall_fscore_support(
        y, pred, average="macro", zero_division=0)
    cm = confusion_matrix(y, pred, labels=[0, 1])
    tn, fp, fn, tp = (int(v) for v in cm.ravel())
    d = {
        "n": int(len(y)),
        "accuracy": float(accuracy_score(y, pred)),
        "precision_macro": float(P),
        "recall_macro": float(R),
        "f1_macro": float(F),
        "kappa": float(cohen_kappa_score(y, pred)),
        "sensibilidad": tp / (tp + fn) if tp + fn else 0.0,
        "especificidad": tn / (tn + fp) if tn + fp else 0.0,
        "vpp": tp / (tp + fp) if tp + fp else 0.0,
        "vpn": tn / (tn + fn) if tn + fn else 0.0,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }
    if proba is not None and len(set(y)) > 1:
        d["roc_auc"] = float(roc_auc_score(y, proba))
    return d


def imprimir(titulo: str, m: dict, nota: str = "") -> None:
    print(f"\n{'=' * 70}\n{titulo}\n{'=' * 70}")
    if nota:
        print(f"  {nota}\n")
    print(f"  n               : {m['n']}")
    print(f"  Accuracy        : {m['accuracy']:.4f}")
    print(f"  Precision-macro : {m['precision_macro']:.4f}")
    print(f"  Recall-macro    : {m['recall_macro']:.4f}")
    print(f"  F1-MACRO        : {m['f1_macro']:.4f}")
    print(f"  Kappa de Cohen  : {m['kappa']:.4f}")
    if "roc_auc" in m:
        print(f"  ROC-AUC         : {m['roc_auc']:.4f}")
    print(f"  Sensibilidad    : {m['sensibilidad']:.4f}")
    print(f"  Especificidad   : {m['especificidad']:.4f}")
    print(f"  VPP / VPN       : {m['vpp']:.4f} / {m['vpn']:.4f}")
    print(f"  Matriz          : TN={m['tn']} FP={m['fp']} "
          f"FN={m['fn']} TP={m['tp']}")


# ════════════════════════════════════════════════════════════════════════════
# Principal
# ════════════════════════════════════════════════════════════════════════════


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endes", type=Path, default=None)
    ap.add_argument("--piloto", type=Path, default=None,
                    help="CSV del piloto con los 9 ítems PHQ-A + riesgo_clinico")
    args = ap.parse_args()

    MODELS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)

    df = cargar_endes(args.endes)
    X = df[ITEMS_ENDES].to_numpy(dtype=float)
    y = df.at_risk.to_numpy()

    # ── Entrenamiento ─────────────────────────────────────────────────────
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEMILLA)
    print(f"\nTrain {len(Xtr)} / Test {len(Xte)}")

    gs = buscador()
    gs.fit(Xtr, ytr)
    print(f"  hiperparámetros: {gs.best_params_}")

    pred_te = gs.predict(Xte)
    proba_te = gs.predict_proba(Xte)[:, 1]
    m_interno = metricas(yte, pred_te, proba_te)
    imprimir(
        "1. MÉTRICAS INTERNAS (ENDES held-out 20 %) — CIRCULARES",
        m_interno,
        "La etiqueta es `phq9_total >= 10` y phq9_total es la suma de las 9\n"
        "  features. Esto mide aproximación a una suma con umbral, NO\n"
        "  capacidad clínica. No reportar como validación del sistema.",
    )

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    cv = cross_val_score(buscador(), X, y, cv=skf, scoring="f1_macro", n_jobs=-1)
    print(f"\n  CV 5-fold F1-macro: {cv.mean():.4f} ± {cv.std():.4f}")

    # Modelo final sobre los 1,370
    final = buscador()
    final.fit(X, y)

    # ── Validación externa ────────────────────────────────────────────────
    externo = None
    comparacion: dict[str, dict] = {}
    permutaciones = None
    piloto = cargar_piloto(args.piloto) if args.piloto else None

    if piloto is not None:
        Xp = piloto[ITEMS_SAMI].to_numpy(dtype=float)
        yp = (piloto.riesgo_clinico.map(ORDEN_RIESGO) >= CORTE_ALERTA)
        yp = yp.astype(int).to_numpy()

        pred_p = final.predict(Xp)
        proba_p = final.predict_proba(Xp)[:, 1]
        externo = metricas(yp, pred_p, proba_p)
        imprimir(
            "2. VALIDACIÓN EXTERNA — contra el juicio ciego de la psicóloga",
            externo,
            "Entrenado en ENDES (1,370 adolescentes, etiqueta por corte).\n"
            "  Evaluado en el piloto (102 casos, etiqueta clínica humana).\n"
            "  Las etiquetas de test son independientes: NO es circular.",
        )

        # Baseline a: el corte publicado, aplicado directo
        phq_t = piloto[ITEMS_SAMI].sum(axis=1).to_numpy()
        comparacion["corte PHQ-A >= 10"] = metricas(
            yp, (phq_t >= CORTE_MODERADO).astype(int))

        # Baseline b: las reglas del EvaluatorService, si vienen en el CSV
        if "modelo_riesgo" in piloto:
            mr = piloto.modelo_riesgo.map(ORDEN_RIESGO)
            ok = mr.notna().to_numpy()
            comparacion["reglas EvaluatorService"] = metricas(
                yp[ok], (mr[ok] >= CORTE_ALERTA).astype(int).to_numpy())

        # Baseline c: SVM entrenado EN el piloto con las mismas 9 features,
        # LOOCV anidado. Es la comparación manzana-con-manzana.
        print("\n  Calculando SVM entrenado en el piloto (LOOCV, 9 features)…")
        loo_pred = cross_val_predict(
            buscador(cv=StratifiedKFold(5, shuffle=True, random_state=SEMILLA)),
            Xp, yp, cv=LeaveOneOut(), n_jobs=-1)
        comparacion["SVM entrenado en el piloto (LOOCV, 9 feats)"] = metricas(
            yp, loo_pred)

        print(f"\n{'=' * 70}\n3. COMPARACIÓN sobre los mismos 102 casos\n{'=' * 70}")
        print(f"  {'modelo':<46}{'F1-macro':>10}{'kappa':>8}{'Sens':>7}{'Espec':>7}")
        print(f"  {'SVM ENDES (este modelo)':<46}{externo['f1_macro']:>10.4f}"
              f"{externo['kappa']:>8.4f}{externo['sensibilidad']:>7.3f}"
              f"{externo['especificidad']:>7.3f}")
        for k, m in comparacion.items():
            print(f"  {k:<46}{m['f1_macro']:>10.4f}{m['kappa']:>8.4f}"
                  f"{m['sensibilidad']:>7.3f}{m['especificidad']:>7.3f}")

        # ── Sensibilidad al orden de los ítems ────────────────────────────
        # Si el mapeo QS700A..I -> PHQ-9 1..9 estuviera permutado, ¿cuánto
        # cambiaría? Si el modelo es en el fondo una suma, casi nada.
        rng = np.random.default_rng(SEMILLA)
        f1s = []
        for _ in range(200):
            perm = rng.permutation(9)
            f1s.append(f1_score(yp, final.predict(Xp[:, perm]),
                                average="macro", zero_division=0))
        permutaciones = {
            "n": 200,
            "f1_macro_media": float(np.mean(f1s)),
            "f1_macro_sd": float(np.std(f1s)),
            "f1_macro_min": float(np.min(f1s)),
            "f1_macro_max": float(np.max(f1s)),
            "f1_macro_orden_correcto": externo["f1_macro"],
        }
        print(f"\n{'=' * 70}\n4. SENSIBILIDAD al orden de los ítems "
              f"(200 permutaciones)\n{'=' * 70}")
        print(f"  orden asumido : {permutaciones['f1_macro_orden_correcto']:.4f}")
        print(f"  permutado     : {permutaciones['f1_macro_media']:.4f} ± "
              f"{permutaciones['f1_macro_sd']:.4f} "
              f"(min {permutaciones['f1_macro_min']:.3f} / "
              f"max {permutaciones['f1_macro_max']:.3f})")
        delta = (permutaciones["f1_macro_orden_correcto"]
                 - permutaciones["f1_macro_media"])
        print(f"  ventaja del orden correcto: {delta:+.4f}")
        print("  → si es cercana a 0, el modelo se apoya en la suma y el "
              "mapeo\n    de ítems no es crítico; si es grande, hay que "
              "confirmarlo con\n    el codebook de INEI antes de desplegar.")

    # ── Persistencia ──────────────────────────────────────────────────────
    meta = {
        "pipeline": final.best_estimator_,
        "features": ITEMS_ENDES,
        "features_sami": ITEMS_SAMI,
        "instrumento": "PHQ-9 / PHQ-A (9 ítems, escala 0-3)",
        "dataset": f"ENDES 2025 (INEI, Perú) — {EDAD_MIN}-{EDAD_MAX} años",
        "n_train": int(len(X)),
        "etiqueta": f"phq9_total >= {CORTE_MODERADO} (circular, ver docstring)",
        "kernel": final.best_params_["svc__kernel"],
        "best_params": final.best_params_,
        "cv_f1_macro_mean": float(cv.mean()),
        "cv_f1_macro_std": float(cv.std()),
        "metricas_internas_circulares": m_interno,
        "validacion_externa_piloto": externo,
        "comparacion_piloto": comparacion,
        "sensibilidad_permutacion": permutaciones,
        "semilla": SEMILLA,
    }
    ruta_modelo = MODELS_DIR / "svm_phq9.joblib"
    import joblib
    joblib.dump(meta, ruta_modelo)
    print(f"\nModelo guardado: {ruta_modelo.relative_to(ROOT)}")

    escribir_reporte(meta, df, piloto)


def escribir_reporte(meta: dict, endes: pd.DataFrame,
                     piloto: pd.DataFrame | None) -> None:
    m = meta["metricas_internas_circulares"]
    e = meta["validacion_externa_piloto"]
    L: list[str] = []
    A = L.append

    A("# SVM sobre PHQ-9 — ENDES 2025, adolescentes 15-17\n")
    A("## Qué cambió\n")
    A("Reemplaza al SVM de DASS-21, que pedía 21 ítems que Sami no recolecta")
    A("y por eso nunca emitió una predicción en producción "
      "(`etiqueta_caso.modelo_svm_clase`")
    A("estaba NULL en los 102 casos etiquetados). Este modelo usa los 9 ítems")
    A("del PHQ-9, que coinciden 1:1 con el PHQ-A del sistema.\n")

    A("## Datos\n")
    A(f"- Fuente: ENDES 2025 (INEI, Perú), microdatos públicos.")
    A(f"- Filtrado a {EDAD_MIN}-{EDAD_MAX} años: **n = {meta['n_train']:,}**.")
    A(f"- No hay casos de 13-14 años: el módulo QS700 se aplica desde los 15.")
    A(f"- Features: 9 ítems PHQ-9 (escala 0-3), sin variables derivadas.")
    A(f"- Etiqueta: `phq9_total >= {CORTE_MODERADO}` — "
      f"{int(endes.at_risk.sum())} de {len(endes)} "
      f"({100 * endes.at_risk.mean():.1f} %).\n")

    A("> **Advertencia metodológica.** `phq9_total` es la suma exacta de las 9")
    A("> features, así que la etiqueta es función determinista de la entrada.")
    A("> Las métricas internas de abajo miden aproximación a una suma con")
    A("> umbral, **no** capacidad clínica. La métrica válida es la validación")
    A("> externa contra el criterio de la psicóloga.\n")

    A("## 1. Métricas internas (ENDES held-out 20 %) — circulares\n")
    A("| Métrica | Valor |")
    A("| --- | --- |")
    for k, lbl in [("accuracy", "Accuracy"), ("precision_macro", "Precision-macro"),
                   ("recall_macro", "Recall-macro"), ("f1_macro", "F1-macro"),
                   ("kappa", "Kappa"), ("roc_auc", "ROC-AUC"),
                   ("sensibilidad", "Sensibilidad"),
                   ("especificidad", "Especificidad")]:
        if k in m:
            A(f"| {lbl} | {m[k]:.4f} |")
    A(f"| CV 5-fold F1-macro | {meta['cv_f1_macro_mean']:.4f} ± "
      f"{meta['cv_f1_macro_std']:.4f} |")
    A(f"\nHiperparámetros: `{meta['best_params']}`\n")

    if e:
        A("## 2. Validación externa — contra el juicio ciego de la psicóloga\n")
        A("Entrenado en ENDES, evaluado en los 102 casos del piloto con la")
        A("etiqueta clínica humana. **Las etiquetas de test son independientes")
        A("de las de entrenamiento: esta comparación no es circular.**\n")
        A("| Métrica | Valor |")
        A("| --- | --- |")
        for k, lbl in [("n", "n"), ("accuracy", "Accuracy"),
                       ("precision_macro", "Precision-macro"),
                       ("recall_macro", "Recall-macro"),
                       ("f1_macro", "F1-macro"), ("kappa", "Kappa de Cohen"),
                       ("roc_auc", "ROC-AUC"), ("sensibilidad", "Sensibilidad"),
                       ("especificidad", "Especificidad"), ("vpp", "VPP"),
                       ("vpn", "VPN")]:
            if k in e:
                v = e[k]
                A(f"| {lbl} | {v if k == 'n' else f'{v:.4f}'} |")
        A(f"\nMatriz: TN={e['tn']} FP={e['fp']} FN={e['fn']} TP={e['tp']}\n")

        A("## 3. Comparación sobre los mismos 102 casos\n")
        A("| Modelo | F1-macro | Kappa | Sens. | Espec. |")
        A("| --- | --- | --- | --- | --- |")
        A(f"| **SVM ENDES (este modelo)** | {e['f1_macro']:.4f} | "
          f"{e['kappa']:.4f} | {e['sensibilidad']:.3f} | "
          f"{e['especificidad']:.3f} |")
        for k, c in meta["comparacion_piloto"].items():
            A(f"| {k} | {c['f1_macro']:.4f} | {c['kappa']:.4f} | "
              f"{c['sensibilidad']:.3f} | {c['especificidad']:.3f} |")
        A("")

    p = meta.get("sensibilidad_permutacion")
    if p:
        A("## 4. Sensibilidad al orden de los ítems\n")
        A("Se asume que `QS700A..QS700I` son los ítems 1..9 del PHQ-9 en orden")
        A("estándar. Falta confirmarlo con el codebook de INEI. Esta prueba")
        A(f"mide cuánto importaría equivocarse ({p['n']} permutaciones):\n")
        A("| | F1-macro |")
        A("| --- | --- |")
        A(f"| Orden asumido | {p['f1_macro_orden_correcto']:.4f} |")
        A(f"| Permutado (media ± sd) | {p['f1_macro_media']:.4f} ± "
          f"{p['f1_macro_sd']:.4f} |")
        A(f"| Permutado (rango) | {p['f1_macro_min']:.3f} – "
          f"{p['f1_macro_max']:.3f} |")
        A("")

    A("## Fuente\n")
    A("> Instituto Nacional de Estadística e Informática (INEI). *Encuesta")
    A("> Demográfica y de Salud Familiar (ENDES) 2025* — microdatos públicos.")
    A("> Módulo de salud mental (cuestionario de salud, sección QS700, PHQ-9),")
    A("> aplicado a personas de 15 años y más.\n")

    destino = REPORTS_DIR / "svm_phq9_endes.md"
    destino.write_text("\n".join(L), encoding="utf-8")
    print(f"Reporte escrito : {destino.relative_to(ROOT)}")

    json_destino = REPORTS_DIR / "svm_phq9_endes.json"
    serial = {k: v for k, v in meta.items() if k != "pipeline"}
    json_destino.write_text(json.dumps(serial, indent=2, ensure_ascii=False),
                            encoding="utf-8")
    print(f"JSON escrito    : {json_destino.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
