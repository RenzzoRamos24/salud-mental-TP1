"""
Preparación del dataset PHQ-9 Student Depression (Mendeley).

Fuente:
    Miraz, Md Abdullah Ibne Aziz (2025). PHQ-9 Student Depression Dataset.
    Mendeley Data, DOI: 10.17632/kkzjk253cy.1. CC BY 4.0.
    https://data.mendeley.com/datasets/kkzjk253cy/1

Hace tres cosas:
  1. Carga el CSV crudo (`data/phq9_student_dataset.csv`).
  2. Mapea las respuestas Likert en texto a enteros 0-3 (formato del sistema).
  3. Mapea la severidad PHQ-9 a las 5 clases de Sami (SIN_RIESGO ... CRITICO).

El resultado se guarda como `data/phq9_prepared.csv` con columnas:
    phq_1 ... phq_9, phq_total, age, gender,
    sleep_quality, study_pressure, financial_pressure,
    riesgo (SIN_RIESGO | BAJO | MEDIO | ALTO | CRITICO)

Uso:
    venv/bin/python scripts/prepare_phq9_dataset.py
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "phq9_student_dataset.csv"
OUT = ROOT / "data" / "phq9_prepared.csv"


LIKERT_MAP = {
    "Not at all": 0,
    "Several days": 1,
    "More than half the days": 2,
    "Nearly every day": 3,
}

# PHQ-9 → escala Sami de riesgo (5 clases que el evaluator usa).
SEVERIDAD_MAP = {
    "Minimal": "SIN_RIESGO",
    "Mild": "BAJO",
    "Moderate": "MEDIO",
    "Moderately severe": "ALTO",
    "Severe": "CRITICO",
}

CTX_MAP = {"Good": 3, "Average": 2, "Bad": 1, "Worst": 0}


def normaliza_texto(s: str) -> str:
    return (s or "").strip()


def main() -> None:
    if not RAW.exists():
        raise SystemExit(
            f"No existe {RAW}. Descárgalo desde Mendeley con:\n"
            "  curl -sL 'https://data.mendeley.com/public-files/datasets/"
            "kkzjk253cy/files/9cef8428-3ca8-41c8-93db-7bd4e8855add/"
            "file_downloaded' -o data/phq9_student_dataset.csv"
        )

    print(f"Cargando {RAW.name}...")
    df = pd.read_csv(RAW)
    df.columns = [c.strip() for c in df.columns]

    # Renombrar a phq_1 ... phq_9 manteniendo el orden del PHQ-9 oficial.
    item_cols = [
        c for c in df.columns
        if c not in ("Age", "Gender", "PHQ_Total", "PHQ_Severity",
                     "Sleep Quality", "Study Pressure", "Financial Pressure")
    ]
    if len(item_cols) != 9:
        raise SystemExit(f"Esperaba 9 ítems PHQ-9; encontré {len(item_cols)}.")

    renames = {old: f"phq_{i+1}" for i, old in enumerate(item_cols)}
    df = df.rename(columns=renames)

    # Mapear Likert a 0-3
    for i in range(1, 10):
        col = f"phq_{i}"
        df[col] = df[col].map(lambda x: LIKERT_MAP.get(normaliza_texto(x)))
        if df[col].isna().any():
            faltantes = df[df[col].isna()][col].count()
            print(f"  ⚠ {col}: {faltantes} valores no mapeables; se eliminan.")
    df = df.dropna(subset=[f"phq_{i}" for i in range(1, 10)])
    for i in range(1, 10):
        df[f"phq_{i}"] = df[f"phq_{i}"].astype(int)

    # Mapear contexto a 0-3
    df["sleep_quality"] = df["Sleep Quality"].map(CTX_MAP)
    df["study_pressure"] = df["Study Pressure"].map(CTX_MAP)
    df["financial_pressure"] = df["Financial Pressure"].map(CTX_MAP)

    # Mapear severidad → Sami
    df["riesgo"] = df["PHQ_Severity"].str.strip().map(SEVERIDAD_MAP)
    if df["riesgo"].isna().any():
        sin_map = df[df["riesgo"].isna()]["PHQ_Severity"].unique()
        raise SystemExit(f"Severidades no mapeables: {sin_map}")

    out = pd.DataFrame({
        **{f"phq_{i}": df[f"phq_{i}"] for i in range(1, 10)},
        "phq_total": df["PHQ_Total"].astype(int),
        "age": df["Age"].astype(int),
        "gender": df["Gender"].str.strip(),
        "sleep_quality": df["sleep_quality"].astype(int),
        "study_pressure": df["study_pressure"].astype(int),
        "financial_pressure": df["financial_pressure"].astype(int),
        "riesgo": df["riesgo"],
    })

    OUT.parent.mkdir(exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"Guardado: {OUT}  (n={len(out)})")
    print("\nDistribución del target:")
    print(out["riesgo"].value_counts().to_string())
    print("\nPrimeras 3 filas:")
    print(out.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
