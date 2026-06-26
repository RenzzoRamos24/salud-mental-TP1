#!/usr/bin/env bash
# Entrypoint para Azure App Service Linux.
# Azure expone el puerto que la app debe usar en $PORT.

set -e

# Configurar HuggingFace cache en /tmp (App Service tiene /home persistente
# pero más lento; /tmp es rápido y suficiente para BETO).
export HF_HOME=${HF_HOME:-/tmp/hf}
export TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE:-/tmp/hf}
mkdir -p "$HF_HOME"

# Crear tablas y sembrar el banco la primera vez (idempotente).
echo "[startup] Aplicando schema + seed banco..."
python -c "
from app.database import engine, Base
import app.models
Base.metadata.create_all(bind=engine)
print('schema OK')
" || true

python -m scripts.bootstrap_postgres || true

# Crear primer admin si no existe.
python -m scripts.seed_admin || true

# Levantar el servidor. Workers=1 porque BETO es singleton en memoria (1.5 GB).
exec gunicorn app.main:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 600 \
  --access-logfile - \
  --error-logfile -
