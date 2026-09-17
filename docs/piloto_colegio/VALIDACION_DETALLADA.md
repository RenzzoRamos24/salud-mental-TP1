# Validación — resultados detallados

Material para ampliar la sección de Validación (~1.5 pág). Todos los números
provienen de artefactos reproducibles: `reports/svm_dass21.json` (entrenamiento)
y consultas directas a la base del piloto (`mental_health.db`, plantilla
"Piloto Colegio · Pack B"). Nada está estimado ni redondeado a mano.

---

## A. Matriz de confusión del SVM

### A.1 Conjunto de prueba del entrenamiento

Modelo: SVM kernel RBF sobre los 21 ítems crudos del DASS-21. Dataset: Open
Psychometrics DASS Responses, submuestra de adolescentes de 13–17 años
(N = 7,269; 5,815 entrenamiento / 1,454 prueba *held-out*). Etiqueta de
referencia: cortes de Lovibond & Lovibond (1995) por subescala — `en_riesgo`
si alguna subescala alcanza Moderado o superior.

**Tabla A.1 — Matriz de confusión, conjunto de prueba (n = 1,454)**

| | Predicho: sin riesgo | Predicho: en riesgo | Total real |
|---|---|---|---|
| **Real: sin riesgo** | 128 (VN) | 2 (FP) | 130 |
| **Real: en riesgo** | 40 (FN) | 1,284 (VP) | 1,324 |
| **Total predicho** | 168 | 1,286 | 1,454 |

**Tabla A.2 — Índices diagnósticos derivados (clase positiva = `en_riesgo`)**

| Índice | Fórmula | Valor |
|---|---|---|
| Sensibilidad (recall) | VP / (VP+FN) = 1284/1324 | 0.9698 |
| Especificidad | VN / (VN+FP) = 128/130 | 0.9846 |
| Valor predictivo positivo | VP / (VP+FP) = 1284/1286 | 0.9984 |
| Valor predictivo negativo | VN / (VN+FN) = 128/168 | 0.7619 |
| Exactitud global | (VP+VN) / N = 1412/1454 | 0.9711 |
| F1-macro | — | 0.9215 |
| F1 ponderado | — | 0.9727 |
| ROC-AUC | — | 0.9977 |
| F1-macro validación cruzada (5-fold, train) | — | 0.9287 ± 0.0066 |

**Lectura.** El modelo comete 42 errores sobre 1,454 casos. El error dominante
es el falso negativo (40 casos, 2.8% del total): estudiantes en riesgo
clasificados como sin riesgo. Esto se refleja en el VPN de 0.7619, el índice
más bajo del conjunto — cuando el modelo dice "sin riesgo", acierta en 3 de
cada 4 casos. Para un tamizaje escolar ese es el índice crítico y conviene
declararlo explícitamente como limitación: el sistema no debe usarse para
*descartar* riesgo, solo para *priorizar* revisión clínica. El desbalance del
dataset (91.0% de casos positivos) explica en parte esta asimetría.

### A.2 Validación externa sobre el piloto

**Tabla A.3 — Matriz de confusión, piloto en el colegio (n = 38)**

| | Predicho: sin riesgo | Predicho: en riesgo | Total real |
|---|---|---|---|
| **Real: sin riesgo** | 7 | 0 | 7 |
| **Real: en riesgo** | 0 | 31 | 31 |

Exactitud, precisión, recall, F1-macro, ROC-AUC y Kappa de Cohen = 1.0000.

**Nota metodológica obligatoria.** Este acuerdo perfecto debe presentarse con
su matiz, porque un jurado lo va a preguntar. La etiqueta de referencia se
obtuvo aplicando los cortes de Lovibond a las tres subescalas, calculadas a
partir de los mismos 21 ítems que el SVM recibe como entrada. La referencia es
entonces una función determinista de las variables predictoras, no un juicio
clínico independiente. Lo que la Tabla A.3 demuestra es **fidelidad de
reproducción** del criterio clínico sobre una población distinta a la de
entrenamiento (adolescentes peruanos vs. muestra internacional de Open
Psychometrics), no capacidad predictiva sobre un diagnóstico externo. La
formulación defendible es: *"el modelo reproduce sin degradación el criterio
Lovibond sobre datos de una población no vista durante el entrenamiento"*. Una
validación de criterio en sentido estricto exigiría contrastar contra
evaluación clínica independiente, lo cual se declara como trabajo futuro.

---

## B. Desglose por subescala del DASS-21

Base: 38 estudiantes del Pack B con los 21 ítems completos (de 39 aplicaciones
cargadas; uno se descartó por ítem ilegible en el papel original). Puntajes de
subescala calculados como la suma de sus 7 ítems multiplicada por 2, según el
procedimiento estándar de la versión de 21 ítems.

**Tabla B.1 — Estadísticos descriptivos y consistencia interna por subescala (n = 38)**

| Subescala | M | DE | Mdn | Mín | Máx | α de Cronbach | ≥ Moderado |
|---|---|---|---|---|---|---|---|
| Depresión | 15.05 | 7.57 | 16.0 | 2 | 30 | 0.723 | 23 (60.5%) |
| Ansiedad | 13.74 | 7.84 | 14.0 | 2 | 32 | 0.772 | 28 (73.7%) |
| Estrés | 18.00 | 7.07 | 18.0 | 2 | 40 | 0.663 | 17 (44.7%) |
| **Escala total (21 ítems)** | — | — | — | — | — | **0.859** | — |

**Tabla B.2 — Distribución por banda de severidad (cortes Lovibond & Lovibond, 1995)**

| Subescala | Normal | Leve | Moderado | Severo | Ext. severo |
|---|---|---|---|---|---|
| Depresión | 10 (26.3%) | 5 (13.2%) | 14 (36.8%) | 6 (15.8%) | 3 (7.9%) |
| Ansiedad | 9 (23.7%) | 1 (2.6%) | 14 (36.8%) | 5 (13.2%) | 9 (23.7%) |
| Estrés | 11 (28.9%) | 10 (26.3%) | 13 (34.2%) | 3 (7.9%) | 1 (2.6%) |

**Tabla B.3 — Patrón de co-ocurrencia entre subescalas en zona de alerta (≥ Moderado)**

| Combinación | n | % |
|---|---|---|
| Depresión + Ansiedad + Estrés | 15 | 39.5% |
| Solo Ansiedad | 7 | 18.4% |
| Ninguna subescala en alerta | 7 | 18.4% |
| Depresión + Ansiedad | 5 | 13.2% |
| Solo Depresión | 2 | 5.3% |
| Ansiedad + Estrés | 1 | 2.6% |
| Depresión + Estrés | 1 | 2.6% |
| **Al menos una subescala en alerta** | **31** | **81.6%** |

**Lectura.**

- La consistencia interna es aceptable en Depresión (α = 0.723) y Ansiedad
  (α = 0.772), y marginal en Estrés (α = 0.663, por debajo del umbral
  convencional de 0.70). La escala total alcanza α = 0.859, un valor bueno.
  Con n = 38 el intervalo de confianza de α es amplio, lo que conviene
  señalar. El α menor de Estrés es un hallazgo esperable: es la subescala
  conceptualmente más heterogénea del DASS.
- Ansiedad es la dimensión más elevada de la muestra: 73.7% en zona de alerta
  y la mayor proporción de casos extremadamente severos (23.7%), pese a tener
  la media más baja de las tres. Esto se explica por los cortes de Lovibond,
  que son más exigentes en Ansiedad (Moderado desde 10) que en Estrés
  (Moderado desde 19).
- El perfil predominante es de **malestar generalizado, no específico**: el
  39.5% de la muestra está en alerta en las tres dimensiones simultáneamente.
  Esto respalda la decisión de diseño de Sami de reportar un riesgo compuesto
  en lugar de etiquetas por trastorno.
- El ítem 21 ("Sentí que la vida no tenía ningún sentido"), marcado como
  bandera de crisis en el sistema, obtuvo valor ≥ 1 en 19 de 38 estudiantes
  (50.0%).
- **Verificación cruzada:** los 31 estudiantes en alerta por al menos una
  subescala coinciden exactamente con los 31 casos `en_riesgo` de la Tabla
  A.3. Las dos tablas se computaron por vías independientes, lo que confirma
  la coherencia interna del pipeline.

---

## C. Encuesta de usabilidad — estado

**No hay datos de usabilidad. La tabla de encuestas del sistema está vacía
(0 registros) tanto en la base local como en la del piloto.** No se aplicó SUS
ni ningún otro instrumento de satisfacción durante las dos sesiones en el
colegio. Cualquier cifra que aparezca en el documento sin haber recolectado
antes sería inventada.

Lo que sí existe es el instrumento implementado y desplegado en el sistema
(`app/models/satisfaction_survey.py`, endpoint `POST /survey/satisfaction`,
resumen agregado en `GET /survey/admin/satisfaction/summary`). **No es SUS**:
son 5 ítems tipo Likert de 1 a 5 —

| Campo | Dimensión medida |
|---|---|
| `facilidad_uso` | Facilidad de uso percibida |
| `utilidad` | Utilidad percibida |
| `confianza` | Confianza en la privacidad de sus datos |
| `recomendaria` | Intención de recomendación (tipo NPS) |
| `nivel_animo_post` | Estado de ánimo después de usar el sistema |

Con eso se reporta un % de satisfacción (media por dimensión y % de respuestas
≥ 4), no un puntaje SUS de 0 a 100.

**Opciones, en orden de solidez:**

1. **Aplicar SUS (recomendado si el asesor lo pidió por nombre).** Son 10
   ítems estandarizados, produce un puntaje 0–100 comparable con la literatura
   y el punto de corte de 68 como "aceptable" está publicado. Requiere agregar
   el instrumento al sistema (o aplicarlo en papel/Google Forms) y una sesión
   de recolección. Es el único camino que permite escribir "SUS = X" con
   respaldo.
2. **Usar el instrumento de 5 ítems que ya está desplegado.** No requiere
   desarrollo — solo respondientes. Se reporta como "% de satisfacción por
   dimensión". Menos comparable con la literatura, pero honesto y ya validado
   internamente en el diseño del sistema.
3. **Declarar la ausencia como limitación.** Escribir en la sección de
   limitaciones que la validación de usabilidad queda pendiente y forma parte
   del trabajo futuro. Es defendible si el tiempo no alcanza, pero deja la
   sección de Validación incompleta respecto de lo que pidió el asesor.

---

## Referencias

- Lovibond, S. H., & Lovibond, P. F. (1995). *Manual for the Depression
  Anxiety Stress Scales* (2ª ed.). Sydney: Psychology Foundation of Australia.
- Open Psychometrics. *Depression Anxiety Stress Scales (DASS) Responses*
  (2017–2019). Dominio público. https://openpsychometrics.org/_rawdata/
- Brooke, J. (1996). SUS: A "quick and dirty" usability scale. En P. W. Jordan
  et al. (Eds.), *Usability Evaluation in Industry* (pp. 189–194). Taylor &
  Francis. *(solo si se opta por SUS)*

---

## Reproducibilidad

| Número | Fuente |
|---|---|
| Tablas A.1–A.2 | `reports/svm_dass21.json` (generado al entrenar el modelo) |
| Tabla A.3 | Validación externa sobre Pack B, documentada en `docs/piloto_colegio/RESULTADOS_VALIDACION.md` §2.2 |
| Tablas B.1–B.3 | `scripts/dass21_subescalas.py` sobre `mental_health.db`, plantilla Pack B |
