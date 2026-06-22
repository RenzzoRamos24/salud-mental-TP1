# Handoff: Diario del estudiante — Sami (Salud Mental Juvenil)

## Resumen
Pantalla principal de un **diario de journaling** para estudiantes de secundaria (12–17 años),
dentro de una app de seguimiento de salud mental llamada **Sami**. El estudiante escribe una
entrada diaria, ve su progreso dentro de un “ciclo de seguimiento” de 14 días, elige cómo se
sintió (selector de ánimo) y guarda. Cada 14 días, al cerrar el ciclo, se le aplica una encuesta
clínica (PHQ-A + GAD-7) — esa pantalla NO está incluida en este handoff, pero el sistema visual
es el mismo.

**Prioridad del proyecto (crítica):** el diseño NO debe verse “hecho por IA”. Debe sentirse
diseñado por una persona — calmado, simple, intencional. Las reglas exactas que logran esto están
en la sección **Principios anti-IA** más abajo; respétalas al implementar.

## Sobre los archivos de diseño
Los archivos de este paquete son **referencias de diseño hechas en HTML/React** (prototipos que
muestran el aspecto y el comportamiento buscado), **no código de producción para copiar tal cual.**
La tarea es **recrear estos diseños en el entorno del codebase destino** (React web, React Native,
Vue, SwiftUI, Flutter, etc.) usando sus patrones y librerías ya establecidos. Si todavía no existe
un entorno, elige el framework más apropiado (para una app móvil de estudiantes, React + Vite o
React Native son buenas opciones) e implementa ahí.

Archivos incluidos:
- `Diario del estudiante.html` — la pantalla principal, interactiva. Ábrela en un navegador para
  ver el comportamiento real (escribir, contar palabras, elegir ánimo, guardar).
- `designs/DiaryStudent.jsx` — el **componente React fuente** de esa pantalla. Es la referencia
  más fiel: todos los valores exactos de color, tipografía, tamaños y estados están aquí.
- `Sistema de diseño.html` — documentación visual completa (principios, color, tipografía,
  componentes, voz/microcopia).
- `Guía de estilo.html` — versión corta de color + tipografía + tokens.

## Fidelidad
**Alta fidelidad (hi-fi).** Colores, tipografía, espaciado e interacciones son finales. Recrea la
UI de forma pixel-perfect usando las librerías y patrones del codebase destino. Los valores exactos
están abajo y en `DiaryStudent.jsx`.

---

## Pantalla: Diario del estudiante (vista “Escribir”)

### Propósito
El estudiante escribe su entrada del día, registra su ánimo y guarda. Es la pantalla por defecto al
entrar a la app.

### Layout
- Contenedor de página de ancho completo, fondo verde claro `#EDF1E8`.
- **Barra superior** (full-width): logo a la izquierda, chip de usuario + “Cerrar sesión” a la derecha.
  Padding `20px 40px`.
- **Columna de contenido centrada**, ancho máximo **720px**, padding lateral `30px`. Todo el
  contenido principal vive en esta columna. (En el prototipo de escritorio la columna se centra con
  márgenes amplios a los lados; en móvil debe ocupar el ancho con padding `20–24px`.)
- Orden vertical dentro de la columna:
  1. Eyebrow (saludo) + título (fecha)
  2. Tarjeta de ciclo (blanca)
  3. Panel de sugerencia (menta)
  4. Área de escritura (tarjeta blanca, es el elemento “héroe”)
  5. Selector de ánimo (4 tarjetas en fila)
  6. Barra inferior: nota de privacidad + botón Guardar

### Componentes (valores exactos)

**Barra superior**
- Logo: “Sami” en Gabarito 700, 20px, color `#2F4A38`; al lado “Diario” en 13px, peso 500, color `#9AA694`.
- Chip de usuario: fondo blanco, radio 999px, padding `5px 15px 5px 6px`, sombra `0 1px 3px rgba(39,53,43,.07)`.
  Avatar: círculo 26px, fondo coral `#E08763`, inicial blanca “R” en 12px/700. Texto “Renzo” 13px/600
  `#3A4A3E` + “· estudiante” en `#9AA694`/500. Todo en una sola línea (`white-space:nowrap`).
- “Cerrar sesión”: 13px/500, color `#9AA694`, hover `#3A4A3E`.

**Eyebrow + título**
- Eyebrow: “Hola, Renzo” — Hanken Grotesk 700, 14px, color coral `#E08763`, margin-bottom 7px.
- Título (fecha): “Sábado 30 de mayo” — Gabarito 700, 37px, line-height 1.05, letter-spacing −0.6px,
  color `#243A2C`, margin-bottom 18px.

**Tarjeta de ciclo** (white card)
- Fondo `#FFFFFF`, radio 18px, sombra de tarjeta `0 1px 2px rgba(39,53,43,.04), 0 6px 20px -10px rgba(39,53,43,.16)`.
- Layout flex: bloque de texto (flex:1) a la izquierda + anillo de progreso a la derecha. Padding `22px 26px`, gap 22px.
- Etiqueta: “CICLO 1” — 11px/700, letter-spacing 0.09em, MAYÚSCULAS, color `#A6B19F`.
- Título: “Día 6 de 14” — Gabarito 600, 20px, color `#2A3A30`, margin `7px 0 14px`.
- **Fila de puntos** (tracker de 14 días): 14 círculos de 13px, gap 7px.
  - Completados (días 1–3): `#4C6B53`.
  - Día actual (día 6): `#E08763` (coral).
  - Restantes: `#E2E8DD`.
- Pie: “3 entradas · hasta el 7 de junio” — 12.5px, color `#9AA694`, margin-top 13px.
- **Anillo de progreso** (SVG, 84px): pista completa `#E4EBDE` stroke 7px; arco de progreso `#4C6B53`
  stroke 7px, linecap round, rotado −90°, fracción = 6/14. Centro: “6/14” en Gabarito 700, 17px,
  `#2F4A38`; debajo “días” en Hanken 600, 8px, `#8A9685`. **Sin degradado** (regla anti-IA).

**Panel de sugerencia** (menta, plano, sin sombra)
- Fondo `#E2EADC`, radio 16px, padding `18px 22px`, margin-top 16px.
- Etiqueta: “PARA EMPEZAR” — mismo estilo de etiqueta (11px/700, 0.09em, mayúsculas, `#A6B19F`).
- Pregunta: “¿Qué tienes en la cabeza hoy?” — Gabarito 600, 19px, color `#2A3A30`, margin-top 7px.

**Área de escritura** (tarjeta héroe)
- Fondo `#FFFFFF`, radio 18px, **sombra héroe** `0 1px 2px rgba(39,53,43,.04), 0 14px 34px -16px rgba(39,53,43,.22)`.
- Textarea: sin borde, fondo transparente, Hanken Grotesk 400, 16.5px, line-height 1.62, color `#27352B`,
  altura 158px, padding `22px 26px 0`. Placeholder “Empieza a escribir…” color `#AEB8A8`.
- Pie del área (sfoot): borde superior `1px solid #EEF2EA`, padding `13px 26px`. Muestra el contador
  de palabras a la izquierda: “{n} palabras”, 12.5px/600, color `#9AA694`. (El lado derecho quedó
  vacío a propósito — se eliminó el texto de autosave por ser “de IA”.)

**Selector de ánimo**
- Etiqueta: “¿CÓMO ESTUVO TU DÍA?” — 11px/700, 0.09em, mayúsculas, `#A6B19F`, margin `20px 0 12px`.
- Grid de 4 columnas iguales, gap 12px.
- Cada tarjeta: fondo blanco, radio 16px, borde `1.5px solid transparent`, padding `17px 8px`,
  sombra sutil `0 1px 3px rgba(39,53,43,.05)`. Contenido: ícono de línea (28px) + label.
  - Hover: `translateY(-2px)` + sombra `0 8px 18px -8px rgba(39,53,43,.2)`.
  - Seleccionado (`.on`): fondo verde `#3F5D4B`, texto e ícono blancos.
- Labels: “Buen día”, “Mezclado”, “Apagado”, “Difícil” — 13.5px/600, `white-space:nowrap`. Color base `#7E8B79`.
- Íconos (línea, stroke 1.6, NO emoji): sol (buen día), gota+círculo (mezclado), nube/óvalo (apagado),
  óvalo con líneas de lluvia (difícil). Ver SVGs exactos en `DiaryStudent.jsx`.

**Barra inferior (guardar)**
- Flex space-between, padding `6px 0 26px`.
- Izquierda: ícono candado de línea (14px) + “Solo tú puedes leerlo.” — 12.5px, color `#8C988A`.
- Botón Guardar: fondo verde `#3F5D4B`, texto blanco, Gabarito 600, 15px, radio 12px, padding `14px 30px`,
  sombra `0 6px 16px -8px rgba(63,93,75,.7)`, `white-space:nowrap`.
  - Deshabilitado (sin texto ni ánimo): fondo `#C9D2C3`, sin sombra, cursor not-allowed.
  - Hover (habilitado): fondo `#36503F`, `translateY(-1px)`.
  - Estado guardado (`.done`): fondo coral `#E08763`, sombra `0 6px 16px -8px rgba(224,135,99,.7)`,
    texto cambia a “Guardado”.

---

## Interacciones y comportamiento
- **Escribir en el textarea**: actualiza el contador “{n} palabras” en vivo (cuenta separando por
  espacios; vacío = 0). Al escribir, si estaba en estado “Guardado”, vuelve a estado normal.
- **Elegir ánimo**: clic en una tarjeta la marca como seleccionada (verde). Solo una a la vez.
  Al cambiar, sale del estado “Guardado”.
- **Botón Guardar**:
  - Habilitado solo si hay texto (≥1 palabra) **o** un ánimo elegido (`canSave = words > 0 || mood`).
  - Al hacer clic: estado `saved = true` → el botón pasa a coral y dice “Guardado”.
  - Cualquier edición posterior (texto o ánimo) revierte a “Guardar”.
- Transiciones: hover de botones/tarjetas ~0.13s ease. Nada de animaciones llamativas.
- **Responsive**: el prototipo es de escritorio (columna centrada 720px). En móvil, la columna ocupa
  el ancho con padding `20–24px`; el selector de ánimo puede pasar a 2×2 si 4 columnas quedan muy
  apretadas (< ~360px). La barra superior mantiene logo izquierda / usuario derecha.

## Gestión de estado
Estado local del componente (no requiere backend para la demo):
- `text: string` — contenido del textarea.
- `mood: 'bueno' | 'mezcla' | 'apagado' | 'dificil' | null` — ánimo elegido.
- `saved: boolean` — si la entrada fue guardada (controla el estilo/texto del botón).
- Derivados: `words` (conteo), `canSave`.

Para producción: al guardar, persistir `{ fecha, texto, mood }` por usuario y por día; el contador de
ciclo (día 6/14, nº de entradas) viene del backend. El tracker de días y el anillo se calculan desde
el progreso del ciclo del usuario.

## Design tokens

**Colores**
- Primario (verde bosque): `#3F5D4B` · variantes texto `#243A2C`, medio `#4C6B53`, hover `#36503F`
- Secundario (coral): `#E08763` · hover `#CC6347`
- Fondo: `#EDF1E8` · Superficie (blanco): `#FFFFFF` · Panel menta: `#E2EADC`
- Borde/hairline: `#DDE4D6` (también se usa `#E2E8DD` / `#EEF2EA` en bordes internos)
- Texto base: `#27352B` · Texto suave: `#8A9685` · Etiquetas: `#A6B19F` · Verde claro (acento punto): `#9EC09B`

**Tipografía**
- Familias: **Gabarito** (títulos, botones, marca — pesos 600/700) y **Hanken Grotesk** (cuerpo, UI,
  etiquetas — pesos 400/500/600/700). Importar de Google Fonts. NO usar Inter/Roboto/Arial.
- Escala: H1 37px/700 (−0.6 tracking) · H2 20px/600 · Eyebrow 15px/700 · Cuerpo 16.5px/400 ·
  Etiqueta 11px/700 (mayús, +0.12em) · Botón 15px/600.
- Números: usar `font-variant-numeric: tabular-nums` en datos (días, contador).

**Radios:** tarjetas 18px · paneles/ánimo 16px · botones 12px · píldoras 999px.
**Sombras (jerarquía):**
- sutil: `0 1px 3px rgba(39,53,43,.06)`
- tarjeta: `0 1px 2px rgba(39,53,43,.04), 0 6px 20px -10px rgba(39,53,43,.16)`
- héroe: `0 1px 2px rgba(39,53,43,.04), 0 14px 34px -16px rgba(39,53,43,.22)`
**Rejilla:** base 4px · columna máx 720px.

## Principios anti-IA (OBLIGATORIO respetar)
La razón de ser de este rediseño. Al implementar, NO introduzcas:
- ❌ Formas “blob” / manchas de color decorativas en las esquinas.
- ❌ Degradados de relleno (anillos, fondos, botones). Todo es color plano.
- ❌ Emojis como íconos o decoración. Usa íconos de línea (stroke ~1.5–1.6).
- ❌ Sombras blandas idénticas en todo. Respeta la jerarquía sutil → tarjeta → héroe.
- ❌ Fuentes por defecto (Inter/Roboto/Arial).
- ❌ Microcopia que sobre-explica, tranquiliza o felicita sin que se pida.
- ❌ Gamificación (rachas, insignias, puntos).

Sí buscar: color con estructura (verde manda, coral solo acentúa), texto mínimo y directo, tono de
persona (“Hola, Renzo”, no “Buenos días, estimado usuario”), espaciado generoso, detalles cuidados.

**Voz / microcopia** — escribe menos. Ejemplos del producto: “Hola, Renzo” · “Día 6 de 14” ·
“¿Qué tienes en la cabeza hoy?” · “Empieza a escribir…” · “Solo tú puedes leerlo.” · “Guardar”.

## Assets
- **Fuentes:** Gabarito y Hanken Grotesk (Google Fonts) — no requieren licencia especial.
- **Íconos:** todos son SVG inline de trazo, definidos en `DiaryStudent.jsx` (no hay librería de
  íconos externa). Puedes reemplazarlos por equivalentes de la librería del codebase (ej. Lucide)
  siempre que sean de línea y mantengan el mismo peso visual.
- **Imágenes:** ninguna. El avatar es una inicial sobre círculo de color.

## Archivos de referencia
- `Diario del estudiante.html` — pantalla interactiva (abrir en navegador).
- `designs/DiaryStudent.jsx` — componente React fuente, valores exactos.
- `Sistema de diseño.html` — sistema visual completo.
- `Guía de estilo.html` — resumen de color/tipografía/tokens.

### Nota sobre `DiaryStudent.jsx`
Es un componente React (vanilla, sin librerías) que se monta en `window.DiaryStudent`. Usa estilos
en un `<style>` embebido con clases prefijadas `.ds`. Tómalo como la fuente de verdad de valores,
pero reescríbelo según las convenciones del codebase destino (CSS Modules, Tailwind, styled-
components, StyleSheet de RN, etc.). El HTML lo escala/centra con un “stage” fijo de 1080×880 solo
para la demo — eso NO es parte del diseño; en producción usa layout responsivo normal.
