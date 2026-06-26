# Arquitectura física de Sami — Despliegue en Azure

Documento de arquitectura para defensa de tesis y despliegue del piloto.

---

## 1. Diagrama de la arquitectura

```
   ┌─────────────┐  ┌──────────────┐  ┌─────────────┐
   │   ALUMNO    │  │  PSICÓLOGA   │  │    ADMIN    │
   │ secundaria  │  │ del colegio  │  │   sistema   │
   └──────┬──────┘  └──────┬───────┘  └──────┬──────┘
          │                │                  │
          └────────────────┼──────────────────┘
                           │
                           │  HTTPS (TLS 1.2+)
                           │  JWT en Authorization header
                           ▼
       ┌──────────────────────────────────────────────────┐
       │  Azure App Service · Linux · Plan B2             │
       │  (3.5 GB RAM · 2 vCPU compartidos)               │
       │                                                  │
       │   ┌──────────────────────────────────────────┐   │
       │   │  Vue 3 SPA (build estático servido       │   │
       │   │  por FastAPI desde /static)              │   │
       │   └──────────────────────────────────────────┘   │
       │                                                  │
       │   ┌──────────────────────────────────────────┐   │
       │   │  FastAPI                                 │   │
       │   │   • JWT auth + OAuth (Google/Microsoft)  │   │
       │   │   • Banco · Plantillas · Cuestionarios   │   │
       │   │   • EvaluatorService                     │   │
       │   │     - Suma puntajes por escala           │   │
       │   │     - Cortes Johnson/Spitzer/Harding…    │   │
       │   │     - Banderas de crisis                 │   │
       │   │     - Riesgo compuesto                   │   │
       │   │   • Citas · Notas · SOS                  │   │
       │   └──────────────────────────────────────────┘   │
       │                                                  │
       │   ┌──────────────────────────────────────────┐   │
       │   │  NLPService (BETO embebido, singleton)   │   │
       │   │   Recognai/bert-base-spanish-wwm-cased-  │   │
       │   │   xnli                                   │   │
       │   │   Solo se invoca para frases incompletas │   │
       │   │   8 categorías emocionales               │   │
       │   └──────────────────────────────────────────┘   │
       └──────────────────────┬───────────────────────────┘
                              │
                              │  TLS / psycopg2
                              ▼
       ┌──────────────────────────────────────────────────┐
       │  Azure Database for PostgreSQL                   │
       │  Flexible Server · Burstable B1ms                │
       │  (2 GB RAM · 1 vCore · 32 GB SSD)                │
       │                                                  │
       │  Tablas (19):                                    │
       │   • users · consents · password_reset_tokens     │
       │   • bank_instrumento · bank_item ·               │
       │     bank_frase_incompleta                        │
       │   • bloque_custom · bloque_custom_item           │
       │   • plantilla_cuestionario · plantilla_bloque    │
       │   • aplicacion_cuestionario ·                    │
       │     respuesta_aplicacion                         │
       │   • citas · clinical_notes · sos_events          │
       │   • access_logs · configuracion ·                │
       │     educational_content · satisfaction_surveys   │
       │                                                  │
       │  Backups automáticos (gestionados por Azure):    │
       │   • Snapshot diario, retención 7 días, gratis    │
       │   • Point-in-time restore                        │
       └──────────────────────────────────────────────────┘
```

---

## 2. Componentes

### 2.1 Azure App Service (Linux, Plan B2)

Un único contenedor lógico que sirve la SPA y la API. **Decisión consciente**: agrupar en un solo App Service simplifica el deploy y minimiza la latencia entre los componentes que más se comunican (FastAPI ↔ BETO).

| Recurso | Valor |
|--|--|
| OS | Linux |
| Runtime | Python 3.12 |
| Plan | App Service Basic B2 |
| RAM | 3.5 GB |
| CPU | 2 vCPU (compartidos) |
| Almacenamiento | 10 GB SSD efímero |
| HTTPS | Forzado, certificado managed gratis |
| Custom domain | Opcional |
| Costo | **~$26 USD/mes** |

**Qué corre dentro:**
- `uvicorn app.main:app` en puerto interno → mapeado a 443 por Azure
- Vue compilado se sirve como estáticos por FastAPI desde `/static`
- BETO se carga en memoria una sola vez (~1.5 GB RAM) y queda como singleton

### 2.2 Azure Database for PostgreSQL Flexible Server (Burstable B1ms)

Almacenamiento persistente de todos los datos clínicos y de gestión.

| Recurso | Valor |
|--|--|
| Edición | Flexible Server |
| Tier | Burstable |
| Compute | B1ms (1 vCore + 2 GB RAM) |
| Almacenamiento | 32 GB SSD Premium |
| Backups | Diarios automáticos, 7 días retención (gratis) |
| SSL | Obligatorio |
| Costo | **~$13 USD/mes** |

---

## 3. Seguridad

| Capa | Mecanismo |
|--|--|
| Transporte | HTTPS forzado, certificado gestionado por Azure (TLS 1.2+) |
| Autenticación | JWT con HS256, expiración 24h |
| Autorización por rol | Decorador `require_role` valida JWT contra cada endpoint protegido |
| Identidades federadas | OAuth 2.0 con Google y Microsoft (PKCE) |
| Secretos | Azure App Service Application Settings (cifradas en reposo) |
| Base de datos | TLS obligatorio + firewall por IP del App Service |
| Auditoría | Tabla `access_logs` registra cada request con `user_id`, `endpoint`, `status` |
| Hash de contraseñas | bcrypt (passlib) |
| CORS | Restringido al dominio del frontend |
| Backups | Diarios, 7 días retención, restauración point-in-time |

---

## 4. Capacidad y desempeño

### Carga del piloto (50 estudiantes)

| Métrica | Valor estimado |
|--|--|
| Total alumnos | 50 |
| Cuestionarios por piloto | ~100 |
| Frases incompletas a procesar por BETO | ~500–700 |
| Tamaño total de datos | < 100 MB |
| Concurrencia esperada | 20–30 alumnos en paralelo (sesión de clase) |

### Tiempos esperados

| Operación | Tiempo |
|--|--|
| Login | < 200 ms |
| Listar instrumentos del banco | < 100 ms |
| Asignar cuestionario | < 150 ms |
| Cargar pregunta a responder | < 100 ms |
| Guardar respuesta individual | < 100 ms |
| Cerrar cuestionario sin frases | < 500 ms |
| Cerrar cuestionario con 5–10 frases (BETO) | **15–30 segundos** |
| Listar resultado (psicóloga) | < 200 ms |

### Estrategia para evitar congestión

El cuello de botella es la inferencia de BETO al cerrar cuestionarios.
Para que el piloto fluya sin esperas, se recomienda **aplicar el cuestionario en 2 sesiones de 25 alumnos**, no en una sola sesión de 50. Esto procesa todo en 2–3 minutos por sesión sin necesidad de escalar el App Service.

Si se requiere mayor concurrencia, el plan se escala verticalmente a B3 (7 GB RAM, +$28/mes) o P1V3 sin cambios de código.

---

## 5. Despliegue (resumen)

```bash
# 1. Crear grupo de recursos
az group create -n sami-rg -l southamerica

# 2. Crear PostgreSQL Flexible Server
az postgres flexible-server create \
  -g sami-rg -n sami-db \
  --tier Burstable --sku-name Standard_B1ms \
  --admin-user samiadmin --admin-password "<SECRET>" \
  --version 16 --storage-size 32

# 3. Crear App Service Plan
az appservice plan create \
  -g sami-rg -n sami-plan \
  --is-linux --sku B2

# 4. Crear Web App con Python 3.12
az webapp create \
  -g sami-rg -p sami-plan -n sami-app \
  --runtime "PYTHON:3.12"

# 5. Configurar variables de entorno
az webapp config appsettings set \
  -g sami-rg -n sami-app --settings \
  DATABASE_URL="postgresql://samiadmin:<SECRET>@sami-db.postgres.database.azure.com/postgres?sslmode=require" \
  JWT_SECRET="<random 32 bytes>" \
  MODEL_NAME="Recognai/bert-base-spanish-wwm-cased-xnli"

# 6. Desplegar código
az webapp deployment source config-zip \
  -g sami-rg -n sami-app --src dist.zip

# 7. Inicializar BD + admin
az webapp ssh -g sami-rg -n sami-app
> python -c "from app.database import engine, Base; import app.models; Base.metadata.create_all(bind=engine)"
> psql $DATABASE_URL -f seeds/banco_instrumentos.sql
> python -m scripts.seed_admin
```

---

## 6. Costos detallados

| Componente | Costo USD/mes | Costo PEN/mes |
|--|--|--|
| App Service B2 Linux | $26 | ~96 |
| PostgreSQL Burstable B1ms | $13 | ~48 |
| Backups DB (incluido) | $0 | — |
| Bandwidth de salida (< 100 GB) | $0 | — |
| Certificado SSL | $0 | — |
| **Total** | **$39** | **~144** |

### Con Azure for Students
- $100 USD de crédito gratis para cuentas `.edu.pe`
- Cubre **~2.5 meses sin pagar**
- Suficiente para el piloto completo

---

## 7. Justificación académica

La arquitectura sigue el **patrón Web-Queue-Worker simplificado** del Microsoft Well-Architected Framework, eligiendo la variante **monolítica modular** por las siguientes razones:

1. **Tamaño de la carga**: 50–200 usuarios concurrentes no justifica el costo operacional de una arquitectura de microservicios.
2. **Simplicidad de operación**: un solo binario reduce los puntos de falla y facilita la observabilidad para el equipo del colegio.
3. **Latencia interna mínima**: BETO embebido evita el round-trip HTTP que tendría una solución con Azure Functions o Container Apps.
4. **Costo defendible**: $39 USD/mes equivale a **$0.78 USD por alumno por mes** asumiendo 50 alumnos activos.
5. **Camino claro de escalado**: el mismo código puede correr en P1V3 o Container Apps cuando el tráfico lo requiera, sin reescritura.

Referencia metodológica:
> Microsoft. (2024). *Azure Well-Architected Framework — Web application*. Microsoft Learn.

---

## 8. Limitaciones declaradas

Estas limitaciones son **conscientes** y se declaran para honestidad académica:

- **No hay CDN** para los estáticos del frontend. Para piloto en una LAN del colegio es irrelevante.
- **No hay autoescalado horizontal** en B2. Si el tráfico crece, requiere intervención manual (un click en el portal).
- **La inferencia de BETO es síncrona**. En cierres simultáneos puede haber esperas de 15–30 s.
- **Backups solo a nivel base de datos**. La aplicación no tiene estado persistente fuera de PostgreSQL, así que esto es suficiente.
- **Application Insights no está activado** por defecto. Se usan los logs del App Service. Para producción se recomienda activarlo.

---

## 9. Trabajo futuro

- Migrar a Container Apps con BETO en contenedor independiente si la base de usuarios crece > 500 alumnos.
- Activar Application Insights para observabilidad detallada.
- Procesamiento asíncrono de BETO con cola para evitar bloqueo en cierre.
- Integrar el SVM cuando se cuente con datos clínicos reales validados.
