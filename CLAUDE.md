# Salud Mental UPC — guía rápida para Claude

Proyecto de tesis: chatbot de bienestar emocional para estudiantes. Está activo, en desarrollo iterativo. Esta guía es para que Claude (vos) sepa moverse rápido sin tener que rastrear todo de cero.

## Stack

| Capa | Tecnología | Path |
|------|------------|------|
| Backend | FastAPI + SQLAlchemy + SQLite | `app/` |
| NLP | `Recognai/bert-base-spanish-wwm-cased-xnli` (BETO + XNLI zero-shot multi-label) | `app/services/nlp_service.py` |
| Frontend | Vue 3 + Vite + Tailwind + Chart.js | `project/` |
| Auth | JWT (estudiante / psicologo / admin) | `app/api/v1/endpoints/auth.py` |

## Levantar el stack

Hay venv ya configurado en la raíz.

```bash
# Backend  (puerto 8000)
venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (puerto 5173 por defecto; durante esta sesión se usó 5179)
cd project && npm run dev
```

Logs típicos durante el desarrollo: `/tmp/uvicorn.log`, `/tmp/vite.log`.

Docs FastAPI: http://127.0.0.1:8000/docs

## Estructura

```
app/
  api/v1/endpoints/   auth, consent, chatbot, users, admin, psychologist,
                       content, sos, survey
  models/             User, UserSession, UserResponse, RiskResult, Cita,
                       ClinicalNote, AccessLog, EducationalContent,
                       SatisfactionSurvey, SosEvent, Configuracion
  schemas/            Pydantic in/out
  services/           auth, chat, nlp, admin, psychologist, content, cita,
                       notes, scheduler, sos, survey, ai_provider
  middleware/         access_log
  database.py         engine + Base + SessionLocal
  config.py           env / settings
  main.py             app, CORS, startup, NLP warmup, scheduler
project/
  src/
    components/       AppTopbar, AuthShell, PageHeader, ResultsScreen,
                      RiskBadge, SOSButton, StatCard
    views/            Login, Register, Forgot/Reset password, Consent,
                      MainMenu, Chat, Results, Profile, MiHistorial,
                      Recursos, SatisfactionSurvey, StudentHistory,
                      PsychologistDashboard, AdminDashboard,
                      AdminChatbotMessages, AdminContent, AdminLogs,
                      AdminReports, AdminSystem
    store/auth.js     reactive store de sesión
    api.js            cliente axios
    router/index.js   rutas con guard por rol y consentimiento
    style.css         design system "Pastel Empático"
  tailwind.config.js  paleta brand / peach / mint / sky2 / risk / cream / ink
SPRINTS.md            registro detallado de sprints 1–8
```

## Design system "Pastel Empático"

Implementado en `project/src/style.css` + `project/tailwind.config.js`. Aplicado en mayo 2026 tomando como referencia los mocks `Menu.png`, `CHATIA.png` y `LOGIN.png` (en `/home/renzo/`).

**Paleta Tailwind:** `brand-*` (lavanda), `peach-*`, `mint-*`, `sky2-*`, `risk-{bajo,medio,alto,critico,sin}`, `cream-{50,100,200}`, `ink-{100..900}`. Body usa `#FBF1E6` (peach pálido).

**Tipografía:**
- `Plus Jakarta Sans` — default (sans)
- `Fraunces` — serif para titulares (clase `.hero-serif`)

**Utilidades clave** (`@layer components`):
- `.hero-serif` + `.hero-mint` — titular serif con segmento mint
- `.menu-card` + `.menu-card-arrow` + `.icon-box-{mint,sky,brand,peach,amber}` — tarjetas del menú
- `.bubble-bot` (cream) / `.bubble-user` (mint sólido) / `.bubble-info` (peach)
- `.dass-tag` (chip mint con punto) / `.opinion-tag` (chip peach)
- `.sami-wordmark` (logo serif) / `.sos-fab` (pill coral flotante)
- `.btn-{primary,secondary,ghost,peach,mint,danger}` / `.btn-sm`
- `.input` / `.input-lg` / `.label` / `.field-hint` / `.field-error`
- `.dsm5-tag` (chip lavanda con punto)
- `.risk-{bajo,medio,alto,critico,sin}`
- `.chip-{brand,peach,mint,ink}`
- `.avatar-{sm,md,lg}`
- `.banner-{info,warn,danger,success,brand}`
- `.card` / `.card-hero` / `.card-pastel` / `.card-peach` / `.card-mint`
- `.page-shell` / `.page-shell-wide`
- `.nav-item` / `.nav-item-active`

**Componentes Vue reutilizables:**
- `AppTopbar` — wordmark Sami + pill usuario + "Cerrar sesión"
- `AuthShell` — fondo degradado peach→mint, card blanca, logo planta peach
- `PageHeader` — título serif con prop `accent` (segmento mint) + icon-box opcional
- `StatCard`, `RiskBadge`, `SOSButton`, `ResultsScreen`

## Convenciones visuales

- En el **flujo estudiante** los CTA principales usan `btn-mint` (no `btn-primary` lavanda).
- Hero/títulos de página usan `.hero-serif`, opcionalmente con `accent` para resaltar un segmento en mint.
- Cards principales son blancas con border `cream-200` y radius 2xl/3xl; no usar shadow agresivo.
- Para vistas nuevas: componer con clases del DS, no introducir azules genéricos `slate-*` ni botones planos.

## Mocks de referencia

Imágenes que el usuario fue compartiendo para alinear el frontend:

| Archivo | Pantalla |
|---------|----------|
| `/home/renzo/Menu.png` | Menú principal (estudiante) |
| `/home/renzo/CHATIA.png` | Chat con Sami (capture larga 1874×12434) |
| `/home/renzo/LOGIN.png` | Login |

Cuando el usuario mande nuevos mocks suele dejarlos en `/home/renzo/` con un nombre descriptivo.

## Estado del trabajo

### Implementación funcional (HUs)
- **37 de 40 HUs completas.**
- Pendientes documentadas en `PENDIENTES.md` (raíz): HU-32 (filtro por riesgo), HU-34 (PDF programático), HU-37 (WebSocket de logs).

### Rediseño visual (estado actual)
Identidad final: **verde agua (emerald) + blanco + negro**, sin pastel ni emojis.
- Paleta única `green-*` (`#10B981` principal, `#34D399` claro, `#ECFDF5` fondos). Aliases `brand`/`mint` apuntan al mismo verde; `peach`/`sky2`/`cream` neutralizados a grises fríos (#F4F5F6).
- Fondo body blanco puro (#FFFFFF), texto `#0A0A0A`.
- Tipografía: **Work Sans** (humanista, sobria). No serif.
- Sombras suaves (`shadow-soft`, `shadow-card`, `shadow-green`) en cards, botones, topbar. Hover de cards eleva con `-translate-y-0.5`.
- Banners y cards de éxito/info: blancas con barra lateral verde (`border-l-4 border-l-green-600`).
- Sin emojis decorativos. Todas las vistas barridas y formateadas con Prettier.
- Recursos diferenciado por rol: estudiante ve líneas de ayuda + consejos; psicólogo/admin ven escalas (PHQ-9, GAD-7, ASRS, UCLA-3, C-SSRS), protocolos por nivel de riesgo y líneas de derivación.
- Copies en tono conversacional, no spec-sheet ("Cuéntale a Sami cómo te has sentido", "Si lo necesitas ahora", "Borrar tu cuenta").

## SPRINTS.md

`SPRINTS.md` (en la raíz) lleva el registro funcional de cada sprint con HUs, endpoints y vistas. Consultalo cuando aparezca una funcionalidad que ya está definida ahí.
