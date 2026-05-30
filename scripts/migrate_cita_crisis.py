"""
Migración idempotente: agrega la columna `es_crisis` a la tabla `citas`.

Contexto: el modelo de ciclos del diario cambió (2026-05-29). Una cita
marcada como `es_crisis=True` que se complete adelanta el cierre del ciclo
en curso. Las citas regulares (es_crisis=False) corren en paralelo sin
afectar la temporalidad del diario.

Uso:
    venv/bin/python scripts/migrate_cita_crisis.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402


def _resolver_db_path() -> Path:
    raw = settings.DATABASE_URL.split("sqlite:///")[-1]
    p = Path(raw)
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[1] / p
    return p.resolve()


def _cols(cur, tabla):
    cur.execute(f"PRAGMA table_info({tabla})")
    return {r[1] for r in cur.fetchall()}


def main() -> int:
    db_path = _resolver_db_path()
    if not db_path.exists():
        print(f"BD no encontrada: {db_path}")
        return 0

    print(f"Migrando citas.es_crisis en {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        citas_cols = _cols(cur, "citas")
        if not citas_cols:
            print("  · tabla citas no existe todavía (se creará al arrancar la app)")
        elif "es_crisis" in citas_cols:
            print("  · citas.es_crisis ya existe")
        else:
            cur.execute(
                "ALTER TABLE citas ADD COLUMN es_crisis BOOLEAN NOT NULL DEFAULT 0"
            )
            print("  + ALTER citas ADD es_crisis")
        conn.commit()
        print("OK")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
