# Pendientes — HUs por implementar

Estado al 2026-05-21: **37 de 40 HUs completas**. Lo que sigue queda parqueado para una sesión futura.

---

## HU-32 — Filtrar estudiantes por nivel de riesgo (psicólogo)

**Donde está hoy:** `project/src/views/PsychologistDashboardView.vue` filtra por nombre/email (`filtro` ref, línea ~16) pero no por nivel de riesgo. El backend ya expone `ultimo_riesgo` por estudiante.

**Cómo abordarlo (~20 min):**
1. Agregar un ref `filtroRiesgo = ref('todos')` con valores `['todos', 'CRÍTICO', 'ALTO', 'MEDIO', 'BAJO', 'SIN_EVAL']`.
2. Sumar al computed `filtrados` un filtro extra:
   ```js
   .filter(e => filtroRiesgo.value === 'todos'
     || (e.ultimo_riesgo || 'SIN_EVAL').toUpperCase() === filtroRiesgo.value)
   ```
3. Encima de la tabla, antes del input de búsqueda, agregar un toggle de chips usando el mismo patrón que `AdminDashboardView.vue` líneas 76-93 (filtro de rol).
4. Mismo patrón visual: card blanca con `chip-brand` activo verde y resto gris hover.

**Sin cambios en backend.**

---

## HU-34 — Exportar reporte individual PDF (psicólogo)

**Donde está hoy:** Hay `window.print()` en `ResultsScreen.vue:233` y `AdminReportsView.vue:87`. Permite "Guardar como PDF" desde el diálogo del navegador, pero no es PDF generado en servidor con plantilla clínica.

**Cómo abordarlo (~1 h):**
1. Instalar `reportlab` (`pip install reportlab` y agregar a `requirements.txt`).
2. Crear `app/services/pdf_service.py` con `generar_reporte_estudiante(student_id, db)` que arme un PDF con:
   - Datos del estudiante (nombre, código, último nivel)
   - Tabla de sesiones con fecha, score, nivel
   - Gráfico embebido (matplotlib → png → image en PDF)
   - Notas privadas del psicólogo (modelo `ClinicalNote`)
   - Conclusión sugerida
3. Endpoint `GET /psychologist/students/{id}/report.pdf` en `app/api/v1/endpoints/psychologist.py` que devuelva `StreamingResponse(io.BytesIO(pdf), media_type='application/pdf')`.
4. En `StudentHistoryView.vue` agregar un botón "Exportar PDF" en `#actions` del `PageHeader` que descargue vía `<a :href="api.pdfUrl(id)" download>`.

**Alternativa rápida:** dejar `window.print()` como está (ya funciona) y solo mejorar la hoja `@media print` en `style.css` para que la versión imprimible se vea más limpia.

---

## HU-37 — Logs en tiempo real (WebSocket)

**Donde está hoy:** `AdminLogsView.vue` refresca cada 5s con `setInterval` + polling al endpoint `/admin/audit-logs`. Funciona como "live", el usuario ve "En vivo · cada 5s" en la UI. Esto técnicamente cubre la HU si la lees como "ver los logs actualizados en tiempo real".

**Cómo abordarlo si se quiere WebSocket real (~2 h):**
1. Backend:
   - Agregar `fastapi-websocket` o usar el built-in. Endpoint `/admin/audit-logs/ws` que mantenga conexión.
   - En `app/middleware/access_log.py`, después de persistir cada log, hacer `broadcast.publish(log_dict)` a todos los clientes conectados.
   - Solo permitir admin via token JWT en query param (`?token=...`).
2. Frontend:
   - En `AdminLogsView.vue` reemplazar `setInterval(cargar, 5000)` por `new WebSocket('ws://localhost:8000/api/v1/admin/audit-logs/ws?token=' + jwt)`.
   - En `socket.onmessage`, `logs.value.unshift(JSON.parse(e.data))` y truncar a 100.
   - Indicador "Conectado" / "Reconectando" en el header.

**Recomendación:** quedarse con el polling 5s actual a menos que sea pedido explícito. Es código simple, no tiene reconexión que mantener, y cinco segundos de latencia es perfectamente aceptable para una auditoría.
