"""Backup read-only de la BD de producción, tabla por tabla, a JSON.

Vuelca cada tabla a backup/backup_<timestamp>/<tabla>.json (más un manifest con
conteos y un README de advertencia). No escribe nada en producción:
conn.set_session(readonly=True). Reemplaza a pg_dump, que no está instalado.

Uso:
    export DATABASE_URL="postgresql://.../samidb?sslmode=require"
    venv/bin/python scripts/backup_produccion.py

Los datos son respuestas de salud mental de menores. backup/ está en
.gitignore: NUNCA commitear ni subir el resultado.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

import psycopg2
import psycopg2.extras

ROOT = Path(__file__).resolve().parents[1]


def serializar(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (bytes, memoryview)):
        return "<binario %d bytes>" % len(bytes(v))
    return v


def main() -> None:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("Falta DATABASE_URL.")

    conn = psycopg2.connect(dsn, connect_timeout=30)
    conn.set_session(readonly=True)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Confirmar solo-lectura.
    cur.execute("show transaction_read_only")
    if cur.fetchone()[0] != "on":
        sys.exit("La conexión NO es read-only. Abortado por seguridad.")

    cur.execute("""
        select tablename from pg_tables
        where schemaname = 'public' order by tablename
    """)
    tablas = [r[0] for r in cur.fetchall()]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = ROOT / "backup" / f"backup_{ts}"
    destino.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "origen": "sami-db-9921877 / samidb (produccion, read-only)",
        "tablas": {},
    }
    total_filas = 0
    print(f"Volcando {len(tablas)} tablas a {destino.relative_to(ROOT)}/ …\n")
    for t in tablas:
        # Nombre de tabla viene del catálogo, no de entrada externa; aun así
        # lo citamos con comillas dobles.
        cur.execute(f'select * from "{t}"')
        filas = [dict((k, serializar(v)) for k, v in dict(r).items())
                 for r in cur.fetchall()]
        (destino / f"{t}.json").write_text(
            json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest["tablas"][t] = len(filas)
        total_filas += len(filas)
        print(f"  {t:<28} {len(filas):>6} filas")

    manifest["total_filas"] = total_filas
    (destino / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (destino / "LEER_ESTO.txt").write_text(
        "DATOS SENSIBLES — respuestas de salud mental de menores de edad.\n"
        "Protegido por la Ley N° 29733 (Perú).\n\n"
        "NO commitear, NO subir a git, NO compartir por canales no cifrados.\n"
        f"Backup read-only de produccion generado el {manifest['generado']}.\n",
        encoding="utf-8")

    print(f"\n  TOTAL: {total_filas} filas en {len(tablas)} tablas")
    print(f"  Backup en: {destino}")
    conn.close()


if __name__ == "__main__":
    main()
