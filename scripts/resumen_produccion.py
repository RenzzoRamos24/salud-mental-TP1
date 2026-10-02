"""
Resumen de SOLO LECTURA de lo que hay hoy en producción.

Para qué
--------
Saber qué se recogió en la última aplicación en el colegio: cuántos alumnos
respondieron, qué dieron los puntajes de PHQ-A y GAD-7, cuántas banderas de
crisis se activaron y qué marcó BETO en las frases. Es el insumo para decidir
qué se puede validar con el etiquetado clínico.

No escribe nada. Hace un solo POST, el de login; todo lo demás son GET.

Uso
---
    venv/bin/python scripts/resumen_produccion.py --admin-password 'LA_CLAVE'

    # Contra la instancia local
    venv/bin/python scripts/resumen_produccion.py \
        --api http://127.0.0.1:8000/api/v1 --admin-password '...'

    # Más rápido, sin abrir cada resultado (solo el dashboard)
    venv/bin/python scripts/resumen_produccion.py --admin-password '...' --rapido

    # Guardar el detalle crudo para analizarlo después
    venv/bin/python scripts/resumen_produccion.py --admin-password '...' \
        --salida reports/produccion_hoy.json

La clave también se puede pasar por entorno (`SAMI_ADMIN_PASSWORD`) para no
dejarla en el historial del shell.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict

API_DEFAULT = "https://sami-app-9921877.azurewebsites.net/api/v1"

# Cortes de los dos instrumentos que corren en producción, para reportar la
# distribución por severidad sin depender de que el backend la devuelva.
PHQA_CORTES = [(0, 4, "mínima"), (5, 9, "leve"), (10, 14, "moderada"),
               (15, 19, "mod. severa"), (20, 27, "severa")]
GAD7_CORTES = [(0, 4, "mínima"), (5, 9, "leve"), (10, 14, "moderada"),
               (15, 21, "severa")]


def severidad(total: int, tabla) -> str:
    for lo, hi, etiqueta in tabla:
        if lo <= total <= hi:
            return etiqueta
    return "?"


def pedir(url, token=None, cuerpo=None, timeout=180):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(
        url, data=datos, method="POST" if cuerpo is not None else "GET"
    )
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        cuerpo_err = e.read().decode()[:200]
        if e.code in (401, 403):
            raise SystemExit(f"HTTP {e.code}: credenciales rechazadas.\n  {cuerpo_err}")
        print(f"  ! HTTP {e.code} en {url}: {cuerpo_err}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        raise SystemExit(f"Sin conexión a {url}\n  {e.reason}")


def barra(n: int, total: int, ancho: int = 24) -> str:
    lleno = round(ancho * n / total) if total else 0
    return "█" * lleno + "·" * (ancho - lleno)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=API_DEFAULT)
    ap.add_argument("--admin-email", default="admin@admin.com")
    ap.add_argument("--admin-password", default=os.environ.get("SAMI_ADMIN_PASSWORD"))
    ap.add_argument("--rapido", action="store_true",
                    help="solo el dashboard, sin abrir cada resultado")
    ap.add_argument("--salida", help="volcar el detalle crudo a este JSON")
    args = ap.parse_args()

    if not args.admin_password:
        raise SystemExit(
            "Falta la clave de admin. Pasala con --admin-password o en la "
            "variable SAMI_ADMIN_PASSWORD."
        )

    print(f"API: {args.api}\n")
    tok = pedir(f"{args.api}/auth/login",
                cuerpo={"email": args.admin_email, "password": args.admin_password})
    if not tok:
        raise SystemExit("No pude autenticar.")
    T = tok["access_token"]
    print(f"Autenticado como {tok['user']['email']} (rol {tok['user']['role']})\n")

    # ── Panorama ──────────────────────────────────────────────────────
    st = pedir(f"{args.api}/psychologist/dashboard-stats", T) or {}
    print("=" * 62)
    print("PANORAMA")
    print("=" * 62)
    print(f"  Estudiantes visibles      : {st.get('total_estudiantes')}")
    print(f"  Cuestionarios asignados   : {st.get('total_cuestionarios_asignados')}")
    print(f"  Cuestionarios completados : {st.get('total_cuestionarios_completados')}")
    dist = st.get("distribucion_riesgo") or {}
    total_dist = sum(dist.values()) or 1
    print("\n  Riesgo de la última evaluación por alumno:")
    for k in ("CRITICO", "ALTO", "MEDIO", "BAJO", "SIN_RIESGO", "sin_evaluacion"):
        v = dist.get(k, 0)
        print(f"    {k:15s} {v:4d}  {barra(v, total_dist)}")
    print(f"\n  En alerta (CRÍTICO/ALTO o crisis): "
          f"{len(st.get('estudiantes_en_alerta') or [])}")

    if args.rapido:
        print("\n(--rapido: no se abrió ningún resultado individual)")
        return

    # ── Detalle por aplicación ────────────────────────────────────────
    alumnos = pedir(f"{args.api}/psychologist/students", T) or []
    con_eval = [a for a in alumnos if a.get("ultima_evaluacion")]
    print(f"\nAbriendo los resultados de {len(con_eval)} alumnos con "
          f"evaluación… (esto tarda un minuto)\n")

    plantillas = Counter()
    instrumentos = Counter()
    puntajes = defaultdict(list)
    severidades = defaultdict(Counter)
    riesgos = Counter()
    n_crisis = n_svm = 0
    frases_total = 0
    frases_crisis = 0
    dominantes = Counter()
    scores_dep = []
    detalle = []

    for i, a in enumerate(con_eval, 1):
        if i % 20 == 0:
            print(f"  … {i}/{len(con_eval)}", flush=True)
        h = pedir(f"{args.api}/psychologist/students/{a['id']}/history", T) or {}
        for apl in (h.get("aplicaciones") or []):
            if not apl.get("completada_at"):
                continue
            res = pedir(f"{args.api}/cuestionarios/aplicacion/{apl['id']}/resultado", T)
            if not res:
                continue
            r = res.get("resultado") or res
            # `/plantillas` filtra por psicólogo, así que como admin no
            # devuelve nombres. Agrupo por composición de instrumentos, que es
            # lo que de verdad describe qué se aplicó y no depende de nombres.
            pid = r.get("plantilla_id") or apl.get("plantilla_id")
            codigos_bloques = [b.get("codigo") for b in (r.get("bloques") or [])]
            if r.get("frases"):
                codigos_bloques.append("FRASES")
            nombre_pl = (" + ".join(codigos_bloques) or "(sin bloques)")
            nombre_pl += f"   [plantilla #{pid}]"
            plantillas[nombre_pl] += 1
            riesgos[(r.get("riesgo_global") or "?").upper().replace("Í", "I")] += 1
            if r.get("crisis_activada"):
                n_crisis += 1
            if r.get("svm_segunda_opinion"):
                n_svm += 1
            for b in (r.get("bloques") or []):
                cod = b.get("codigo")
                instrumentos[cod] += 1
                if isinstance(b.get("puntaje"), (int, float)):
                    puntajes[cod].append(b["puntaje"])
                    if cod == "PHQ-A":
                        severidades[cod][severidad(b["puntaje"], PHQA_CORTES)] += 1
                    elif cod == "GAD-7":
                        severidades[cod][severidad(b["puntaje"], GAD7_CORTES)] += 1
            fr = r.get("frases") or []
            frases_total += len(fr)
            for f in fr:
                if f.get("crisis"):
                    frases_crisis += 1
                dominantes[f.get("dominante")] += 1
                sc = f.get("scores") or {}
                if "depresion" in sc:
                    scores_dep.append(float(sc["depresion"]))
            detalle.append({
                "aplicacion_id": apl["id"],
                "codigo_alumno": a.get("codigo_acceso"),
                "completada_at": apl["completada_at"],
                "plantilla": nombre_pl,
                "riesgo": r.get("riesgo_global"),
                "crisis": bool(r.get("crisis_activada")),
                "bloques": [
                    {"codigo": b.get("codigo"), "puntaje": b.get("puntaje"),
                     "severidad": b.get("severidad"),
                     "bandera_crisis": bool(b.get("bandera_crisis"))}
                    for b in (r.get("bloques") or [])
                ],
                "n_frases": len(fr),
                "n_frases_crisis": sum(1 for f in fr if f.get("crisis")),
                "svm": r.get("svm_segunda_opinion"),
            })

    print("\n" + "=" * 62)
    print("QUÉ SE APLICÓ  (agrupado por composición real del cuestionario)")
    print("=" * 62)
    for nombre, n in plantillas.most_common():
        print(f"  {n:4d}  {nombre}")
    print(f"\n  Instrumentos que aparecen: {dict(instrumentos)}")

    print("\n" + "=" * 62)
    print("PUNTAJES")
    print("=" * 62)
    for cod, vals in puntajes.items():
        if not vals:
            continue
        print(f"\n  {cod}  (n={len(vals)})")
        print(f"    media {statistics.mean(vals):.1f} | mediana "
              f"{statistics.median(vals):.1f} | rango {min(vals)}–{max(vals)}")
        if severidades[cod]:
            total = sum(severidades[cod].values())
            for et, n in severidades[cod].most_common():
                print(f"    {et:14s} {n:4d}  {barra(n, total)}")

    print("\n" + "=" * 62)
    print("RIESGO Y CRISIS")
    print("=" * 62)
    tot_r = sum(riesgos.values()) or 1
    for k, n in riesgos.most_common():
        print(f"  {k:15s} {n:4d}  {barra(n, tot_r)}")
    print(f"\n  Aplicaciones con bandera de crisis: {n_crisis} de {tot_r} "
          f"({n_crisis / tot_r:.1%})")

    print("\n" + "=" * 62)
    print("BETO SOBRE LAS FRASES")
    print("=" * 62)
    print(f"  Frases con texto           : {frases_total}")
    print(f"  Marcadas como crisis       : {frases_crisis}"
          f"{f' ({frases_crisis / frases_total:.1%})' if frases_total else ''}")
    if dominantes:
        tot_d = sum(dominantes.values())
        print("\n  Categoría dominante:")
        for k, n in dominantes.most_common():
            print(f"    {str(k):14s} {n:4d}  {barra(n, tot_d)}")
    if scores_dep:
        scores_dep.sort()
        print(f"\n  Score de 'depresion': mediana "
              f"{statistics.median(scores_dep):.3f} | máx {max(scores_dep):.3f}")
        for u in (0.25, 0.35, 0.45, 0.55):
            n = sum(1 for s in scores_dep if s >= u)
            print(f"    ≥ {u}: {n:4d} frases")

    print("\n" + "=" * 62)
    print("SVM")
    print("=" * 62)
    print(f"  Aplicaciones con salida del SVM: {n_svm}")
    if n_svm == 0:
        print("  Cero, como se esperaba: el paquete de deploy no incluye")
        print("  `models/`, así que el .joblib no está en el servidor y")
        print("  SVMService degrada en silencio. Ver DEPLOY.md:57.")

    if args.salida:
        from pathlib import Path
        Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
        Path(args.salida).write_text(
            json.dumps({
                "api": args.api,
                "panorama": st,
                "plantillas": dict(plantillas),
                "instrumentos": dict(instrumentos),
                "riesgos": dict(riesgos),
                "n_crisis": n_crisis,
                "frases_total": frases_total,
                "frases_crisis": frases_crisis,
                "dominantes": {str(k): v for k, v in dominantes.items()},
                "n_svm": n_svm,
                "detalle": detalle,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nDetalle crudo → {args.salida}")


if __name__ == "__main__":
    main()
