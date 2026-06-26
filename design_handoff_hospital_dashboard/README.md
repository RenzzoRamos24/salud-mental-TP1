# Handoff: Apollo — Hospital Dashboard

> ⚠️ **REGLA NÚMERO UNO — NO TOCAR EL DISEÑO.**
> El diseño visual de este dashboard ya está **terminado y aprobado**. Tu trabajo es implementar **SOLO el backend y los datos reales** (información dinámica, APIs, estado, persistencia). El **layout, colores, tipografía, espaciados, iconos, sombras y márgenes deben quedar EXACTAMENTE IGUAL** a lo que ves en el archivo de diseño. No "mejores", no "modernices", no "ajustes" nada visual. Si algo se ve raro al integrarlo, replica el HTML/CSS tal cual antes de cambiar nada.

---

## Overview
Dashboard administrativo de un hospital ("Apollo"). Es una sola pantalla con:
- Barra lateral de navegación + tarjeta de soporte.
- Barra superior con buscador e iconos de utilidad.
- 3 tarjetas de KPIs (Patients, Appointments, Revenue).
- Panel de anatomía (pulmones) con 3 medidores radiales.
- Cuadrícula de "Specialities".
- Gráfica de barras "Patients by Age".
- Widget de chat flotante ("Monster Bot").

## About the Design Files
El archivo `Hospital Dashboard.dc.html` es una **referencia de diseño hecha en HTML** (un prototipo que muestra el aspecto y comportamiento deseado), **no** código de producción para copiar tal cual al stack. La tarea es **recrear este diseño dentro del entorno existente del proyecto** (React, Vue, Angular, etc.) usando sus patrones y librerías; si no hay entorno todavía, elige el framework más apropiado.

Dicho esto — y esto es lo importante para este encargo — **el marcado y los estilos de este archivo son la fuente de verdad visual definitiva**. Cópialos literalmente (estructura de elementos, valores de estilo en línea, SVGs de iconos) a tus componentes. Lo único que cambias es de dónde salen los **datos**: hoy están hardcodeados, deben venir del backend.

## Fidelity
**Alta fidelidad (hifi).** Mockup pixel-perfect con colores, tipografía, espaciados e interacciones finales. Recrea la UI tal cual; aplica los datos reales por encima sin alterar la presentación.

---

## Qué es DISEÑO (no tocar) vs qué es DATO (implementar)

**DISEÑO — fijo, copiar verbatim:**
- Toda la estructura de layout (sidebar 264px, topbar 64px, grid de 2 columnas `minmax(0,1fr) 372px`, etc.).
- Todos los valores de estilo en línea (colores, radios, sombras, paddings, fuentes).
- Todos los iconos SVG.
- La ilustración de pulmones y los medidores radiales (son SVG generados — replícalos igual).
- Los textos de etiqueta fijos: "Patients", "Appointments", "Revenue", "View All", "this month", "Specialities", "Patients by Age", "Customer Support", "Hospital Admin", "Department Admin", nombres de menú, "Hi! What can I do for you?", etc.

**DATO — dinámico, viene del backend:**

| Elemento en pantalla | Valor actual (mock) | Fuente backend sugerida |
|---|---|---|
| KPI Patients | `980` | `GET /api/stats/patients` → total |
| KPI Patients % | `+40%` | mismo endpoint → variación vs mes anterior |
| KPI Appointments | `260` | `GET /api/stats/appointments` → total |
| KPI Appointments % | `+30%` | mismo endpoint → variación |
| KPI Revenue | `$6800` | `GET /api/stats/revenue` → total (formatear moneda) |
| KPI Revenue % | `+20%` | mismo endpoint → variación |
| Rango de fechas | `05/27/2026 - 06/25/2026` | selector que filtra todos los KPIs/gráfica |
| Usuario sidebar | `Ema Wilson` / `Department Admin` / avatar | `GET /api/me` |
| Soporte | `0987654321` | config / `GET /api/settings` |
| Specialities | Orthopedic 9, Kidney 5, Liver 6, Surgery 12, Laboratory 5 | `GET /api/specialities` → `[{name, count}]` |
| Medidores Left/Health/Right | 42% / 72% / 34% | `GET /api/patient/lung-metrics` (o el contexto que aplique) |
| Patients by Age (barras) | array de 22 alturas hardcodeadas | `GET /api/stats/patients-by-age` → `[{ageBucket, count}]` |
| Chat "Monster Bot" | mensaje estático | opcional: integrar bot/soporte real |
| Badges de notificación (topbar) | puntos de color fijos | opcional: contadores reales de notificaciones |

> Las etiquetas Specialities (texto + icono) son diseño; los **números** son dato. Las alturas de las barras son dato; los ejes/grid son diseño.

---

## Screens / Views

### Screen: Hospital Dashboard (única vista)
**Purpose:** Vista general de operación del hospital para un admin de departamento.

**Layout (exacto):**
- Raíz: `display:flex; height:100vh; font-family:'Figtree'`.
- **Sidebar:** `width:264px; flex:0 0 264px; background:#fff; border-right:1px solid #eef1f2;` en columna. Secciones: logo (alto 64px), perfil centrado, `<nav>` scrolleable (flex:1), tarjeta de soporte abajo.
- **Main:** `flex:1`, columna. Topbar (`height:64px`) + `<main>` scrolleable con `background:linear-gradient(180deg,#e9f4f1 0%,#f5f7f8 220px)` y `padding:22px 26px 40px`.
- Dentro de main: fila breadcrumb + datepicker; luego grid `grid-template-columns:minmax(0,1fr) 372px; gap:20px` (izq = KPIs + Specialities apilados con `gap:20px`; der = panel pulmones). Debajo, full width, la tarjeta "Patients by Age" (`margin-top:20px`).

**Componentes (medidas y estilos exactos en el HTML — referencia rápida):**
- **Tarjetas (KPI / Specialities / pulmones / chart):** `background:#fff; border-radius:18px; padding:22px; box-shadow:0 6px 20px rgba(35,80,95,.05)`.
- **KPI:** icono en círculo `56px` con `border:1.5px solid #d3e8e3; color:#0e8d7e`; número `font-size:34px; font-weight:800; color:#243239`; etiqueta `color:#8b999e`. Pie: link "View All" teal + bloque derecho con `%` (`#1aa896`, 700) y pill "this month" (`background:#e3f3ef; color:#0e8d7e; border-radius:7px`).
- **Specialities:** grid de 5, cada celda `border:1px solid #eef1f2; border-radius:14px; padding:20px 12px; text-align:center`, icono SVG `44px` teal, nombre `font-weight:700`, número `font-size:24px; font-weight:800; color:#1aa896`.
- **Panel pulmones:** SVG de pulmones (gradiente `#7fc3e8→#2f6fb0`, bronquios `#b5732f`) + 3 medidores radiales SVG (`r=22`, stroke 7, track `#eef1f2`): Left 42% teal, Health 72% rojo `#ef4444`, Right 34% teal.
- **Patients by Age:** contenedor `height:230px`; líneas de grid dasheadas `#eef1f2`; barras flex con `gap:6px`, ancho `58%`, color `rgba(26,168,150,.28)` (las últimas 3 más oscuras `rgba(14,141,126,.55)`), `border-radius:5px 5px 0 0`.
- **Soporte (sidebar):** `background:linear-gradient(135deg,#1aa896,#0c8475); border-radius:14px`, número `font-weight:800; font-size:17px` blanco.
- **Nav activo:** `background:#e3f3ef; color:#0e8d7e; font-weight:700` + chip de icono con gradiente teal. Inactivos: `color:#5a6a70` con hover `background:#f4f7f7`.
- **Chat widget:** fijo `right:26px; bottom:24px; width:300px; border-radius:16px; box-shadow:0 14px 40px rgba(30,60,70,.18)`; burbuja `background:#f1f4f4; border-radius:12px 12px 12px 4px`.

## Interactions & Behavior
- **Sidebar nav:** items navegables (`<a>`). El activo es "Hospital Admin". Hover `#f4f7f7`. Cablear a las rutas reales de la app.
- **Buscador (topbar):** input `Search`; conectar a búsqueda global real.
- **Datepicker:** al cambiar el rango, refetch de KPIs y de la gráfica.
- **"View All":** navega al listado correspondiente (pacientes / citas / ingresos).
- **Iconos topbar:** flag (idioma), star (favoritos), grid (apps), gift, chat. Sus puntos de color son badges de notificación → contadores reales.
- **Chat widget:** toggle de apertura/cierre (la "✕" lo cierra). En el diseño hay un prop `showChat` (boolean) que lo muestra/oculta.
- **Estados de carga:** mientras se hace fetch, muestra skeletons que respeten exactamente las mismas cajas/tamaños (no cambies el layout).
- **Estados vacíos/error:** si un endpoint falla, muestra el valor en blanco o un guion dentro del mismo contenedor; nunca alteres la estructura.
- **Responsive:** el diseño está pensado para escritorio ancho. Mantén el comportamiento del prototipo; cualquier breakpoint adicional es a tu criterio sin romper la composición de escritorio.

## State Management
Estado mínimo sugerido (adáptalo al stack):
- `dateRange` → dispara refetch de `stats` y `patientsByAge`.
- `stats` `{ patients, patientsPct, appointments, appointmentsPct, revenue, revenuePct }`.
- `specialities` `[{ name, count }]`.
- `lungMetrics` `{ left, health, right }` (porcentajes 0–1).
- `patientsByAge` `[{ ageBucket, count }]`.
- `me` `{ name, role, avatarUrl }`.
- `chatOpen` (boolean, UI).
Data fetching al montar + en cada cambio de `dateRange`.

## Design Tokens
**Colores**
- Primario teal (texto/iconos): `#0e8d7e`
- Teal acento (números/%): `#1aa896`
- Teal fondo suave (pills/activo): `#e3f3ef`
- Gradiente teal (logo/soporte/chips): `#22b8a6 → #0e8d7e`, soporte `#1aa896 → #0c8475`
- Texto fuerte: `#243239` · texto cuerpo: `#33424a` · texto secundario: `#5a6a70` · muted: `#8b999e` / `#9aa7ab`
- Bordes: `#eef1f2`, `#e7ecec` · fondo app: `#f5f7f8` · fondo input/hover: `#f8fafa` / `#f4f7f7`
- Gradiente header main: `#e9f4f1 → #f5f7f8`
- Pulmones: `#7fc3e8 → #2f6fb0`, bronquios `#b5732f`
- Medidor Health (rojo): `#ef4444` · track medidores: `#eef1f2`
- Badges topbar: amarillo `#f5b301`, verde `#1fbf75`, rojo `#ef4444`

**Tipografía:** `Figtree` (Google Fonts), pesos 400/500/600/700/800. Números KPI 34/800, número speciality 24/800, título sección 18/700, body 14, muted 12–13.

**Radios:** tarjetas 18px · celdas/soporte/datepicker 12–14px · pills 7px · chips de icono 9–11px · chat 16px.

**Sombras:** tarjetas `0 6px 20px rgba(35,80,95,.05)` · chat `0 14px 40px rgba(30,60,70,.18)` · soporte `0 8px 18px rgba(15,130,115,.3)`.

**Espaciado:** padding tarjeta 22px · gaps de grid 16–20px · padding main 22/26px.

## Assets
- **Fuente:** Figtree vía Google Fonts (`https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800`).
- **Iconos:** todos son SVG inline (sin librería externa) — cópialos del HTML o sustitúyelos por los equivalentes de tu set de iconos manteniendo grosor/tamaño.
- **Pulmones + medidores:** SVG generados en código (ver la clase logic del `.dc.html`). Si tienes la imagen anatómica real, puede reemplazar el SVG manteniendo la misma caja.
- **Avatares (`Ema Wilson`, usuario topbar, bot):** placeholders de `i.pravatar.cc`. Reemplazar por las imágenes reales del usuario/backend.

## Files
- `Hospital Dashboard.dc.html` — el diseño completo (marcado + estilos en línea + la lógica que genera SVGs de pulmones, medidores y barras). **Esta es la referencia visual a recrear pixel-perfect.** Los valores numéricos dentro son mocks a sustituir por datos del backend.
