# SVM — trabajo en pausa

Este documento parquea el trabajo de Machine Learning. El sistema funciona **sin SVM**; el SVM es una segunda opinión opcional sobre el riesgo compuesto que ya calcula el `EvaluatorService` por reglas.

Se retoma cuando el usuario lo indique. Mientras tanto, la prioridad es la aplicación.

---

## Estado al 2026-06-24

### ✅ Lo que ya está descargado y listo

**Dataset elegido para entrenamiento real:** Open Source Psychometrics Project — DASS-42
- URL: https://openpsychometrics.org/_rawdata/DASS_data_21.02.19.zip
- 39,775 respuestas reales (2017–2019).
- 42 ítems Likert que cubren **depresión, ansiedad y estrés** (14 ítems cada uno).
- Demográficos: edad, género, país, educación.
- **7,269 adolescentes 13–17 años**, coincide con tu población.
- Public domain.

**Archivos en disco:**
```
data/dass_raw.zip                6.8 MB  (zip original)
data/dass/data.csv               20 MB   (39775 filas × 172 columnas)
data/dass/codebook.txt                   (documentación oficial)
```

### ⚠️ Lo que existe pero NO se usa en defensa

Un primer experimento que hicimos con dataset sintético (Mendeley PHQ-9). El F1 de 0.91 resultó engañoso porque `phq_total` estaba en las features (es función directa de la etiqueta). Lo dejamos como **baseline desechable**, no se cita en la tesis.

```
data/phq9_student_dataset.csv     (Mendeley sintético, no usar)
data/phq9_prepared.csv            (idem)
scripts/prepare_phq9_dataset.py   (idem)
scripts/train_svm.py              (idem)
models/svm_riesgo.joblib          (idem)
reports/svm_training.md           (idem)
```

---

## Cuando se retome — checklist técnico

1. **Preparación** `scripts/prepare_dass_dataset.py`:
   - Cargar `data/dass/data.csv`.
   - Filtrar a `13 ≤ age ≤ 17`.
   - Restar 1 a cada `QxA` para llevar la escala a 0–3.
   - Sumar por dimensión:
     - Depression: items 3, 5, 10, 13, 16, 17, 21, 24, 26, 31, 34, 37, 38, 42
     - Anxiety: items 2, 4, 7, 9, 15, 19, 20, 23, 25, 28, 30, 36, 40, 41
     - Stress: items 1, 6, 8, 11, 12, 14, 18, 22, 27, 29, 32, 33, 35, 39
   - Aplicar cuts oficiales DASS-42 → severidad por dimensión.
   - Label global = peor severidad de las 3, mapeada a `SIN_RIESGO/BAJO/MEDIO/ALTO/CRITICO`.
   - Guardar `data/dass_prepared.csv`.

2. **Entrenamiento** `scripts/train_svm_dass.py`:
   - Features: los 42 ítems individuales + age + gender (one-hot).
   - Pipeline: `StandardScaler → SVC(kernel='rbf', class_weight='balanced')`.
   - 5-fold StratifiedKFold sobre train, hold-out 20%.
   - Guardar modelo en `models/svm_riesgo_dass.joblib`.
   - Reporte en `reports/svm_dass.md` (F1-macro por clase, matriz, CV).

3. **Integración al `EvaluatorService`** (opcional, último):
   - Normalizar las features de Sami (PHQ-A/GAD-7 totals → percentiles 0–1) para que el modelo entrenado en DASS pueda usarse en producción.
   - Agregar al resultado de `EvaluatorService.evaluar()` un campo `riesgo_svm` como segunda opinión junto al `riesgo_global` basado en reglas.
   - En la vista de resultado de la psicóloga, mostrar ambos lado a lado.

---

## Cuts oficiales DASS-42

| Severidad | Depression | Anxiety | Stress |
|--|--|--|--|
| Normal | 0–9 | 0–7 | 0–14 |
| Mild | 10–13 | 8–9 | 15–18 |
| Moderate | 14–20 | 10–14 | 19–25 |
| Severe | 21–27 | 15–19 | 26–33 |
| Extremely Severe | 28+ | 20+ | 34+ |

Mapeo a riesgo global de Sami: peor severidad entre las 3 dimensiones.

| Peor severidad | Riesgo Sami |
|--|--|
| Normal en las 3 | SIN_RIESGO |
| Mild en alguna | BAJO |
| Moderate en alguna | MEDIO |
| Severe en alguna | ALTO |
| Extremely Severe en alguna | CRITICO |

---

## Cita académica del dataset

> Open Source Psychometrics Project. (2019). *DASS Data (2017–2019)*. Raw data archive. Retrieved from https://openpsychometrics.org/_rawdata/. Public domain.

Acompañar con la cita original de la escala:

> Lovibond, S. H., & Lovibond, P. F. (1995). *Manual for the Depression Anxiety Stress Scales* (2nd ed.). Sydney: Psychology Foundation.
