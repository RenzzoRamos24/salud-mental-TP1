# Pendientes

Estado al 2026-06-24 tras el rediseño completo a sistema de cuestionarios.

---

## Funcional — listo

- Banco fijo de instrumentos (PHQ-A, GAD-7, SRQ-20, RSES, WHO-5, UCLA-3) cargado por seed y expuesto vía `/api/v1/banco`.
- 40 frases incompletas adaptadas de Sacks SSCT, divididas en 8 áreas.
- Bloques custom: creación, edición y eliminación por la psicóloga, con cortes sugeridos por tercios.
- Plantillas: creación, edición, eliminación y asignación.
- Flujo del alumno: lista de pendientes, vista paso a paso con barra de progreso, guardado parcial y cierre.
- Evaluator: scoring por escala con cortes Johnson/Spitzer/Harding/Rosenberg/WHO/Hughes, banderas de crisis (PHQ-A #9, SRQ-20 #17, BETO ideación) y riesgo compuesto.
- BETO sobre frases incompletas: 8 categorías emocionales.
- Panel psicóloga: dashboard, lista de alumnos, alertas, historial, resultado con termómetros + frases analizadas.
- Admin: usuarios, métricas de cuestionarios, modelo NLP, backups, auditoría.
- SOS visible globalmente para el alumno.

---

## Tesis — pendiente de implementación

Estas piezas no son requisitos funcionales, son entregables académicos planificados en `PLAN_RECOLECCION_DATOS.md` y `METRICAS_VALIDACION.md`.

### SVM de riesgo — parqueado
- **Dataset elegido (real):** DASS-42 de Open Source Psychometrics Project, 39,775 respuestas reales, 7,269 adolescentes 13–17 años. Descargado en `data/dass/`.
- **Estado:** entrenamiento pospuesto a pedido del usuario para priorizar la aplicación. Checklist técnico para retomar en `SVM_PARKED.md`.
- **Baseline desechable:** un primer experimento con Mendeley PHQ-9 sintético dejó F1 inflado por leakage de feature; no se cita en la tesis.

### Evaluación de BETO
- **Benchmark público listo:** `scripts/eval_beto_emoevent.py` corre el clasificador sobre EmoEvent (Plaza-del-Arco 2020, Apache-2.0, 1,656 tweets test español). Output queda en `reports/beto_emoevent.md`. Es defendible como evidencia primaria.
- **Set propio (opcional, refuerza dominio específico):** construir 100 respuestas a frases incompletas etiquetadas para mostrar performance en el dominio de Sami. Reportar recall específico de `ideacion_suicida` (≥ 0.90).

### Piloto psicométrico
- Reclutar 20–30 estudiantes de secundaria del colegio piloto.
- Aplicar PHQ-A + GAD-7 + RSES.
- Calcular α de Cronbach por escala con CI 95%.

### Concordancia clínica
- Preparar 30 vignettes (15 reales del piloto + 15 sintéticos).
- Entrega ciega a una psicóloga para clasificación de riesgo.
- Calcular κ Cohen, sensibilidad, especificidad y tasa de falsos negativos en `CRITICO`.

### Rendimiento
- Script `scripts/load_test.py` con locust (50 usuarios virtuales × 10 min).
- Reportar latencia p50/p95/p99 por endpoint.

### Usabilidad
- Sesión moderada con 5–10 usuarios + cuestionario SUS.
- Reportar puntaje SUS y problemas observados.

---

## Operacional — recomendado pero no bloqueante

- Borrar `backups/*.db` con schema antiguo (si quedaron de versiones previas).
- Decidir qué hacer con `app/services/scheduler_service.py` (corre todos los días a las 02:00 backups; sigue funcionando).
- Actualizar `SPRINTS.md` añadiendo el sprint de migración a cuestionarios.
