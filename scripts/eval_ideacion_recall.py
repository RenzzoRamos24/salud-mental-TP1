"""
Recall de ideación suicida de BETO contra el ground truth clínico.

Entrada
-------
1. El CSV que devolvió la psicóloga, con la columna `ideacion_presente`
   llena (1/0) y opcionalmente `confianza` (alta/media/baja).
2. La clave privada `_clave_muestra.json` que generó
   `scripts/muestrear_frases_ideacion.py` (mapea id → frase + scores).

Qué calcula
-----------
Matriz de confusión (TP/FP/TN/FN) y recall en dos configuraciones del
clasificador, para poder reportar la del piloto y la vigente:

  (a) CONFIG PILOTO — la que corrió sobre el Pack C el 2026-07-02.
      8 hipótesis, `multi_label=True` (sigmoide independiente por hipótesis),
      bandera de crisis = score de `ideacion_suicida` >= 0.40.
      Las constantes se extraen del commit dd4df28 (anterior a 6850641,
      que eliminó la categoría), así que no dependen de mi transcripción.
      Requiere re-ejecutar el modelo: ~3-4 min en CPU para 100 frases.

  (b) CONFIG ACTUAL — 4 hipótesis, `multi_label=False` (softmax),
      bandera de crisis = `depresion` domina Y score >= 0.55.
      Sale de los scores ya guardados en `resultado_json`; no re-ejecuta nada.
      Se reporta además la variante sin regla de dominancia
      (`depresion` >= 0.55 a secas), que es como suele describirse el umbral.

Advertencia de muestreo
-----------------------
La muestra es ESTRATIFICADA, no aleatoria simple. Sobre la muestra, el recall
es interpretable pero la prevalencia y el PPV están inflados (los estratos
clínicos están sobre-representados a propósito). Por eso se reportan también
las métricas proyectadas al corpus de 510 frases con los pesos del muestreo.
Para el paper: citar recall de la muestra y PPV/prevalencia proyectados.

Uso
---
    # Solo config actual (rápido, sin cargar el modelo)
    venv/bin/python -m scripts.eval_ideacion_recall --etiquetas ruta/al.csv --solo-actual

    # Las dos configuraciones
    venv/bin/python -m scripts.eval_ideacion_recall --etiquetas ruta/al.csv

    # Excluir las frases que la psicóloga marcó con confianza baja
    venv/bin/python -m scripts.eval_ideacion_recall --etiquetas ruta/al.csv --min-confianza media

    # Análisis de sensibilidad: puntuar la frase completa (estímulo + respuesta)
    # en vez de solo la respuesta, que es lo único que vio BETO en producción.
    venv/bin/python -m scripts.eval_ideacion_recall --etiquetas ruta/al.csv --texto-completo
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "piloto_colegio" / "etiquetado_ideacion"
CLAVE = OUT_DIR / "_clave_muestra.json"
REPORTS = ROOT / "reports"

COMMIT_CONFIG_PILOTO = "dd4df28"   # último estado con `ideacion_suicida`
UMBRAL_ACTUAL_CRISIS = 0.55
ORDEN_CONFIANZA = {"baja": 0, "media": 1, "alta": 2}


# ── Carga de etiquetas ────────────────────────────────────────────────────

def leer_etiquetas(path: Path, min_confianza: str | None) -> dict[str, dict]:
    with path.open(encoding="utf-8-sig") as fh:
        filas = list(csv.DictReader(fh))
    if not filas:
        raise SystemExit(f"{path} está vacío.")
    faltan = {"id", "ideacion_presente"} - set(filas[0])
    if faltan:
        raise SystemExit(f"Al CSV le faltan columnas: {sorted(faltan)}")

    etiquetas, sin_etiquetar, descartadas, invalidas = {}, [], [], []
    for r in filas:
        fid = (r.get("id") or "").strip()
        crudo = (r.get("ideacion_presente") or "").strip().lower()
        conf = (r.get("confianza") or "").strip().lower()
        if not crudo:
            sin_etiquetar.append(fid)
            continue
        if crudo in ("1", "si", "sí", "s", "true", "x"):
            y = 1
        elif crudo in ("0", "no", "n", "false"):
            y = 0
        else:
            invalidas.append((fid, crudo))
            continue
        if min_confianza and conf:
            if ORDEN_CONFIANZA.get(conf, -1) < ORDEN_CONFIANZA[min_confianza]:
                descartadas.append(fid)
                continue
        etiquetas[fid] = {"y": y, "confianza": conf or None}

    if invalidas:
        print(f"  ! {len(invalidas)} valores no interpretables en "
              f"'ideacion_presente' (ignorados): {invalidas[:5]}")
    if sin_etiquetar:
        print(f"  ! {len(sin_etiquetar)} filas sin etiquetar (ignoradas)")
    if descartadas:
        print(f"  ! {len(descartadas)} filas descartadas por confianza < {min_confianza}")
    return etiquetas


# ── Config (a): reconstruir el clasificador del piloto desde git ──────────

def constantes_historicas() -> tuple[dict, float]:
    """
    Extrae CATEGORIAS_EMOCIONALES y UMBRAL_CRISIS del código tal como estaba
    en el commit del piloto. Ejecuta el módulo histórico en un namespace
    aislado — así las constantes son las del repo, no una transcripción.
    """
    try:
        fuente = subprocess.run(
            ["git", "show", f"{COMMIT_CONFIG_PILOTO}:app/services/nlp_service.py"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise SystemExit(
            f"No pude recuperar el código histórico ({COMMIT_CONFIG_PILOTO}): {e}\n"
            "Corré con --solo-actual y reportá únicamente la config vigente."
        )

    if "multi_label=True" not in fuente:
        raise SystemExit(
            "El módulo histórico no usa multi_label=True — revisá el commit "
            "antes de confiar en la reconstrucción de la config (a)."
        )

    ns: dict = {}
    sys.path.insert(0, str(ROOT))
    exec(compile(fuente, f"<git:{COMMIT_CONFIG_PILOTO}:nlp_service.py>", "exec"), ns)
    cats = ns["CATEGORIAS_EMOCIONALES"]
    umbral = float(ns["UMBRAL_CRISIS"])
    if "ideacion_suicida" not in cats:
        raise SystemExit("El código histórico no tiene 'ideacion_suicida'.")
    return cats, umbral


def scores_config_piloto(textos: list[str], cats: dict) -> list[float]:
    """Re-ejecuta BETO con las 8 hipótesis del piloto y devuelve el score de ideación."""
    from transformers import pipeline
    from app.config import settings

    print(f"  cargando {settings.MODEL_NAME} (CPU si DEVICE=-1)…", flush=True)
    clf = pipeline("zero-shot-classification",
                   model=settings.MODEL_NAME, device=settings.DEVICE)
    claves = list(cats.keys())
    hipotesis = [cats[k] for k in claves]
    hip_a_clave = dict(zip(hipotesis, claves))

    out = []
    for i, t in enumerate(textos, 1):
        res = clf(t.strip(), candidate_labels=hipotesis, multi_label=True)
        s = {hip_a_clave[h]: float(v) for h, v in zip(res["labels"], res["scores"])}
        out.append(s["ideacion_suicida"])
        if i % 20 == 0:
            # flush: si se redirige la salida a un log, el progreso se ve igual.
            print(f"    {i}/{len(textos)}", flush=True)
    return out


# ── Métricas ─────────────────────────────────────────────────────────────

def matriz(pares: list[tuple[int, int, float]]) -> dict:
    """pares = [(y_true, y_pred, peso), ...] → conteos crudos y ponderados."""
    m = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    w = {"TP": 0.0, "FP": 0.0, "TN": 0.0, "FN": 0.0}
    for y, p, peso in pares:
        k = "TP" if (y and p) else "FN" if (y and not p) else "FP" if p else "TN"
        m[k] += 1
        w[k] += peso
    return {"crudo": m, "ponderado": {k: round(v, 2) for k, v in w.items()}}


def derivadas(c: dict) -> dict:
    TP, FP, TN, FN = c["TP"], c["FP"], c["TN"], c["FN"]
    div = lambda a, b: round(a / b, 4) if b else None
    n = TP + FP + TN + FN
    return {
        "n": round(n, 2),
        "prevalencia": div(TP + FN, n),
        "recall_sensibilidad": div(TP, TP + FN),
        "especificidad": div(TN, TN + FP),
        "precision_ppv": div(TP, TP + FP),
        "vpn": div(TN, TN + FN),
        "exactitud": div(TP + TN, n),
        "f1": div(2 * TP, 2 * TP + FP + FN),
    }


def bloque(nombre: str, descripcion: str, pares: list[tuple[int, int, float]]) -> dict:
    m = matriz(pares)
    return {
        "config": nombre,
        "descripcion": descripcion,
        "muestra": {**m["crudo"], **derivadas(m["crudo"])},
        "proyectado_al_corpus": {**m["ponderado"], **derivadas(m["ponderado"])},
    }


def imprimir(b: dict) -> None:
    print(f"\n── {b['config']} ──")
    print(f"   {b['descripcion']}")
    for etiqueta, k in (("MUESTRA", "muestra"), ("PROYECTADO A 510", "proyectado_al_corpus")):
        d = b[k]
        print(f"   [{etiqueta}] TP={d['TP']}  FP={d['FP']}  TN={d['TN']}  FN={d['FN']}  (n={d['n']})")
        print(f"      recall={d['recall_sensibilidad']}  precision={d['precision_ppv']}  "
              f"especificidad={d['especificidad']}  VPN={d['vpn']}  F1={d['f1']}")


# ── Main ─────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--etiquetas", type=Path, required=True,
                    help="CSV devuelto por la psicóloga")
    ap.add_argument("--clave", type=Path, default=CLAVE)
    ap.add_argument("--solo-actual", action="store_true",
                    help="no re-ejecuta BETO; reporta solo la config vigente")
    ap.add_argument("--texto-completo", action="store_true",
                    help="config (a) sobre estímulo+respuesta en vez de solo la respuesta")
    ap.add_argument("--min-confianza", choices=["baja", "media", "alta"],
                    help="descarta etiquetas por debajo de este nivel")
    args = ap.parse_args()

    if not args.clave.exists():
        raise SystemExit(f"Falta la clave {args.clave}. Corré primero "
                         "scripts/muestrear_frases_ideacion.py")

    clave = json.loads(args.clave.read_text(encoding="utf-8"))
    por_id = {f["id"]: f for f in clave["frases"]}
    pesos = {k: v["peso"] for k, v in clave["estratos"].items()}

    print(f"Leyendo etiquetas de {args.etiquetas}")
    etiquetas = leer_etiquetas(args.etiquetas, args.min_confianza)

    huerfanos = set(etiquetas) - set(por_id)
    if huerfanos:
        raise SystemExit(f"IDs que no están en la clave: {sorted(huerfanos)[:10]}")

    ids = sorted(etiquetas)
    n_pos = sum(etiquetas[i]["y"] for i in ids)
    print(f"\nEtiquetas utilizables: {len(ids)}  "
          f"(ideación=1: {n_pos}, ideación=0: {len(ids) - n_pos})")

    if n_pos == 0:
        print("\n! Ninguna frase fue etiquetada como ideación. El recall no está\n"
              "  definido (TP+FN = 0). Reportá la especificidad y decí en el paper\n"
              "  que el corpus no contenía casos positivos según criterio clínico.")

    bloques = []

    # ── (b) config actual, desde los scores guardados ──────────────────
    pares_dom, pares_simple = [], []
    for i in ids:
        f, y = por_id[i], etiquetas[i]["y"]
        peso = pesos[f["estrato"]]
        dep = f["scores_actuales"].get("depresion", 0.0)
        domina = f["dominante_actual"] == "depresion"
        pares_dom.append((y, int(domina and dep >= UMBRAL_ACTUAL_CRISIS), peso))
        pares_simple.append((y, int(dep >= UMBRAL_ACTUAL_CRISIS), peso))

    bloques.append(bloque(
        "(b) ACTUAL — regla de producción",
        f"'depresion' domina Y score >= {UMBRAL_ACTUAL_CRISIS} "
        "(4 hipótesis, softmax). Scores de resultado_json.",
        pares_dom))
    bloques.append(bloque(
        "(b') ACTUAL — umbral simple",
        f"'depresion' >= {UMBRAL_ACTUAL_CRISIS} sin regla de dominancia.",
        pares_simple))

    # ── (a) config del piloto, re-ejecutando el modelo ─────────────────
    if not args.solo_actual:
        print(f"\nReconstruyendo la config del piloto desde {COMMIT_CONFIG_PILOTO}…")
        cats, umbral_a = constantes_historicas()
        print(f"  {len(cats)} hipótesis, UMBRAL_CRISIS={umbral_a}")
        textos = [
            f"{por_id[i]['estimulo']} {por_id[i]['respuesta']}".strip()
            if args.texto_completo else por_id[i]["respuesta"]
            for i in ids
        ]
        scores_a = scores_config_piloto(textos, cats)
        pares_a = [
            (etiquetas[i]["y"], int(s >= umbral_a), pesos[por_id[i]["estrato"]])
            for i, s in zip(ids, scores_a)
        ]
        entrada = "estímulo + respuesta" if args.texto_completo else "solo la respuesta"
        bloques.insert(0, bloque(
            "(a) PILOTO — ideación @ 0.40",
            f"8 hipótesis, multi_label=True, 'ideacion_suicida' >= {umbral_a} "
            f"(commit {COMMIT_CONFIG_PILOTO}). Entrada: {entrada}.",
            pares_a))
        for i, s in zip(ids, scores_a):
            por_id[i]["score_ideacion_piloto"] = round(s, 4)

    for b in bloques:
        imprimir(b)

    # ── Persistencia ───────────────────────────────────────────────────
    REPORTS.mkdir(exist_ok=True)
    salida = {
        "fuente_etiquetas": str(args.etiquetas),
        "semilla_muestreo": clave["semilla"],
        "n_corpus": clave["n_corpus"],
        "n_etiquetadas": len(ids),
        "n_positivas": n_pos,
        "min_confianza": args.min_confianza,
        "entrada_config_a": "estimulo+respuesta" if args.texto_completo else "respuesta",
        "estratos": clave["estratos"],
        "resultados": bloques,
        "detalle": [
            {
                "id": i,
                "estrato": por_id[i]["estrato"],
                "estimulo": por_id[i]["estimulo"],
                "respuesta": por_id[i]["respuesta"],
                "ideacion_presente": etiquetas[i]["y"],
                "confianza": etiquetas[i]["confianza"],
                "score_depresion_actual": por_id[i]["scores_actuales"].get("depresion"),
                "dominante_actual": por_id[i]["dominante_actual"],
                "score_ideacion_piloto": por_id[i].get("score_ideacion_piloto"),
            }
            for i in ids
        ],
    }
    (REPORTS / "ideacion_ground_truth.json").write_text(
        json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")

    md = ["# Recall de ideación suicida — BETO contra ground truth clínico\n",
          f"- Corpus Pack C: {clave['n_corpus']} frases.",
          f"- Muestra estratificada etiquetada: {len(ids)} "
          f"({n_pos} con ideación según criterio clínico).",
          f"- Semilla de muestreo: {clave['semilla']}.",
          "",
          "> La muestra es estratificada: el recall es interpretable tal cual, "
          "pero prevalencia y PPV sobre la muestra están inflados a propósito. "
          "Usar la columna proyectada para esos dos.",
          ""]
    for b in bloques:
        md += [f"## {b['config']}", "", b["descripcion"], "",
               "| | TP | FP | TN | FN | Recall | Precisión | Especificidad | VPN | F1 |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for etq, k in (("Muestra", "muestra"), ("Proyectado a 510", "proyectado_al_corpus")):
            d = b[k]
            md.append(f"| {etq} | {d['TP']} | {d['FP']} | {d['TN']} | {d['FN']} | "
                      f"{d['recall_sensibilidad']} | {d['precision_ppv']} | "
                      f"{d['especificidad']} | {d['vpn']} | {d['f1']} |")
        md.append("")
    (REPORTS / "ideacion_ground_truth.md").write_text("\n".join(md), encoding="utf-8")

    print(f"\nReportes → {REPORTS/'ideacion_ground_truth.json'}")
    print(f"           {REPORTS/'ideacion_ground_truth.md'}")


if __name__ == "__main__":
    main()
