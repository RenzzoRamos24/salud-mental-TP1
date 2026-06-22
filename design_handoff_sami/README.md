# Handoff: Sami — Diario Inteligente

## Overview
Sami es una aplicación web de diario inteligente para estudiantes universitarios. La interfaz permite registrar entradas diarias en texto libre, organizar por etiquetas, revisar el historial por ciclos de 14 días, y completar encuestas clínicas de cierre (PHQ-A + GAD-7) al terminar cada ciclo.

Diseño de referencia: Day One (Mac) para el layout de 3 paneles + Stoic para la paleta calmada.

---

## Sobre los archivos de diseño
Los archivos en este bundle son **prototipos de referencia en HTML/JSX/CSS** — muestran el look, los textos, el comportamiento y la navegación deseados, pero **no son código de producción para copiar directamente**.

La tarea es **recrear estas pantallas en el entorno del codebase real** (React + framework existente) usando sus patrones y librerías establecidas. Si no existe un entorno aún, React + Vite es la elección natural para este producto.

## Fidelidad
**Alta fidelidad (hifi).** Colores exactos, tipografía, espaciados e interacciones funcionando. El desarrollador debe recrear la UI pixel-perfect usando las librerías del codebase, tomando los tokens de este documento como fuente de verdad.

---

## Pantallas / Vistas

### 1. Inicio
**Propósito:** Primera pantalla del día. Muestra la pregunta del día o la entrada de hoy, entradas recientes y el estado del ciclo activo.

**3 variantes** (el usuario puede elegir la preferida desde Ajustes o Tweaks):
- **Hoy** (default): grid de 2 columnas — tarjeta principal izquierda (pregunta del día + CTA "Escribir la entrada de hoy" ó preview de la entrada existente + "Seguir escribiendo") + lista de entradas recientes derecha + strip del ciclo.
- **Tarjetas:** hub de 4 cards navegables (Diario, Mi historial, Recursos, Perfil) en grid 2×2.
- **Calma:** vista centrada de pantalla completa, solo la pregunta del día en grande, un botón y el strip del ciclo. Sin columnas.

**Layout Hoy:**
```
topbar (52px)
──────────────────────────────────────────────
padding: 36px 40px
max-width: 980px centrado

grid: 1.4fr 1fr, gap: 14px
  izquierda:
    card principal (padding 24px):
      label 12.5px ink-3 / título 18px 700 / body 13.5px ink-2 / btn primary
    card ciclo (padding 16px 24px):
      strip ciclo
  derecha:
    card entradas recientes:
      cabecera 13.5px bold + link "Ver todas" accent
      lista entry-row sin bordes externos
```

---

### 2. Diario (pantalla principal)
**Propósito:** Escribir y releer entradas. Es la pantalla más usada.

**Layout: 3 paneles fijos, sin scroll de página**
```
topbar (52px)
──────────────────────────────────────────────
grid: 216px | 312px | 1fr   altura: calc(100vh - 52px)

Panel 1 — Sidebar (bg: #f0f0f2, border-right)
  grupos: "Hoy", "Todas las entradas" + contadores
  etiquetas con punto de color + contador
  padding: 14px 10px

Panel 2 — Lista de entradas (bg: white, border-right, overflow-y: auto)
  sticky header: "Diario" + botón + (28×28, border-radius 7px, bg accent)
  agrupadas por mes (label mes 13px bold)
  entry-row: datebox (34px) + meta (título 2 líneas + excerpt 2 líneas + etiqueta)
  fila seleccionada: bg accent, todo el texto blanco

Panel 3 — Editor (bg: white, overflow-y: auto)
  sticky header: fecha larga + badge "Hoy"
  banner de encuesta de cierre (si el ciclo terminó)
  body: max-width 760px, margin auto, padding 30px 36px
    input título: 23px 700, border 0, placeholder ink-3
    textarea body: 15px, line-height 1.65, border 0, resize none
  encuesta de ciclo diario (solo en entrada de hoy, si el ciclo NO terminó)
  footer sticky: tagpicker + contador de palabras "guardado"
```

**Guardado:** en tiempo real sobre `localStorage` (clave `sami-diary-v1`). Cada keystroke llama a `saveEntry(entry)`.

**Nueva entrada:** botón `+` del panel 2. Si ya existe entrada de hoy, la selecciona; si no, crea `{ id: "u-" + Date.now(), date: hoy, title: "", body: "", tag: null }` y la guarda.

---

### 3. Encuesta de ciclo diario (dentro del editor)
**Propósito:** 3 preguntas de escala (ánimo, sueño, carga) en la entrada de hoy. Solo aparece si el ciclo NO ha terminado aún.

**Layout:** tarjeta `cycle-card` incrustada entre el body del editor y el footer.
- Fondo: `var(--bg)`, border, border-radius 10px, padding 18px 20px
- Título + hint
- 3 preguntas de escala con 5 opciones cada una (botones flex 1, se colorean en accent al elegir)
- Botón "Enviar" (deshabilitado hasta responder las 3)
- Al enviar: toast "Encuesta del día enviada" + la tarjeta cambia a estado completado

**Persistencia:** `localStorage` clave `sami-cycle-v1`, objeto `{ "2026-06-12": { animo: 0, sueno: 1, carga: 2 } }`.

---

### 4. Encuesta de cierre de ciclo (pantalla completa)
**Propósito:** Al completar los 14 días de un ciclo, el usuario responde 9 ítems PHQ-A + 7 ítems GAD-7.

**Acceso:** banner en el editor del Diario + enlace en Mi historial + enlace en Inicio.

**Layout:**
```
fondo: var(--panel) / overflow-y: auto
columna centrada: max-width 620px, padding 44px 28px 60px

header: "Cierre del ciclo 3" (izq) + "1/16" (der), font-size 12.5px ink-3
barra de 16 segmentos: height 4px, gap 4px, border-radius 2px
  - respondido: accent
  - actual: accent 45%
  - pendiente: var(--line)

módulo: "PHQ-A · pregunta 1" (turquesa, uppercase 11.5px)
pregunta: 21px 600, line-height 1.45
subtítulo: "Pensando en los últimos 14 días", 13px ink-3

4 opciones Likert (columna, gap 8px):
  cada opción: flex row, gap 14px, border 1px line, border-radius 10px, padding 12px 16px
  número (0-3): 26×26px box, bg var(--bg), border-radius 7px, 13px 600
  label: 14px 600 / descripción: 12.5px ink-3
  seleccionado: border accent + box-shadow 0 0 0 1px accent + bg accent 7% + número bg accent blanco

nav: Atrás (izq) + Saltar/Terminar (der)
auto-avance: 260ms tras elegir (excepto la última)

pantalla "Enviando…": botón deshabilitado, spinner textual
error: tarjeta roja "No pudimos guardar tu respuesta. Intenta de nuevo."
pie: "Tus respuestas son confidenciales. Solo las ve tu psicóloga." 12px ink-3
```

**Resumen final:**
```
"Gracias por responder." / párrafo
grid 2 cols: tarjeta PHQ-A + tarjeta GAD-7
  cada tarjeta: nombre uppercase / puntaje grande (30px 700) / badge nivel / texto acción
badge niveles:
  Mínima/Leve → bg var(--bg), color ink-2
  Moderada     → bg #fbf1e6, color #b96a1f
  Severa       → bg #fdf3f3, color #d12c2c

Crisis (si respuesta 9 del PHQ-A ≥ 1):
  tarjeta roja: "Pide ayuda ahora." / texto + "Línea 113, opción 5"
  
botón "Volver al diario"
```

**Severidades PHQ-A:** 0-4 Mínima · 5-9 Leve · 10-14 Moderada · 15-19 Moderada-severa · 20-27 Severa
**Severidades GAD-7:** 0-4 Mínima · 5-9 Leve · 10-14 Moderada · 15-21 Severa

**Persistencia:** `localStorage` clave `sami-close-v1`: `{ status: "done", answers: [0,1,2,...], ts: 1234567890 }`

---

### 5. Mi historial
**Propósito:** Ver en qué días se escribió, ciclo por ciclo, con el detalle de entradas al costado.

**Layout:**
```
page (overflow-y: auto) / max-width: 880px

h1 + subtítulo

grid: 1.2fr 1fr, gap 28px

izquierda — card:
  select "Período": opciones = ciclos (ej. "Ciclo 3 · 30 de mayo – 12 de junio de 2026")
  CalPeriodo: solo las semanas del ciclo elegido
    cabecera 7 columnas: dom lun mar mié jue vie sáb (10px bold uppercase ink-3)
    celdas cuadradas (aspect-ratio 1.2, border-radius 8px):
      - día con entrada: bg accent, color blanco, cursor pointer, hover brightness 92%
      - día del ciclo sin entrada: bg accent 11%
      - fuera del ciclo: color var(--line) (atenuado)
      - hoy: box-shadow inset 0 0 0 1.5px accent
  leyenda: 2 swatches con descripción

derecha — card:
  header: nombre del ciclo + rango + resumen + link encuesta de cierre
  subheader: "ENTRADAS DE ESTE PERÍODO" 11.5px uppercase ink-3
  lista entry-row clicable (abre la entrada en el Diario)
```

---

### 6. Recursos
**Propósito:** Líneas de ayuda y lecturas cortas.

**Layout:**
```
page / max-width: 820px

"Si necesitás ayuda ahora" → grid 3 cols:
  cada card: icono teléfono (accent) / nombre 14px bold / descripción / número de teléfono 19px bold / horario

"Para leer con calma" → card rowlist:
  cada fila: icono doc (ink-3) | título 13.5px bold + descripción 12.5px ink-2 | tiempo de lectura (der)
```

---

### 7. Perfil
**Propósito:** Datos personales, recordatorio, contraseña, borrar cuenta.

**Layout:** columna, max-width 560px, 3 cards:
1. Datos (nombre editable, email disabled, select recordatorio diario) + btn "Guardar cambios"
2. Cambio de contraseña (3 inputs password) + btn "Cambiar contraseña"
3. Borrar cuenta (texto advertencia + btn danger → confirma con 2 botones)

---

## Interacciones y comportamiento

| Acción | Comportamiento |
|--------|---------------|
| Clic en entry-row del historial | Navega a Diario con esa entrada seleccionada |
| Clic en `+` del Diario | Crea nueva entrada de hoy o selecciona la existente |
| Elegir opción Likert (encuesta cierre) | Auto-avanza 260ms (excepto última pregunta) |
| Guardar cambios (perfil) | Toast "Cambios guardados" por 2.4s |
| Completar encuesta diaria | Toast + tarjeta pasa a estado "completado" |
| Cambio de combo en historial | Calendario y lista de entradas se actualizan |

**Toast:** fixed bottom-center, bg ink, color white, padding 9px 16px, border-radius 9px, fade-in 200ms, desaparece a los 2400ms.

---

## Estado y persistencia

```
localStorage["sami-diary-v1"]  = { [entryId]: { id, date, title, body, tag } }
localStorage["sami-cycle-v1"]  = { ["YYYY-MM-DD"]: { animo, sueno, carga } }
localStorage["sami-close-v1"]  = { status: "pending"|"done", answers: number[], ts: number }
```

**Modelo de entrada:**
```ts
interface Entry {
  id: string;          // "e01" | "u-" + timestamp
  date: string;        // "YYYY-MM-DD"
  title: string;
  body: string;
  tag: "universidad" | "animo" | "sueno" | "gratitud" | null;
}
```

---

## Design tokens

```css
--accent: #0d9488;        /* turquesa */
--bg: #f5f5f6;
--panel: #ffffff;
--sidebar: #f0f0f2;
--line: #e4e4e8;
--line-soft: #ececef;
--ink: #1d1d1f;
--ink-2: #56565c;
--ink-3: #8e8e95;
--radius: 10px;
--font: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, "Helvetica Neue", sans-serif;
```

**Colores de etiquetas:**
```
universidad: #5b8def
animo:       #e8883a
sueno:       #8e6fd8
gratitud:    #3aa66f
```

**Topbar:** height 52px, bg panel, border-bottom 1px line
**Nav activo:** bg accent 11%, color accent, font-weight 600
**Botón primary:** bg accent, color white, border-radius 8px, padding 7px 14px, font-size 13.5px 600
**Botón default:** bg panel, border 1px line, color ink
**Botón danger:** color #d12c2c, border #f0d2d2

---

## Archivos de diseño
```
Sami - Diario.html   — prototipo principal (entry point)
sami.css             — todos los tokens y estilos
sami-data.js         — datos de ejemplo (usuario, entradas, ciclos, encuestas)
sami-shared.jsx      — Topbar, iconos, helpers de fecha, hooks de localStorage
sami-home.jsx        — Pantalla Inicio (3 variantes)
sami-diario.jsx      — Diario 3 paneles + encuesta diaria
sami-encuesta.jsx    — Encuesta de cierre PHQ-A + GAD-7
sami-historial.jsx   — Mi historial (calendario + combo)
sami-pages.jsx       — Recursos + Perfil
sami-app.jsx         — Router + Tweaks + montaje de React
tweaks-panel.jsx     — Panel de tweaks (solo para el prototipo, no producción)
```

---

## Assets
- Sin imágenes externas. Iconos: SVG inline trazados a mano (stroke, 18px, strokeWidth 1.7).
- Avatar de usuario: iniciales sobre fondo `var(--ink)` en un círculo de 26px.
- Logo Sami: letra "S" blanca sobre cuadrado accent (26×26px, border-radius 7px).

---

## Notas para el desarrollador
1. **No hay backend en este prototipo** — todo corre en localStorage. La implementación real necesita auth, API REST/GraphQL y base de datos para entradas, ciclos y encuestas.
2. El prototipo asume que **la fecha de hoy es 2026-06-12** (constante en `sami-data.js`). En producción usar `new Date()`.
3. Los **textos de las preguntas** de PHQ-A y GAD-7 están adaptados al habla informal latinoamericana — no son la escala clínica literal. Confirmar con el equipo clínico antes de publicar.
4. El bloque de **crisis** (pregunta 9 PHQ-A ≥ 1) debe activar también una notificación al psicólogo en el sistema real, no solo mostrar el bloque rojo.
5. El diario guarda en **tiempo real** (onChange), no hay botón "Guardar" — mantener ese patrón en producción.
