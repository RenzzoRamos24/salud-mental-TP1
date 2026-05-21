"""
Migración: añade columnas PHQ-9 / GAD-7 a user_responses y risk_results.

Idempotente: comprueba antes de cada ALTER si la columna ya existe.

Uso:
    python -m scripts.migrate_phq9_gad7
"""
import sqlite3
import sys
from pathlib import Path

# Permite importar app/* aunque se ejecute desde el repo raíz
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings  # noqa: E402


COLUMNAS_USER_RESPONSES = [
    ("item_codigo", "VARCHAR(20)"),
    ("modulo", "VARCHAR(10)"),
    ("criterio_dsm5", "VARCHAR(200)"),
    ("score_likert", "INTEGER"),
    ("confianza_likert", "FLOAT"),
    ("score_origen", "VARCHAR(20)"),
]

COLUMNAS_RISK_RESULTS = [
    ("phq9_total", "INTEGER"),
    ("gad7_total", "INTEGER"),
    ("phq9_severidad", "VARCHAR(30)"),
    ("gad7_severidad", "VARCHAR(30)"),
    ("crisis_protocolo", "BOOLEAN DEFAULT 0"),
]

COLUMNAS_USER_SESSIONS = [
    ("fase", "VARCHAR(20) DEFAULT 'apertura'"),
    ("modulos_orden", "VARCHAR(50)"),
    ("apertura_texto", "TEXT"),
]


def _resolver_db_path() -> Path:
    url = settings.DATABASE_URL
    if not url.startswith("sqlite"):
        raise RuntimeError(
            f"Esta migración solo soporta SQLite. DATABASE_URL={url}"
        )
    # sqlite:///./mental_health.db  → mental_health.db
    raw = url.split("sqlite:///")[-1]
    p = Path(raw)
    if not p.is_absolute():
        p = Path(__file__).resolve().parents[1] / p
    return p.resolve()


def _columnas_existentes(cur: sqlite3.Cursor, tabla: str) -> set:
    cur.execute(f"PRAGMA table_info({tabla})")
    return {row[1] for row in cur.fetchall()}


def _migrar_tabla(cur: sqlite3.Cursor, tabla: str, columnas: list) -> int:
    existentes = _columnas_existentes(cur, tabla)
    if not existentes:
        print(f"  ⚠️  Tabla `{tabla}` no existe; se creará al primer arranque.")
        return 0
    agregadas = 0
    for nombre, tipo in columnas:
        if nombre in existentes:
            print(f"  · {tabla}.{nombre} ya existe — saltado")
            continue
        sql = f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}"
        print(f"  + {sql}")
        cur.execute(sql)
        agregadas += 1
    return agregadas


def main() -> int:
    db_path = _resolver_db_path()
    if not db_path.exists():
        print(f"⚠️  BD no encontrada en {db_path}. Nada que migrar.")
        return 0

    print(f"🔧 Migrando {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        n1 = _migrar_tabla(cur, "user_responses", COLUMNAS_USER_RESPONSES)
        n2 = _migrar_tabla(cur, "risk_results", COLUMNAS_RISK_RESULTS)
        n3 = _migrar_tabla(cur, "user_sessions", COLUMNAS_USER_SESSIONS)
        # Marcar sesiones legacy como ya pasadas la apertura (no quedan colgadas
        # en una fase que no existía cuando se crearon).
        cur.execute(
            "UPDATE user_sessions SET fase = 'evaluacion' "
            "WHERE fase IS NULL OR fase = 'apertura' AND pregunta_actual > 0"
        )
        conn.commit()
        print(f"✅ Migración OK — {n1 + n2 + n3} columnas añadidas.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
