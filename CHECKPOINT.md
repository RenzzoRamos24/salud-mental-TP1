# Checkpoint — sesión 2026-05-29 / 30 (madrugada)

Sesión completa de planificación + implementación. El usuario quería
avanzar el código antes de dormir; se terminó todo lo accionable de la
sesión y queda commiteado (`ebb4d03`).

---

## 1. Decisiones de diseño tomadas

### 1.1. Sami es un diario, no un chatbot
El flujo conversacional de 10 preguntas (chatbot) sobra. El diario es la
pieza fuerte del sistema porque su ventana de 14 días encaja literal
con el PHQ-A.

### 1.2. Modelo de ciclos
El ciclo dura **14 días desde la primera entrada** del alumno. Cierra
automáticamente al cumplir el día 14, **siempre**. Día 15 = Día 1 del
Ciclo N+1. Las **citas regulares** corren **en paralelo** al ciclo.
**Excepción:** una cita marcada `es_crisis=True` que se complete
**adelanta el cierre** del ciclo. Al día siguiente arranca el siguiente.

### 1.3. Tabla días→puntos PHQ-A (defensa)
Tabla por traducción literal de las frases Johnson 2002:
0 días = 0, 1-7 = 1, 8-11 = 2, 12-14 = 3.

---

## 2. Implementado y commiteado (`ebb4d03`)

### Backend

| Archivo | Cambio |
|---|---|
| `app/models/cita.py` | + columna `es_crisis: Boolean` |
| `app/schemas/cita.py` | `es_crisis` en CitaCreate / CitaUpdate / CitaOut |
| `app/services/cita_service.py` | `crear()` acepta y persiste `es_crisis` |
| `app/services/ciclo_service.py` | **Reescritura completa**: cierre por tiempo, citas regulares paralelas, citas de crisis adelantan cierre. |
| `app/services/diario_analisis_service.py` | + `reporte_ciclo(db, user_id, ini, fin)`: agrega por días-con-síntoma y mapea con la tabla Johnson. Devuelve PHQ-A total, GAD-7 total, severidades, `items_detalle` y confiabilidad (baja <5, media 5-9, alta ≥10). |
| `app/api/v1/endpoints/psychologist.py` | + `GET /students/{id}/reporte-ciclo?ciclo=N` |
| `scripts/migrate_cita_crisis.py` | Migración idempotente para `es_crisis` (ya ejecutada). |

### Frontend

| Archivo | Cambio |
|---|---|
| `project/src/router/index.js` | Rutas `/chat`, `/resultados`, `/admin/mensajes-chatbot` eliminadas. Imports limpiados. |
| `project/src/views/MainMenuView.vue` | Tile "Mensajes de Sami" sacado del menú admin. |
| `project/src/api.js` | + `reporteCicloEstudiante(student_id, ciclo)` |
| `project/src/views/StudentHistoryView.vue` | + sección "Reporte del ciclo" con tabla por ítem (días con síntoma, puntos, frase oficial). + checkbox "Atención de crisis" en modal de cita. |
| `project/src/views/PsychologistDashboardView.vue` | + checkbox "Atención de crisis" en modal de cita. + badge "Crisis" en lista de próximas citas. |

### Documentos

| Archivo | Cambio |
|---|---|
| `docs/generar_documento_sami.py` | Reescrito en lenguaje sencillo, con todo el flujo nuevo. |
| `docs/Diseño_del_sistema_Sami.docx` | Regenerado, 52 KB. |
| `CHECKPOINT.md` | Este archivo. |

### Verificación
- Backend importa OK con 79 rutas.
- `vite build` corre sin errores.
- `info_ciclo_estudiante` y `reporte_ciclo` smoke-tested.

---

## 3. Lo que NO está hecho (siguiente sesión)

### 3.1. Figma — mockups
Requiere interacción del usuario con Figma. Plan: usar el skill
`figma-generate-design` para empujar las pantallas clave desde el código.
Frames a crear/actualizar:
- Login / asentimiento.
- Vista del diario con prompt + zona de escritura + consejo.
- Vista "Mi proceso" del alumno.
- Dashboard psicóloga con las 3 bandejas (crítica / cierres / cohorte).
- Reporte de ciclo (la nueva sección de `StudentHistoryView`).
- Modal de cita con flag de crisis.

### 3.2. Duplicación de "resumen del diario" vs "reporte de ciclo"
`StudentHistoryView` ahora muestra **dos** secciones de análisis:
- La antigua "Estado de evaluación" + "Métricas agregadas" (`resumen_diario_estudiante` con promedios).
- La nueva "Reporte del ciclo" (`reporte_ciclo` con días-con-síntoma).

Conviven sin romperse, pero conceptualmente la nueva reemplaza a la
antigua. Decidir si se elimina la antigua o se deja como "preview en
curso" para ciclos abiertos.

### 3.3. Chatbot backend
Ocultado del frontend pero el código sigue en repo:
- `app/api/v1/endpoints/chatbot.py`, `app/services/chat_service.py`,
  `app/services/session_service.py`, `app/models/session.py`,
  `app/models/response.py`, `app/schemas/chat.py`,
  `project/src/views/ChatView.vue`,
  `project/src/views/ResultsView.vue`,
  `project/src/views/AdminChatbotMessagesView.vue`,
  `project/src/components/ResultsScreen.vue`.

Datos en `mental_health.db` (tablas `user_sessions`, `user_responses`)
conservados como histórico. Decidir si se borran en una limpieza
posterior.

### 3.4. HUs pendientes originales
De `PENDIENTES.md`:
- HU-32 (filtro por riesgo en panel psicólogo, ~20 min)
- HU-34 (PDF programático, ~1 h)
- HU-37 (WebSocket logs, ~2 h)

### 3.5. Testing real
Levantar el stack, probar el flujo completo como alumno (escribir
varias entradas en distintos días) y como psicóloga (ver reporte de
ciclo, agendar cita de crisis, completarla y verificar que cierre el
ciclo). No se hizo en esta sesión, solo smoke tests de imports.

---

## 4. Cómo retomar mañana

1. Levantar el stack:
   ```bash
   venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
   cd project && npm run dev &
   ```
2. Probar el flujo del diario como estudiante y validar `StudentHistoryView`
   como psicóloga.
3. Decidir qué hacer con la duplicación de "resumen" vs "reporte de ciclo".
4. Empezar Figma según 3.1.
5. Atacar las HU-32 / HU-34 / HU-37 si queda tiempo.

---

## 5. Referencia rápida

- `CLAUDE.md` — guía del proyecto.
- `SPRINTS.md` — sprints 1-6 (no actualizado con 7+8 todavía, pendiente).
- `PENDIENTES.md` — HU-32, HU-34, HU-37.
- `docs/Diseño_del_sistema_Sami.docx` — documento de defensa.
- Memorias en `~/.claude/projects/-home-renzo-salud-mental-TP1/memory/`.
- Commit más reciente: `ebb4d03 feat: Sprint 7 (diario) + Sprint 8 (refactor de ciclos + reporte clínico)`.
