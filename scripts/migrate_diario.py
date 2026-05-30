"""
Migración manual de la tabla `diario_entradas`.

No es estrictamente necesaria: `Base.metadata.create_all()` en `app/main.py`
crea la tabla automáticamente al arrancar la app contra SQLite. Este script
queda como respaldo para entornos donde quieras ejecutar la migración
explícitamente (MySQL en producción, por ejemplo).

Uso:
    venv/bin/python scripts/migrate_diario.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import engine, Base
from app.models.diario_entrada import DiarioEntrada  # noqa: F401
from app.models.diario_analisis import DiarioAnalisis  # noqa: F401

print("Creando tabla diario_entradas si no existe…")
DiarioEntrada.__table__.create(bind=engine, checkfirst=True)
print("Creando tabla diario_analisis si no existe…")
DiarioAnalisis.__table__.create(bind=engine, checkfirst=True)
print("Listo.")
