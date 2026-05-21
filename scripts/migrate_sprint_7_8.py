"""
Migración Sprint 7 + 8: tablas nuevas y columnas en users.
Idempotente — comprueba antes de cada CREATE / ALTER.

Uso:
    python -m scripts.migrate_sprint_7_8
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings  # noqa: E402


COLUMNAS_USERS = [
    ("estado_caso", "VARCHAR(20) DEFAULT 'activo'"),
    ("psicologo_id", "VARCHAR(36)"),
    ("grado", "VARCHAR(20)"),
]

TABLAS_NUEVAS = {
    "clinical_notes": """
        CREATE TABLE IF NOT EXISTS clinical_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id VARCHAR(36) NOT NULL,
            psicologo_id  VARCHAR(36) NOT NULL,
            texto TEXT NOT NULL,
            etiqueta VARCHAR(50),
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (estudiante_id) REFERENCES users(id),
            FOREIGN KEY (psicologo_id)  REFERENCES users(id)
        )
    """,
    "educational_content": """
        CREATE TABLE IF NOT EXISTS educational_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo VARCHAR(200) NOT NULL,
            descripcion TEXT NOT NULL,
            tipo VARCHAR(20) NOT NULL DEFAULT 'articulo',
            categoria VARCHAR(30),
            url VARCHAR(500),
            contenido TEXT,
            autor VARCHAR(120),
            icono VARCHAR(10) DEFAULT '📄',
            activo BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    """,
    "satisfaction_surveys": """
        CREATE TABLE IF NOT EXISTS satisfaction_surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(36) NOT NULL,
            facilidad_uso INTEGER NOT NULL,
            utilidad INTEGER NOT NULL,
            confianza INTEGER NOT NULL,
            recomendaria INTEGER NOT NULL,
            nivel_animo_post INTEGER,
            comentario TEXT,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """,
    "sos_events": """
        CREATE TABLE IF NOT EXISTS sos_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id VARCHAR(36) NOT NULL,
            origen VARCHAR(20),
            mensaje TEXT,
            estado VARCHAR(20) NOT NULL DEFAULT 'abierto',
            timestamp DATETIME NOT NULL,
            atendido_por VARCHAR(36),
            atendido_en DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """,
}

CONTENIDO_SEED = [
    ("Respiración 4-7-8 para calmar la ansiedad",
     "Una técnica simple de 90 segundos para bajar la activación cuando los nervios te ganan.",
     "articulo", "ansiedad", None, None, "Sami", "🌬️"),
    ("Higiene del sueño en adolescentes",
     "Por qué dormir bien es clave a tu edad y 6 hábitos para lograrlo.",
     "articulo", "sueño", None, None, "Sami", "😴"),
    ("¿Qué es la anhedonia? Cuando ya nada te emociona",
     "Conoce este síntoma del estado de ánimo bajo y cómo identificarlo en ti.",
     "articulo", "depresion", None, None, "Sami", "🌧️"),
    ("Técnica 5-4-3-2-1 para salir del espiral",
     "Cinco cosas que ves, cuatro que tocas, tres que escuchas… aterrízate en el presente.",
     "infografia", "ansiedad", None, None, "Sami", "🧘"),
    ("Cómo hablar con tus papás sobre lo que sientes",
     "Guía paso a paso para iniciar la conversación con un adulto de confianza.",
     "articulo", "autocuidado", None, None, "Sami", "💬"),
    ("Línea 113 — ¿Cuándo y cómo llamar?",
     "Qué esperar al llamar a la línea nacional de salud mental del MINSA.",
     "articulo", "crisis", "https://www.gob.pe/8702-llamar-a-la-linea-113",
     None, "Sami", "📞"),
]


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
        print(f"⚠️  BD no encontrada: {db_path}")
        return 0

    print(f"🔧 Migrando Sprint 7+8 en {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        # Tablas nuevas
        for nombre, ddl in TABLAS_NUEVAS.items():
            cur.execute(ddl)
            print(f"  ✓ tabla {nombre}")

        # Columnas en users
        users_cols = _cols(cur, "users")
        if users_cols:
            for col, tipo in COLUMNAS_USERS:
                if col in users_cols:
                    print(f"  · users.{col} ya existe")
                else:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col} {tipo}")
                    print(f"  + ALTER users ADD {col}")

        # Seed inicial de contenido psicoeducativo (si está vacío)
        cur.execute("SELECT COUNT(*) FROM educational_content")
        if cur.fetchone()[0] == 0:
            from datetime import datetime
            now = datetime.utcnow().isoformat()
            for titulo, desc, tipo, cat, url, contenido, autor, icono in CONTENIDO_SEED:
                cur.execute(
                    """INSERT INTO educational_content
                       (titulo, descripcion, tipo, categoria, url, contenido, autor, icono,
                        activo, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,1,?,?)""",
                    (titulo, desc, tipo, cat, url, contenido, autor, icono, now, now),
                )
            print(f"  🌱 seeded {len(CONTENIDO_SEED)} artículos psicoeducativos")

        conn.commit()
        print("✅ Migración OK")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
