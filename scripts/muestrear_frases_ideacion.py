"""
Muestreo estratificado de frases del Pack C para etiquetado clínico ciego.

Objetivo
--------
Construir el ground truth de ideación suicida que falta para poder reportar
recall en el paper (ver TABLAS_TESIS.md:105 — "No existe un ground truth
clínico frase a frase para este corpus").

Salidas
-------
docs/piloto_colegio/etiquetado_ideacion/frases_para_etiquetar.csv
    CSV CIEGO que se le entrega a la psicóloga. Columnas:
    id, texto, ideacion_presente, confianza.
    NO contiene scores de BETO, ni categoría dominante, ni estrato, ni el
    orden original — a propósito. Si la etiquetadora ve la predicción del
    modelo, el ground truth queda contaminado y el recall deja de ser una
    validación independiente.

docs/piloto_colegio/etiquetado_ideacion/_clave_muestra.json
    Clave privada id → (app_id, numero, área, estímulo, respuesta, estrato,
    scores actuales de BETO, peso de muestreo). NO SE ENTREGA. La necesita
    `scripts/eval_ideacion_recall.py` para cruzar las etiquetas.

Diseño del muestreo
-------------------
Muestreo estratificado sin reposición sobre las 510 frases, con semilla fija.
Los estratos evitan que la muestra sea solo "lo que BETO ya marcó alto", que
sesgaría el ground truth hacia los aciertos del modelo:

  clinica_alta      max(depresion, ansiedad) >= 0.40
  clinica_media     0.25 <= max(depresion, ansiedad) < 0.40
  benigna_confiada  domina 'adaptativo'/'neutral' con score >= 0.55
  baja_todas        ningún score llega a 0.40 (el modelo no se compromete)
  aleatoria_simple  sorteo simple sobre todo lo que quedó fuera

Los pesos (N_estrato / n_muestreado) quedan guardados para poder proyectar
las métricas al corpus completo además de reportarlas sobre la muestra.

Uso
---
    venv/bin/python -m scripts.muestrear_frases_ideacion
    venv/bin/python -m scripts.muestrear_frases_ideacion --n 120 --seed 7
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sqlite3
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "mental_health.db"
OUT_DIR = ROOT / "docs" / "piloto_colegio" / "etiquetado_ideacion"

# Cuotas por estrato (se recortan si el estrato tiene menos frases).
CUOTAS = {
    "clinica_alta": 30,
    "clinica_media": 15,
    "benigna_confiada": 20,
    "baja_todas": 15,
    "aleatoria_simple": 20,
}

CLINICAS = ("depresion", "ansiedad")
NO_CLINICAS = ("adaptativo", "neutral")


def cargar_frases(db_path: Path) -> list[dict]:
    """Lee las frases del Pack C con los scores que BETO dejó en resultado_json."""
    con = sqlite3.connect(db_path)
    filas = con.execute(
        """
        SELECT a.id, a.resultado_json
        FROM aplicacion_cuestionario a
        JOIN plantilla_cuestionario p ON p.id = a.plantilla_id
        WHERE p.nombre LIKE '%Pack C%'
        ORDER BY a.id
        """
    ).fetchall()
    con.close()

    frases = []
    for app_id, rj in filas:
        if not rj:
            continue
        for f in json.loads(rj).get("frases", []):
            scores = f.get("scores") or {}
            respuesta = (f.get("respuesta") or "").strip()
            if not scores or not respuesta:
                continue
            frases.append({
                "app_id": app_id,
                "numero": f.get("numero"),
                "area": f.get("area"),
                "estimulo": (f.get("pregunta") or "").strip(),
                "respuesta": respuesta,
                "scores": {k: float(v) for k, v in scores.items()},
                "dominante": f.get("dominante"),
                "crisis_actual": bool(f.get("crisis")),
            })
    return frases


def estratificar(frases: list[dict]) -> dict[str, list[dict]]:
    estratos: dict[str, list[dict]] = {k: [] for k in CUOTAS}
    for f in frases:
        s = f["scores"]
        max_clin = max(s.get(k, 0.0) for k in CLINICAS)
        max_todas = max(s.values())
        dom = f["dominante"]
        if max_clin >= 0.40:
            estratos["clinica_alta"].append(f)
        elif max_clin >= 0.25:
            estratos["clinica_media"].append(f)
        elif dom in NO_CLINICAS and s.get(dom, 0.0) >= 0.55:
            estratos["benigna_confiada"].append(f)
        elif max_todas < 0.40:
            estratos["baja_todas"].append(f)
        else:
            estratos["aleatoria_simple"].append(f)
    return estratos


def clave_texto(f: dict) -> tuple[str, str]:
    """Identidad textual: mismo estímulo + misma respuesta = frase idéntica."""
    norm = lambda t: unicodedata.normalize("NFKC", t).strip().lower()
    return (norm(f["estimulo"]), norm(f["respuesta"]))


def muestrear(estratos: dict[str, list[dict]], n_total: int, rng: random.Random):
    """Sortea sin reposición, evitando frases textualmente idénticas."""
    escala = n_total / sum(CUOTAS.values())
    vistos: set[tuple[str, str]] = set()
    muestra: list[dict] = []
    resumen = {}

    for nombre, cuota in CUOTAS.items():
        pool = list(estratos[nombre])
        rng.shuffle(pool)
        objetivo = max(1, round(cuota * escala)) if pool else 0
        elegidas = []
        for f in pool:
            if len(elegidas) >= objetivo:
                break
            k = clave_texto(f)
            if k in vistos:
                continue          # no gastamos etiquetas en frases repetidas
            vistos.add(k)
            f = dict(f, estrato=nombre)
            elegidas.append(f)
        muestra.extend(elegidas)
        resumen[nombre] = {
            "N_estrato": len(pool),
            "n_muestreado": len(elegidas),
            # Peso para proyectar la muestra al corpus de 510 frases.
            "peso": round(len(pool) / len(elegidas), 4) if elegidas else None,
        }
    return muestra, resumen


def asignar_ids(muestra: list[dict], rng: random.Random) -> list[dict]:
    """
    IDs opacos y desordenados: el orden del CSV no debe dejar ver qué frases
    vinieron del mismo alumno ni en qué orden se respondieron.
    """
    codigos = rng.sample(range(1000, 10000), len(muestra))
    for f, c in zip(muestra, codigos):
        f["id"] = f"F-{c}"
    # Orden final por id → cualquier rastro del orden original desaparece.
    return sorted(muestra, key=lambda f: f["id"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100, help="tamaño objetivo de la muestra")
    ap.add_argument("--seed", type=int, default=20260910)
    ap.add_argument("--db", type=Path, default=DB)
    args = ap.parse_args()

    if not args.db.exists():
        raise SystemExit(f"No encuentro la base {args.db}")

    rng = random.Random(args.seed)
    frases = cargar_frases(args.db)
    print(f"Frases del Pack C con score de BETO: {len(frases)}")

    estratos = estratificar(frases)
    for nombre, pool in estratos.items():
        print(f"  {nombre:18s} N={len(pool):4d}")

    muestra, resumen = muestrear(estratos, args.n, rng)
    muestra = asignar_ids(muestra, rng)
    print(f"\nMuestra final: {len(muestra)} frases")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── CSV ciego para la psicóloga ────────────────────────────────────
    csv_path = OUT_DIR / "frases_para_etiquetar.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "texto", "ideacion_presente", "confianza"])
        for f in muestra:
            # La frase completa (estímulo + lo que escribió el alumno) es la
            # unidad clínica: "duermo" a secas no se puede juzgar.
            texto = f"{f['estimulo']} {f['respuesta']}".strip()
            w.writerow([f["id"], texto, "", ""])
    print(f"CSV ciego  → {csv_path}")

    # ── Clave privada ─────────────────────────────────────────────────
    clave_path = OUT_DIR / "_clave_muestra.json"
    clave_path.write_text(json.dumps({
        "semilla": args.seed,
        "n_corpus": len(frases),
        "n_muestra": len(muestra),
        "estratos": resumen,
        "advertencia": (
            "ARCHIVO PRIVADO. No entregar a la persona que etiqueta: contiene "
            "las predicciones de BETO."
        ),
        "frases": [
            {
                "id": f["id"],
                "app_id": f["app_id"],
                "numero": f["numero"],
                "area": f["area"],
                "estrato": f["estrato"],
                "estimulo": f["estimulo"],
                "respuesta": f["respuesta"],
                "scores_actuales": f["scores"],
                "dominante_actual": f["dominante"],
                "crisis_actual": f["crisis_actual"],
            }
            for f in muestra
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Clave privada → {clave_path}  (NO enviar)")

    print("\nComposición de la muestra:")
    for nombre, r in resumen.items():
        print(f"  {nombre:18s} n={r['n_muestreado']:3d} de N={r['N_estrato']:4d}"
              f"   peso={r['peso']}")


if __name__ == "__main__":
    main()
