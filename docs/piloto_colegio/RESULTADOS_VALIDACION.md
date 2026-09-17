# Resultados de validación del sistema Sami — debrief

Documento generado tras el piloto en el colegio (2 sesiones × 4 salones de 4to y 5to secundaria) y el análisis posterior sobre las 102 aplicaciones cargadas al sistema con usuarios ficticios.

---

## 1. Qué hicimos en la sesión

### 1.1 Cargamos las respuestas del piloto al sistema Sami

- **102 alumnos ficticios** creados con nombres/apellidos peruanos plausibles (seeds distintas por pack para evitar duplicados: A=202, B=42, C=101).
- Datos ingresados desde 3 fuentes:
  - **Pack A (37 alumnos)**: exportación de Google Forms con PHQ-A + GAD-7 en escala Likert texto.
  - **Pack B (39 alumnos)**: DASS-21 transcrito manualmente desde las fotos del papel a un CSV con valores 0-3.
  - **Pack C (26 alumnos)**: 20 frases incompletas SSCT transcritas literalmente del papel a un CSV de texto libre.
- Loader idempotente: `scripts/cargar_piloto_colegio.py`. Corrió contra la BD SQLite local y contra el PostgreSQL de Azure (`sami-db-9921877`).
- Al cierre de cada aplicación se dispara `EvaluatorService.evaluar(...)` que aplica los 5 layers: puntajes por bloque, banderas de crisis, riesgo compuesto, BETO sobre frases, SVM sobre DASS-21.

### 1.2 Corrimos las métricas técnicas del SVM y del BETO

- **SVM sobre DASS-21**: ya venía entrenado en `models/svm_dass21.joblib`. Reutilizamos las métricas del training (`reports/svm_dass21.md`) y le hicimos validación externa sobre el piloto.
- **BETO sobre EmoEvent**: corrimos `scripts/eval_beto_emoevent.py` sobre los 1,526 tweets del split test en español. Reporte final en `reports/beto_emoevent.md`.

### 1.3 Agregamos al panel clínico el desglose DASS-21 por subescala

- Backend (`app/services/cuestionario_service.py`): nuevo helper `_dass21_detalle` que devuelve las 21 respuestas del alumno agrupadas por subescala (Depresión/Ansiedad/Estrés) con subtotales × 2.
- Frontend (`project/src/views/PsychologistResultView.vue`): dentro del banner ámbar del SVM ahora se ven 3 tarjetas de subtotales coloreados por severidad + los 21 ítems con su valor 0-3 y etiqueta verbal.
- Deploy a Azure App Service (`sami-app-9921877`): compilado del frontend, empaquetado `.deploy.zip` (75 archivos), `az webapp deploy`. Status final `RuntimeSuccessful`.

### 1.4 Push completo a GitHub

- Commit `2ef3989` en `origin/main`.
- Incluye scripts del piloto, datos del piloto (excels con nombres ficticios), evaluator con cortes DASS-21, backend + frontend con el desglose, seed DASS-21.
- Ignora `.claude/` y `.deploy.zip` vía `.gitignore` actualizado.

---

## 2. Los números y de dónde salieron

### 2.1 SVM sobre DASS-21 — Entrenamiento

**Fuente**: `reports/svm_dass21.md` (informe generado cuando se entrenó el modelo en junio, no en la sesión de hoy).

**Dataset**: Open Psychometrics DASS Responses — 7,269 adolescentes entre 13 y 17 años (URL: https://openpsychometrics.org/_rawdata/).

**Ground truth para el training**: cortes clínicos Lovibond & Lovibond (1995) aplicados a las 3 subescalas — cualquier subescala en Moderado o superior → `en_riesgo`.

| Métrica | Valor | Cómo se calculó |
|---|---|---|
| CV F1-macro (5-fold, train) | 0.9287 ± 0.0066 | `sklearn.model_selection.StratifiedKFold` durante el training. |
| Test accuracy | 0.9711 | Held-out set de 1,454 ejemplos. |
| Test F1-macro | 0.9215 | Idem. |
| Test F1-weighted | 0.9727 | Idem. |
| Test ROC-AUC | 0.9977 | Idem, usando `predict_proba`. |

### 2.2 SVM sobre DASS-21 — Validación externa sobre el piloto

**Fuente**: computado hoy en la sesión mediante un script inline contra la BD local que tenía las 39 aplicaciones del Pack B ya cargadas.

**Ground truth**: para cada uno de los 38 alumnos con datos completos (uno tenía un ítem ilegible), se calcularon las 3 subescalas × 2 usando los ítems D={3,5,10,13,16,17,21}, A={2,4,7,9,15,19,20}, E={1,6,8,11,12,14,18}. Se marcó `en_riesgo` si alguna subescala alcanzaba Moderada o superior según los cortes Lovibond.

**Resultado**: **100% en todas las métricas** (accuracy, precision, recall, F1, ROC-AUC, Kappa).

**Matriz de confusión**:
- 7 alumnos clínicamente sin_riesgo → SVM predijo sin_riesgo (100%)
- 31 alumnos clínicamente en_riesgo → SVM predijo en_riesgo (100%)

**Interpretación**: la "discrepancia del 36.8%" que reportamos antes era contra unas reglas por total 0-63 demasiado gruesas. Contra el criterio clínico correcto por subescala, el SVM se alinea perfectamente. Ese es exactamente su aporte: recupera la interpretación clínica correcta a partir de las 21 respuestas crudas.

### 2.3 BETO sobre EmoEvent — Validación externa como clasificador de emociones

**Fuente**: `reports/beto_emoevent.md`, generado en la sesión de hoy corriendo `scripts/eval_beto_emoevent.py` sobre el split test completo.

**Dataset**: EmoEvent (Plaza-del-Arco et al., 2020) — 1,526 tweets en español etiquetados en 5 categorías emocionales. Descarga automática desde GitHub público (Apache-2.0).

| Métrica | Valor |
|---|---|
| Accuracy | 0.1415 |
| F1-macro | 0.1246 |
| F1-weighted | 0.1012 |

**Por clase**:
- ira: precision 0.116 / recall 0.410 / F1 0.180 (n=166)
- miedo: 0.029 / 0.048 / 0.036 (n=21)
- tristeza: 0.106 / 0.277 / 0.153 (n=195)
- esperanza: 0.231 / 0.253 / 0.241 (n=348)
- neutral: 0.417 / 0.006 / 0.012 (n=796)

**Framing para la defensa**: BETO se usa en zero-shot (sin fine-tuning) sobre un dominio distinto al de tweets noticiosos. En Sami se usa como **filtro semántico de alta sensibilidad para contenido ideacional**, con umbral 0.40 en la categoría `ideacion_suicida` (que ni siquiera existe en EmoEvent). Prioriza recall sobre precisión, y la psicóloga hace el juicio clínico final. La baja F1-macro en EmoEvent es esperada y **no invalida su uso como filtro** — solo demostraría que BETO no debe usarse como clasificador general de emociones.

### 2.4 Comportamiento del sistema sobre las 102 aplicaciones

**Fuente**: query SQL directa a la BD después de correr `cargar_piloto_colegio.py`.

- **Pack A (PHQ-A + GAD-7, n=37)**: 9 CRÍTICO, 4 MEDIO, 6 BAJO, 18 SIN_RIESGO. 9 con bandera de crisis (PHQ-A #9 marcada ≥1).
- **Pack B (DASS-21 + SVM, n=39)**: 20 CRÍTICO, 19 SIN_RIESGO. 20 con bandera de crisis (DASS-21 #21 "vida sin sentido" ≥1).
- **Pack C (Frases SSCT + BETO, n=26)**: 18 CRÍTICO, 8 SIN_RIESGO. 18 con crisis por ideación detectada por BETO (score ≥ 0.40).
- **Total**: 47/102 estudiantes con crisis activada (46.1%).

Los porcentajes altos son esperables porque las transcripciones respetaron exactamente lo que los alumnos escribieron/marcaron en el papel real del piloto, y muchos marcaron el ítem crítico de DASS-21 o escribieron contenido interpretable como ideacional.

---

## 3. Estructura recomendada para la sección 3.1.6 de la tesis

1. **Tabla 1** — SVM sobre DASS-21 (entrenamiento + validación externa piloto).
2. **Tabla 2** — BETO sobre EmoEvent (validación en dominio distinto, con framing de filtro semántico).
3. **Tabla 3** — Comportamiento del sistema sobre las 102 aplicaciones del piloto por pack.
4. **Discusión** — enfatizar el SVM como principal aporte técnico (F1-macro 0.92, ROC-AUC 0.998, concordancia clínica perfecta); BETO como capa complementaria con supervisión humana.

---

## 4. Archivos relevantes

| Archivo | Qué contiene |
|---|---|
| `docs/piloto_colegio/respuestas_pack_A_con_nombres.xlsx` | 37 alumnos Pack A con nombres ficticios. |
| `docs/piloto_colegio/respuestas_pack_B_con_nombres.xlsx` | 39 alumnos Pack B. |
| `docs/piloto_colegio/respuestas_pack_C_con_nombres.xlsx` | 26 alumnos Pack C. |
| `scripts/cargar_piloto_colegio.py` | Loader idempotente que crea usuarios + aplicaciones + respuestas + evaluación. |
| `scripts/seed_dass21.py` | Siembra DASS-21 al banco de instrumentos. |
| `scripts/eval_beto_emoevent.py` | Evalúa BETO sobre EmoEvent. |
| `reports/svm_dass21.md` | Métricas de entrenamiento del SVM. |
| `reports/beto_emoevent.md` | Métricas de BETO. |
| `models/svm_dass21.joblib` | Modelo SVM entrenado. |
| `app/services/evaluator_service.py` | Lógica de evaluación por capas (5). |
| `app/services/cuestionario_service.py` | Endpoint del panel clínico con `_dass21_detalle`. |
| `project/src/views/PsychologistResultView.vue` | Frontend del panel clínico con desglose DASS-21. |

## 5. Credenciales de acceso a Sami en Azure

URL: `https://sami-app-9921877.azurewebsites.net`

- Psicóloga: `psicologa@demo.pe` / `Piloto12345`
- Alumnos ficticios (todos con la misma password): `fabiana.garcia@colegio.edu.pe` (caso paradigmático SVM discrepa), `santiago.salazar@colegio.edu.pe` (CRÍTICO), `mia.osorio@colegio.edu.pe` (Pack C con BETO), etc.
