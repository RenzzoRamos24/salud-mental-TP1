# Sami — guía rápida para Claude

Proyecto de tesis: sistema de evaluación de salud mental para estudiantes de secundaria de un colegio privado. La psicóloga arma cuestionarios desde un banco clínico y los asigna a los alumnos; el sistema los evalúa y genera reportes.

## Stack

| Capa | Tecnología | Path |
|------|------------|------|
| Backend | FastAPI + SQLAlchemy + SQLite | `app/` |
| NLP | `Recognai/bert-base-spanish-wwm-cased-xnli` (BETO + XNLI zero-shot multi-label) | `app/services/nlp_service.py` |
| Frontend | Vue 3 + Vite + Tailwind | `project/` |
| Auth | JWT (estudiante / psicologo / admin) | `app/api/v1/endpoints/auth.py` |

## Primer arranque (sistema vacío)

```bash
# 1. Variables de entorno (copia + completa)
cp .env.example .env

# 2. Crear tablas + sembrar el banco fijo de instrumentos
rm -f mental_health.db
venv/bin/python -c "from app.database import engine, Base; import app.models; Base.metadata.create_all(bind=engine)"
venv/bin/python -c "import sqlite3; c=sqlite3.connect('mental_health.db'); c.executescript(open('seeds/banco_instrumentos.sql').read()); c.commit()"

# 3. Crear el primer admin (default: admin@admin.com / Admin12345 — cambia en .env)
venv/bin/python -m scripts.seed_admin

# 4. Levantar servicios
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
cd project && npm run dev    # puerto 5173
```

Docs FastAPI: http://127.0.0.1:8000/docs

Las psicólogas y estudiantes se registran desde `/register`. El admin solo se crea
con `seed_admin` (no se permite alta vía UI por integridad de roles).

## Modelo conceptual

```
Banco fijo (validado, no editable)
  └─ BankInstrumento (PHQ-A, GAD-7, SRQ-20, RSES, WHO-5, UCLA-3)
       └─ BankItem (ítems con criterio DSM-5 + banderas de crisis)
  └─ BankFraseIncompleta (40 frases, 8 áreas, adaptación SSCT)

Banco personalizado (psicóloga)
  └─ BloqueCustom (nombre, escala, cortes)
       └─ BloqueCustomItem (preguntas propias)

Plantilla
  └─ PlantillaCuestionario (nombre, descripción)
       └─ PlantillaBloque (referencia a instrumento, custom o áreas de frases)

Aplicación (asignación al alumno)
  └─ AplicacionCuestionario (estado: pendiente → en_progreso → completado → revisado)
       └─ RespuestaAplicacion (valor_num o valor_texto por ítem)
       └─ resultado_json: bloques con puntaje/severidad + frases con clasificación BETO
```

## Estructura

```
app/
  api/v1/endpoints/
    auth, consent, users, psychologist, admin, content, survey, sos,
    bank, plantilla, cuestionario
  models/
    user, consent, password_reset, cita, clinical_note, access_log,
    configuracion, educational_content, satisfaction_survey, sos_event,
    bank (todos los modelos del sistema de cuestionarios)
  services/
    auth, consent, user, content, survey, sos, cita, notes, oauth,
    nlp (BETO zero-shot 8 categorías), admin, psychologist, scheduler,
    bank, plantilla, cuestionario, evaluator
  schemas/    pydantic in/out (auth, user, consent, cita, admin,
              psychologist, bank)
  middleware/ access_log
  database, config, main

project/src/
  components/  AppTopbar, AuthShell, PageHeader, RiskBadge, SOSButton,
               StatCard, StudentTable, AlertRow, SevChip
  views/
    Auth:           Login, Register, Forgot/Reset password, OAuthCallback
    Onboarding:     Consent
    Comunes:        MainMenu, Profile, Recursos, SatisfactionSurvey
    Alumno:         StudentQuestionnaires, StudentAnswer
    Psicóloga:      PsychologistDashboard, PsychologistStudents,
                    PsychologistAlerts, StudentHistory,
                    PsychologistBank, PsychologistCustomBlock,
                    PsychologistTemplates, PsychologistAssign,
                    PsychologistResult
    Admin:          AdminDashboard, AdminSystem, AdminContent,
                    AdminReports, AdminLogs
  store/auth.js    sesión reactiva (JWT)
  api.js           cliente axios
  router/index.js  rutas con guard por rol y consentimiento
seeds/
  banco_instrumentos.sql   DDL + inserts del banco fijo
```

## Reglas funcionales del sistema

1. **Las 6 escalas validadas no son editables** desde la UI. Su validez depende de la redacción literal publicada.
2. **Bloques custom**: la psicóloga define nombre, escala (likert o binaria), ítems y cortes. El sistema sugiere cortes por tercios (`GET /banco/sugerir-cortes`).
3. **Evaluación por capas** (`EvaluatorService`):
   - Capa 1: puntaje por bloque con cortes científicos.
   - Capa 2: banderas de crisis (PHQ-A #9 ≥ 1, SRQ-20 #17 = 1, BETO ideación ≥ 0.40).
   - Capa 3: riesgo compuesto a partir del número de bloques en zona de alerta.
   - Capa 4: BETO clasifica las frases incompletas en 8 categorías emocionales.
4. **El alumno nunca ve el reporte clínico**. Solo confirmación de cierre y SOS.
5. **El sistema no diagnostica**: reporta señales y banderas, la psicóloga interpreta.

## Identidad visual

Verde agua + blanco + negro. Tailwind: `green-*`, `brand-*`/`mint-*` (alias del verde), `cream-*` (neutros fríos). Fondo body blanco puro. Tipografía Work Sans. Sombras suaves. Sin emojis decorativos.

Utilidades clave en `project/src/style.css`: `.hero-serif`, `.hero-mint`, `.menu-card`, `.card`, `.card-hero`, `.btn-{primary,mint,ghost,coral}`, `.chip-mint`, `.label-kicker`, `.banner-{info,warn,danger,success}`, `.page-shell`, `.page-shell-wide`.

## Documentos clave

- `BANCO_INSTRUMENTOS.md` — referencia científica de las 6 escalas + 40 frases.
- `METRICAS_VALIDACION.md` — 6 dimensiones de validación con umbrales.
- `PLAN_RECOLECCION_DATOS.md` — cómo obtener los datos para cada métrica.
- `PENDIENTES.md` — qué falta (entregables académicos, no funcionales).
- `seeds/banco_instrumentos.sql` — DDL + inserts del banco fijo.

## SVM clínico (vigente, 2026-10-15)

`models/svm_clinico.joblib` es el primer modelo de Sami entrenado contra
**criterio clínico humano** y no contra el corte de un instrumento.

| | |
|---|---|
| Entrada | los 16 ítems que el sistema ya recolecta: PHQ-A 1..9 + GAD-7 1..7 (0-3) |
| Features | 29 (16 crudas + 13 derivadas de reglas publicadas, `app/services/svm_features.py`) |
| Etiqueta | juicio ciego de `SAMI-PSI-01`, binarizado en `riesgo_clinico >= MEDIO` |
| Entrenamiento | 102 casos del piloto del colegio (55 en alerta / 47 fuera) |
| Validación | LOOCV anidado: **F1-macro 0.9313 · κ 0.8630 · AUC 0.9443 · sens 0.891 · espec 0.979 · VPP 0.980** |
| Modelo final | `kernel=linear`, `C=3`, `k=6` — sobreviven `phq_total`, `gad_total`, `total`, `gad_n_ge2`, `crisis`, `phq_cognitiva` |

Supera a las reglas del `EvaluatorService` (F1-macro 0.8529 · κ 0.7081):
Δ F1 +0.0797, IC95 [+0.0199, +0.1381], gana en 99.6 % de 5 000 remuestreos
pareados. De los 10 casos donde discrepan, el SVM acierta 9 — 8 son estudiantes
con PHQ-A 9-15 sin ideación que las reglas dejaban pasar.

**No es caja negra**: el modelo final es lineal sobre 6 cantidades con
significado clínico, auditable a mano. Ecuación explícita en
`paper-datos-medidos-v1.md` (verificada: reproduce `decision_function` a 4e-6).

El conjunto de features **no está inflado**: repitiendo el LOOCV con la
elección de representación anidada dentro de cada fold da exactamente lo mismo
(0.9313), y elige las 29+SelectKBest en 90 de 102 vueltas. Lo que sí queda por
declarar: las candidatas y la rejilla se definieron explorando estos 102 casos.

Reentrenar: `venv/bin/python scripts/train_svm_clinico.py --casos data/clinico/casos_etiquetados.csv`
(exportar el CSV antes con `scripts/exportar_casos_etiquetados.py`; `data/` no se
versiona porque son respuestas de menores). Detalle: `reports/svm_clinico.md`.

**Advertencia de uso**: va como segunda opinión, no reemplaza al
`EvaluatorService`. Las reglas tienen 0 falsos negativos en CRÍTICO y son
auditables ítem por ítem; además el SVM es binario y no modela los 5 niveles.

### SVM de ENDES (superado, 2026-10-13)

`models/svm_phq9.joblib` — entrenaba contra `phq9_total >= 10`, que es la suma
de sus propias features, así que equivale matemáticamente a la regla
"PHQ-A total >= 10" (métricas idénticas a 4 decimales; permutar los 9 ítems no
mueve nada, sd 0.0000 sobre 200 permutaciones). Validación externa contra los
102 casos: F1-macro 0.784 · κ 0.571 · AUC 0.863 — por debajo de las reglas.
Sirve como contraejemplo de circularidad, no como modelo. Antes de él estuvo el
de DASS-21, que pedía 21 ítems que el sistema nunca recolectó y por eso jamás
emitió una predicción (artefactos en `.deprecated/`).

### Concordancia clínica medida (2026-10-13/15)

La psicóloga evaluadora (`SAMI-PSI-01`) etiquetó a ciegas 102 de los 104 casos
de la cohorte. Primer patrón de oro externo del proyecto.

- Reglas vs criterio clínico, **binario** (MEDIO+): F1-macro 0.853 · κ 0.708 ·
  sens 0.782 · espec 0.936 · VPP 0.935. **Falsos negativos en CRÍTICO: 0 de 6.**
- Reglas vs criterio clínico, **5 niveles**: κ simple 0.121, pero κ ponderado
  lineal 0.447 y cuadrático 0.665. O sea: el sistema **ordena** igual que la
  psicóloga y lo que está mal son los cortes. Nunca emite ALTO (la columna está
  vacía: los 21 ALTO de la psicóloga caen en CRÍTICO 20 / MEDIO 1).
- **Acortar el instrumento cuesta caro.** PHQ-2+GAD-2 (4 ítems): F1-macro 0.784,
  y pierde 8 de los 30 casos con ideación. Hay 6 estudiantes bajo el corte de
  ambas escalas cortas que marcaron el ítem 9, y la psicóloga derivó a los 6.
  Añadir solo el ítem 9 a los 4 ítems recupera 30/30.

Falta: `etiqueta_frase` sigue en 0 (sin eso no hay validación de BETO contra
criterio clínico) y `SAMI-PSI-02` no etiquetó nada (sin κ inter-evaluador — es
la limitación más fuerte del trabajo).

**Pendiente de verificar**: `modelo_crisis` es True en 39 casos pero solo 31
tienen PHQ-A #9 >= 1. Los otros 8 vienen de otra vía de la capa 2 —
probablemente BETO con ideación >= 0.40 sobre las frases. Si se confirma, es el
primer dato de impacto real de BETO en decisiones del sistema.

## Dataset de validación BETO (incorporado)

El sistema usa **BETO zero-shot** — no requiere dataset para funcionar. Pero
para validar académicamente el clasificador (defensa de tesis), está incluido
el script `scripts/eval_beto_emoevent.py` que descarga **EmoEvent** (Plaza-del-Arco
et al., 2020) directamente desde GitHub público (Apache-2.0), corre BETO sobre
los 1,656 tweets etiquetados del split test en español, y produce un reporte
en `reports/beto_emoevent.md` con F1-macro, accuracy, matriz de confusión y
clasificación por clase.

```bash
# Evaluación completa (~10 min con CPU + descarga del modelo la 1ra vez)
venv/bin/python scripts/eval_beto_emoevent.py

# Prueba rápida con 100 ejemplos
venv/bin/python scripts/eval_beto_emoevent.py --limite 100
```

Mapeo EmoEvent → Sami:
`anger→ira`, `fear→miedo`, `sadness→tristeza`, `joy→esperanza`, `others→neutral`.
`disgust` y `surprise` se descartan (no son categorías de Sami).
