# Auditoría de requisitos — Sami

Verificación de las 53 historias de usuario del `Product_Backlog_Sprints_v3.xlsx`
(Sprints 1–11) contra el código real. Cada HU se marcó revisando el endpoint,
el servicio y la vista que la implementan, no la documentación.

**Resultado: 50 de 53 HU completas (94%), 2 incompletas, 1 sin implementar, y
1 defecto de privacidad en una HU que sí está implementada.**

---

## 1. Estado por sprint

| Sprint | HU | Estado |
|---|---|---|
| 1 — Autenticación | HU-01, 02, 03, 26, 27 | 5/5 ✅ |
| 2 — Perfil y usuarios | HU-04, 05, 06, 20 | 4/4 ✅ |
| 3 — Cuestionarios y NLP | HU-08, 09, 12 | 3/3 ✅ |
| 4 — Contenido y SOS | HU-11, 25, 29, 31 | 4/4 ✅ |
| 5 — Panel psicóloga | HU-14, 15, 16, 17, 19 | 5/5 ✅ |
| 6 — Administración | HU-22, 23, 37 ✅ · **HU-21 ❌** | 3/4 |
| 7 — Proceso del alumno | HU-28, 30 ✅ · **HU-41 ⚠️** | 2/3 |
| 8 — Reportes y gestión | HU-18, 32, 33, 34, 35, 38, 40 | 7/7 ✅ |
| 9 — Sistema de cuestionarios | HU-42, 43, 44, 45, 46, 47 | 6/6 ✅ |
| 10 — SVM, OAuth, despliegue | HU-48, 49, 50, 51, 53, 54 ✅ · **HU-52 ⚠️** | 6/7 |
| 11 — Padres y firma | HU-55, 56, 57, 58, 59 | 5/5 ✅ |

---

## 2. Hallazgo crítico — fuga de notas internas al alumno

**Severidad: alta.** Contradice la regla 4 del diseño ("el alumno nunca ve el
reporte clínico") y la separación de visibilidad por rol.

El modelo `Cita` distingue explícitamente dos campos
(`app/models/cita.py:20-24`):

- `notas` — notas internas de la psicóloga. El comentario del propio modelo
  dice: *"Distinto de las notas clínicas privadas (clinical_notes) y de notas
  internas (notas)"*.
- `resumen_para_estudiante` — *"Resumen breve que el alumno SÍ ve en su panel"*.

El problema es que ambos llegan al alumno:

1. `CitaService._enriquecer` (`app/services/cita_service.py:23`) incluye
   `notas` en el diccionario de salida.
2. `CitaOut` (`app/schemas/cita.py:43`) expone `notas` como campo público.
3. `GET /users/me/citas` (`app/api/v1/endpoints/users.py:70`) devuelve
   `List[CitaOut]` directamente al estudiante autenticado.
4. `StudentHomeView.vue` **renderiza** ese campo como título de la sesión en
   cuatro lugares (líneas 613, 785, 814, 837): `{{ c.notas || "Sesión" }}`.

**Consecuencia.** Toda anotación interna que la psicóloga escriba al crear o
editar una cita (`POST /psicologo/citas`, `PUT /psicologo/citas/{id}`) se
muestra al alumno en su panel. Si escribe "sospecha de violencia familiar,
confirmar con tutoría", el alumno lo lee.

**Atenuante parcial:** cuando la cita la solicita el propio alumno,
`notas` se rellena con su `motivo` (`cita_service.py:129`), así que en ese
caso ve su propio texto. La fuga afecta a las citas creadas por la psicóloga.

**Corrección sugerida:** crear un `CitaOutEstudiante` sin el campo `notas`
(dejando `resumen_para_estudiante`) y usarlo en `GET /users/me/citas`; en el
frontend, reemplazar `c.notas` por un rótulo genérico o por
`c.resumen_para_estudiante`. Es un cambio acotado, ~30 líneas.

---

## 3. HU no implementadas o incompletas

### HU-21 — Configurar parámetros generales del sistema ❌ No implementada

*"Como Administrador quiero configurar parámetros generales del sistema para
adaptarlo a las necesidades del colegio."*

- El modelo `Configuracion` (`app/models/configuracion.py`) existe y crea su
  tabla, pero es código muerto: se importa en `admin.py:15` con
  `# noqa: F401`, únicamente para registrar la tabla en el metadata.
- **No hay ningún endpoint** de lectura ni escritura de configuración.
- `AdminSystemView.vue` no tiene ninguna llamada relacionada: solo consulta
  info del modelo NLP, backups y estadísticas.

Es la única HU del backlog sin nada de implementación funcional.

### HU-41 — Cierre automático de ciclos ⚠️ Mitad implementada

*"…cerrar automáticamente los ciclos de evaluación cada 14 días **y disparar la
encuesta de cierre**."*

- ✅ El cierre funciona: `_cierre_ciclos_job` (`scheduler_service.py:65`) corre
  a las 03:00 y marca como `expirada` toda aplicación pendiente o en progreso
  con más de 14 días (`CICLO_DIAS_VENTANA`).
- ❌ **No dispara la encuesta de cierre.** El job termina en el `commit` del
  cambio de estado; no crea ninguna encuesta ni notifica al alumno. La segunda
  mitad de la HU no existe.

### HU-52 — Mensaje de la psicóloga al alumno ⚠️ Funciona, pero ver §2

Está implementada correctamente: la psicóloga escribe en
`resumen_para_estudiante` vía `PUT /psicologo/citas/{id}` y el alumno lo lee en
`StudentHomeView.vue:191-202`. Se marca en amarillo solo porque convive con la
fuga del campo `notas` descrita arriba, que hay que arreglar en el mismo sitio.

---

## 4. Deuda no funcional

Esto no está en el backlog de HU, pero es lo que un jurado o un revisor va a
mirar.

| Ítem | Estado | Comentario |
|---|---|---|
| **Pruebas automatizadas** | ❌ **Ninguna** | No existe un solo archivo `test_*.py` en el repositorio. Cero cobertura sobre el `EvaluatorService`, que es el componente con lógica clínica más sensible del sistema. |
| Prueba de carga (`scripts/load_test.py`) | ❌ No existe | Planificada en `PENDIENTES.md:46` (locust, 50 usuarios × 10 min, latencias p50/p95/p99). |
| Middleware de auditoría | ✅ Activo | `AccessLogMiddleware` registrado en `main.py:31`. |
| Despliegue en Azure | ✅ Operativo | App Service + PostgreSQL, HTTPS forzado. |
| Backups automáticos | ✅ Activos | Diarios a las 02:00, con purga por retención. |

**La ausencia de tests es el hallazgo no funcional más serio.** El
`EvaluatorService` decide qué alumno se marca como CRÍTICO; ahora mismo nada
impide que un refactor cambie un corte silenciosamente. Un set mínimo de
pruebas sobre las 5 capas del evaluator (una por instrumento, más los casos
frontera de cada corte y las banderas de crisis) es alcanzable en pocas horas y
cambia sustancialmente la defensa de la calidad del sistema.

---

## 5. Deuda académica (validación)

Del plan en `METRICAS_VALIDACION.md` y `PENDIENTES.md`:

| Dimensión | Estado |
|---|---|
| Rendimiento del SVM | ✅ Completo — entrenamiento + validación externa, ver `VALIDACION_DETALLADA.md` |
| Rendimiento de BETO | ✅ Completo — EmoEvent multiclase y binario |
| Consistencia interna (α Cronbach) | ⚠️ Parcial — calculada para DASS-21 (Pack B). **Falta PHQ-A y GAD-7**, y los datos ya están cargados: el Pack A tiene 37 alumnos con ambas escalas. Es computable hoy, sin recolectar nada. |
| Usabilidad (SUS o % satisfacción) | ❌ Sin datos — 0 registros en `satisfaction_surveys` |
| Concordancia clínica (κ de Cohen) | ❌ No iniciada — requiere 30 vignettes evaluadas a ciegas por una psicóloga |
| Rendimiento del sistema (latencias) | ❌ No iniciada — falta el script de carga |

---

## 6. Prioridades sugeridas

1. **Arreglar la fuga de `notas`** (§2). Es un defecto de privacidad en un
   sistema de salud mental de menores. ~30 líneas.
2. **Calcular α de Cronbach para PHQ-A y GAD-7** sobre el Pack A. Los datos ya
   están en la base; cierra una dimensión de validación sin trabajo de campo.
3. **Tests del `EvaluatorService`.** El mayor retorno por hora invertida para
   la calidad defendible del sistema.
4. **Recolectar usabilidad** (SUS o el instrumento de 5 ítems ya desplegado).
   Requiere una sesión con usuarios reales — es lo que más tarda en
   calendario, conviene arrancarlo ya.
5. **HU-21 y la encuesta de cierre de HU-41.** Son las dos brechas
   funcionales; ninguna es bloqueante para la defensa, pero completan el
   backlog al 100%.

---

## 7. Auditoría inversa: código → backlog (HU faltantes)

Las secciones anteriores verifican backlog → código. Esta verifica lo
contrario: **funcionalidad que existe y funciona, pero que ninguna HU del
backlog v3 describía.** Se recorrieron los 90 endpoints registrados en
`app.main`, los 88 métodos de `project/src/api.js` y las 31 vistas del router.

Resultado: **16 funcionalidades implementadas sin historia de usuario.** Se
incorporaron como HU-60 … HU-75 en `Product_Backlog_Sprints_v4.xlsx`.

| HU | Funcionalidad sin historia | Evidencia en código | Sprint |
|---|---|---|---|
| HU-60 | Login con Microsoft (OAuth) | `POST /auth/oauth/microsoft`, `api.oauthMicrosoft` | 10 |
| HU-61 | Cambiar contraseña autenticado | `PUT /users/me/password` | 2 |
| HU-62 | Registro y acceso del rol Padre | `RegisterView.vue` (rol padre), `schemas/auth.py:16`, guard del router | 11 |
| HU-63 | Ver la psicóloga asignada | `GET /users/me/psicologo` | 7 |
| HU-64 | Horarios sugeridos para la cita | `GET /users/me/slots-sugeridos` | 7 |
| HU-65 | Bandeja de SOS de la psicóloga | `GET /sos/abiertos`, `PATCH /sos/{id}/atender`, `PsychologistSOSView.vue` | 5 |
| HU-66 | Guardado parcial del cuestionario | `POST /cuestionarios/responder/{id}/guardar` | 9 |
| HU-67 | Psicóloga vincula padre a estudiante | `GET /psychologist/padres`, `POST/DELETE .../assign-padre` | 11 |
| HU-68 | Estado y recarga del modelo NLP | `GET /admin/nlp/modelo`, `POST /admin/nlp/recargar` | 6 |
| HU-69 | Tablero de reportes del admin | `GET /admin/cuestionarios/stats`, `AdminReportsView.vue` | 8 |
| HU-70 | Resumen de la encuesta de satisfacción | `GET /survey/admin/satisfaction/summary` | 6 |
| HU-71 | Detalle de un hijo (padre) | `GET /padre/hijos/{id}`, `PadreHijoView.vue` | 11 |
| HU-72 | Marcar aplicación como revisada | `POST /cuestionarios/aplicacion/{id}/marcar-revisado` | 9 |
| HU-73 | Respaldo manual y estado del scheduler | `POST /admin/backup`, `GET /admin/scheduler/info` | 6 |
| HU-74 | Reprogramar o cancelar una cita | `PUT`/`DELETE /psychologist/citas/{id}` | 5 |
| HU-75 | Panel clínico rediseñado (shell + sidebar) | `AppShellPsico.vue`, `AppSidebar.vue`, `App.vue:89` | 10 |

Cada una se asignó al sprint donde encaja funcionalmente y está marcada en el
Excel con la nota «Regularización». Los totales por sprint, por épica y de
story points se recalcularon: **69 HU y 308 SP** (antes 53 HU y 257 SP).

### Defecto documental detectado de paso

`HU-42` menciona DASS-21 como parte del banco, y la capa 5 del evaluador
(`_segunda_opinion_svm`) depende de que ese instrumento exista. Pero
**`seeds/banco_instrumentos.sql` no incluye DASS-21**: se siembra aparte con
`scripts/seed_dass21.py`, y el arranque documentado en `CLAUDE.md` no ejecuta
ese script. En una instalación limpia siguiendo la guía, el SVM (HU-48 y
HU-49) nunca se dispara porque ninguna plantilla puede contener DASS-21.
Corrección: añadir `venv/bin/python -m scripts.seed_dass21` al primer arranque.

---

## 8. Criterios de aceptación

El backlog v3 **no tenía criterios de aceptación en ninguna de sus 53 HU** —
solo una columna de «Notas / Justificación» con la razón de negocio. Se
redactaron **164 escenarios en formato Gherkin** (Dado / Cuando / Entonces)
cubriendo las 69 HU, escritos contra el comportamiento real del código.

Ubicación en `Product_Backlog_Sprints_v4.xlsx`:

- Hoja **Product Backlog**, columna J — el bloque Gherkin completo de cada HU
  junto a su historia; columna K — el estado verificado en código.
- Hoja **Criterios de Aceptación** — un escenario por fila (HU, Sprint, Rol,
  N.º, título del escenario, pasos), que es el formato manejable para
  trazabilidad y para derivar casos de prueba.

Cada HU tiene entre 1 y 5 escenarios: el camino feliz más los casos borde
relevantes (permisos por rol, validaciones, estados vacíos, y las reglas de
privacidad que separan lo que ve el alumno de lo que ve la psicóloga).

Fuente reproducible: `scripts/criterios_aceptacion.py` (los criterios) y
`scripts/generar_backlog_v4.py` (genera el Excel desde v3).
