# SVM sobre PHQ-A — reentrenamiento con ENDES

Reemplaza a DASS-42 como fuente de entrenamiento del SVM para los
cuestionarios que se aplican hoy. El modelo de DASS-21 se conserva sin
tocar para que los 39 reportes del piloto de julio 2026 sigan siendo
reproducibles.

- **Script**: `scripts/train_svm_endes.py`
- **Artefacto**: `models/svm_endes_phq9.joblib` (versión `endes-phq9-1.0`)
- **Reporte largo**: `reports/svm_endes.md` + `.json` (se regeneran al correr
  el script; `reports/` no está en git)

```bash
venv/bin/python scripts/train_svm_endes.py --edad-max 17
```

## El dato

`estudiantes_phq9_endes2025.xlsx` — Encuesta Demográfica y de Salud
Familiar del INEI, módulo de salud mental.

| | |
|---|---|
| Registros totales | 2 238 (edades 15–24) |
| Filtrados a ≤ 17 años | **1 370** |
| Ítems | `QS700A`–`QS700I`, escala 0–3, sin valores faltantes |
| Etiqueta | `en_riesgo` si la suma de los 9 ítems ≥ 10 (Kroenke 2001) |
| Positivos | 110 (8.0 %) |
| Partición | 1 096 entrenamiento / 274 prueba, estratificada |

Los 9 ítems mapean 1:1 contra el PHQ-A del banco de Sami: misma escala,
mismo orden, misma redacción adaptada. `QS700H` (agitación / lentitud
psicomotora) tiene la media más baja (0.097), que es lo esperable en
PHQ-9 y sirve como control de que el orden de columnas es el correcto.

El corte ≥ 10 coincide con el que ya usa `PHQA_CORTES` para "moderada",
así que el modelo y las reglas hablan de la misma frontera.

## Métricas — población objetivo (≤ 17 años)

| Métrica | Valor |
|---|---|
| CV F1-macro (5-fold sobre entrenamiento) | **0.9461 ± 0.0293** |
| Accuracy (prueba) | 0.9818 |
| F1-macro (prueba) | 0.9418 |
| F1-weighted (prueba) | 0.9823 |
| ROC-AUC (prueba) | 0.9978 |
| **Sensibilidad en `en_riesgo`** | **0.9545** |
| Especificidad | 0.9841 |
| Precisión en `en_riesgo` | 0.840 |
| Valor predictivo negativo | 0.996 |

Matriz de confusión sobre las 274 de prueba:

| real \ predicho | sin_riesgo | en_riesgo |
|---|---|---|
| **sin_riesgo** | 248 | 4 |
| **en_riesgo** | 1 | 21 |

Un falso negativo. En tamizaje de salud mental ese es el error que
importa, y por eso la sensibilidad (0.955) va antes que la accuracy en
la tabla.

Variante ≤ 16 años (n = 1 015, 71 positivos), por si hace falta acotar
más la edad: CV F1-macro 0.9400 ± 0.0248 · accuracy 0.9951 · F1-macro
0.9802 · ROC-AUC 0.9985 · sensibilidad 0.9286 · especificidad 1.0.

## Lo que estas métricas no dicen

**La regla de una línea le gana al modelo.** Sobre el mismo conjunto de
prueba:

| | SVM | `suma de los 9 ítems ≥ 10` |
|---|---|---|
| Accuracy | 0.9818 | **1.0** |
| F1-macro | 0.9418 | **1.0** |
| Sensibilidad | 0.9545 | **1.0** |

No es una sorpresa ni un error del entrenamiento: es aritmética. La
etiqueta se define como `suma(ítems) ≥ 10` y las features son esos
mismos ítems. Verificado en el archivo: `phq9_total` es exactamente la
suma de las nueve columnas, y `severidad_3` es un corte sobre ese total.
El modelo está aprendiendo a aproximar una suma, y la aproxima con 98 %
de acierto en lugar del 100 % que da sumar.

Entonces el 0.9461 de CV F1-macro es un número correcto y reproducible,
pero mide *qué tan bien el SVM reproduce el corte del PHQ-9*, no *qué
tan bien detecta depresión*. Reportarlo como lo segundo sería
sobrevender lo que hay.

El mismo problema tenía el modelo de DASS-21 (entrenado y evaluado
contra los cortes de Lovibond), así que el cambio de dataset mejora la
procedencia del dato — población peruana, adolescente, encuesta oficial,
contra una muestra voluntaria de internet — pero no rompe la
circularidad.

**Cómo se rompe.** Entrenando contra algo que no sea función de los
ítems: el riesgo que asignan las psicólogas. Es exactamente lo que está
recogiendo el módulo de etiquetado (`SAMI-PSI-01` y `SAMI-PSI-02`, 104
casos cada una, a ciegas e independientes). Cuando esas etiquetas estén,
la comparación SVM contra juicio clínico aparece en
**Etiquetado · Métricas** y ésa sí es una validación externa.

Para la defensa, la lectura defendible de esta sección es: el SVM
funciona, es reproducible y está entrenado con datos peruanos reales de
la población objetivo; su validez clínica está pendiente de la
validación contra criterio experto, que ya está instrumentada.

## Integración

`EvaluatorService._segunda_opinion_svm` elige el modelo según los
bloques que trae el cuestionario:

| Bloques presentes | Modelo |
|---|---|
| DASS-21 | `svm_dass21.joblib` (piloto de julio) |
| DASS-21 + PHQ-A | `svm_dass21.joblib` — prioridad, para no alterar reportes ya emitidos |
| PHQ-A | `svm_endes_phq9.joblib` |
| ninguno de los dos | sin segunda opinión |

Si falta alguna de las 9 respuestas, no opina — devuelve `None` en lugar
de imputar. El resultado guardado incluye `instrumento`, que es lo que
la pantalla del reporte muestra en el encabezado; los resultados
anteriores a este cambio no traen el campo y se leen como DASS-21.

Los dos `.joblib` viajan en el paquete de despliegue y el workflow falla
si alguno no está, antes y después de comprimir.

## Fuente

> Instituto Nacional de Estadística e Informática (INEI). *Encuesta
> Demográfica y de Salud Familiar (ENDES)*. Módulo de salud mental,
> cuestionario PHQ-9 (variables QS700A–QS700I). Lima, Perú.

> Kroenke K, Spitzer RL, Williams JB. *The PHQ-9: validity of a brief
> depression severity measure*. J Gen Intern Med. 2001;16(9):606-613.

## Por qué el `.xlsx` no está en el repositorio

`estudiantes_phq9_endes2025.xlsx` trae `HHID_salud` — el identificador de
hogar de ENDES — en la misma fila que las respuestas de salud mental. El
repositorio es público, así que el archivo queda fuera de git
(`.gitignore`) y vive solo en la máquina de trabajo.

Lo que sí viaja es el modelo entrenado. Para reentrenar hay que
conseguir el archivo del portal de microdatos del INEI y ponerlo en la
raíz del repositorio.
