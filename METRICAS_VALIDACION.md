# Métricas de validación — Sami

Documento maestro de métricas para la validación del sistema, organizado en 6 dimensiones. Cada dimensión responde a una pregunta distinta del jurado y aporta a un capítulo distinto de la tesis.

> **Principio rector.** Cada métrica debe (1) responder a una pregunta específica, (2) tener un umbral objetivo declarado y (3) ser calculable con los datos que el sistema captura. Lo que no se mide, no se afirma.

---

## Índice de dimensiones

1. [ML — Clasificador SVM de riesgo](#1-ml--clasificador-svm-de-riesgo)
2. [NLP — BETO sobre frases incompletas](#2-nlp--beto-sobre-frases-incompletas)
3. [Psicometría de las escalas](#3-psicometría-de-las-escalas)
4. [Concordancia clínica con experto](#4-concordancia-clínica-con-experto)
5. [Rendimiento operacional del sistema](#5-rendimiento-operacional-del-sistema)
6. [Usabilidad y experiencia de usuario](#6-usabilidad-y-experiencia-de-usuario)

---

## 1. ML — Clasificador SVM de riesgo

**Pregunta de validación:** ¿el modelo predice correctamente el nivel de riesgo del estudiante?

**Diseño:** evaluación sobre un set de prueba (held-out) + validación cruzada k=5 sobre el set de entrenamiento.

**Clases predichas:** `SIN_RIESGO`, `BAJO`, `MEDIO`, `ALTO`, `CRÍTICO`.

| Métrica | Cómo se calcula | Umbral objetivo |
|--|--|--|
| Accuracy global | aciertos / total | ≥ 0.75 |
| Precision (por clase) | TP / (TP + FP) | ≥ 0.70 cada una |
| Recall (por clase) | TP / (TP + FN) | ≥ 0.70 (≥ 0.90 en `CRÍTICO`) |
| F1-score (por clase + macro) | media armónica precision/recall | F1-macro ≥ 0.75 |
| AUC-ROC (one-vs-rest) | área bajo curva ROC por clase | ≥ 0.80 |
| Matriz de confusión 5×5 | distribución real vs predicho | Reporte completo, no umbral |
| K-fold CV (k=5) | media ± desviación de F1-macro | Desviación < 0.05 |

**Justificación de umbrales.** En tamizaje clínico el costo de un falso negativo en categoría crítica es muy superior al de un falso positivo, por eso el recall en `CRÍTICO` se exige más alto.

**Salidas del experimento.**
- Tabla de métricas por clase.
- Matriz de confusión.
- Curva ROC por clase.
- Reporte de feature importance (permutation importance, ya que SVM no expone coeficientes lineales si usa kernel RBF).

---

## 2. NLP — BETO sobre frases incompletas

**Pregunta de validación:** ¿BETO clasifica correctamente el contenido emocional de las respuestas abiertas?

**Diseño:** evaluación sobre ~200 respuestas a frases incompletas etiquetadas manualmente por el investigador (y validadas por la psicóloga si está disponible).

**Etiquetas multi-label:** `tristeza`, `ansiedad`, `ira`, `miedo`, `soledad`, `ideación_suicida`, `esperanza`, `neutral`.

| Métrica | Qué mide | Umbral objetivo |
|--|--|--|
| Accuracy por etiqueta | aciertos binarios etiqueta-a-etiqueta | ≥ 0.75 promedio |
| F1 macro / weighted | rendimiento global multi-label | F1-macro ≥ 0.65 |
| Confianza promedio | probabilidad media de la etiqueta ganadora | ≥ 0.55 |
| Kappa de Cohen (κ) | concordancia BETO vs etiquetado humano | ≥ 0.60 (sustancial) |
| Recall en `ideación_suicida` | sensibilidad para la bandera más crítica | **≥ 0.90** |
| Tasa de falsos positivos críticos | falsa alarma de ideación | ≤ 0.10 |

**Justificación de umbrales.** BETO es zero-shot (no entrenado específicamente para este dominio), por lo que un F1-macro ≥ 0.65 es razonable para tesis. El recall en ideación se exige alto por razones éticas: es preferible una falsa alarma a perder un caso real.

**Set de evaluación.**
- 200 frases incompletas reales o sintéticas.
- Cada frase etiquetada con 0 o más categorías.
- Idealmente etiquetadas por 2 personas → calcular κ inter-anotador antes de evaluar BETO.

---

## 3. Psicometría de las escalas

**Pregunta de validación:** ¿los cuestionarios son confiables y mantienen su estructura en estudiantes de secundaria del colegio privado piloto?

**Diseño:** análisis post-hoc sobre los resultados de ≥ 50 aplicaciones reales del sistema.

| Métrica | Qué mide | Umbral objetivo |
|--|--|--|
| α de Cronbach (por escala) | consistencia interna entre ítems | ≥ 0.70 aceptable / ≥ 0.80 bueno |
| Correlación ítem-total corregida | aporte de cada ítem al constructo | > 0.30 |
| McDonald's ω | alternativa robusta a Cronbach | ≥ 0.70 |
| Análisis factorial exploratorio (EFA) | estructura dimensional | Reproducir estructura original |
| Test-retest (si aplicable) | estabilidad temporal | r ≥ 0.70 con 2 semanas de gap |
| Cargas factoriales (CFA confirmatorio) | ajuste a modelo teórico | CFI ≥ 0.90, RMSEA ≤ 0.08 |

**Cuándo se calcula.** Requiere mínimo n = 50 aplicaciones por escala para estabilidad estadística. Antes de eso, los valores no son interpretables.

**Salida del experimento.**
- Tabla de α por escala con N y CI 95%.
- Heatmap de correlaciones ítem-total.
- Resultados EFA (varianza explicada, eigenvalues).

---

## 4. Concordancia clínica con experto

**Pregunta de validación:** ¿el sistema clasifica el riesgo de forma compatible con el criterio clínico de un profesional?

**Diseño:** la psicóloga clasifica ciega un set de N ≥ 30 casos (con todas las respuestas del estudiante a la vista pero sin ver la salida del sistema). Se compara su clasificación con la del sistema.

| Métrica | Qué mide | Umbral objetivo |
|--|--|--|
| κ de Cohen | acuerdo más allá del azar | ≥ 0.60 (sustancial) |
| κ ponderado | penaliza menos errores cercanos | ≥ 0.70 |
| Sensibilidad clínica | TP / (TP + FN) tomando psicóloga como gold | ≥ 0.85 |
| Especificidad clínica | TN / (TN + FP) | ≥ 0.75 |
| VPP (valor predictivo positivo) | TP / (TP + FP) | ≥ 0.70 |
| VPN (valor predictivo negativo) | TN / (TN + FN) | ≥ 0.85 |
| Tasa de falsos negativos en `CRÍTICO` | casos críticos no detectados | **= 0** ideal, ≤ 0.05 aceptable |

**Diseño del experimento (resumido).**
1. Reclutar N = 30–50 estudiantes voluntarios.
2. Cada uno completa el cuestionario en el sistema.
3. La psicóloga revisa las respuestas crudas (sin ver el output del sistema) y asigna nivel de riesgo.
4. Comparar ambas clasificaciones.

**Limitación honesta a declarar.** Un solo evaluador clínico = no se puede calcular acuerdo inter-evaluador. Con 2 psicólogas se mejora la validez (κ inter-evaluador como referencia).

---

## 5. Rendimiento operacional del sistema

**Pregunta de validación:** ¿el sistema responde en tiempos aceptables y es estable?

**Diseño:** logs del servidor + cargas de prueba con `locust` o equivalente.

| Métrica | Qué mide | Umbral objetivo |
|--|--|--|
| Latencia p50 endpoint evaluación | mediana de tiempo de respuesta | < 1.5 s |
| Latencia p95 endpoint evaluación | percentil 95 | < 3 s |
| Latencia p99 endpoint evaluación | peor caso típico | < 5 s |
| Tiempo de inferencia BETO (frase) | clasificación zero-shot por respuesta | < 500 ms |
| Tiempo de inferencia SVM | predicción + probabilidades | < 50 ms |
| Tasa de errores 5xx | fallos del backend | < 0.5% |
| Disponibilidad (uptime) | tiempo activo / tiempo total | ≥ 99% durante la fase de pruebas |
| Tasa de completitud del cuestionario | finalizados / iniciados | ≥ 85% |

**Salidas del experimento.**
- Histograma de latencias por endpoint.
- Gráfico p50/p95/p99 a lo largo del tiempo.
- Tasa de errores por endpoint.

---

## 6. Usabilidad y experiencia de usuario

**Pregunta de validación:** ¿los estudiantes y psicólogas pueden y quieren usar el sistema?

**Diseño:** prueba con usuarios moderada (5–10 estudiantes + 2 psicólogas).

| Métrica | Qué mide | Umbral objetivo |
|--|--|--|
| SUS (System Usability Scale) | usabilidad estándar de la industria | ≥ 68 (promedio) / ≥ 80 (excelente) |
| Tasa de éxito de tarea | % de tareas clave completadas sin ayuda | ≥ 80% |
| Tiempo de tarea (cuestionario completo) | minutos en completar | ≤ 20 min |
| Errores por usuario | clics erróneos, retrocesos | ≤ 3 por sesión |
| CSAT (satisfacción) | escala 1–5 final | media ≥ 4 |
| NPS (opcional) | recomendación 0–10 | ≥ 30 |

**Salidas del experimento.**
- Puntaje SUS por usuario y agregado.
- Lista de problemas observados (ordenados por severidad).
- Citas literales de comentarios (análisis cualitativo).

---

## Matriz de cobertura: dimensión → capítulo de la tesis

| Dimensión | Tipo | Capítulo tesis | Cuándo se mide |
|--|--|--|--|
| 1. ML SVM | Cuantitativa técnica | Modelo / Resultados | Tras entrenar el modelo |
| 2. NLP BETO | Cuantitativa técnica | Modelo / Resultados | Antes del despliegue |
| 3. Psicometría | Cuantitativa clínica | Instrumentos | n ≥ 50 aplicaciones |
| 4. Concordancia clínica | Cuantitativa clínica | Validación con experto | n ≥ 30 casos comparados |
| 5. Rendimiento | Cuantitativa operacional | Implementación | Carga de prueba |
| 6. Usabilidad | Mixta | Evaluación con usuarios | 5–10 usuarios moderados |

---

## Tabla resumen de umbrales clave

| Métrica | Umbral mínimo defendible en tesis |
|--|--|
| SVM — F1-macro | ≥ 0.75 |
| SVM — Recall `CRÍTICO` | ≥ 0.90 |
| BETO — F1-macro | ≥ 0.65 |
| BETO — Recall `ideación_suicida` | ≥ 0.90 |
| Cronbach α (todas las escalas) | ≥ 0.70 |
| κ Cohen sistema vs psicóloga | ≥ 0.60 |
| Sensibilidad clínica | ≥ 0.85 |
| Falsos negativos en `CRÍTICO` | = 0 |
| Latencia p95 | < 3 s |
| Completitud del cuestionario | ≥ 85% |
| SUS | ≥ 68 |

---

## Lo que no se va a medir (y por qué)

Declararlo es parte de la honestidad académica:

- **Validez predictiva longitudinal** (¿el sistema predice qué pasará en 6 meses?) — fuera del alcance temporal de la tesis.
- **Comparación contra otro chatbot equivalente** — no existe un benchmark directo en castellano para adolescentes peruanos.
- **Costo-beneficio económico** — análisis de impacto institucional, no técnico.
- **Equidad por subgrupos demográficos** — la muestra de tesis no permite estratificar de forma estadísticamente válida.

---

## Próximos pasos para activar la medición

1. Implementar logging estructurado en cada endpoint para capturar latencias.
2. Reservar un endpoint `/admin/metricas` que exponga α de Cronbach, completitud y latencias en tiempo casi-real.
3. Construir el set de evaluación BETO (200 frases etiquetadas).
4. Coordinar con la psicóloga el experimento de concordancia clínica (n ≥ 30).
5. Diseñar el cuestionario SUS y la guía de prueba moderada para usabilidad.
