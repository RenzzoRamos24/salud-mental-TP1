# Handoff: Sami — Panel Clínico (Psicólogo)

## Overview
Lado clínico de Sami, la app de diario para estudiantes. Permite a la psicóloga de bienestar estudiantil hacer **triaje** de sus estudiantes según los resultados de las encuestas de cierre de ciclo (PHQ-A + GAD-7), revisar la **evolución** de cada uno y llevar una **ficha clínica** con notas.

Es la contraparte del lado estudiante (ver handoff `design_handoff_sami`). Comparten el mismo sistema visual (tokens en `sami.css`).

---

## Sobre los archivos de diseño
Los archivos de este bundle son **prototipos de referencia en HTML/JSX/CSS** — definen look, textos, datos y comportamiento, pero **no son código de producción**. La tarea es **recrear estas pantallas en el codebase real** (React + el framework existente) usando sus patrones y librerías. Si no hay entorno aún, React + Vite es la elección natural.

## Fidelidad
**Alta fidelidad (hifi).** Colores, tipografía, espaciados, gráficos e interacciones funcionando. Tomar los tokens de este documento como fuente de verdad.

---

## Modelo de datos (clínico)

```ts
interface Cycle {
  n: number;            // número de ciclo
  start: string;        // "YYYY-MM-DD"
  end: string;
  phqa: number;         // 0–27
  gad7: number;         // 0–21
  crisis: boolean;      // ítem 9 del PHQ-A ≥ 1
  dias: number;         // días escritos de 14
  encurso?: boolean;
}
interface Student {
  id: string;
  name: string; initials: string;
  carrera: string; anio: string; email: string;
  ultimaActividad: string;        // "YYYY-MM-DD"
  entradasCompartidas: boolean;   // ¿compartió su diario con la psicóloga?
  cycles: Cycle[];
  notas: { fecha: string; autor: string; texto: string }[];
}
```

### Tablas de severidad (idénticas al lado estudiante)
```
PHQ-A: 0-4 Mínima · 5-9 Leve · 10-14 Moderada · 15-19 Moderada-severa · 20-27 Severa
GAD-7: 0-4 Mínima · 5-9 Leve · 10-14 Moderada · 15-21 Severa
```

### Lógica derivada (no almacenada — se calcula)
- **Riesgo del estudiante** = el peor de su nivel PHQ-A / GAD-7 del último ciclo; si `crisis` → "Crisis" (máxima prioridad).
- **Tendencia** = diferencia de PHQ-A entre los dos últimos ciclos: `≥ +3` empeora (↑ rojo), `≤ -3` mejora (↓ verde), si no Estable (→ gris).
- **Alertas** se generan así, ordenadas por `rank` desc:
  - `crisis` (rank 100): último ciclo con `crisis: true`
  - `crit` (rank 80): nivel severa / moderada-severa
  - `warn` (rank 50): nivel moderada
  - `idle` (rank 30): sin actividad ≥ 14 días

---

## Pantallas / Vistas

### 1. Panel (dashboard de triaje)
**Propósito:** Lo primero que ve la psicóloga. Resumen + qué requiere atención hoy.

**Layout** (`max-width: 920px`, padding 36px 40px):
```
saludo: "Sábado 13 de junio de 2026" (sub) + "Hola, Lucía" (h1) + subtítulo

tiles: grid 4 columnas, gap 14px
  cada tile: card, número 27px 700 + label 12.5px ink-3
  tile de alertas con valor > 0: variante "alarm" → border #f2cfcb, bg #fdf6f5, número #c0392b
  [ Estudiantes a tu cargo | Alertas que requieren atención | Ciclos cerrados esta semana | Ciclos en curso ]

card "Requieren tu atención" (+ link "Ver todas las alertas"):
  hasta 4 alert-rows
  alert-row: badge-ico (34×34, redondeado) + texto (título 13.5px 600 / subtítulo 12.5px ink-2) + cuándo + chevron
    crit → ícono triángulo, bg #fbecec color #c0392b
    warn → ícono triángulo, bg #fbf3e7 color #b07a25
    idle → ícono luna, bg var(--bg) color ink-3

card "Todos tus estudiantes" (+ link "Ver lista completa"):
  StudentTable con los primeros 4
```

### 2. Estudiantes (lista)
**Propósito:** Lista completa con buscador, ordenada por riesgo.

```
h1 + subtítulo
input de búsqueda (filtra por nombre o carrera), max-width 320px
card con StudentTable completa
```

**StudentTable** — grid de columnas `34px 1.6fr 1fr 1fr 130px 16px`:
```
cabecera (list-head): "" | Estudiante | PHQ-A | GAD-7 | Estado | ""
  uppercase 11px bold ink-3, border-bottom

cada fila (stu-row, clicable → abre ficha):
  avatar 34px (color derivado del id) con iniciales
  nombre 13.5px 600 (block) + "carrera · año" 12px ink-3 (block)
  PHQ-A: número 15px 700 + " /27" 11px ink-3
  GAD-7: número 15px 700 + " /21"
  Estado: chip de severidad (o crisis-flag rojo) + tendencia (↑/↓/→ con texto)
  chevron
  hover: bg var(--bg)
```

**Chip de severidad** (`.sev`): pastilla con punto + texto. Colores por nivel:
```
mínima:   bg #eef4ef  texto #4a7a5c
leve:     bg #eef3fb  texto #3f6fb0
moderada: bg #fbf3e7  texto #b07a25
mod-sev:  bg #fbeee6  texto #b5601f
severa:   bg #fbecec  texto #c0392b
```
**crisis-flag**: ícono + "Crisis", bg #fbecec, border #f2cfcb, color #c0392b, 11.5px 700.

### 3. Alertas
**Propósito:** Cola priorizada de todas las alertas (mismo `alert-row` que el panel, sin truncar). Subtítulo: "N críticas · M en total". `max-width: 720px`.

### 4. Ficha clínica (pantalla principal)
**Propósito:** Vista 360° de un estudiante. Es el corazón del lado clínico.

```
back-link "‹ Volver"

ficha-head (flex, border-bottom):
  avatar 56px + [ nombre h1 23px / "carrera · año · email" 13px ink-3 / chip severidad o crisis-flag + "Última actividad hace X" ]
  actions (margin-left auto): btn "Contactar" + btn primary "Agendar sesión"

[si crisis] crisis-banner: bg #fbecec, border #f2cfcb
  ícono + "Protocolo de crisis activado" (#b5322a) + texto guía (derivar a Línea 113 opción 5)

ficha-grid: grid 1fr 300px, gap 24px, align-items start

  COLUMNA PRINCIPAL:
    panel-card "Evolución por ciclos":
      grid 2 columnas → un gráfico PHQ-A y un gráfico GAD-7
      cada uno: título + "último: X/max" + EvolChart (SVG)

    panel-card "Ciclos completados":
      cyc-item por ciclo (orden desc):
        cyc-row clicable: "Ciclo N" + rango + "X de 14 días" + scores (PHQ-A, GAD-7) + crisis-flag + chevron que rota
        al expandir: chips de severidad + CycleDetail (desglose por ítem)

  COLUMNA LATERAL:
    panel-card "Notas clínicas":
      textarea (nota-input) + btn "Guardar nota"
      lista de notas (fecha · autor · "(tú)" si propia) orden desc
    panel-card "Diario del estudiante":
      privacy-note (caja gris con candado):
        si entradasCompartidas → "X eligió compartir sus entradas contigo…" + btn "Ver entradas compartidas"
        si no → "El contenido del diario es privado. Solo ves los resultados de las encuestas…"
```

**EvolChart (SVG, gráfico de líneas con bandas de severidad):**
- viewBox 460×150, padding L28 R12 T12 B22.
- Fondo: bandas horizontales por rango de severidad (rect con opacity 0.5). Colores suaves:
  ```
  severa  #f6dfdc · mod-sev #f6e6d6 · moderada #f7eed9 · leve #e7eef8 · mínima #e9f1ea
  ```
- Eje Y: líneas en 0 y máx, etiquetas 9.5px ink-3.
- Línea de datos: stroke `var(--accent)` 2.2px, con puntos (círculo blanco borde accent) y, sobre cada punto, el valor (10.5px 700) y debajo la etiqueta "C{n}".

**CycleDetail (desglose por ítem):** dos bloques (PHQ-A 9 ítems / GAD-7 7 ítems). Cada `item-line`: nombre del ítem + barra de progreso (0–3 → 0–100%, fill accent) + valor. (En el prototipo el desglose se genera para sumar el total; en producción vienen las respuestas reales por ítem.)

Etiquetas de ítems usadas:
```
PHQ-A: Interés/placer, Ánimo decaído, Sueño, Energía, Apetito, Autoimagen,
       Concentración, Movimiento/habla, Pensamientos de daño
GAD-7: Nervios, No parar de preocuparse, Preocupación excesiva,
       Dificultad para relajarse, Inquietud, Irritabilidad, Miedo a algo malo
```

---

## Interacciones y comportamiento

| Acción | Comportamiento |
|--------|---------------|
| Clic en fila de estudiante / alerta | Abre la Ficha clínica de ese estudiante |
| Buscar en Estudiantes | Filtra por nombre o carrera en vivo |
| Clic en un ciclo (ficha) | Despliega/colapsa el desglose por ítem |
| Escribir nota + "Guardar nota" | Agrega a la lista (orden desc) + toast "Nota guardada en la ficha" |
| "Contactar" / "Agendar sesión" | Toast (placeholder — conectar a email/agenda real) |
| Nav "Alertas" | Badge rojo con el número de alertas críticas |

**Topbar clínico:** wordmark "Sami · Clínico", nav [Panel · Estudiantes · Alertas (badge)], userchip con la psicóloga. Mismo estilo que el topbar del estudiante (52px, etc.).

**Toast:** fixed bottom-center, bg ink, color white, fade-in 200ms, 2400ms.

---

## Estado y persistencia
```
localStorage["sami-psico-notas-v1"] = { [studentId]: [{ fecha, autor, texto, propia: true }] }
```
Las notas nuevas se guardan localmente y se fusionan con `student.notas` (las precargadas). Todo lo demás (estudiantes, ciclos) es de solo lectura en el prototipo.

**Constante de fecha:** el prototipo asume hoy = `2026-06-13` (en `sami-psico-data.js`). En producción usar `new Date()`.

---

## Design tokens
Idénticos al lado estudiante (`sami.css`):
```css
--accent: #0d9488;  --bg: #f5f5f6;  --panel: #ffffff;
--sidebar: #f0f0f2; --line: #e4e4e8; --line-soft: #ececef;
--ink: #1d1d1f;     --ink-2: #56565c; --ink-3: #8e8e95;
--radius: 10px;
--font: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, "Helvetica Neue", sans-serif;
```
Colores clínicos adicionales (severidad/alertas) están listados arriba en cada componente y centralizados en `sami-psico.css`.

Avatares de estudiante: color derivado del id, de la paleta `["#0d9488","#5b8def","#e8883a","#8e6fd8","#3aa66f","#d3792c"]`.

---

## Archivos de diseño
```
Sami — Clínico.html      — prototipo principal (entry point)
sami.css                 — tokens y estilos base (compartido con el estudiante)
sami-psico.css           — estilos clínicos (severidad, tiles, tabla, ficha, gráfico)
sami-psico-data.js       — datos de ejemplo (psicóloga, 6 estudiantes, ciclos)
sami-psico-shared.jsx    — severidad, tendencia, topbar, EvolChart, helpers de fecha, iconos
sami-psico-panel.jsx     — Panel, StudentTable, Estudiantes, Alertas, buildAlerts
sami-psico-ficha.jsx     — Ficha clínica (evolución, ciclos, desglose, notas)
sami-psico-app.jsx       — router + montaje
```

---

## Assets
- Sin imágenes. Iconos: SVG inline (stroke, 1.7–1.8px). Gráficos: SVG dibujado en `EvolChart`.
- Avatares: iniciales sobre color sólido.

---

## Notas para el desarrollador
1. **Sin backend en el prototipo.** La implementación real necesita: auth de psicólogos, API para estudiantes/ciclos/respuestas, y almacenamiento seguro de notas clínicas (datos sensibles de salud — aplicar el estándar de privacidad que corresponda).
2. **Privacidad del diario:** respetar el límite — la psicóloga ve resultados de encuestas, NO el texto del diario, salvo consentimiento explícito (`entradasCompartidas`). Este es un requisito de diseño, no un detalle visual.
3. **Crisis (ítem 9 del PHQ-A ≥ 1):** además del banner, debe disparar notificación/protocolo real al equipo clínico, no solo UI.
4. El **desglose por ítem** en la ficha está simulado en el prototipo (genera valores que suman el total). En producción mostrar las respuestas reales ítem por ítem que ya se capturan en la encuesta de cierre del estudiante.
5. Los **textos PHQ-A/GAD-7** abreviados son etiquetas de UI, no la escala clínica literal — confirmar redacción con el equipo clínico.
