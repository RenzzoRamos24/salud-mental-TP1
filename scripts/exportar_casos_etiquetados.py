"""Exporta de producción los casos etiquetados por la psicóloga, a CSV.

El etiquetado solo existe en producción (Azure Postgres); la SQLite local no
tiene las tablas. Este script hace **una** lectura de solo-lectura y deja un
CSV con el que se entrena y valida local, sin volver a tocar producción.

Qué sale: `aplicacion_id` (seudónimo), los valores Likert de los ítems de
instrumentos, y el juicio de la psicóloga. **No sale ningún dato personal**:
ni nombre, ni correo, ni código de acceso, ni las frases incompletas (texto
libre que podría identificar).

Uso
---
    export DB_SERVER=... DB_NAME=... DB_USER=... DB_PASS=...
    venv/bin/python scripts/exportar_casos_etiquetados.py \
        --salida data/clinico/casos_etiquetados.csv

El CSV no se versiona (ver .gitignore): son respuestas de menores de edad.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

EVALUADOR_DEFECTO = "SAMI-PSI-01"

CAMPOS_ETIQUETA = [
    "aplicacion_id", "completada_at", "riesgo_clinico", "requiere_derivacion",
    "ideacion_presente", "modelo_riesgo", "modelo_crisis",
    "modelo_svm_clase", "predominante", "n_items_respondidos",
]


def dsn() -> str:
    faltan = [v for v in ("DB_SERVER", "DB_NAME", "DB_USER", "DB_PASS")
              if not os.environ.get(v)]
    if faltan:
        sys.exit(f"Faltan variables de entorno: {', '.join(faltan)}")
    return (f"host={os.environ['DB_SERVER']}.postgres.database.azure.com "
            f"port=5432 dbname={os.environ['DB_NAME']} "
            f"user={os.environ['DB_USER']} password={os.environ['DB_PASS']} "
            f"sslmode=require connect_timeout=20")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", type=Path,
                    default=Path("data/clinico/casos_etiquetados.csv"))
    ap.add_argument("--evaluador", default=EVALUADOR_DEFECTO,
                    help=f"código de acceso del evaluador (def. {EVALUADOR_DEFECTO})")
    args = ap.parse_args()

    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(dsn())
    conn.set_session(readonly=True)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    cur.execute("""
        select e.aplicacion_id, a.completada_at, e.riesgo_clinico,
               e.requiere_derivacion, e.ideacion_presente, e.modelo_riesgo,
               e.modelo_crisis, e.modelo_svm_clase, e.predominante
        from etiqueta_caso e
        join users u on u.id = e.evaluador_id
        join aplicacion_cuestionario a on a.id = e.aplicacion_id
        where u.codigo_acceso = %s
        order by e.aplicacion_id
    """, (args.evaluador,))
    etiquetas = {r["aplicacion_id"]: dict(r) for r in cur.fetchall()}
    if not etiquetas:
        sys.exit(f"Sin etiquetas para el evaluador {args.evaluador}")
    print(f"etiquetas de {args.evaluador}: {len(etiquetas)}")

    cur.execute("""
        select aplicacion_id, origen, valor_num
        from respuesta_aplicacion
        where valor_num is not null and aplicacion_id = any(%s)
    """, (list(etiquetas),))
    items: dict[int, dict[str, int]] = {}
    origenes: set[str] = set()
    for r in cur.fetchall():
        items.setdefault(r["aplicacion_id"], {})[r["origen"]] = r["valor_num"]
        origenes.add(r["origen"])
    print(f"casos con respuestas numéricas: {len(items)}")

    cols = sorted(o for o in origenes if o.startswith("INSTR:"))
    campos = CAMPOS_ETIQUETA + cols

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with args.salida.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        for aid, et in sorted(etiquetas.items()):
            resp = items.get(aid, {})
            fila = {k: et.get(k) for k in CAMPOS_ETIQUETA if k in et}
            fila["aplicacion_id"] = aid
            fila["n_items_respondidos"] = len(resp)
            fila.update({c: resp.get(c) for c in cols})
            w.writerow(fila)

    print(f"\nescrito: {args.salida}")
    print(f"filas: {len(etiquetas)} | columnas de ítems: {len(cols)}")


if __name__ == "__main__":
    main()
