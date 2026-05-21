# Salud Mental UPC — Registro de Sprints

> **Stack:** FastAPI + SQLite (backend) · Vue 3 + Vite + Tailwind + Chart.js (frontend)  
> **Modelo NLP:** `Recognai/bert-base-spanish-wwm-cased-xnli` (BETO + XNLI, zero-shot multi-label)  
> **Escalas clínicas de referencia:** PHQ-9, GAD-7, ASRS, UCLA-3, C-SSRS

---

## Sprint 1 — Autenticación, consentimiento y perfil ✅

**Estado:** Completado y commiteado (`2e538df`)  
**Objetivo:** Infraestructura base: registro, acceso seguro y gestión de identidad del estudiante.

### Historias de usuario

| HU | Historia | Módulo |
|----|----------|--------|
| HU-01 | Como Estudiante quiero registrarme con mis datos personales para acceder al sistema | `auth.py` / `RegisterView.vue` |
| HU-02 | Como Estudiante quiero iniciar sesión con JWT para navegar de forma segura según mi rol | `auth_service.py` / `LoginView.vue` |
| HU-03 | Como Estudiante quiero firmar el consentimiento informado antes de usar el chatbot | `consent.py` / `ConsentView.vue` |
| HU-04 | Como Estudiante quiero ver y editar mi perfil personal | `users.py` / `ProfileView.vue` |
| HU-05 | Como Estudiante quiero recuperar mi contraseña si la olvido | `password_reset.py` / `ForgotPasswordView.vue` |
| HU-06 | Como Administrador quiero gestionar usuarios (activar/desactivar) desde un panel | `admin.py` / `AdminDashboardView.vue` |

### Lo que se construyó

- Modelos ORM: `User`, `UserSession`, `UserResponse`, `RiskResult`
- Sistema JWT con roles: `estudiante`, `psicologo`, `admin`
- Base de datos SQLite con creación automática de tablas en startup
- Pantallas: `LoginView`, `RegisterView`, `ConsentView`, `ForgotPasswordView`, `ResetPasswordView`, `ProfileView`, `MainMenuView`, `AdminDashboardView`

---

## Sprint 2 — Panel del psicólogo ✅

**Estado:** Completado y commiteado (`2e538df`)  
**Objetivo:** Dar al psicólogo visibilidad sobre el estado general de sus estudiantes.

### Historias de usuario

| HU | Historia | Módulo |
|----|----------|--------|
| HU-10 | Como Psicólogo quiero ver la lista de todos los estudiantes con su último nivel de riesgo | `psychologist.py` / `PsychologistDashboardView.vue` |
| HU-11 | Como Psicólogo quiero ver el resumen de sesiones completadas por cada estudiante | `psychologist_service.py` |

### Lo que se construyó

- `PsychologistService.listar_estudiantes()`: devuelve para cada estudiante sus sesiones totales, completadas, último riesgo/score y fecha de evaluación
- `PsychologistDashboardView.vue`: tabla con filtros, badge de riesgo coloreado, acceso al historial individual

---

## Sprint 3 — Núcleo funcional: chatbot PLN + encuestas + modelo BERT ✅

**Estado:** Completado y commiteado (`2e538df`)  
**Puntos de historia:** 26 | **Duración:** 3 semanas  
**Objetivo:** Sprint más importante del proyecto. Implementa el chatbot conversacional, la aplicación de PHQ-9 y GAD-7, y la integración del modelo BERT. Es el corazón del sistema.

### Historias de usuario

| HU | Historia | Criterios de aceptación | Módulo |
|----|----------|------------------------|--------|
| HU-07 | Como Estudiante quiero conversar con el chatbot basado en PLN para expresar cómo me siento emocionalmente | El estudiante responde 10 preguntas abiertas en formato chat · Cada respuesta se persiste · La sesión pasa a "completada" al finalizar | `chatbot.py` / `chat_service.py` / `ChatView.vue` |
| HU-08 | Como Estudiante quiero responder encuestas validadas como PHQ-9 y GAD-7 para que el sistema analice mi estado de salud mental | Las 10 preguntas cubren PHQ-9, GAD-7, ASRS, UCLA-3 y C-SSRS · Las respuestas quedan mapeadas a condiciones clínicas | `session_service.py` / `ChatView.vue` |
| HU-09 | Como Sistema quiero analizar el texto del estudiante mediante el modelo BERT para detectar señales tempranas de ansiedad, depresión o estrés | El modelo clasifica 6 condiciones con score y nivel · Se genera explicación clínica en español · El resultado se muestra al estudiante con gráfico | `nlp_service.py` / `ResultsView.vue` |

### Lo que se construyó

#### HU-07 — Chatbot conversacional (PLN)

- **`ChatView.vue`**: interfaz estilo ChatGPT, burbuja del sistema + input del usuario, barra de progreso de 10 preguntas, transición automática a resultados al completar
- **`ChatService`**: orquesta el flujo sesión → respuesta → avance → cierre; valida estado y evita respuestas duplicadas
- **`/api/v1/chatbot/sesion`** (POST): crea sesión y devuelve pregunta 1  
- **`/api/v1/chatbot/responder`** (POST): guarda respuesta y devuelve siguiente pregunta o señal de completado  
- **`/api/v1/chatbot/analizar`** (POST): dispara el análisis NLP sobre la sesión completa

#### HU-08 — Encuestas validadas PHQ-9 y GAD-7

10 preguntas abiertas alineadas a escalas clínicas validadas, redactadas de forma conversacional para capturar matices en el texto libre:

| # | Condición objetivo | Escala de referencia |
|---|-------------------|----------------------|
| 1 | Depresión — anhedonia | PHQ-9 ítem 2 |
| 2 | Depresión — ánimo y autoestima | PHQ-9 ítems 1, 6 |
| 3 | Ansiedad — preocupación y tensión | GAD-7 ítems 1-3 |
| 4 | TDAH — inatención | ASRS-v1.1 ítems 1-4 |
| 5 | TDAH — hiperactividad / impulsividad | ASRS-v1.1 ítems 5-6 |
| 6 | Estrés académico y adaptación provincia→Lima | — |
| 7 | Soledad | UCLA-3 Loneliness Scale |
| 8 | Sueño y somatización | PHQ-9 ítem 3 |
| 9 | Ideación suicida / autolesión | PHQ-9 ítem 9 + C-SSRS |
| 10 | Red de apoyo y búsqueda de ayuda | — |

#### HU-09 — Modelo BERT para análisis de texto

- **Modelo:** `Recognai/bert-base-spanish-wwm-cased-xnli` (BETO + XNLI, ~400 MB)
- **Técnica:** Zero-shot multi-label classification con hypothesis templating en español
- **`NLPService` (Singleton, thread-safe):**
  - Carga única del modelo en memoria (double-check locking)
  - Un solo forward pass sobre el texto concatenado de las 10 respuestas
  - Keyword boost por condición (refuerza score cuando hay términos clínicos explícitos)
  - Umbrales calibrados por condición (riesgo suicida: 0.40 — sensibilidad alta)
  - Generación de explicación clínica en español con recomendaciones por condición
- **`ResultsView.vue`**: perfil de riesgo global, gráfico de barras horizontales con score por condición, indicaciones y conclusión para el psicólogo, botón Imprimir/PDF

**Condiciones detectadas y umbrales:**

| Condición | Umbral | Escala |
|-----------|--------|--------|
| Depresión | 0.55 | PHQ-9 |
| Ansiedad | 0.55 | GAD-7 |
| TDAH | 0.55 | ASRS |
| Estrés académico | 0.50 | — |
| Soledad | 0.50 | UCLA-3 |
| Riesgo suicida | 0.40 | C-SSRS |
| Estabilidad emocional | 0.60 | — |

**Niveles de riesgo global:**

| Nivel | Criterio |
|-------|----------|
| CRÍTICO | Riesgo suicida detectado (score ≥ 0.40) |
| ALTO | ≥2 condiciones detectadas, o alguna con confianza ≥75% |
| MEDIO | 1 condición detectada con confianza moderada |
| BAJO | Ninguna condición detectada + estabilidad alta |

---

## Sprint 4 — Cierre del valor para el estudiante ✅

**Estado:** Implementado — pendiente de commit  
**Puntos de historia:** 16 | **Duración:** 4 semanas  
**Objetivo:** El estudiante recibe recomendaciones personalizadas, accede a recursos UPC, ve su historial emocional y recibe notificaciones de seguimiento. Aquí se completa la experiencia del usuario final.

### Historias de usuario

| HU | Historia | Criterios de aceptación | Estado |
|----|----------|------------------------|--------|
| HU-10 | Como Estudiante quiero recibir recomendaciones personalizadas según el estado emocional detectado | Se muestran tarjetas con pasos concretos por cada condición detectada; si no hay condiciones, se dan recomendaciones de mantenimiento | ✅ Implementado |
| HU-11 | Como Estudiante quiero acceder a los recursos de salud mental disponibles en la UPC para buscar apoyo profesional | Vista con Bienestar Estudiantil UPC, líneas de crisis nacionales (Línea 113, SALUDLINE, Teléfono de la Esperanza) y consejos de autocuidado | ✅ Implementado |
| HU-12 | Como Estudiante quiero ver mi historial emocional para conocer mi evolución a lo largo del tiempo | El estudiante ve su serie temporal de riesgo en un gráfico de línea y el detalle de cada sesión con conversación y scores por respuesta | ✅ Implementado |
| HU-13 | Como Estudiante quiero recibir notificaciones para realizar mis encuestas periódicas de seguimiento emocional | Banner de recordatorio en el menú si han pasado ≥7 días desde la última evaluación, o si nunca se ha evaluado | ✅ Implementado |

### Cambios realizados

#### HU-10 — Recomendaciones personalizadas

**`project/src/components/ResultsScreen.vue`** — nueva sección de recomendaciones
- Mapeo `RECOMENDACIONES` por condición: título, icono y 4 pasos concretos de acción
- Si hay condiciones detectadas: tarjetas individuales con badge de confianza y pasos en lista
- Si no hay condiciones: sección verde de recomendaciones de mantenimiento
- Condiciones cubiertas: Depresión, Ansiedad, TDAH, Estrés académico, Soledad, Riesgo suicida

#### HU-11 — Recursos de salud mental UPC

**`project/src/views/RecursosView.vue`** — vista nueva accesible por todos los roles
- Alerta de crisis destacada al tope (Línea 113 opción 5)
- Tarjetas de líneas de emergencia: Línea 113 MINSA · SALUDLINE 106 · Teléfono de la Esperanza
- Servicios dentro de la UPC: Bienestar Estudiantil (dirección, teléfono, horario) + Centro Médico
- 6 tarjetas de autocuidado: sueño, actividad física, red de apoyo, respiración, rutina, desconexión digital
- CTA para iniciar evaluación desde la vista

#### HU-12 — Historial emocional del estudiante

**`app/api/v1/endpoints/chatbot.py`** — nuevo endpoint `GET /chatbot/mi-historial`
- Requiere autenticación (cualquier rol); reutiliza `PsychologistService.historial_estudiante()` con el `user_id` del JWT

**`project/src/views/MiHistorialView.vue`** — vista nueva para el estudiante
- Header con datos propios (nombre, email, contadores, último riesgo)
- Gráfico de línea Chart.js: evolución temporal del nivel de riesgo
- Acordeón de sesiones: pregunta + respuesta + badge de nivel/condición por respuesta
- Estado vacío con CTA a `/chat` si no hay evaluaciones
- Enlace a recursos UPC al final

**`project/src/api.js`** — nuevo método `api.miHistorial()`

**`project/src/router/index.js`** — nueva ruta `/mi-historial` (rol: estudiante)

#### HU-13 — Notificaciones de seguimiento

**`project/src/views/MainMenuView.vue`** — banner de recordatorio
- En `onMounted`: llama a `api.miHistorial()` para obtener `ultima_evaluacion`
- Si nunca evaluó: "Aún no tienes evaluaciones. ¡Comienza ahora!"
- Si han pasado ≥7 días: "Han pasado N días desde tu última evaluación. Se recomienda hacerlo semanalmente."
- Botón "Evaluar ahora" integrado en el banner

#### Opciones del menú del estudiante — actualización

Se agregaron dos tarjetas nuevas al menú del estudiante:
- **Mi historial emocional** (`/mi-historial`) — icono 📈
- **Recursos de salud mental** (`/recursos`) — icono 🩺

### Pendiente (Sprint 4 → backlog)

- [ ] Notificaciones por email (requiere servidor SMTP o servicio externo como SendGrid)
- [ ] Backfill de `score_riesgo / nivel_riesgo / condicion_dominante` en sesiones anteriores: `python -m scripts.backfill_response_scores`
- [ ] Migración de BD en entornos existentes (3 columnas nuevas en `user_responses`)
- [ ] Commit del Sprint 4

---

## Sprint 4b — Historial detallado para el psicólogo (HU-20) ✅

**Estado:** Implementado junto con Sprint 4 — pendiente de commit

### Historia de usuario

| HU | Historia | Estado |
|----|----------|--------|
| HU-20 | Como Psicólogo quiero ver el historial emocional completo de un estudiante con evolución temporal y conversación detallada | ✅ Implementado |

### Cambios realizados

**`app/models/response.py`** — 3 nuevos campos en `UserResponse`: `score_riesgo`, `nivel_riesgo`, `condicion_dominante`

**`app/services/nlp_service.py`** — `analizar_respuesta_individual()`: score de criticidad por respuesta individual

**`app/services/chat_service.py`** — `_calcular_scores_por_respuesta()`: se ejecuta al completar análisis, persiste los 3 campos

**`app/services/psychologist_service.py`** — `historial_estudiante()`: sesiones + conversación + serie temporal

**`project/src/views/StudentHistoryView.vue`** — vista del psicólogo con gráfico de línea + acordeón de sesiones

**`scripts/backfill_response_scores.py`** — migración de sesiones anteriores

---

---

## Sprint 5 — Panel del psicólogo: monitoreo y atención profesional ✅

**Estado:** Implementado — pendiente de commit  
**Puntos de historia:** 25 | **Duración:** 5 semanas  
**Objetivo:** Los psicólogos acceden al sistema, ven el dashboard, reciben alertas de riesgo, consultan historiales y agendan citas. Habilita la intervención humana profesional.

### Historias de usuario

| HU | Historia | Criterios de aceptación | Estado |
|----|----------|------------------------|--------|
| HU-14 | Como Psicólogo quiero iniciar sesión para acceder al panel de monitoreo | Login unificado con roles — el JWT identifica al psicólogo y le da acceso a `/psicologo` | ✅ Ya implementado (Sprint 1) |
| HU-15 | Como Psicólogo quiero visualizar un dashboard con métricas generales | 5 tarjetas: Total · CRÍTICO · ALTO · MEDIO · BAJO+Sin eval; datos en tiempo real desde BD | ✅ Implementado |
| HU-16 | Como Psicólogo quiero recibir alertas tempranas cuando un estudiante presente riesgo alto | Panel de alertas visible al tope del dashboard; lista de estudiantes CRÍTICO/ALTO con acceso directo a cita e historial | ✅ Implementado |
| HU-17 | Como Psicólogo quiero acceder al historial emocional de un estudiante específico | Vista de historial con gráfico de evolución + acordeón de sesiones con conversación y scores | ✅ Ya implementado (Sprint 4b/HU-20) |
| HU-19 | Como Psicólogo quiero agendar una cita con un estudiante | Modal de agendamiento (fecha, hora, modalidad, notas); estados pendiente/confirmada/completada/cancelada; disponible desde dashboard y desde el historial del estudiante | ✅ Implementado |

### Cambios realizados

#### Backend

**`app/models/cita.py`** — nuevo modelo `Cita`
- Campos: `psicologo_id`, `estudiante_id`, `fecha` (YYYY-MM-DD), `hora` (HH:MM), `modalidad` (presencial/virtual), `estado` (pendiente/confirmada/cancelada/completada), `notas`
- Tabla `citas` creada automáticamente en startup

**`app/schemas/cita.py`** — schemas Pydantic: `CitaCreate`, `CitaUpdate`, `CitaOut` (incluye nombre/apellido/email del estudiante)

**`app/services/cita_service.py`** — CRUD completo
- `crear()`, `listar()` (filtrable por estudiante), `actualizar()`, `cancelar()`

**`app/services/psychologist_service.py`** — nuevo método `stats_dashboard()`
- Itera todos los estudiantes activos, obtiene su último `RiskResult`
- Devuelve: `total_estudiantes`, `distribucion_riesgo` (por nivel), `estudiantes_en_alerta` (CRÍTICO/ALTO, ordenados por severidad y fecha)

**`app/api/v1/endpoints/psychologist.py`** — 5 nuevos endpoints
- `GET /psychologist/dashboard-stats` — métricas HU-15/HU-16
- `POST /psychologist/citas` — crear cita
- `GET /psychologist/citas` — listar citas (con filtro opcional por estudiante)
- `PUT /psychologist/citas/{id}` — actualizar estado/notas
- `DELETE /psychologist/citas/{id}` — cancelar cita

#### Frontend

**`project/src/views/PsychologistDashboardView.vue`** — revamp completo
- 5 tarjetas de métricas (HU-15): Total · CRÍTICO · ALTO · MEDIO · BAJO+Sin eval
- Panel de alertas tempranas (HU-16): lista de CRÍTICO/ALTO con botones "Agendar cita" y "Ver historial"
- Próximas citas (HU-19): lista de citas no canceladas con acciones Confirmar/Completada/Cancelar
- Tabla de estudiantes (HU-17): añade botón "+ Cita" por fila
- Modal de agendamiento integrado

**`project/src/views/StudentHistoryView.vue`** — añadido
- Botón "+ Agendar cita" en el header
- Modal de agendamiento idéntico al del dashboard
- Badge de confirmación "Cita agendada" tras guardar

**`project/src/api.js`** — 4 nuevos métodos: `dashboardStats()`, `crearCita()`, `listarCitas()`, `actualizarCita()`, `cancelarCita()`

---

## Sprint 6 — Administración y mantenimiento del sistema ✅

**Estado:** Implementado — pendiente de commit  
**Puntos de historia:** 26 | **Duración:** 5 semanas  
**Objetivo:** El administrador configura encuestas, audita accesos, gestiona respaldos y calibra el modelo BERT. Asegura sostenibilidad y cumplimiento Ley 29733.

### Historias de usuario

| HU | Historia | Criterios de aceptación | Estado |
|----|----------|------------------------|--------|
| HU-21 | Como Administrador quiero configurar las preguntas y la frecuencia de las encuestas | Admin edita las N preguntas del chatbot + frecuencia en días; cambios se aplican en caliente y persisten entre reinicios | ✅ Implementado |
| HU-22 | Como Administrador quiero auditar los accesos al sistema | Cada llamada a `/api/v1` queda en `access_logs` con usuario, rol, endpoint, status y IP; el admin puede filtrar y paginar | ✅ Implementado |
| HU-23 | Como Administrador quiero realizar respaldos automáticos de la BD | Botón "Crear respaldo" copia `mental_health.db` a `backups/backup_YYYYMMDD_HHMMSS.db`; lista los backups existentes con tamaño y fecha | ✅ Implementado |
| HU-24 | Como Administrador quiero reentrenar periódicamente el modelo BERT | Botón "Recargar modelo" descarga el singleton de `NLPService` de memoria; panel muestra estado (cargado/no cargado), dispositivo, tiempo de carga | ✅ Implementado |
| HU-36 | Como Administrador quiero configurar los umbrales del modelo BERT | Sliders + inputs numéricos por condición; los cambios se aplican de inmediato a `settings.CONDICIONES` y persisten en BD | ✅ Implementado |

### Cambios realizados

#### Backend — 4 archivos nuevos

**`app/models/configuracion.py`** — tabla `configuraciones` (clave/valor JSON)
- Almacena: `preguntas_encuesta` (lista JSON), `frecuencia_evaluacion_dias` (int), `bert_umbrales` (dict JSON)

**`app/models/access_log.py`** — tabla `access_logs`
- Campos: `user_id`, `email`, `role`, `method`, `endpoint`, `status_code`, `ip`, `timestamp`

**`app/middleware/access_log.py`** — `AccessLogMiddleware` (Starlette BaseHTTPMiddleware)
- Intercepta cada request a `/api/v1`; extrae usuario del JWT; persiste en `access_logs` después de la respuesta (no bloquea)

**`app/services/admin_service.py`** — expandido con 10 nuevos métodos
- `get_encuesta()` / `update_encuesta()` — HU-21: lee/escribe preguntas + frecuencia
- `get_audit_logs()` — HU-22: paginado, filtrable por rol y endpoint
- `crear_backup()` / `listar_backups()` — HU-23: copia SQLite a `backups/`
- `get_umbrales()` / `update_umbrales()` — HU-36: lee/aplica umbrales BERT
- `get_modelo_info()` / `recargar_modelo()` — HU-24: estado y reset del singleton
- `aplicar_config_inicio()` — carga umbrales y preguntas desde BD al arrancar

**`app/api/v1/endpoints/admin.py`** — 9 nuevos endpoints
- `GET/PUT /admin/config/encuesta`
- `GET /admin/audit-logs`
- `POST /admin/backup` · `GET /admin/backups`
- `GET/PUT /admin/bert/umbrales`
- `GET /admin/bert/modelo` · `POST /admin/bert/recargar`

**`app/main.py`** — 2 cambios
- Agrega `AccessLogMiddleware` al stack de middlewares
- En startup: llama `AdminService.aplicar_config_inicio()` para cargar config persistida

#### Frontend — 1 vista nueva

**`project/src/views/AdminSystemView.vue`** — vista con 4 pestañas
- **Encuesta** (HU-21): tabla editable de preguntas + input de frecuencia + botón guardar
- **Auditoría** (HU-22): tabla paginada de access logs con filtros por rol y endpoint; colores por status code
- **Respaldos** (HU-23): lista de backups con tamaño/fecha + botón "Crear respaldo ahora"
- **Modelo BERT** (HU-24 + HU-36): panel de estado del modelo (cargado/tiempo/dispositivo) + botón recargar + sliders/inputs de umbrales por condición

**`project/src/views/MainMenuView.vue`** — nueva opción "Configuración del sistema" (⚙️) para admins → `/admin/sistema`

**`project/src/router/index.js`** — nueva ruta `/admin/sistema` (rol: admin)

**`project/src/api.js`** — 10 nuevos métodos: `adminGetEncuesta`, `adminUpdateEncuesta`, `adminGetAuditLogs`, `adminCrearBackup`, `adminListarBackups`, `adminGetUmbrales`, `adminUpdateUmbrales`, `adminGetModeloInfo`, `adminRecargarModelo`

---

## Arquitectura del proyecto

```
salud-mental-TP1/
├── app/
│   ├── api/v1/endpoints/
│   │   ├── auth.py          → HU-01, HU-02, HU-03, HU-05
│   │   ├── users.py         → HU-04
│   │   ├── admin.py         → HU-06
│   │   ├── chatbot.py       → HU-07, HU-08, HU-09
│   │   ├── psychologist.py  → HU-10, HU-11, HU-20
│   │   └── consent.py       → HU-03
│   ├── models/              → SQLAlchemy ORM (User, UserSession, UserResponse, RiskResult)
│   ├── services/            → lógica de negocio por dominio
│   ├── schemas/             → validación Pydantic
│   └── config.py            → modelo NLP, condiciones, umbrales, keywords
├── project/src/
│   ├── views/               → una View por pantalla
│   ├── components/          → componentes reutilizables
│   └── api.js               → cliente Axios centralizado
└── scripts/
    └── backfill_response_scores.py   → migración Sprint 4
```
