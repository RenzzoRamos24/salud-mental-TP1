# Handoff: SENTIR · Panel clínico (salud mental juvenil)

## Overview
SENTIR es una plataforma de salud mental juvenil. Este handoff cubre la **vista del profesional clínico** (rol "Clínico", p. ej. la psicóloga Carla) para revisar el seguimiento de un estudiante. El estudiante escribe un diario; cada ciclo de 14 días se le aplican encuestas clínicas (PHQ-A para depresión, GAD-7 para ansiedad) y un modelo de lenguaje (RoBERTa) estima condiciones a partir de los textos. El clínico ve la evolución, las condiciones detectadas, la adherencia y el detalle por ciclo.

Son **3 pantallas** conectadas:
1. **Panel clínico** — dashboard de tarjetas (resumen accionable del estudiante).
2. **Reporte de bienestar** — reporte visual oscuro (snapshot del estado actual + tendencia).
3. **Reporte completo** — desglose por ciclo a todo el ancho (gráficos por ciclo + detalle DSM-5 + extractos del diario).

`Reporte de bienestar` enlaza a `Reporte completo` mediante el botón "Ver reporte completo".

## About the Design Files
Los archivos `.html` de este bundle son **referencias de diseño creadas en HTML/CSS/JS plano** — prototipos que muestran el aspecto y el comportamiento deseados, **no** código de producción para copiar tal cual. La tarea es **recrear estos diseños en el entorno del codebase destino** (lo más probable React) usando sus patrones y librerías existentes (componentes, sistema de tokens, librería de gráficos, router). Si todavía no existe un entorno, elegir el framework más apropiado (sugerencia: **React + TypeScript + Vite**, con una librería de charts como Recharts/visx o SVG a medida) e implementarlos ahí.

Los gráficos (barras, líneas, medidor, radar) están dibujados a mano con SVG en los prototipos para tener control exacto del look; en el codebase pueden rehacerse con una librería de charts respetando los mismos colores, marcadores y etiquetas.

## Fidelity
**Alta fidelidad (hifi).** Colores, tipografía, espaciado y estados son finales. Recrear la UI fielmente con las librerías del codebase. Los datos son de demostración (estudiante "María Alejandra Torres Huanca") y deben venir de la API real.

---

## Design Tokens

### Color
| Token | Hex | Uso |
|---|---|---|
| `--green` | `#0D9488` | Primario de marca. Botones, acentos, barras, serie PHQ-A, estados activos. |
| `--green-deep` | `#0E3B38` | Texto de títulos (Gabarito), fondo del hero oscuro, isotipo. |
| `--green-mid` | `#3FA89C` | Verde intermedio (iconos sutiles). |
| `--mint` / `--bright` | `#5FC7BC` / `#34E0C9` | Acentos sobre el hero oscuro (líneas, radar, gauge). |
| `--green-tint` | `#E6F3F1` | Fondo de píldoras/badges verdes, nav activo. |
| `--green-line` | `#CFE6E2` | Bordes suaves sobre verde. |
| `--amber` | `#E8913C` | Secundario / serie GAD-7 / severidad "moderada". Texto oscuro: `#B26A1E`. |
| `--amber-tint` | `#FBEBD7` | Fondo de badges ámbar/severidad. |
| `--good` | `#2BB673` | Severidad "mínima", adherencia alta, ratio normal. |
| `--mild` | `#E8B04B` | Severidad "leve", ánimo "regular". |
| `--warn` | `#E8913C` | Severidad "moderada". |
| `--bad` | `#E25555` | Severidad "severa", riesgo, adherencia baja. |
| `--gray-bar` | `#9FB0AD` | Ánimo "bajo" (neutro en barras apiladas). |
| `--violet` | `#6D5BD0` (bg `#EEEBFB`) | Badge "RoBERTa · orientativo". |
| `--bg` | `#F1F5F4` | Fondo de página (claro). |
| `--surface` | `#FFFFFF` | Tarjetas. |
| `--ink` | `#143230` | Texto principal. |
| `--muted` | `#6E8C88` | Texto secundario. |
| `--faint` | `#9DB2AE` | Etiquetas, ejes de gráficos. |
| `--line` / `--line-soft` | `#E4EBE9` / `#EEF3F2` | Bordes y separadores. |

**Escala de severidad (PHQ-A y GAD-7):** 0–4 mínima (verde `#2BB673`) · 5–9 leve (amarillo `#E8B04B`) · 10–14 moderada (naranja `#E8913C`) · 15+ severa (rojo `#E25555`).

### Hero oscuro (Reporte de bienestar)
Fondo: superposición de gradientes
```
radial-gradient(120% 90% at 78% 8%, rgba(52,224,201,.16), transparent 55%),
radial-gradient(90% 80% at 12% 100%, rgba(13,148,136,.30), transparent 60%),
linear-gradient(155deg,#15564F 0%,#0E3B38 46%,#0A2826 100%)
```
Borde interior: `inset 0 0 0 1px rgba(255,255,255,.06)`. Texto blanco con opacidades `.55–.7` para secundarios.

### Tipografía
- **Gabarito** (Google Fonts), pesos 600/700/800 → títulos, marca "SENTIR", números grandes, botones.
- **Hanken Grotesk** (Google Fonts), pesos 400/500/600/700 → cuerpo, etiquetas, tablas, datos.
- Números: `font-variant-numeric: tabular-nums` (clase `.num`).
- Escala aprox.: H1 estudiante 25px/700 Gabarito; títulos de tarjeta (h2) 16.5px/600 Gabarito; números grandes de score 40px/800 Gabarito; cuerpo 13.5–14px Hanken; etiquetas 11px/700 mayúsculas `letter-spacing:.06–.12em`.

### Radio, sombra, espaciado
- Radios: tarjetas **18px**; hero **26px**; botones **11–12px**; inputs/segment **8–10px**; píldoras/chips **999px**.
- Sombra de tarjeta: `0 1px 2px rgba(20,50,48,.04), 0 8px 28px -16px rgba(20,50,48,.18)`.
- Sombra del hero: `0 24px 60px -28px rgba(14,59,56,.55)`.
- Padding de tarjeta: ~22px 24px. Gap de grids: 16–20px.
- Topbar: alto 62px, padding lateral `clamp(20px,4vw,48px)`.

---

## Screens / Views

### 1) Panel clínico (`SENTIR · Panel clínico.html`)
**Propósito:** resumen accionable del estudiante en una grilla de 4 tarjetas.
**Layout:** topbar sticky (full width) + contenido centrado `max-width:1180px`. Grilla `grid-template-columns: 1.55fr 1fr; gap:20px`, 2×2. Colapsa a 1 columna < 920px.

- **Topbar:** burger (3 líneas), isotipo SVG + "SENTIR" (Gabarito 800, 20px, `--green-deep`) + divisor + "Clínico" (`--muted`). Nav: "Panel" (activo, fondo `--green-tint`), "Estudiantes", "Alertas" con badge ámbar "1". Derecha: avatar redondo verde "CM" + "Carla M." + chevron.
- **Crumb:** "‹ Volver a estudiantes" (`--muted`, 13.5px/600).
- **Title row:** avatar 58px verde "MT"; H1 "María Alejandra Torres Huanca"; meta: píldora severidad ("● Moderada-severa", texto `#B26A1E`, fondo `--amber-tint`) + email + "· Última actividad hoy". Derecha: botón "Contactar" (ghost: fondo blanco, `inset 0 0 0 1px --line`) + "Agendar sesión" (solid verde).
- **Tarjeta 1 · Actividad del diario:** título + subtítulo; herramientas: input de fecha falso ("jun 2026") + segment control "Diario | Por ciclo" (activo = fondo verde, texto blanco). **Bar chart** SVG: modo Diario = min escritos/día (10 barras verdes, eje 0–20); modo Por ciclo = días escritos por ciclo (3 barras: C1 verde 14, C2 ámbar 5, C3 rojo 3, eje 0–14). Barras radius 6, valor encima, gridlines `#EEF3F2`, ejes `--faint`.
- **Tarjeta 2 · Encuestas aplicadas:** badge "PHQ-A · GAD-7". Tabla: Fecha · Ciclo · Test (píldora `phq` verde / `gad` ámbar) · Puntaje (derecha) · Acción (iconos ver/descargar). Filas: 21 may C1 17/27 y 11/21; 4 jun C2 4/27 y 4/21; 18 jun C3 3/27 y 2/21.
- **Tarjeta 3 · Evolución clínica:** leyenda (● PHQ-A verde, ● GAD-7 ámbar). **Line chart** SVG dos series con área translúcida, puntos con badge de valor (rect redondeado del color de la serie): PHQ-A [17,4,3], GAD-7 [11,4,2] en C1–C3, eje 0–20.
- **Tarjeta 4 · Condiciones detectadas:** badge violeta "RoBERTa · orientativo". Filas con barra de confianza (track `--bg`, fill verde; "Riesgo suicida" fill rojo): Depresión 65, Estrés académico 64, Ansiedad 56, Soledad 43, TDAH 21, Riesgo suicida 5. Pie: icono alerta + descargo "Indicadores orientativos…".

### 2) Reporte de bienestar (`SENTIR · Reporte de bienestar.html`)
**Propósito:** snapshot visual del estado actual + tendencia (no por ciclo). Diseño "reporte" oscuro. `max-width:1010px`.
**Hero (oscuro, radio 26px):**
- Top: marca "SENTIR" (isotipo claro + wordmark). Banda tipo "edad biológica" con 3 segmentos: "PHQ-A actual 3 /27 · leve", "GAD-7 actual 2 /21 · leve", "▼ Bajó 14 puntos · mejora clínica sostenida" (texto `--bright`). Derecha: toggle decorativo + icono campana + avatar "MT".
- Subtítulo: "‹ Reporte de bienestar" (Gabarito 700, 19px) + píldora "Moderada-severa" (ámbar). Descripción en blanco `.6`.
- **Grilla `178px 1fr 226px`** (colapsa <720px):
  - **Radar** (izq, SVG 6 ejes: Ánimo, Sueño, Energía, Concentración, Social, Apetito; valores 0–100; polígono `--bright` translúcido; anillos a 25/50/75/100).
  - **Medidor** (centro, SVG): gauge de 270° (gap abajo), valor 62 ("Percentil de carga · Riesgo relativo"), aguja blanca, arco con gradiente `#34E0C9→#0D9488`. Alrededor, en **abanico superior**, 6 **callouts** posicionados con JS (concéntricos al gauge, radio `min(156, anchoWrap/2-44)`, ángulos 146/123/100/80/57/34): Depresión 65%, Estrés académico 64%, Ansiedad 56%, Soledad 43%, TDAH 21%, Riesgo suicida 5% (icono + % + nombre). **Recalcular en `resize`.** Importante: deben quedar holgados respecto al número central.
  - **Columna derecha:** mini-card "Constancia del diario 64% · Media"; mini-card con line chart "Tendencia del puntaje · baja = mejora" ([17,11,4,4,3,2]); botón blanco "Ver reporte completo →" → navega a `SENTIR · Reporte completo.html`.
- **3 tarjetas claras debajo** (grid 1fr×3, colapsa <720px):
  - **Índice de riesgo clínico:** "0.42 · leve", píldora "Moderado", **escala de gradiente** horizontal (verde→rojo) con marcador a 40%, etiquetas Bajo/Medio/Alto. Lista "Señales detectadas en el diario" (2 columnas con chevrons). Link "Ver reporte →" → `Reporte completo`.
  - **Señales del diario:** "60-80% Tono emocional positivo" + filas con rango y "?" (Menciones de estrés 20-40%, Lenguaje de aislamiento 5-15%, Auto-referencia negativa 2-10%, Lenguaje de riesgo 0-3%) + dos ratios (Ratio positivo/negativo "Subóptimo" 1.4 ámbar; Coherencia narrativa "Normal" 3.7 verde).
  - **Estrés académico:** "64 · percentil 75", **escala de gradiente** con marcador a 75%, ticks 0–100, insight con `<b>` resaltado, "Cambio en el tiempo +2.5 ▲14.2%", lista de implicaciones con viñetas ámbar.

### 3) Reporte completo (`SENTIR · Reporte completo.html`)
**Propósito:** desglose por ciclo. **Full width** (`width:100%; max-width:1760px; padding:24px clamp(20px,4vw,48px) 80px`).
- Misma topbar + title row que el Panel. Crumb "‹ Volver al reporte de bienestar" → `Reporte de bienestar`. Selector de año falso "2026 · 3 ciclos con datos".
- **Fila A (2 col):** tarjetas "Depresión · PHQ-A" (badge "Leve", "3/27", **line chart de severidad**) y "Ansiedad · GAD-7" ("2/21"). El line chart: línea gris con área tenue, **línea punteada** en el máximo (27/21), marcadores **círculos abiertos coloreados por severidad** (C1 rojo/naranja, C2–C3 verdes), valor encima del color de severidad, leyenda "Verde = mínima · Amarillo = leve · Naranja = moderada · Rojo = severa". PHQ [17,4,3], GAD [11,4,2].
- **Fila B (2 col):** "Condiciones detectadas" (igual que Panel) y "Adherencia y ánimo": barras de días por ciclo (C1 14/14 verde, C2 5/14 ámbar, C3 3/14 rojo) + "Estado de ánimo auto-reportado" con leyenda 4 colores (Bien/Regular/Bajo/Muy bajo) y **barras apiladas** por ciclo.
- **Detalle por ciclo (full-width, acordeón):** filas Ciclo 3 (abierto por defecto, "· en curso"), Ciclo 2, Ciclo 1. Cada cabecera: nombre + rango de fechas + scores PHQ-A/GAD-7 + chevron (rota 180° al abrir). Cuerpo expandido:
  - **Banner** (tinte verde, o ámbar en C1): píldoras de severidad ("● Mínima"), título de estado, descargo DSM-5.
  - **Bloques "PHQ-A · Depresión" y "GAD-7 · Ansiedad":** cabecera con score "/27"·"/21" y filas de síntomas (nombre + frecuencia en itálica gris arriba + "x/3" en ámbar). Ítems del ciclo 3 (todos 1/3 "Algunos días"): anhedonia, ánimo deprimido, fatiga; ansiedad excesiva, preocupación múltiple. (C2 y C1 tienen su propio desglose, generado como ejemplo plausible.)
  - **"Lo que escribió · base de la detección":** extractos del diario por fecha (label fecha mayúsculas + blockquote itálico con borde izquierdo verde). **Estos mensajes deben verse sí o sí.** Ciclo 3: entradas 18/19/20 jun (textos exactos en el HTML).
- **Fila final (2 col):** "Notas clínicas" (textarea + botón "Guardar nota" + "Todavía no hay notas…") y "Diario del estudiante" (aviso de privacidad con candado: "El contenido del diario es privado…").

---

## Interactions & Behavior
- **Navegación:** botón/links "Ver reporte completo" → `Reporte completo`; crumb → vuelve atrás. En el codebase, usar el router (rutas: `/estudiante/:id/panel`, `/estudiante/:id/bienestar`, `/estudiante/:id/completo`).
- **Segment "Diario | Por ciclo"** (Panel, tarjeta 1): cambia el dataset del bar chart. Estado local activo.
- **Acordeón de ciclos** (Reporte completo): click en la cabecera togglea `.open`; chevron rota 180°. Ciclo 3 abierto por defecto. Animar `max-height`/opacity con la librería del codebase (en el prototipo es display none/block).
- **Callouts del medidor** (Reporte de bienestar): posicionados por JS de forma concéntrica al gauge; **recalcular en `resize`**. En React, calcular tras montar (ref + ResizeObserver) o reimplementar con posicionamiento por ángulos.
- **Hover:** iconos de acción en tablas pasan de `--faint` a `--green`; botones y filas con feedback sutil.
- **Responsive:** grids colapsan a 1 columna (Panel <920px; reportes <880/720px). Topbar y hero fluidos.

## State Management
- `student` (perfil + severidad + última actividad), `cycles[]` (rango fechas, días escritos, PHQ-A, GAD-7, ítems por síntoma, entradas de diario), `conditions[]` (nombre + confianza %), `mood[]` (distribución por ciclo), `adherence[]` (días/total por ciclo), `wellbeingDimensions[]` (radar), `riskIndex`, `academicStress`, `textSignals[]`.
- UI local: `activeBarMode` ('daily'|'weekly'), `openCycleId`, `clinicalNotes` (textarea + guardar).
- Datos vienen de la API; los del prototipo son mock. Severidad se deriva de los puntajes (ver escala arriba).

## Design Tokens
Ver sección **Design Tokens** arriba (colores, tipografía, radios, sombras, espaciado, gradientes del hero y de las escalas).

## Assets
- **Isotipo SENTIR** (perfil humano + onda): incluido como `SENTIR-isotipo.svg` (vectorial), `SENTIR-isotipo.png` y `SENTIR-logo-completo.png`. En los HTML va inline como SVG (2 colores: trazo `--green-deep` o claro sobre oscuro, y la onda en `--green`/`--bright`). Usar el SVG en el codebase.
- **Iconos:** line icons inline (1.6–2px stroke, `currentColor`): burger, chevron, campana, ojo (ver), descarga, candado, alerta, y los de condiciones (cerebro, libro, onda, persona, rayo, alerta). Reemplazar por la librería de iconos del codebase (p. ej. lucide-react) manteniendo el estilo lineal.
- **Fuentes:** Google Fonts Gabarito + Hanken Grotesk.
- **Charts:** dibujados con SVG a mano en los prototipos. Reimplementar con la librería de charts del codebase o SVG, conservando colores/marcadores/etiquetas.

## Files
Incluidos en este bundle:
- `SENTIR · Panel clínico.html` — dashboard de 4 tarjetas.
- `SENTIR · Reporte de bienestar.html` — reporte oscuro (snapshot).
- `SENTIR · Reporte completo.html` — desglose por ciclo (full width).
- `Guía de estilo.html` — guía de estilo base de la marca (referencia de color/tipografía; nota: define el verde de marca alterno `#3F5D4B`/coral; **estas pantallas usan el sistema teal `#0D9488` descrito arriba**, que es el vigente para el producto clínico).
- `SENTIR-isotipo.svg`, `SENTIR-isotipo.png`, `SENTIR-logo-completo.png` — logo.

> Nota: los datos del estudiante "María Alejandra Torres Huanca" son de demostración. Las pantallas deben poblarse desde la API real.
