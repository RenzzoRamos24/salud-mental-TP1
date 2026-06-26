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

## SVM — parqueado

El SVM está **en pausa intencional**. El sistema funciona sin él: el
`EvaluatorService` calcula el riesgo compuesto por reglas con cortes
publicados (Johnson, Spitzer, Harding…), lo cual es la base académica
defendible. El SVM se incorporará como segunda opinión cuando se retome.

Detalles del trabajo congelado, dataset elegido (DASS-42 real con 39,775
respuestas, 7,269 adolescentes 13–17 años) y checklist técnico para
retomar: ver `SVM_PARKED.md`.

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
