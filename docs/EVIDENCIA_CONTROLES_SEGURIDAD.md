# Evidencia de controles de seguridad — Sami

Material para la revisión de los controles marcados "por verificar": WAF,
Key Vault, Application Insights, actualizaciones y versionado.

**Fecha:** 2026-10-04
**Instalación:** `https://sami-app-9921877.azurewebsites.net`
**Repositorio:** `https://github.com/RenzzoRamos24/salud-mental-TP1`

## Cómo se obtuvo esto

Tres fuentes, todas reproducibles:

1. **Peticiones HTTP a producción** — cabeceras, TLS, redirección. No
   requiere credenciales.
2. **El repositorio** — configuración de la aplicación, dependencias
   declaradas, secretos en el código, historial de git.
3. **Azure CLI** — *no disponible al momento de escribir esto*: la sesión
   tenía la verificación en dos pasos vencida (`AADSTS50078`). Todo lo que
   dependa de consultar el portal queda marcado como **pendiente**.

Lo que no pude comprobar está dicho como no comprobado, no como ausente.

---

## 1. WAF (Web Application Firewall)

**Estado: no hay, con alta confianza.**

El inventario de recursos documentado en `DEPLOY.md` es:

| Recurso | Nombre | Tier |
|---|---|---|
| Resource Group | sami-rg | — |
| App Service Plan | sami-plan | Linux B2 |
| Web App | sami-app-9921877 | Python 3.12 |
| PostgreSQL Server | sami-db-9921877 | Burstable B1ms |
| PostgreSQL Database | samidb | — |

No figura Application Gateway, Front Door ni Azure WAF — que son los únicos
servicios que proveerían WAF en esta arquitectura. El tráfico llega
directo al App Service.

Lo confirma la respuesta HTTP: el encabezado `Server` es `uvicorn`, o sea que
responde el proceso de la aplicación sin intermediario que lo enmascare.

**Para cerrarlo definitivamente** (requiere sesión activa):

```bash
az resource list -o table
az network application-gateway list -o table
az network front-door list -o table
```

---

## 2. Key Vault

**Estado: no se usa.**

Dos evidencias independientes:

- **No hay ninguna referencia en el código.** Búsqueda sobre todo el
  repositorio de `keyvault`, `key_vault`, `azure.identity`,
  `DefaultAzureCredential`: cero resultados. `requirements.txt` tampoco
  incluye `azure-keyvault-secrets` ni `azure-identity`.
- **Los secretos viven en App Settings**, en texto plano. `DEPLOY.md`
  documenta las variables configuradas: `DATABASE_URL`, `JWT_SECRET`,
  `ADMIN_PASSWORD`, entre otras. Cualquiera con rol Contributor sobre la
  Web App puede leerlas.

### Hallazgo asociado — secretos en el repositorio público

Verificado que el repositorio responde **HTTP 200 sin credenciales**, o sea
que es público. Y contiene credenciales reales:

| Ubicación | Contenido |
|---|---|
| `scripts/generar_reporte_colegio.py:558` | contraseña de la cuenta del colegio, en texto plano |
| `DEPLOY.md:27-28` | usuario y contraseña del admin del sistema |
| `CLAUDE.md:25` | las mismas credenciales de admin |
| `scripts/azure_reeval_beto.sh:13` | contraseña de admin como valor por defecto |

Lo confirmé descargando el archivo desde `raw.githubusercontent.com` sin
autenticarme: la contraseña del colegio es legible por cualquiera.

La cuenta del colegio da acceso al panel clínico de **221 estudiantes
menores de edad** con sus respuestas de salud mental y su clasificación de
riesgo.

**Esto es lo más urgente de todo este documento**, por encima de WAF o
Application Insights. Son tres pasos: cambiar las dos contraseñas, sacar los
valores del código (que los lea de variables de entorno) y reescribir el
historial de git o rotar lo expuesto — porque borrar el archivo hoy no
elimina lo que quedó en los commits anteriores.

---

## 3. Application Insights

**Estado: no está instrumentado en la aplicación.**

- Sin referencias a `applicationinsights`, `opencensus` ni
  `azure-monitor-opentelemetry` en el código ni en `requirements.txt`.
- `DEPLOY.md` no lista `APPLICATIONINSIGHTS_CONNECTION_STRING` entre las
  variables configuradas.

Puede existir el recurso con instrumentación automática del App Service
(que da métricas de plataforma sin tocar el código), pero **no hay telemetría
de aplicación**: ni trazas, ni dependencias, ni excepciones correlacionadas.

**Lo que sí existe** es registro propio:

- `app/middleware/access_log.py` — middleware que registra cada petición.
- Tabla `access_logs` con: `user_id`, `email`, `role`, `method`, `endpoint`,
  `status_code`, `ip`, `timestamp`.
- Consultable desde el panel de admin.

Es auditoría de accesos, no observabilidad. Sirve para "quién vio qué", no
para detectar degradación o errores en producción.

**Para cerrarlo:**

```bash
az monitor app-insights component show -g sami-rg --app <nombre>
az webapp config appsettings list -g sami-rg -n sami-app-9921877 \
  --query "[?contains(name,'APPLICATIONINSIGHTS')].name"
```

---

## 4. Actualizaciones

**Estado: versiones fijadas, sin proceso de actualización.**

`requirements.txt` fija versiones exactas, lo cual es bueno para
reproducibilidad. El problema es que nadie las mueve: no hay Dependabot,
ni renovate, ni CI que avise.

Las que importan desde el punto de vista de seguridad:

| Paquete | Versión fijada | Observación |
|---|---|---|
| `fastapi` | 0.104.1 | de octubre 2023 |
| `uvicorn` | 0.24.0 | de octubre 2023 |
| `python-jose[cryptography]` | 3.3.0 | maneja los JWT; sin publicar desde 2021 |
| `bcrypt` | 4.0.1 | hash de contraseñas |
| `transformers` | 4.35.2 | de noviembre 2023 |
| `torch` | 2.3.0 | ~1.5 GB en memoria |
| `sqlalchemy` | 2.0.23 | ORM |

Runtime: **Python 3.12** sobre App Service Linux.

No corrí un análisis de vulnerabilidades porque haría falta `pip-audit` o
`safety` contra la base de datos de CVE, y eso excede lo que se puede
afirmar sin ejecutarlo. **Recomendación concreta:**

```bash
venv/bin/pip install pip-audit
venv/bin/pip-audit -r requirements.txt
```

Eso da la lista real de CVE con su severidad, que es lo que corresponde
adjuntar a una revisión en vez de una sospecha por antigüedad.

---

## 5. Versionado

**Estado: control de versiones sí; versionado de releases no.**

| Aspecto | Situación |
|---|---|
| Control de versiones | Git, 57 commits en `main` |
| Remoto | GitHub (público) |
| Etiquetas / releases | **0 tags** |
| Versionado semántico | No se usa |
| Pipeline de CI/CD | No hay — el despliegue es manual con `az webapp deploy` |
| Entorno de pruebas | No hay: se despliega directo a producción |
| Trazabilidad despliegue→commit | Ninguna; nada marca qué commit está corriendo |
| API versionada | Sí, por ruta: `/api/v1/...` |

El punto que más pesa: **no se puede saber qué versión está en producción**.
El historial de despliegues de Azure registra la hora, no el commit. Para
reconstruir qué código corre hay que cruzar fechas a mano.

Con etiquetar cada despliegue (`git tag v1.0.0`) y exponer la versión en un
endpoint de salud, eso se resuelve.

---

## Hallazgos adicionales

Encontrados al revisar, no estaban en la lista pero corresponden a la misma
revisión.

### CORS abierto a cualquier origen

`app/main.py:36-37`:

```python
CORSMiddleware,
allow_origins=["*"],
```

Cualquier sitio web puede hacer peticiones a la API desde el navegador de un
usuario autenticado. Debería limitarse al dominio propio.

### El JWT tiene un secreto por defecto inseguro

`app/config.py:37`:

```python
JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production-please")
```

En producción la variable está configurada, así que no se usa el valor por
defecto. Pero si alguien despliega sin definirla, el sistema arranca igual y
**cualquiera puede firmar tokens válidos**. Debería negarse a arrancar.

Configuración: `HS256`, expiración **1440 minutos (24 horas)**. Para datos
clínicos de menores, 24 horas es largo.

### Faltan cabeceras de seguridad

La respuesta de producción no incluye ninguna de:

- `Strict-Transport-Security` (HSTS)
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options` o `frame-ancestors` (protección contra clickjacking)
- `Content-Security-Policy`
- `Referrer-Policy`

Son cinco líneas de middleware en FastAPI.

### Sin límite de intentos de autenticación

No hay rate limiting en `/auth/login` ni en `/auth/login-codigo`. Los códigos
de acceso de los alumnos tienen formato predecible (`SAMI-4TO-01` a
`SAMI-5TO-53`) y **son la credencial completa**: sin contraseña, sin segundo
factor. Un script los recorre todos en minutos.

Es, en mi lectura, el riesgo técnico más alto después de los secretos
expuestos.

---

## Lo que sí está bien resuelto

Para que la revisión quede equilibrada:

- **HTTPS forzado.** HTTP responde 301 hacia HTTPS.
- **TLS 1.3** con `TLS_AES_256_GCM_SHA384`, certificado válido.
- **Contraseñas con bcrypt** vía passlib (`app/core/security.py:10`). No hay
  contraseñas recuperables en la base.
- **Cookies de afinidad con `HttpOnly` y `Secure`.**
- **Autorización por rol** consistente: `require_role(...)` en cada endpoint,
  verificado en pruebas (un estudiante recibe 403 en las rutas de psicólogo).
- **Auditoría de accesos** persistida con usuario, endpoint, IP y timestamp.
- **API versionada** bajo `/api/v1`.
- **`.env` no está en git**; solo `.env.example`.

---

## Prioridad sugerida

| # | Acción | Por qué primero |
|---|---|---|
| 1 | Rotar las credenciales expuestas y sacarlas del código | Están públicas **ahora**, dan acceso a datos de 221 menores |
| 2 | Rate limiting en los endpoints de login | Los códigos son enumerables y son la credencial completa |
| 3 | Cerrar CORS al dominio propio | Una línea |
| 4 | Cabeceras de seguridad | Cinco líneas de middleware |
| 5 | Que falle el arranque sin `JWT_SECRET` | Evita un despliegue inseguro silencioso |
| 6 | `pip-audit` y actualizar lo que aparezca | Necesita el informe real antes de decidir |
| 7 | Etiquetar releases y exponer la versión | Trazabilidad |
| 8 | Key Vault / Application Insights / WAF | Mejoras de infraestructura, más costosas y menos urgentes |

Los cinco primeros son horas de trabajo, no semanas.

---

## Pendiente de confirmar en el portal

Requiere sesión de Azure activa (la verificación en dos pasos estaba
vencida):

```bash
az login --tenant "0e0cb060-09ad-49f5-a005-68b9b49aa1f6"

# Inventario completo de recursos
az resource list -o table

# Configuración de la Web App
az webapp show -g sami-rg -n sami-app-9921877 \
  --query "{https_only:httpsOnly, tls:siteConfig.minTlsVersion, \
            ftps:siteConfig.ftpsState, identidad:identity}"

# Nombres de App Settings (sin valores)
az webapp config appsettings list -g sami-rg -n sami-app-9921877 \
  --query "[].name" -o tsv

# Reglas de firewall de PostgreSQL — ¿está abierto a 0.0.0.0?
az postgres flexible-server firewall-rule list \
  -g sami-rg -n sami-db-9921877 -o table

# Backups y retención
az postgres flexible-server show -g sami-rg -n sami-db-9921877 \
  --query "backup"
```

La regla de firewall de PostgreSQL es la que más me interesaría ver: si
quedó abierta a todo internet, pasa al primer puesto de la lista de
prioridades.
