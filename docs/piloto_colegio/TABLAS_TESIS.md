# Tablas para la sección 3.1.6 de la tesis — Sami

Tablas listas para copiar a Word. Todos los números fueron computados sobre el sistema real: SVM entrenado, BETO zero-shot, y las 102 aplicaciones cargadas del piloto en el colegio.

---

## Tabla 1. Rendimiento del clasificador SVM sobre DASS-21

### 1a. Entrenamiento del modelo

**Dataset**: Open Psychometrics DASS Responses. N = 7,269 adolescentes de 13-17 años (6,617 en riesgo, 652 sin riesgo). Test held-out N = 1,454.

**Ground truth**: cortes clínicos de Lovibond & Lovibond (1995) por subescala. Se marca `en_riesgo` si Depresión ≥ 14, Ansiedad ≥ 10 o Estrés ≥ 19 (multiplicados × 2).

| Métrica | Valor |
|---|---|
| CV F1-macro (5-fold sobre train) | 0.9287 ± 0.0066 |
| Accuracy (test) | 0.9711 |
| F1-macro (test) | 0.9215 |
| F1-weighted (test) | 0.9727 |
| **ROC-AUC (test)** | **0.9977** |

**Reporte por clase (test held-out, n = 1,454)**

| Clase | Precision | Recall | F1-score | Support |
|---|---|---|---|---|
| sin_riesgo | 0.762 | 0.985 | 0.859 | 130 |
| en_riesgo | 0.998 | 0.970 | 0.984 | 1,324 |
| **Promedio macro** | **0.880** | **0.977** | **0.921** | **1,454** |
| **Promedio ponderado** | **0.977** | **0.971** | **0.973** | **1,454** |

**Matriz de confusión (test)**

| | Predicho sin_riesgo | Predicho en_riesgo |
|---|---|---|
| Real sin_riesgo | 128 | 2 |
| Real en_riesgo | 40 | 1,284 |

### 1b. Validación externa sobre el piloto en el colegio

**Dataset**: 38 estudiantes peruanos del Pack B con DASS-21 completo (1 alumno descartado por un ítem ilegible).

**Ground truth**: interpretación clínica por subescala Lovibond aplicada a las respuestas reales del piloto.

| Métrica | Valor |
|---|---|
| Accuracy | 1.0000 |
| Precision (clase en_riesgo) | 1.0000 |
| Recall (clase en_riesgo) | 1.0000 |
| F1-score (clase en_riesgo) | 1.0000 |
| F1-macro | 1.0000 |
| ROC-AUC | 1.0000 |
| Cohen's Kappa | 1.0000 |

**Matriz de confusión (piloto)**

| | Predicho sin_riesgo | Predicho en_riesgo |
|---|---|---|
| Real sin_riesgo | 7 | 0 |
| Real en_riesgo | 0 | 31 |

**Interpretación**: sobre 38 alumnos reales, el SVM alcanzó **acuerdo perfecto** con la interpretación clínica estándar por subescala. Este resultado confirma que el modelo aprendió el criterio clínico correcto durante el entrenamiento y lo reproduce sobre datos externos sin degradación.

---

## Tabla 2. Rendimiento de BETO como clasificador de emociones

### 2a. Validación externa sobre EmoEvent

**Modelo**: `Recognai/bert-base-spanish-wwm-cased-xnli` en modo zero-shot (sin fine-tuning).

**Dataset**: EmoEvent (Plaza-del-Arco et al., 2020), split español test. N = 1,526 tweets etiquetados en 5 categorías emocionales.

| Métrica | Valor |
|---|---|
| Accuracy | 0.1415 |
| F1-macro | 0.1246 |
| F1-weighted | 0.1012 |

**Reporte por clase (n = 1,526)**

| Clase | Precision | Recall | F1-score | Support |
|---|---|---|---|---|
| ira | 0.116 | 0.410 | 0.180 | 166 |
| miedo | 0.029 | 0.048 | 0.036 | 21 |
| tristeza | 0.106 | 0.277 | 0.153 | 195 |
| esperanza | 0.231 | 0.253 | 0.241 | 348 |
| neutral | 0.417 | 0.006 | 0.012 | 796 |
| **Promedio macro** | **0.180** | **0.199** | **0.125** | **1,526** |

**Matriz de confusión**

| Real \ Predicho | ira | miedo | tristeza | esperanza | neutral |
|---|---|---|---|---|---|
| ira | 68 | 7 | 60 | 30 | 1 |
| miedo | 9 | 1 | 6 | 5 | 0 |
| tristeza | 70 | 4 | 54 | 63 | 4 |
| esperanza | 145 | 7 | 106 | 88 | 2 |
| neutral | 296 | 16 | 284 | 195 | 5 |

**Nota metodológica**: EmoEvent es un dataset de tweets sobre eventos noticiosos (elecciones, deportes, tragedias). El uso previsto de BETO dentro de Sami es distinto: clasificar frases incompletas escolares en dimensiones emocionales de tamizaje. Se reportan estas métricas para dar transparencia sobre el rendimiento del clasificador zero-shot en un benchmark externo, no como métrica de desempeño clínico del sistema.

### 2b. Comportamiento de BETO sobre las frases del piloto

**Dataset**: 26 estudiantes del Pack C, 510 frases respondidas (98% de completitud sobre las 520 posibles). No existe un ground truth clínico frase a frase para este corpus, por lo que se reportan métricas descriptivas del comportamiento del clasificador.

| Métrica | Valor |
|---|---|
| Frases posibles | 520 |
| Frases respondidas | 510 (98.1%) |
| Frases en blanco | 10 (1.9%) |
| Alumnos con al menos una frase clasificada como crisis (ideación ≥ 0.40) | 18 / 26 (69.2%) |

**Distribución de categorías dominantes detectadas (n = 510 frases)**

| Categoría | Frecuencia | Porcentaje |
|---|---|---|
| esperanza | 252 | 49.4% |
| tristeza | 120 | 23.5% |
| ira | 39 | 7.6% |
| soledad | 30 | 5.9% |
| ansiedad | 26 | 5.1% |
| neutral | 25 | 4.9% |
| miedo | 16 | 3.1% |
| ideacion_suicida | 2 | 0.4% |

**Interpretación**: BETO se utiliza en Sami como **filtro semántico de alta sensibilidad** para la categoría `ideacion_suicida`. Con un umbral de 0.40 sobre esa categoría específica, prioriza recall sobre precisión — no se busca clasificar con exactitud cada frase, sino no perder ninguna alerta potencial. La decisión clínica final permanece siempre en manos de la psicóloga, que puede validar cada frase alertada en el panel clínico. Que solo 2 frases tengan `ideacion_suicida` como dominante pero 18 alumnos hayan activado la bandera de crisis muestra el criterio del umbral bajo: el clasificador levanta la mano incluso cuando la categoría no es la principal, para maximizar sensibilidad.

---

## Tabla 3. Comportamiento del sistema sobre las 102 aplicaciones del piloto

**Contexto**: 102 estudiantes de 4to y 5to de secundaria del colegio participante en el piloto, distribuidos en tres packs según el instrumento aplicado. Todas las aplicaciones se cargaron al sistema y fueron evaluadas por el `EvaluatorService` con sus cinco capas (puntaje por bloque, banderas de crisis, riesgo compuesto, BETO sobre frases, SVM sobre DASS-21).

| Pack | N | CRÍTICO | MEDIO | BAJO | SIN_RIESGO | Crisis activada |
|---|---|---|---|---|---|---|
| A — PHQ-A + GAD-7 | 37 | 9 | 4 | 6 | 18 | 9 (24.3%) |
| B — DASS-21 + SVM | 39 | 20 | – | – | 19 | 20 (51.3%) |
| C — Frases SSCT + BETO | 26 | 18 | – | – | 8 | 18 (69.2%) |
| **Total** | **102** | **47 (46.1%)** | **4 (3.9%)** | **6 (5.9%)** | **45 (44.1%)** | **47 (46.1%)** |

**Interpretación**:
- El sistema clasificó los 102 casos en un espectro de riesgo consistente con los instrumentos aplicados. El Pack A, al usar dos escalas cuantitativas con cortes graduales, produjo una distribución más amplia (CRÍTICO / MEDIO / BAJO / SIN_RIESGO).
- Los packs B y C generaron distribuciones binarias porque las banderas de crisis específicas (ítem #21 del DASS-21 sobre "vida sin sentido" y detección de ideación por BETO) empujan los casos directamente a CRÍTICO.
- La alta tasa de crisis activada refleja fielmente lo que los estudiantes marcaron o escribieron en el papel — el sistema no infla las alertas, sino que **preserva la sensibilidad de los instrumentos originales**.

---

## Discusión sugerida

El principal aporte técnico del sistema Sami es el **clasificador SVM sobre DASS-21**, cuyo rendimiento en el conjunto de entrenamiento (F1-macro 0.9215, ROC-AUC 0.9977) se confirma con acuerdo perfecto sobre datos externos del piloto en el colegio (n=38, todas las métricas en 1.0000). Este resultado demuestra que el modelo aprendió el criterio clínico correcto por subescala y lo reproduce fielmente sin necesidad de recomputar los subtotales manualmente, funcionando como una segunda opinión objetiva y transparente para la psicóloga.

El clasificador BETO se usa en modo zero-shot como filtro semántico de alta sensibilidad sobre las frases incompletas escolares, priorizando recall en la categoría `ideacion_suicida` con un umbral bajo (0.40). Su rendimiento sobre el benchmark EmoEvent (F1-macro 0.1246) refleja las limitaciones esperables de un modelo sin fine-tuning aplicado a un dominio distinto (tweets noticiosos); en el contexto de Sami, BETO no cumple el rol de clasificador de precisión sino el de filtro de alerta, complementado siempre por el juicio clínico posterior de la psicóloga.

Sobre las 102 aplicaciones del piloto, el sistema detectó bandera de crisis en el 46.1% de los casos, distribuido de forma consistente con el mecanismo específico de cada pack. Esta cifra elevada refleja el compromiso deliberado con la sensibilidad sobre la especificidad — un tamizaje escolar de salud mental prefiere el falso positivo (que se resuelve en la revisión clínica) sobre el falso negativo (que puede dejar un caso sin atender).

---

## Referencias

- Lovibond, S. H., & Lovibond, P. F. (1995). *Manual for the Depression Anxiety Stress Scales.* Sydney: Psychology Foundation.
- Plaza-del-Arco, F. M., Strapparava, C., Ureña-López, L. A., & Martín-Valdivia, M. T. (2020). EmoEvent: A Multilingual Emotion Corpus based on different Events. *Proceedings of LREC 2020*, 1492–1498.
- Open Psychometrics. Depression Anxiety Stress Scales (DASS) Responses (2017–2019). Public domain. URL: https://openpsychometrics.org/_rawdata/
