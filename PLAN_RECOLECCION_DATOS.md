# Plan de recolección de datos para validación — Sami

Documento operativo que responde a la pregunta: **"¿de dónde van a salir los datos que reportamos como métricas en la tesis?"**.

Complementa a `METRICAS_VALIDACION.md` (qué se mide) explicando *cómo se obtiene cada dato*.

> **Principio.** No tenemos dataset clínico anotado, ni 500 estudiantes pre-existentes, ni horas ilimitadas de una psicóloga. La validación se diseña en torno a lo que **sí se puede obtener** con honestidad académica.

---

## Resumen ejecutivo

| Dim. | Qué se valida | Fuente de datos | Tiempo de obtención |
|--|--|--|--|
| 1 | Clasificador SVM | Dataset sintético (n=500) etiquetado con reglas clínicas | 1 día |
| 2 | BETO sobre frases | Set propio (n=100) etiquetado manualmente | 6 horas (+ κ inter-anotador opcional) |
| 3 | Psicometría de escalas | Piloto con n=20–30 estudiantes de secundaria (colegio privado piloto) | 1–2 semanas |
| 4 | Concordancia clínica | 30 casos clasificados ciegos por psicóloga | 1 semana (incl. preparación) |
| 5 | Rendimiento | Logs del backend + locust con 50 usuarios virtuales | 1 día |
| 6 | Usabilidad | 5–10 usuarios + cuestionario SUS | 1 semana |

---

## Dim. 1 — Datos para validar SVM

### Problema
No existe un dataset clínico real, etiquetado con niveles de riesgo, en castellano y para adolescentes peruanos.

### Solución: dataset sintético etiquetado con reglas
1. Generar n = 500 "estudiantes virtuales".
2. Para cada uno, muestrear puntajes de las 6 escalas desde distribuciones realistas (truncated normal con μ y σ tomadas de literatura: Johnson 2002, Spitzer 2006, Mari 1986).
3. La **etiqueta de riesgo** (`SIN_RIESGO`, `BAJO`, `MEDIO`, `ALTO`, `CRÍTICO`) se asigna con la regla determinista de la Capa 3 — no es asignada por la psicóloga, es matemática.
4. Inyectar ~5% de ruido para que el SVM no sobreaprenda trivialmente.
5. Split 80/20: entrenar / evaluar.

### Lo que se reporta
- F1-macro, accuracy, AUC sobre el set de prueba sintético.
- Matriz de confusión 5×5.
- Validación cruzada k=5.

### Limitación que se declara
> "Por la imposibilidad de obtener un dataset clínico real anotado, la evaluación del SVM se realiza sobre datos sintéticos generados a partir de las distribuciones publicadas. Demuestra **viabilidad del pipeline** pero no la **performance en producción** — esto último queda como trabajo futuro."

### Artefactos a producir
- `scripts/generar_dataset_sintetico.py`
- `data/dataset_sintetico_svm.csv`
- `reports/svm_evaluation.ipynb`

---

## Dim. 2 — Datos para validar BETO

### Problema
BETO se usa zero-shot. Necesitamos un conjunto pequeño de respuestas a frases incompletas con etiquetas reales para medir cómo se comporta.

### Solución: set propio + benchmark público

**a) Set propio (n = 100 respuestas)**
1. Generar 100 respuestas plausibles a las 40 frases incompletas, cubriendo las 8 áreas.
2. Etiquetar cada respuesta con 0 o más de estas categorías:
   `tristeza`, `ansiedad`, `ira`, `miedo`, `soledad`, `ideación_suicida`, `esperanza`, `neutral`.
3. (Opcional) Pedir a una segunda persona etiquetar las mismas → calcular κ inter-anotador.

**b) Benchmark público español**
- Correr BETO zero-shot sobre **EmoEvent** o **TASS** (corpus de emoción en castellano).
- Reportar F1 sobre esos sets para contextualizar.

### Lo que se reporta
- Accuracy por etiqueta, F1-macro, F1-weighted.
- κ Cohen vs etiquetado humano.
- Recall específico de `ideación_suicida` (por ética debe ser ≥ 0.90).

### Artefactos a producir
- `data/beto_eval_frases.json` (100 ejemplos etiquetados)
- `scripts/eval_beto.py`
- `reports/beto_evaluation.ipynb`

---

## Dim. 3 — Datos para psicometría

### Problema
Cronbach, EFA y test-retest requieren respuestas reales. Necesitamos un piloto.

### Solución: piloto con n = 20–30 estudiantes de secundaria

**Población objetivo**
- Estudiantes de un colegio privado de secundaria (edades aprox. 11–17 años).
- Coordinación previa con la dirección del colegio y el área psicopedagógica.

**Reclutamiento**
- Coordinación con tutoría / departamento psicopedagógico del colegio.
- Convocatoria por aula con autorización previa de los padres (consentimiento informado del menor + asentimiento del estudiante).
- Incentivo: feedback personalizado del resultado (no clínico) al estudiante y reporte agregado al colegio.

**Protocolo**
- Cada participante completa: PHQ-A + GAD-7 + RSES (26 ítems, ~10 min).
- Opcional: subset completa también SRQ-20 + WHO-5 + UCLA-3.
- Para test-retest: 5–10 participantes vuelven a aplicar a las 2 semanas.

### Lo que se reporta
- α de Cronbach por escala (con CI 95%).
- Correlación ítem-total.
- Test-retest (Pearson) si se logra repetir.
- Comparación: "α obtenido vs α publicado en estudio original".

### Limitación que se declara
> "El tamaño muestral n=25 limita la precisión de las estimaciones; los CI 95% obtenidos son anchos. Sirve como evidencia preliminar de consistencia en estudiantes de secundaria del colegio piloto, no como validación poblacional generalizable."

### Artefactos a producir
- `data/piloto_psicometria.csv`
- `reports/psicometria.ipynb`

---

## Dim. 4 — Datos para concordancia clínica

### Problema
Se necesita un evaluador clínico que clasifique casos ciegos, para comparar con la salida del sistema.

### Solución: 30 casos clasificados por una psicóloga

**Composición del set de 30 casos:**
- **15 casos reales** tomados del piloto de Dim. 3, anonimizados (sin nombre, sin edad exacta).
- **15 casos sintéticos** diseñados para cubrir las 5 clases de riesgo (3 por clase).
  - Esto asegura que las clases minoritarias (`CRÍTICO`) estén representadas.

**Protocolo de evaluación:**
1. La psicóloga recibe un PDF con las respuestas crudas (sin output del sistema).
2. Para cada caso, asigna nivel de riesgo + justificación breve.
3. Tiempo estimado: 4 min por caso × 30 = **2 horas totales**.
4. Después se compara su clasificación con la del sistema.

### Lo que se reporta
- κ de Cohen (acuerdo) y κ ponderado.
- Sensibilidad, especificidad, VPP, VPN.
- Tasa de falsos negativos en clase `CRÍTICO` (debe ser 0 o cercana).
- Tabla de discrepancias con justificación cualitativa.

### Limitación que se declara
> "Solo se contó con un evaluador clínico, lo que impide medir acuerdo inter-clínico. Los resultados son referenciales y deben replicarse con ≥ 2 evaluadores en estudios posteriores."

### Artefactos a producir
- `data/clinical_validation_cases.pdf`
- `data/clinical_validation_responses.csv`
- `reports/concordancia_clinica.ipynb`

---

## Dim. 5 — Datos de rendimiento

### Problema
Necesitamos medir latencias y errores bajo carga.

### Solución: logs estructurados + locust

**Setup**
1. Middleware existente `access_log` ya captura request/response.
2. Agregar campo `latencia_ms` por request.
3. Script `scripts/load_test.py` con locust:
   - 50 usuarios virtuales concurrentes.
   - Mix realista: 70% GET (consultas) / 30% POST (envío de respuestas).
   - Duración: 10 minutos.

### Lo que se reporta
- Latencia p50, p95, p99 por endpoint.
- Tasa de errores 5xx.
- Throughput (requests/s sostenido).
- Tiempo de inferencia BETO + tiempo de inferencia SVM medidos por separado.

### Artefactos a producir
- `scripts/load_test.py`
- `reports/performance.md`

---

## Dim. 6 — Datos de usabilidad

### Problema
Necesitamos retroalimentación de usuarios reales sobre la experiencia.

### Solución: prueba moderada con 5–10 usuarios

**Reclutamiento**
- 5–7 estudiantes (perfil objetivo).
- 2–3 psicólogas (perfil profesional).
- Total: 7–10 participantes.

**Protocolo por sesión (~45 min)**
1. Saludo + consentimiento + presentación del sistema (5 min).
2. **Tareas guiadas:**
   - Tarea A: registrarte y completar el primer cuestionario.
   - Tarea B: ver tu resultado e interpretarlo.
   - Tarea C (psicóloga): armar una plantilla custom desde el bank.
3. Pensamiento en voz alta + observación de errores.
4. **Cuestionario SUS** (10 preguntas estándar).
5. Entrevista corta (~5 min): qué confundió, qué gustó, qué cambiarían.

### Lo que se reporta
- Puntaje SUS por participante + agregado (media + DE).
- Lista priorizada de problemas observados (por frecuencia × severidad).
- Tiempo promedio de tarea.
- Tasa de éxito de tarea sin ayuda.
- Citas literales relevantes (análisis cualitativo).

### Artefactos a producir
- `data/sus_responses.csv`
- `data/observed_issues.md`
- `reports/usability.md`

---

## Calendario sugerido (3 semanas)

| Semana | Actividad |
|--|--|
| 1 | Generar dataset sintético + entrenar SVM (Dim. 1). Construir set BETO (Dim. 2). Setup logging + load test (Dim. 5). |
| 2 | Reclutar piloto + corrida PHQ-A/GAD-7/RSES (Dim. 3). Prueba moderada con 5–10 usuarios (Dim. 6). |
| 3 | Entregar set de 30 casos a la psicóloga (Dim. 4). Procesar todos los datos. Generar gráficos y tablas para la tesis. |

---

## Cómo defender esto ante el jurado

**Pregunta típica:** *"¿Por qué validaron el SVM con datos sintéticos?"*

**Respuesta:** *"Por la naturaleza del problema, no existe en castellano para adolescentes peruanos un dataset clínico anotado con niveles de riesgo. Construir uno requeriría un estudio epidemiológico paralelo fuera del alcance temporal de esta tesis. Optamos por evaluar **viabilidad arquitectónica** sobre datos sintéticos generados con distribuciones publicadas, y **viabilidad clínica** sobre 30 casos evaluados por una profesional. Ambas validaciones son complementarias y declaramos sus límites."*

**Pregunta típica:** *"¿N=25 no es muy poco para Cronbach?"*

**Respuesta:** *"Es un piloto. Reportamos α con CI 95% y comparamos con los α publicados en los estudios originales. La consistencia se mantiene; la generalización requiere muestreo poblacional, lo cual es trabajo futuro."*

---

## Lo no negociable

- Todos los participantes firman consentimiento informado.
- Las respuestas en casos clínicos se anonimizan antes de salir del sistema.
- La psicóloga firma una hoja simple aceptando colaborar en la validación.
- Nada se publica con identidad de participantes.
