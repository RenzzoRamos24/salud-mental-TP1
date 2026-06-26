# Handoff: Panel del Alumno — Sami

> ⚠️ **REGLA NÚMERO UNO — NO TOCAR EL DISEÑO.**
> El diseño visual ya está **terminado y aprobado**. Tu trabajo es implementar **SOLO el backend y los datos reales** (información dinámica, APIs, estado, persistencia, navegación real). El **layout, colores, tipografía, espaciados, iconos, sombras y márgenes deben quedar EXACTAMENTE IGUAL** al archivo de diseño. No "mejores", no "modernices", no "ajustes" nada visual. Si algo se ve raro al integrarlo, replica el HTML/CSS tal cual antes de cambiar nada.

> ⚠️ **REGLA NÚMERO DOS — EL ROL "TUTOR" NO EXISTE.**
> No introduzcas en ningún lado el concepto de "tutor" / "tutoría" / "clase" / "curso". Este panel es **solo de apoyo psicológico**: el alumno usa el cuestionario, las reuniones con el psicólogo y el SOS. El apoyo personal se llama **"Hablar con psicólogo"**.

> ⚠️ **REGLA NÚMERO TRES — EL CUESTIONARIO ES EXTERNO.**
> El cuestionario **NO se implementa aquí**. Ya existe una **plantilla aparte** para el cuestionario. En este panel, "Cuestionario" es solo un **acceso con un botón** ("Comenzar cuestionario") que **enlaza a esa plantilla externa**. Conecta el `href` de esos botones a la ruta/URL real del cuestionario. No construyas el formulario de preguntas dentro de este panel.

---

## Overview
Panel de inicio para un **alumno**, marca **Sami**. App de una sola página con navegación interna por vistas (sin recarga). Vistas:
- **Inicio** — KPIs + acceso al cuestionario + recursos + SOS + próximas reuniones + gráfica de ánimo.
- **Cuestionario** — pantalla de acceso (botón) al cuestionario externo + historial de envíos + nota de confidencialidad.
- **Reuniones** — agenda completa de reuniones con el psicólogo.
- **Recursos de apoyo** — biblioteca de materiales (filtros + destacado + grilla).
- **Mi bienestar** — registro de ánimo del día + gráfica semanal + resumen + consejo.
- **Mi Perfil** — datos del alumno + preferencias + psicólogo asignado + cuenta.

## About the Design Files
`Panel del Alumno.dc.html` es una **referencia de diseño en HTML** (prototipo de aspecto y comportamiento), **no** código de producción para copiar directo al stack. Recréalo dentro del entorno existente del proyecto (React, Vue, Angular, etc.) con sus patrones y librerías; si no hay entorno aún, elige el framework más apropiado.

El marcado y los estilos en línea son la **fuente de verdad visual definitiva**: cópialos literalmente (estructura, valores de estilo, SVGs). Lo único que cambias es de dónde salen los **datos** (hoy mockeados → backend) y conectar la **navegación real** (rutas).

## Fidelity
**Alta fidelidad (hifi).** Mockup pixel-perfect con colores, tipografía, espaciados e interacciones finales.

---

## Navegación entre vistas
- El panel es una SPA: el **sidebar** cambia la vista activa (`Inicio`, `Cuestionario`, `Reuniones`, `Recursos de apoyo`, `Mi bienestar`, `Mi Perfil`). En el prototipo es estado interno (`view`); en producción usa el **router** del stack (una ruta por vista). El ítem activo se resalta (fondo `#e3f3ef`, texto teal, chip de icono con gradiente) y el **breadcrumb** refleja la vista.
- Varios enlaces internos también navegan: "Ver agenda" / "Agenda" → Reuniones; "Historial" → Cuestionario; "Mi bienestar" → Mi bienestar; "Ver todos" (recursos) → Recursos; "Agendar reunión" (perfil) → Reuniones.

---

## Qué es DISEÑO (no tocar) vs qué es DATO (implementar)

**DISEÑO — fijo, copiar verbatim:** toda la estructura de layout (sidebar 264px, topbar 64px, grids), todos los estilos en línea, todos los iconos SVG, las gráficas/barras, y los textos de etiqueta fijos (nombres de menú, títulos de sección, textos de botones, nota de confidencialidad, etc.).

**DATO — dinámico, viene del backend:**

| Vista | Elemento | Mock | Fuente backend sugerida |
|---|---|---|---|
| Global | Usuario (sidebar/topbar/perfil) | `Lucas Ferreira` · `Alumno · 3.º Año` · avatar | `GET /api/me` |
| Inicio | KPI Estado de ánimo | `Bien` (↑ mejor) | `GET /api/me/wellbeing/summary` |
| Inicio | KPI Cuestionarios enviados | `5` (+2 este mes) | `GET /api/me/questionnaires/summary` |
| Inicio | KPI Próxima reunión | `Hoy 16:00 · Psic. Méndez` | `GET /api/meetings/next` |
| Inicio | Gráfica de ánimo (7 barras) | niveles 1–5 por día | `GET /api/me/wellbeing?range=week` |
| Cuestionario | **Botón "Comenzar cuestionario"** | `href="#"` | **enlazar a la plantilla externa del cuestionario** |
| Cuestionario | Historial de envíos | 3 ítems (fecha, ánimo, estado) | `GET /api/me/questionnaires` |
| Reuniones | Reunión destacada (en vivo) | fecha/hora/modalidad/enlace/objetivo | `GET /api/meetings/next` |
| Reuniones | Próximas + anteriores | 2 próximas, 1 pasada | `GET /api/meetings?status=upcoming\|past` |
| Reuniones | Horarios para agendar | 4 slots | `GET /api/psychologist/slots` · `POST /api/meetings` |
| Recursos | Filtros + destacado + grilla | 6 materiales | `GET /api/resources` |
| Mi bienestar | Selector de ánimo del día | 5 niveles | `POST /api/me/wellbeing` |
| Mi bienestar | Gráfica semanal + resumen | promedio, racha, envíos | `GET /api/me/wellbeing?range=week` |
| Mi Perfil | Información personal | nombre, año, correo, teléfono, doc, contacto emergencia | `GET /api/me` |
| Mi Perfil | Preferencias (3 switches) | recordatorios, correo, modo privado | `GET/PUT /api/me/preferences` |
| Mi Perfil | Psicólogo asignado | `Psic. Carla Méndez` | `GET /api/me/psychologist` |
| SOS | Llamar / chat psicólogo / apoyo emocional | links fijos | `GET /api/support/sos` |

> Etiquetas e iconos = diseño; números, nombres, fechas, títulos y duraciones = dato.

---

## Vistas en detalle

### Sidebar (común)
Logo **Sami** (icono burbuja-chat teal) · perfil del alumno · nav (Inicio, Cuestionario, Reuniones, Recursos de apoyo, SOS · Ayuda, Mi bienestar, Mi Perfil) · tarjeta **Hablar con psicólogo** (gradiente teal, icono corazón) abajo, que lleva a Reuniones.

### Topbar (común)
Buscador "Buscar en Sami…" + iconos (notificaciones, mensajes) + avatar. **No hay bot/chat flotante** (se eliminó intencionalmente — no lo reintroduzcas).

### Inicio
Grid `minmax(0,1fr) 372px`. Izquierda: 3 KPIs, **acceso al cuestionario** (tarjeta horizontal con botón), recursos (grid 2×2). Derecha: SOS (rojo) + Reuniones con el psicólogo (destacada + lista). Abajo full-width: gráfica "Tu estado de ánimo".

### Cuestionario
**Solo acceso**: bloque de bienvenida + tarjeta centrada con botón **"Comenzar cuestionario"** (→ plantilla externa). Lateral: **historial** de cuestionarios enviados (fecha · ánimo · `Revisado`) + tarjeta "100% confidencial". **No construir el formulario aquí.**

### Reuniones
Tabs (Próximas/Pasadas) + botón "Agendar reunión". **Destacada**: cabecera con psicólogo, grid de detalles (Fecha, Hora, Modalidad, Enlace), objetivo de la sesión y acciones (Unirse a la videollamada, Reagendar, Añadir al calendario, Cancelar). **Reunión 2** (Online, seguimiento semanal) y **Reunión 3** (Presencial, con ubicación y "Cómo llegar"), cada una con acciones. **Anteriores**: "Primera sesión" marcada `Realizada` con "Ver resumen". Lateral: ficha del **psicólogo** (Enviar mensaje / Ver perfil) + **Agendar nueva reunión** con slots.

### Recursos de apoyo
Chips de filtro (Todos, Estrés, Sueño, Ansiedad, Mindfulness) · recurso **destacado** (ejercicio guiado) · grilla 3 columnas de tarjetas (PDF, Video, Artículo, Actividad, Audio, Guía) con duración y enlace por tipo de color.

### Mi bienestar
Selector de ánimo del día (5 caras, "Bien" preseleccionado con outline teal) · gráfica "Tu ánimo esta semana" · lateral: resumen (ánimo promedio, racha, cuestionarios enviados) + tarjeta "Consejo del día" (gradiente teal).

### Mi Perfil
Cabecera (avatar + nombre + "Editar perfil") · **Información personal** (grid 2 col de campos) · **Preferencias** (3 toggles: recordatorios ON, correo ON, modo privado OFF) · lateral: **Tu psicólogo** (→ Agendar) + **Cuenta** (Cambiar contraseña, Cerrar sesión).

---

## State Management
- `view` (vista activa) → en producción, **router**.
- `me { name, role, id, email, phone, document, emergencyContact, avatarUrl }`
- `preferences { meetingReminders, emailNotifications, privateMode }`
- `psychologist { name, area, avatarUrl, available }`
- `wellbeing { todayMood, weekLevels[], average, streak }`
- `questionnaires { sentCount, history[] }` (+ link a la plantilla externa)
- `meetings { next, upcoming[], past[], slots[] }`
- `resources []`
- `sos { phone, chatUrl, emotionalSupportUrl }`

## Design Tokens
**Colores:** primario teal `#0e8d7e`; acento `#1aa896`; teal suave `#e3f3ef`; gradientes `#22b8a6→#0e8d7e` y `#1aa896→#0c8475`. SOS rojo `#ff6b6b→#e0413c` (sólido `#e0524c`). Tipos de recurso: azul `#3a78b3`/`#eaf0fb`, ámbar `#d98a1f`/`#fef3e2`, morado `#7a5cc4`/`#efeafa`, rojo `#e0524c`/`#fdecec`. Texto `#243239`/`#33424a`/`#5a6a70`, muted `#8b999e`,`#9aa7ab`. Bordes `#eef1f2`,`#e7ecec`. Fondo `#f5f7f8`; header `#e9f4f1→#f5f7f8`. Verde estado `#1fbf75`, amarillo `#f5b301`.

**Tipografía:** `Figtree` (Google Fonts) 400/500/600/700/800. Números KPI 30–34/800, títulos de sección 18/700, body 14, muted 12–13.

**Radios:** tarjetas 18 · celdas/tarjetas internas 12–16 · pills 7/20 · chips de icono 9–14 · botones 10–12.
**Sombras:** tarjeta `0 6px 20px rgba(35,80,95,.05)` · SOS `0 12px 26px rgba(224,65,60,.32)` · sidebar card `0 8px 18px rgba(15,130,115,.3)` · botón teal `0 6px 14px rgba(15,130,115,.3)`.

## Assets
- **Fuente:** Figtree vía Google Fonts.
- **Iconos:** SVG inline (sin librería) — copiar del HTML o sustituir por el set del proyecto manteniendo grosor/tamaño.
- **Gráficas/barras:** generadas en código (ver la clase logic del `.dc.html`).
- **Avatares (alumno, psicólogos):** placeholders de `i.pravatar.cc` → reemplazar por imágenes reales.

## Files
- `Panel del Alumno.dc.html` — diseño completo de las 6 vistas (marcado + estilos en línea + lógica de navegación y gráficas). **Referencia visual a recrear pixel-perfect.** Contenido numérico/textual = mock a sustituir por backend. **No reintroducir "tutor", el bot flotante, ni el formulario del cuestionario (es externo).**
