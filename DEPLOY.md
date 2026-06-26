# Despliegue en Azure — Sami

## URL pública

```
https://sami-app-9921877.azurewebsites.net
```

## Recursos creados

| Recurso | Nombre | Tier | Costo/mes |
|--|--|--|--|
| Resource Group | sami-rg | — | — |
| App Service Plan | sami-plan | Linux B2 | ~$26 |
| Web App | sami-app-9921877 | Python 3.12 | (incluido en plan) |
| PostgreSQL Server | sami-db-9921877 | Burstable B1ms | ~$13 |
| PostgreSQL Database | samidb | — | — |

**Total: ~$39 USD/mes** (gratis los primeros meses con Azure for Students).

Región: Brazil South (cercana a Perú).

## Credenciales

Admin del sistema:
```
Email:    admin@admin.com
Password: Admin12345
```

DB (uso interno, ya configurada en App Settings):
```
Host:     sami-db-9921877.postgres.database.azure.com
User:     samiadmin
Database: samidb
```

⚠ La contraseña de la DB está en `.azure-config` (chmod 600). No commitear ese archivo al repo.

## Comandos útiles

```bash
source .azure-config

# Ver logs en vivo
az webapp log tail -g $RG -n $APP_NAME

# Restart
az webapp restart -g $RG -n $APP_NAME

# Re-deploy con cambios nuevos
cd /home/renzo/salud-mental-TP1/project && npm run build
cd /home/renzo/salud-mental-TP1
venv/bin/python -c "
import zipfile, os
from pathlib import Path
INCLUDES = ['app', 'project/dist', 'scripts/seed_admin.py', 'scripts/bootstrap_postgres.py', 'startup.sh', 'requirements.txt']
EXCLUDES = ('__pycache__', '.pyc', '/node_modules/', '/.git/')
with zipfile.ZipFile('.deploy.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for inc in INCLUDES:
        p = Path(inc)
        if p.is_file():
            z.write(p, p.as_posix())
        else:
            for f in p.rglob('*'):
                if f.is_dir(): continue
                fp = f.as_posix()
                if any(e in fp for e in EXCLUDES): continue
                z.write(f, fp)
"
az webapp deploy -g $RG -n $APP_NAME --src-path .deploy.zip --type zip

# SSH a la app (debug)
az webapp ssh -g $RG -n $APP_NAME

# Métricas de costo
az consumption usage list --top 10
```

## Variables de entorno configuradas

`DATABASE_URL`, `JWT_SECRET`, `MODEL_NAME`, `DEVICE`, `HF_HOME`,
`ADMIN_EMAIL`, `ADMIN_PASSWORD`, `WEBSITES_ENABLE_APP_SERVICE_STORAGE`,
`SCM_DO_BUILD_DURING_DEPLOYMENT`.

## Notas técnicas

- BETO se descarga (~1.1 GB) la primera vez que se invoca la inferencia. El
  primer request a las frases incompletas tarda 2–3 minutos. Después queda
  cacheado en /tmp/hf hasta el siguiente restart del container.
- Backups de Postgres: automáticos, 7 días de retención, gratis. Restauración
  point-in-time disponible desde el portal.
- HTTPS: forzado. Certificado managed por Azure (gratis).
- Logs: `az webapp log tail` muestra stdout/stderr en vivo.

## Bajar todo (cleanup)

```bash
az group delete -n sami-rg --yes --no-wait
```

Esto borra todo: app, db, backups, plan. No se puede deshacer.
