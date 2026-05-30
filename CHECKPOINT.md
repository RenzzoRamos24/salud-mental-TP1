# Checkpoint — sesión 2026-05-29 (noche)

Sesión de planificación + implementación parcial. El usuario se fue a
dormir, retoma mañana temprano. Este documento describe exactamente qué
quedó hecho, qué quedó pendiente y por qué.

---

## 1. Decisiones de diseño tomadas en esta sesión

### 1.1. Sami es un diario, no un chatbot

El usuario decidió que el flujo conversacional de 10 preguntas (chatbot)
sobra: el **diario es la pieza fuerte** del sistema. Tener ambos era
redundante y confuso.

- El menú del estudiante (`MainMenuView.vue`) **ya promociona el diario
  como tarjeta destacada**. No incluye chatbot. ✅ Ya correcto antes de
  esta sesión.
- El código del chatbot **NO se borró todavía** (decisión pendiente del
  usuario). La ruta `/chat` sigue existiendo, accesible por URL directa.
  Está efectivamente deprecado por ausencia en el menú.

**Pendiente de decisión (mañana):**
- ¿Borramos chatbot del todo (ChatView, ResultsScreen, chat_service,
  session_service, modelos UserSession/UserResponse, endpoint
  chatbot.py, schemas/chat.py)?
- O lo dejamos como "modo legado" para datos históricos.

### 1.2. Modelo de ciclos del diario (refactor crítico)

Antes: el ciclo cerraba cuando había una **cita marcada como completada**.
Esto acoplaba la temporalidad del diario a la disponibilidad de la
psicóloga, lo cual era confuso e impráctico.

Ahora (modelo limpio, acordado):

- Un ciclo dura **14 días desde la primera entrada** de ese ciclo.
- **Cierra automáticamente al día 14**, sin importar el resultado clínico
  ni si hay cita pendiente.
- **Día 15 = Día 1 del Ciclo N+1** automáticamente. El diario no se
  detiene.
- Las **citas regulares** corren **EN PARALELO** al ciclo. No lo cierran
  ni lo reinician.
- **Excepción: cita con `es_crisis=True`** marcada como completada
  **adelanta el cierre** del ciclo. Al día siguiente arranca el ciclo
  N+1. Razón: tras una crisis y la intervención clínica, mejor empezar
  fresco que arrastrar días bajo la sombra del evento.

### 1.3. Tabla días-con-síntoma → puntos PHQ-A (defensa de tesis)

Defensa argumentativa para el jurado: las 4 etiquetas del PHQ-A
(Johnson, 2002) se traducen aritméticamente sobre 14 días así:

| Días | Puntos | Frase oficial |
|---|---|---|
| 0 | 0 | "Nunca" |
| 1–7 | 1 | "Algunos días" |
| 8–11 | 2 | "Más de la mitad de los días" |
| 12–14 | 3 | "Casi todos los días" |

"Más de la mitad de 14" = aritméticamente > 7, o sea ≥ 8. No hay
invención, es traducción literal.

---

## 2. Lo que se implementó en esta sesión

### Backend

| Archivo | Cambio |
|---|---|
| `app/models/cita.py` | + columna `es_crisis: Boolean` (default False) |
| `app/schemas/cita.py` | + `es_crisis` en CitaCreate / CitaUpdate / CitaOut |
| `app/services/cita_service.py` | `crear()` acepta `es_crisis`, `_enriquecer()` lo expone |
| `app/services/ciclo_service.py` | **Reescrito completo**: cierre por tiempo, citas regulares paralelas, citas de crisis adelantan cierre. Mantiene la API pública `info_ciclo_estudiante()` con el mismo shape. |
| `app/services/diario_analisis_service.py` | + `DiarioAnalisisService.reporte_ciclo(db, user_id, ciclo_inicio, ciclo_fin)`: agrega por días-con-síntoma y mapea con la tabla Johnson. Devuelve `phqa_total`, `gad7_total`, severidades, items_detalle con `dias_con_sintoma`, `puntos` y `frase_likert`, confiabilidad por cobertura (baja <5, media 5-9, alta ≥10). |
| `scripts/migrate_cita_crisis.py` | Migración idempotente para agregar `es_crisis` a `citas`. **Ya se ejecutó** contra `mental_health.db`. |

### Documento de defensa (Word)

| Archivo | Cambio |
|---|---|
| `docs/generar_documento_sami.py` | Reescritura completa del body: lenguaje llano, secciones nuevas (cuándo entra Sami, consentimiento, día a día del alumno, ciclos con el modelo nuevo, papel de BERT/DSM-5, qué ve la psicóloga, plan de implementación con stack y sprints). Apéndices A/B/C conservados. |
| `docs/Diseño_del_sistema_Sami.docx` | Regenerado. **52 KB**. Listo para mostrar al asesor. |

### Memoria persistente del usuario

Tres archivos nuevos en `~/.claude/projects/-home-renzo-salud-mental-TP1/memory/`:

- `phqa_dias_a_puntos.md` — defensa de la tabla días→puntos
- `modelo_ciclos_diario.md` — modelo operativo de ciclos (cierre por tiempo, cita paralela, crisis adelanta)
- Actualización de `MEMORY.md` con índices a los anteriores

### Verificación

- `app.main` importa sin errores (78 rutas).
- `info_ciclo_estudiante()` corrió contra un estudiante real de la BD:
  devolvió "en_curso", día 8 del Ciclo 1, motivo_cierre_esperado=tiempo.
- `reporte_ciclo()` y `_frase_likert()` smoke-tested.

---

## 3. Lo que quedó pendiente para mañana

### 3.1. Decisión sobre el chatbot (alta prioridad)

El usuario debe decidir si:

- (A) Borramos el chatbot completamente: rutas, vistas, servicios,
  modelos, endpoints, schemas. Implica también limpiar referencias en
  `psychologist_service` (que hoy combina sesiones de chat + diario en
  el historial).
- (B) Lo dejamos como legado, accesible solo por URL, sin promoción.
  Mínimo trabajo.

Mi recomendación: **(A) parcial** — borrar la vista y el endpoint del
estudiante, dejar el modelo `UserSession`/`UserResponse` (porque hay
datos históricos en `mental_health.db`) y simplificar el historial del
psicólogo a solo-diario.

### 3.2. Hookear el nuevo `reporte_ciclo()` al dashboard de la psicóloga

`reporte_ciclo()` existe pero todavía **no se llama desde ningún
endpoint**. Hoy el panel del psicólogo usa
`PsychologistService.resumen_diario_estudiante()` que hace **promedios
de phq9_total por entrada** — clínicamente incorrecto según nuestra
defensa.

Tareas:

- Agregar endpoint `GET /psychologist/students/{id}/reporte-ciclo/{ciclo_n}` que llame a `reporte_ciclo()`.
- Actualizar `StudentHistoryView.vue` para mostrar los ciclos cerrados con su PHQ-A inferido (no promedio).
- Decidir si `resumen_diario_estudiante()` se reemplaza por completo o se mantiene como vista "preview en proceso".

### 3.3. UI para marcar una cita como "atención de crisis"

Hoy `Cita.es_crisis` existe en backend pero **no hay UI** para que la
psicóloga la marque al agendar. Falta:

- Checkbox "¿Esta cita es atención de crisis?" en el modal de
  agendamiento en `PsychologistDashboardView.vue` y
  `StudentHistoryView.vue`.
- Mostrar el badge "Crisis" en la lista de próximas citas.

### 3.4. Mockups en Figma

El usuario quiere pasar el plan a Figma. Frames a crear/actualizar:

- Onboarding del alumno (login → asentimiento → primera entrada).
- Vista del diario con prompt de Sami + zona de escritura + consejo al cierre.
- Vista "Mi proceso" del alumno (calendario de ciclos cerrados + racha).
- Dashboard psicóloga con las 3 bandejas (críticas / cierres / cohorte).
- Reporte de ciclo (lo nuevo de `reporte_ciclo()`).
- Modal de cita con flag de crisis.

### 3.5. Limpiar archivos untracked

`git status` muestra varios archivos del módulo diario y otros sin
commitear desde antes de esta sesión. Después de validar el refactor de
ciclos, hacer un commit grande que englobe:

- Sprint 7 (diario)
- Sprint 8 (refactor de ciclos)
- Documento Word actualizado
- Migración `migrate_cita_crisis.py`

---

## 4. Cómo retomar mañana

1. Abrir `docs/Diseño_del_sistema_Sami.docx` y validar que esté listo
   para el asesor.
2. Levantar el stack:
   ```bash
   venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
   cd project && npm run dev &
   ```
3. Probar el flujo del diario como estudiante para verificar que el
   refactor de `ciclo_service` no rompió nada visible.
4. Decidir 3.1 (qué hacer con el chatbot) y arrancar.
5. Implementar 3.2 (hookear `reporte_ciclo` al dashboard).
6. Implementar 3.3 (UI para marcar citas como crisis).
7. Pasar a Figma según 3.4.

---

## 5. Archivos clave para no perder el hilo

- `CLAUDE.md` — guía rápida del proyecto.
- `SPRINTS.md` — registro de sprints 1-6 (no se actualizó esta sesión).
- `PENDIENTES.md` — HU-32, HU-34, HU-37 antiguos.
- `CHECKPOINT.md` — este archivo. Es lo más reciente.
- `docs/Diseño_del_sistema_Sami.docx` — documento de defensa, listo.
- Memorias en `~/.claude/projects/-home-renzo-salud-mental-TP1/memory/`.
