"""SVM clínico de Sami: 16 ítems (PHQ-A + GAD-7) → riesgo MEDIO o superior.

Por qué reemplaza al SVM de ENDES
---------------------------------
`train_svm_phq9_endes.py` entrena contra `phq9_total >= 10`, que es la suma de
sus propias features: el modelo resultante es matemáticamente la regla
"PHQ-A total >= 10" y no aporta nada sobre ella (métricas idénticas a 4
decimales; permutar los ítems no mueve el resultado). Este modelo entrena
contra el **criterio de la psicóloga**, que es información que no está en las
features. Por eso sí puede discrepar de los cortes, y de hecho discrepa.

Datos
-----
102 casos del piloto del colegio, etiquetados a ciegas por `SAMI-PSI-01`
(exportar con `scripts/exportar_casos_etiquetados.py`). Etiqueta binaria:
`riesgo_clinico >= MEDIO`. 55 en alerta, 47 fuera.

Features
--------
29 columnas: los 16 ítems crudos + 13 derivadas de reglas publicadas
(ver `app/services/svm_features.py`). `SelectKBest` elige k adentro de cada
fold. Con n=102 el modelo no puede inferir el PHQ-9, el GAD-7 y el DSM-5 solo;
se le dan calculados y los 102 casos se usan para lo que no está en los
manuales: cómo pondera *esta* psicóloga en *este* colegio.

Honestidad sobre la validación
------------------------------
Dos LOOCV, ambos con **cada predicción fuera de muestra**:

  A (principal) — familia 29 + SelectKBest; k, C, gamma y kernel se eligen
    con CV interna dentro del fold. Es el número del modelo que se guarda.
  B (control)   — además elige la *representación* (16 crudas / 13 derivadas /
    29 + SelectKBest) dentro del fold. Responde la objeción "elegiste las
    features mirando los 102 casos": si B no cae respecto de A, esa elección
    no estaba inflando nada.

Lo que **queda** por declarar: el conjunto de representaciones candidatas y la
rejilla de hiperparámetros se definieron tras explorar estos mismos 102 casos.
Es un sesgo de segundo orden que B no elimina; solo una cohorte nueva lo hace.

Limitaciones a declarar en la tesis
-----------------------------------
- n=102, **un solo** evaluador. Sin κ inter-evaluador (`SAMI-PSI-02` no
  etiquetó): no se sabe cuánto del acierto es "la psicóloga" y cuánto "el
  criterio clínico".
- Etiqueta binaria MEDIO+. La calibración en 5 niveles del sistema sigue mala
  (κ 0.121) y este modelo no la arregla: no la modela.
- No reemplaza al `EvaluatorService`. Las reglas tienen 0 falsos negativos en
  CRÍTICO y son auditables ítem por ítem; el SVM no. Va como segunda opinión.

Uso
---
    venv/bin/python scripts/train_svm_clinico.py --casos data/clinico/casos_etiquetados.csv
    venv/bin/python scripts/train_svm_clinico.py --casos ... --rapido   # salta el control B

Salidas
-------
    models/svm_clinico.joblib    pipeline (entrada: 16 ítems crudos) + metadatos
    reports/svm_clinico.md       reporte de métricas
    reports/svm_clinico.json     las mismas métricas, legibles por máquina
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import (accuracy_score, classification_report,
                             cohen_kappa_score, confusion_matrix,
                             precision_recall_fscore_support, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.svm_features import (  # noqa: E402
    ITEMS, NOMBRES_FEATURES, construir_features, derivar,
)

warnings.filterwarnings("ignore")

SEMILLA = 20261013
ORDEN_RIESGO = {"SIN_RIESGO": 0, "BAJO": 1, "MEDIO": 2, "ALTO": 3, "CRITICO": 4}
CORTE_ALERTA = "MEDIO"
N_BOOTSTRAP = 5000

GRID_SVC = {
    "svc__C": [0.1, 0.3, 1, 3, 10, 30],
    "svc__gamma": ["scale", 0.01, 0.03, 0.1],
    "svc__kernel": ["rbf", "linear"],
}
GRID_K = {"sel__k": [4, 6, 8, 12, 16, 20]}


def cv_interna() -> StratifiedKFold:
    return StratifiedKFold(5, shuffle=True, random_state=SEMILLA)


def pipeline_29() -> Pipeline:
    """La familia que se guarda: 16 crudas → 29 features → SelectKBest → SVC.

    El `FunctionTransformer` hace que el estimador entrenado reciba los 16
    ítems crudos, no las 29 features. Lo que se guarda es desplegable tal cual.
    """
    return Pipeline([
        ("feat", FunctionTransformer(construir_features)),
        ("sc", StandardScaler()),
        ("sel", SelectKBest(f_classif)),
        ("svc", SVC(class_weight="balanced", random_state=SEMILLA)),
    ])


def pipeline_crudas() -> Pipeline:
    return Pipeline([
        ("sc", StandardScaler()),
        ("svc", SVC(class_weight="balanced", random_state=SEMILLA)),
    ])


def pipeline_derivadas() -> Pipeline:
    return Pipeline([
        ("feat", FunctionTransformer(derivar)),
        ("sc", StandardScaler()),
        ("svc", SVC(class_weight="balanced", random_state=SEMILLA)),
    ])


# Las tres representaciones candidatas del control B. Todas reciben los 16
# ítems crudos, así que la elección entre ellas puede ocurrir dentro del fold.
CANDIDATAS: dict[str, tuple] = {
    "16 crudas": (pipeline_crudas, GRID_SVC),
    "13 derivadas": (pipeline_derivadas, GRID_SVC),
    "29 + SelectKBest": (pipeline_29, {**GRID_SVC, **GRID_K}),
}


def buscar(fabrica, grid) -> GridSearchCV:
    return GridSearchCV(fabrica(), grid, scoring="f1_macro", cv=cv_interna(),
                        n_jobs=1)


class SelectorAnidado(BaseEstimator, ClassifierMixin):
    """Elige representación + hiperparámetros viendo solo el entrenamiento."""

    def fit(self, X, y):
        mejor = -np.inf
        self.elegida_, self.modelo_ = None, None
        for nombre, (fabrica, grid) in CANDIDATAS.items():
            g = buscar(fabrica, grid)
            g.fit(X, y)
            if g.best_score_ > mejor:
                mejor, self.elegida_, self.modelo_ = g.best_score_, nombre, g
        self.classes_ = np.array([0, 1])
        return self

    def predict(self, X):
        return self.modelo_.predict(X)

    def decision_function(self, X):
        return self.modelo_.decision_function(X)


def metricas(y_true, pred, dec=None) -> dict:
    P, R, F, _ = precision_recall_fscore_support(y_true, pred, average="macro",
                                                 zero_division=0)
    tn, fp, fn, tp = (int(v) for v in
                      confusion_matrix(y_true, pred, labels=[0, 1]).ravel())
    m = {
        "f1_macro": float(F), "precision_macro": float(P),
        "recall_macro": float(R), "accuracy": float(accuracy_score(y_true, pred)),
        "kappa": float(cohen_kappa_score(y_true, pred)),
        "sensibilidad": tp / (tp + fn) if tp + fn else 0.0,
        "especificidad": tn / (tn + fp) if tn + fp else 0.0,
        "vpp": tp / (tp + fp) if tp + fp else 0.0,
        "vpn": tn / (tn + fn) if tn + fn else 0.0,
        "falsos_negativos": fn, "falsos_positivos": fp,
        "verdaderos_positivos": tp, "verdaderos_negativos": tn,
    }
    if dec is not None:
        m["roc_auc"] = float(roc_auc_score(y_true, dec))
    return m


def imprimir(titulo: str, y_true, pred, m: dict) -> None:
    print(f"\n{'-' * 78}\n{titulo}\n{'-' * 78}")
    print(classification_report(y_true, pred, digits=4, zero_division=0,
                                target_names=["no_alerta", "alerta"]))
    print(f"  F1-MACRO        : {m['f1_macro']:.4f}")
    print(f"  Kappa de Cohen  : {m['kappa']:.4f}")
    print(f"  Accuracy        : {m['accuracy']:.4f}")
    if "roc_auc" in m:
        print(f"  ROC-AUC         : {m['roc_auc']:.4f}")
    print(f"  Sensibilidad    : {m['sensibilidad']:.4f}")
    print(f"  Especificidad   : {m['especificidad']:.4f}")
    print(f"  VPP / VPN       : {m['vpp']:.4f} / {m['vpn']:.4f}")
    print(f"  FN / FP         : {m['falsos_negativos']} / "
          f"{m['falsos_positivos']}")


def loocv(estimador_fabrica, X, y, n_jobs: int, con_eleccion: bool = False):
    """LOOCV manual: una sola pasada devuelve predicción, margen y elección."""
    def vuelta(i: int):
        # Los workers de loky no heredan los filtros del proceso padre.
        warnings.filterwarnings("ignore")
        tr = np.delete(np.arange(len(y)), i)
        est = estimador_fabrica()
        est.fit(X[tr], y[tr])
        xi = X[i:i + 1]
        elegida = getattr(est, "elegida_", None) if con_eleccion else None
        return (int(est.predict(xi)[0]), float(est.decision_function(xi)[0]),
                elegida)

    salida = Parallel(n_jobs=n_jobs)(delayed(vuelta)(i) for i in range(len(y)))
    return (np.array([s[0] for s in salida]),
            np.array([s[1] for s in salida]),
            [s[2] for s in salida])


def bootstrap_pareado(y, pred_a, pred_b, n: int = N_BOOTSTRAP) -> dict:
    """Diferencia de F1-macro entre dos predictores, remuestreando los casos."""
    rng = np.random.default_rng(SEMILLA)
    d = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2:
            continue
        fa = precision_recall_fscore_support(y[i], pred_a[i], average="macro",
                                            zero_division=0)[2]
        fb = precision_recall_fscore_support(y[i], pred_b[i], average="macro",
                                            zero_division=0)[2]
        d.append(fa - fb)
    d = np.array(d)
    return {"delta_medio": float(d.mean()),
            "ic95": [float(np.percentile(d, 2.5)),
                     float(np.percentile(d, 97.5))],
            "gana_pct": float(100 * (d > 0).mean()),
            "n_remuestreos": int(len(d))}


def cargar(csv: Path):
    p = pd.read_csv(csv)
    faltan = [c for c in ITEMS if c not in p.columns]
    if faltan:
        sys.exit(f"El CSV no tiene las columnas de ítems: {faltan}")
    incompletos = p[p[ITEMS].isna().any(axis=1)]
    if len(incompletos):
        print(f"  descartados por ítems faltantes: {len(incompletos)} "
              f"({list(incompletos.aplicacion_id)})")
        p = p.dropna(subset=ITEMS).reset_index(drop=True)
    desconocidas = set(p.riesgo_clinico) - set(ORDEN_RIESGO)
    if desconocidas:
        sys.exit(f"Niveles de riesgo no reconocidos: {desconocidas}")
    X = p[ITEMS].to_numpy(dtype=float)
    y = (p.riesgo_clinico.map(ORDEN_RIESGO)
         >= ORDEN_RIESGO[CORTE_ALERTA]).astype(int).to_numpy()
    reglas = (p.modelo_riesgo.map(ORDEN_RIESGO)
              >= ORDEN_RIESGO[CORTE_ALERTA]).astype(int).to_numpy()
    return p, X, y, reglas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--casos", type=Path, required=True,
                    help="CSV de scripts/exportar_casos_etiquetados.py")
    ap.add_argument("--rapido", action="store_true",
                    help="salta el control B (elección de representación anidada)")
    ap.add_argument("--n-jobs", type=int, default=-1)
    args = ap.parse_args()

    print("=" * 78)
    print("SVM CLÍNICO — 16 ítems (PHQ-A + GAD-7) → riesgo MEDIO o superior")
    print("=" * 78)
    p, X, y, reglas = cargar(args.casos)
    print(f"  casos                 : {len(y)}")
    print(f"  en alerta (MEDIO+)    : {int(y.sum())}")
    print(f"  fuera de alerta       : {int((y == 0).sum())}")
    print(f"  features              : {len(NOMBRES_FEATURES)} "
          f"({len(ITEMS)} crudas + {len(NOMBRES_FEATURES) - len(ITEMS)} derivadas)")

    # ── A: validación principal ───────────────────────────────────────────
    print("\n[A] LOOCV, familia 29 + SelectKBest (k/C/gamma elegidos dentro)…")
    pred_a, dec_a, _ = loocv(lambda: buscar(pipeline_29, {**GRID_SVC, **GRID_K}),
                             X, y, args.n_jobs)
    m_a = metricas(y, pred_a, dec_a)
    imprimir("[A] PRINCIPAL — cada predicción fuera de muestra (n=%d)" % len(y),
             y, pred_a, m_a)

    # ── B: control de la elección de features ─────────────────────────────
    m_b, elecciones = None, []
    if args.rapido:
        print("\n[B] saltado (--rapido)")
    else:
        print("\n[B] LOOCV eligiendo también la representación dentro del fold…"
              "\n    (lento: entrena las 3 familias en cada una de las "
              f"{len(y)} vueltas)")
        pred_b, dec_b, elecciones = loocv(SelectorAnidado, X, y, args.n_jobs,
                                          con_eleccion=True)
        m_b = metricas(y, pred_b, dec_b)
        imprimir("[B] CONTROL — la representación también se elige dentro",
                 y, pred_b, m_b)
        print("\n  Representación elegida, por vuelta:")
        for nombre, c in pd.Series(elecciones).value_counts().items():
            print(f"    {nombre:<20} {c:3d} vueltas  "
                  f"({100 * c / len(elecciones):.1f} %)")
        delta = m_a["f1_macro"] - m_b["f1_macro"]
        print(f"\n  A - B = {delta:+.4f} F1-macro. "
              f"{'B no cae: la elección de features no estaba inflando.' if delta <= 0.01 else 'B cae: reportar B, no A.'}")

    # ── Referencia: las reglas del EvaluatorService ────────────────────────
    m_reglas = metricas(y, reglas)
    imprimir("REFERENCIA — reglas del EvaluatorService (no entrenadas)",
             y, reglas, m_reglas)

    comparacion = bootstrap_pareado(y, pred_a, reglas)
    print(f"\n  Bootstrap pareado ({comparacion['n_remuestreos']} remuestreos), "
          "SVM - reglas:")
    print(f"    delta F1-macro {comparacion['delta_medio']:+.4f}  "
          f"IC95 [{comparacion['ic95'][0]:+.4f}, {comparacion['ic95'][1]:+.4f}]"
          f"  gana {comparacion['gana_pct']:.1f} %")

    # ── Dónde discrepan ───────────────────────────────────────────────────
    dif = np.where(pred_a != reglas)[0]
    discrepancias = []
    print(f"\n  Casos donde el SVM y las reglas discrepan: {len(dif)}")
    print(f"  {'caso':>6} {'psicóloga':>10} {'svm':>4} {'reglas':>7} "
          f"{'ítem9':>6} {'phq':>4} {'gad':>4}  acierta")
    for i in dif:
        acierta = "SVM" if pred_a[i] == y[i] else "reglas"
        fila = {"aplicacion_id": int(p.aplicacion_id[i]),
                "psicologa": p.riesgo_clinico[i], "svm": int(pred_a[i]),
                "reglas": int(reglas[i]), "item9": int(X[i, 8]),
                "phq_total": int(X[i, :9].sum()), "gad_total": int(X[i, 9:].sum()),
                "acierta": acierta}
        discrepancias.append(fila)
        print(f"  {fila['aplicacion_id']:>6} {fila['psicologa']:>10} "
              f"{fila['svm']:>4} {fila['reglas']:>7} {fila['item9']:>6} "
              f"{fila['phq_total']:>4} {fila['gad_total']:>4}  {acierta}")

    # ── Modelo final: la familia A sobre los 102 ───────────────────────────
    print("\nAjustando el modelo final sobre los 102 casos…")
    final = buscar(pipeline_29, {**GRID_SVC, **GRID_K})
    final.fit(X, y)
    print(f"  hiperparámetros: {final.best_params_}")

    sel = final.best_estimator_.named_steps["sel"]
    elegidas = [NOMBRES_FEATURES[j] for j in np.where(sel.get_support())[0]]
    print(f"  features elegidas ({len(elegidas)} de {len(NOMBRES_FEATURES)}): "
          f"{', '.join(elegidas)}")

    importancia = sorted(zip(NOMBRES_FEATURES,
                             SelectKBest(f_classif, k="all")
                             .fit(construir_features(X), y).scores_),
                         key=lambda t: -t[1])

    meta = {
        "pipeline": final.best_estimator_,
        "entrada": ITEMS,
        "features": NOMBRES_FEATURES,
        "features_elegidas": elegidas,
        "modulo_features": "app.services.svm_features.construir_features",
        "etiqueta": f"criterio de la psicóloga: riesgo_clinico >= {CORTE_ALERTA}",
        "dataset": f"piloto colegio, n={len(y)}, evaluador único (SAMI-PSI-01)",
        "n_train": int(len(y)),
        "best_params": final.best_params_,
        "validacion_principal_loocv": m_a,
        "validacion_control_representacion_anidada": m_b,
        "elecciones_control": (dict(pd.Series(elecciones).value_counts())
                               if elecciones else None),
        "reglas_evaluator": m_reglas,
        "svm_vs_reglas_bootstrap": comparacion,
        "discrepancias": discrepancias,
        "importancia_anova": [[n, float(f)] for n, f in importancia],
        "semilla": SEMILLA,
        "entrenado_en": datetime.now().isoformat(timespec="seconds"),
    }

    (ROOT / "models").mkdir(exist_ok=True)
    import joblib
    ruta = ROOT / "models" / "svm_clinico.joblib"
    joblib.dump(meta, ruta)
    print(f"\nModelo guardado: {ruta.relative_to(ROOT)}")

    escribir_reporte(meta)


def escribir_reporte(meta: dict) -> None:
    m_a = meta["validacion_principal_loocv"]
    m_b = meta["validacion_control_representacion_anidada"]
    m_r = meta["reglas_evaluator"]
    c = meta["svm_vs_reglas_bootstrap"]
    n = meta["n_train"]

    def tabla(m: dict) -> str:
        return (f"| F1-macro | {m['f1_macro']:.4f} |\n"
                f"| κ de Cohen | {m['kappa']:.4f} |\n"
                f"| Accuracy | {m['accuracy']:.4f} |\n"
                + (f"| ROC-AUC | {m['roc_auc']:.4f} |\n" if "roc_auc" in m else "")
                + f"| Sensibilidad | {m['sensibilidad']:.4f} |\n"
                f"| Especificidad | {m['especificidad']:.4f} |\n"
                f"| VPP / VPN | {m['vpp']:.4f} / {m['vpn']:.4f} |\n"
                f"| Falsos negativos | {m['falsos_negativos']} |\n"
                f"| Falsos positivos | {m['falsos_positivos']} |\n")

    L = [
        "# SVM clínico — PHQ-A + GAD-7 → riesgo MEDIO o superior", "",
        f"Entrenado el {meta['entrenado_en']}. "
        f"Reproducir: `venv/bin/python scripts/train_svm_clinico.py --casos <csv>`.",
        "",
        "## Qué es",
        "",
        "Primer modelo de Sami entrenado contra **criterio clínico humano** y no",
        "contra el corte de un instrumento. Entrada: los 16 ítems que el sistema",
        "ya recolecta (PHQ-A 1..9 y GAD-7 1..7, escala 0-3). Salida: si el caso",
        "cae en zona de alerta (riesgo MEDIO o superior según la psicóloga).",
        "",
        f"- **Datos**: {meta['dataset']}.",
        f"- **Etiqueta**: {meta['etiqueta']}.",
        f"- **Features**: {len(meta['features'])} "
        f"({len(meta['entrada'])} ítems crudos + 13 derivadas de reglas "
        "publicadas, ver `app/services/svm_features.py`).",
        f"- **Hiperparámetros**: `{meta['best_params']}`.",
        f"- **Features que sobreviven a SelectKBest**: "
        f"{', '.join(meta['features_elegidas'])}.",
        "",
        "A diferencia del SVM de ENDES, la etiqueta **no** es función de las",
        "features: la psicóloga aporta información que no está en los puntajes.",
        "Por eso el modelo puede discrepar de los cortes, y discrepa.",
        "",
        f"## Validación principal — LOOCV anidado (n={n})", "",
        "Cada una de las predicciones es fuera de muestra: `k`, `C`, `gamma` y",
        "`kernel` se eligen con CV interna sobre el entrenamiento del fold, y el",
        "caso evaluado no participa de esa elección.", "",
        "| Métrica | Valor |", "|---|---|", tabla(m_a).rstrip(), "",
    ]

    if m_b:
        L += [
            "## Control — ¿y si las features también se eligen adentro?", "",
            "La objeción natural: el conjunto de features se eligió mirando estos",
            "mismos casos. Para medirlo, se repite el LOOCV dejando que el",
            "procedimiento elija **también la representación** (16 crudas / 13",
            "derivadas / 29 + SelectKBest) dentro de cada fold.", "",
            "| Métrica | Valor |", "|---|---|", tabla(m_b).rstrip(), "",
            "Elección por vuelta:", "",
        ]
        for nombre, cnt in (meta["elecciones_control"] or {}).items():
            L.append(f"- `{nombre}`: {cnt} de {n} vueltas "
                     f"({100 * cnt / n:.1f} %)")
        delta = m_a["f1_macro"] - m_b["f1_macro"]
        L += [
            "",
            f"**A − B = {delta:+.4f} F1-macro.** " + (
                "El control no cae, así que fijar las features por criterio "
                "clínico no estaba inflando el resultado: el procedimiento "
                "llega al mismo lugar eligiéndolas a ciegas."
                if delta <= 0.01 else
                "El control cae: el número a reportar es el del control, no el "
                "principal."),
            "",
            "Lo que el control **no** elimina: el conjunto de representaciones",
            "candidatas y la rejilla de hiperparámetros se definieron tras",
            "explorar estos 102 casos. Es un sesgo de segundo orden que solo una",
            "cohorte nueva descarta. Declararlo en la tesis.",
            "",
        ]

    L += [
        "## Referencia — las reglas del EvaluatorService", "",
        "Las reglas no se entrenan: son los cortes publicados más las banderas",
        "de crisis. Son la línea base que hay que superar para justificar un",
        "modelo.", "",
        "| Métrica | Valor |", "|---|---|", tabla(m_r).rstrip(), "",
        "### SVM contra reglas, bootstrap pareado", "",
        f"Sobre {c['n_remuestreos']} remuestreos de los {n} casos:", "",
        f"- Δ F1-macro medio: **{c['delta_medio']:+.4f}**",
        f"- IC 95 %: [{c['ic95'][0]:+.4f}, {c['ic95'][1]:+.4f}]",
        f"- El SVM gana en **{c['gana_pct']:.1f} %** de los remuestreos",
        "",
        ("El intervalo no cruza cero: la ventaja no se explica por azar de "
         "muestreo." if c["ic95"][0] > 0 else
         "El intervalo cruza cero: la ventaja no es distinguible del azar."),
        "",
        f"### Dónde discrepan ({len(meta['discrepancias'])} casos)", "",
        "| caso | psicóloga | SVM | reglas | ítem 9 | PHQ-A | GAD-7 | acierta |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for d in meta["discrepancias"]:
        L.append(f"| {d['aplicacion_id']} | {d['psicologa']} | {d['svm']} | "
                 f"{d['reglas']} | {d['item9']} | {d['phq_total']} | "
                 f"{d['gad_total']} | {d['acierta']} |")

    L += [
        "",
        "## Qué features pesan (F de ANOVA, sobre los 102 casos)", "",
        "| feature | F |", "|---|---|",
    ]
    for nombre, f in meta["importancia_anova"][:12]:
        L.append(f"| `{nombre}` | {f:.2f} |")

    L += [
        "",
        "## Limitaciones a declarar", "",
        f"1. **n={n} y un solo evaluador.** Sin κ inter-evaluador "
        "(`SAMI-PSI-02` no etiquetó), no se puede separar \"acierta el criterio "
        "clínico\" de \"reproduce a esta psicóloga\".",
        "2. **Etiqueta binaria.** La calibración en 5 niveles del sistema sigue "
        "mala (κ 0.121); este modelo no la modela y por lo tanto no la arregla.",
        "3. **No reemplaza al `EvaluatorService`.** Las reglas tienen 0 falsos "
        "negativos en CRÍTICO y son auditables ítem por ítem; el SVM no es "
        "explicable al mismo nivel. El uso previsto es segunda opinión, con las "
        "reglas conservando la decisión de derivación.",
        "4. **Sesgo de selección de segundo orden** (ver el control, arriba).",
        "5. **Sin validación temporal ni en otra institución.** Los 102 casos "
        "son una cohorte, un colegio, un momento.",
        "",
    ]

    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "svm_clinico.md").write_text("\n".join(L) + "\n",
                                                     encoding="utf-8")
    serial = {k: v for k, v in meta.items() if k != "pipeline"}
    serial["elecciones_control"] = ({str(k): int(v) for k, v in
                                     (meta["elecciones_control"] or {}).items()}
                                    or None)
    (ROOT / "reports" / "svm_clinico.json").write_text(
        json.dumps(serial, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8")
    print("Reporte guardado: reports/svm_clinico.md (+ .json)")


if __name__ == "__main__":
    main()
