# Handoff: Sami — Sistema de evaluación de salud mental escolar

## Overview
**Sami** es un sistema web para que la **psicóloga** de un colegio privado peruano arme cuestionarios desde un banco clínico y se los asigne a estudiantes de secundaria (11–17 años), y para que el **alumno** los responda. Este paquete cubre dos productos de la app:

1. **Panel de la psicóloga** (`Panel Psicologa.dc.html`) — app de escritorio con shell de sidebar y 13 vistas (dashboard, triage de riesgo, resultado clínico, ficha del alumno, banco de instrumentos, plantillas, asignación, citas, alertas, SOS, recursos, cuenta).
2. **Cuestionario del alumno** (`Cuestionario Alumno.dc.html`) — la hoja tipo A4 donde el alumno responde un cuestionario en un solo lienzo scrolleable (no paginado).

## About the Design Files
Los `.dc.html` de este bundle son **prototipos de referencia** que muestran el look final y las interacciones. Están escritos con un runtime propietario (Design Components) y **NO deben portarse literalmente**. La tarea es **recrear estos diseños en el codebase real**: **Vue 3 + Tailwind CSS + Work Sans**, usando los componentes y patrones que ya existan en la app. Trata el HTML como fuente de verdad visual y de interacción; reimplementa la lógica en componentes Vue idiomáticos.

Para leer un prototipo: la lógica está en una clase `Component` (métodos que devuelven datos vía `renderVals()`) y la plantilla usa `{{ holes }}`, `<sc-for>`, `<sc-if>`. Ignora esa sintaxis del runtime; te interesan **el markup inline-styled, los datos de ejemplo y los handlers**.

## Fidelity
**Alta fidelidad (hi-fi).** Colores, tipografía, espaciados, radios e interacciones son finales y deben recrearse fielmente. Donde el codebase ya tenga un componente equivalente (botón, input, modal, chip), úsalo respetando estos tokens.

---

## Design Tokens (paleta final — teal/agua)

> El producto migró de verde esmeralda a **teal** para tener identidad propia. **El rojo queda reservado exclusivamente para riesgo/crisis.** La escala de riesgo (rojo→celeste) es semántica, no decorativa.

### Color — marca
| Uso | Hex |
|---|---|
| **Primario (teal)** — botones, activo, progreso, acentos | `#45988C` |
| Teal claro (hover, líneas, foco) | `#74B8AE` · borde hover `#9ECFC6` |
| Teal muy claro (líneas de bloque, fondos suaves) | `#C5E1DC` |
| Fondo teal lavado (chips, áreas, selección) | `#EDF5F3` |
| Teal oscuro (texto sobre claro, eyebrows) | `#2F7D72` / `#347F74` |
| Fondo app (gris) | `#F4F5F6` |
| Superficie / hoja / card | `#FFFFFF` |
| Borde de card | `#ECECEE` |
| Texto principal | `#0A0A0A` · pregunta `#1F2937` · cuerpo `#344054` |
| Texto secundario | `#475467` / `#667085` · sutil `#98A2B3` · placeholder `#9CA3AF` |
| Número/ícono apagado | `#B0B7BF` · borde input `#E5E7EB` |
| **SOS (coral)** — solo el botón flotante de ayuda | `#F87171` |

### Color — escala de RIESGO (semántica, no tocar)
| Nivel | Texto | Fondo chip | Borde chip | Punto/barra |
|---|---|---|---|---|
| Crítico | `#B91C1C` | `#FEF2F2` | `#FECACA` | `#DC2626` |
| Alto | `#C2410C` | `#FFF7ED` | `#FED7AA` | `#F97316` |
| Medio | `#B45309` | `#FFFBEB` | `#FDE68A` | `#F59E0B` |
| Bajo | `#0369A1` | `#F0F9FF` | `#BAE6FD` | `#0EA5E9` |
| Sin riesgo | `#2F7D72` | `#EDF5F3` | `#C5E1DC` | `#45988C` |
| Sin evaluación | `#6B7280` | `#F4F5F6` | `#E5E7EB` | `#9CA3AF` |

> En gráficos, las bandas de riesgo usan tintes suaves: Sin riesgo `#74B8AE`, Bajo `#7DD3FC`, Medio `#FCD34D`, Alto `#FDBA74`, Crítico `#FCA5A5`. Líneas de tendencia de riesgo en celeste `#0EA5E9`.

### Tipografía — Work Sans (400/500/600/700)
- El **encabezado del dashboard** ("Hola, Lucía") y títulos de ficha/resultado usan **Newsreader** (serif, peso 500) como acento editorial. Todo lo demás es Work Sans.
- H1 dashboard (Newsreader): 30px/500, `-0.01em`. H1 de vista (Work Sans): 22–24px/700.
- Card title 14–15px/700 · valor de stat 30–32px/700 (`-0.02em`) · label 13px/600 · sub 12px/`#98A2B3`.
- Eyebrow de sección: 11–12.5px/700, `uppercase`, `letter-spacing 0.05em`, color teal.
- Nav item 13.5px/500. Chip 12px/600. Body 13–14px.

### Radios / sombras / espaciado
- Card `18px` · botón/input `11–14px` · chip/pill/gauge `99px` · avatar `10–12px`.
- Sombra card: `0 1px 2px rgba(16,24,40,.04)`; hover card `0 4px 14px -6px rgba(16,24,40,.12)`.
- Sombra botón primario: `0 8px 18px -6px rgba(69,152,140,.5)`.
- Sidebar 242px. Topbar 60px. Main `padding 26px 32px 64px`, `max-width 1180px`.

### Animaciones
```css
@keyframes pop { 0%{transform:scale(.96);opacity:0} 100%{transform:scale(1);opacity:1} }
@keyframes slidedown { from{opacity:0;transform:translateY(-6px)} to{opacity:1;transform:none} }
@keyframes ckpop { 0%{transform:scale(.3);opacity:0} 55%{transform:scale(1.25)} 100%{transform:scale(1);opacity:1} }
```
> Nota: se quitaron deliberadamente los separadores middot "·" del copy (se veían generados por IA). Usa comas, guiones largos "—" o paréntesis para separar metadatos. No reintroducir "·".

---

## PRODUCTO 1 — Panel de la psicóloga

### Shell (en todas las vistas)
- **Sidebar 242px** (blanco, borde derecho `#ECECEE`, sticky full-height): logo arriba (el usuario lo provee), nav agrupado en 3 secciones con encabezado en `uppercase #B0B7BF`:
  - **Clínico**: Panel, Estudiantes, Alertas (badge rojo con conteo crítico), SOS, Citas.
  - **Instrumentos**: Banco, Plantillas, Asignar.
  - **Cuenta**: Recursos, Mi cuenta.
  - Ítem activo: fondo teal `#45988C`, texto blanco, sombra teal. Hover: fondo `#F4F7F6`, ícono teal. Íconos lucide (stroke `#98A2B3`).
  - Pie del sidebar: card negra de **Emergencias** con "Línea 113, op. 5 / MINSA, atención 24/7".
- **Topbar 60px** (sticky): breadcrumb ("Sami Clínico › {vista}"), buscador (input con ícono lupa), campana con badge de conteo crítico, chip de perfil (avatar iniciales + nombre).
- **Botón SOS flotante** (abajo-derecha, coral `#F87171`, pill): "SOS abiertos" + badge con conteo. Siempre visible.
- **Toast de éxito**: pill negra centrada arriba, con check teal, auto-cierra a ~2.8s. Se dispara al asignar, guardar plantilla/bloque/nota.

### Modelo de datos (ejemplo en el prototipo, método `STUDENTS()` y `RISK()`)
- 16 alumnos con: `id, nombre, email, grado, riesgo (critico|alto|medio|bajo|sin_riesgo|sin_eval), crisis (bool), cuest (nº), ultima (texto)`. Nombres peruanos realistas (ficticios).
- En producción: la cohorte, riesgos y conteos vienen del backend. **El puntaje crudo NO se muestra al alumno** — solo a la psicóloga.

### Vista: PANEL (dashboard, inspirado en layout tipo "Apollo")
1. Saludo editorial (Newsreader) + fecha.
2. **Fila superior** (grid `1fr 320px`): a la izquierda 3 stat-cards (Estudiantes evaluados / Citas este mes / En riesgo — esta en rojo), y debajo "Áreas clínicas en observación" (5 cards con ícono + conteo: Depresión PHQ-A, Ansiedad GAD-7, Autoestima RSES, Bienestar WHO-5, Soledad UCLA-3). A la derecha, card **"Pulso del colegio"**: gauge grande (Bienestar 72/100) + 3 mini-gauges (Ánimo/Ansiedad/Conexión).
3. **3 gráficos SVG cuantitativos** (hechos a mano, sin librería — recrear con tu librería de charts, p. ej. ApexCharts/Chart.js):
   - **Evaluaciones por mes**: barras agrupadas por banda de riesgo (5 series), **eje Y 0–40**, leyenda.
   - **Alumnos evaluados**: área suavizada Nuevos vs Seguimiento, **eje Y 0–35**.
   - **Carga clínica por mes**: **doble eje** — barras = nº evaluaciones (Y izq 0–30), línea = riesgo promedio % (Y der 0–100%, celeste).
4. **Tabla "Últimas evaluaciones"**: #, alumno (avatar+nombre), grado, fecha, chip de riesgo, acción "Ver" (→ Resultado), con paginación.

### Vista: ESTUDIANTES
Tabla completa de la cohorte con header de columnas, avatar coloreado por riesgo, chip de riesgo, última eval, acciones Ver/Asignar. Buscador del topbar filtra por nombre/correo.

### Vista: ALERTAS
Cola priorizada (crítico y alto). Cada alerta es una card con borde/fondo de severidad, avatar, nombre + chip, **motivo clínico** (ej. "PHQ-A ítem 9 positivo + SOS activado"), fecha, botón "Ver resultado". Estado vacío incluido.

### Vista: SOS
Lista de pedidos de ayuda que el alumno disparó. Card con borde rojo, avatar, fecha, origen, **mensaje del alumno en bloque citado** (si lo hay), botón "Marcar atendido" (cambia a chip "Atendido"). Banner ámbar de recordatorio de derivación a Línea 113. El conteo de no atendidos alimenta el badge del botón SOS flotante.

### Vista: RESULTADO CLÍNICO (la más importante)
Resultado de una aplicación (ej. Camila Rojas, #0142):
- Botón volver a ficha.
- **Banner de crisis** (si aplica): fondo rojo, explica la señal (ideación PHQ-A ítem 9 + SOS) y el protocolo; CTAs "Agendar cita de crisis" (rojo) y "Registrar contacto".
- Dos cards: **Riesgo global** (chip + nº señales) y **Estado** (+ botón "Marcar revisado" → toast).
- **Termómetros por bloque** (grid 2col): 6 dominios (PHQ-A, GAD-7, SRQ-20, RSES, WHO-5, UCLA-3) con puntaje `p/max`, barra de progreso coloreada por severidad y etiqueta ("moderada-severa", etc.).
- **Frases incompletas analizadas**: card por frase con área, pregunta-stem, respuesta citada, **chips de categorías sugeridas** (soledad, miedo, desesperanza…) y chip rojo "ideación detectada" cuando corresponde. Aclarar: "el sistema señala posibles temas, no diagnostica".

### Vista: FICHA DEL ALUMNO
Header con avatar grande, nombre, correo/grado, botones "+ Cita" y "+ Asignar cuestionario". **Historial de cuestionarios** (tabla: #, fechas asignada/completada, chip riesgo, estado, Ver). **Notas clínicas privadas**: formulario (etiqueta + textarea + Guardar) y lista de notas con chip de etiqueta, fecha y borrar. Las notas se agregan/borran en vivo (estado local en el prototipo; persistir en backend).

### Vista: BANCO DE INSTRUMENTOS
- **Escalas validadas** (grid 2col, expandibles, marcadas "no editables"): PHQ-A, GAD-7, SRQ-20, RSES, WHO-5, UCLA-3. Al expandir: lista de ítems con badges "crítico" (ítems de ideación) e "inverso" (ítems con puntaje invertido en RSES), + cita académica al pie. **Los textos exactos de todos los ítems están en el método `bancoDefs()` del prototipo.**
- **Frases incompletas — áreas**: chips (Familia, Autoconcepto, Escuela, Pares, Emociones, Miedos, Futuro, Identidad).
- **Bloques personalizados**: cards con dominio, nº ítems, tipo de escala, cortes; botones Editar/Eliminar; botón "Nuevo bloque" → vista Bloque personalizado.

### Vista: PLANTILLAS
Lista de plantillas (cards con nombre, descripción, nº bloques/preguntas, Editar/Asignar/Eliminar). Botón "Nueva plantilla" abre un **builder inline**:
- Nombre + descripción.
- Checkboxes de **escalas validadas** (con nº de ítems), de **bloques personalizados**, y chips toggle de **áreas de frases**.
- **Contador en vivo**: "Total estimado: N preguntas" que suma según lo seleccionado.
- Guardar (→ toast) / Cancelar.

### Vista: ASIGNAR
Form simple (max 560px): select de plantilla + select de alumno + botón "Asignar cuestionario" (→ toast "asignado a {alumno}"). Aparece en el panel del alumno.

### Vista: BLOQUE PERSONALIZADO (wizard)
4 secciones en cards: **Identificación** (nombre, dominio, instrucción) · **Escala** (toggle Likert/Binaria, min/max) · **Preguntas** (filas con nº, textarea, check "inverso", borrar; botón agregar) · **Cortes** (3 umbrales coloreados sin-alerta/posible/alto, con rango auto-calculado). Guardar/Cancelar.

### Vista: CITAS
Botón "Nueva cita". Secciones **Próximas** e **Histórico**: cada cita es una card con avatar, alumno (+ chip "Atención de crisis" si aplica), fecha—modalidad, chip de estado (Programada/Completada/Cancelada), acciones.

### Vista: RECURSOS
3 bloques: **Escalas de referencia** (cards con código, descripción, rango), **Protocolos por nivel** (crítico/alto/medio con pasos accionables, coloreados por severidad), **Líneas de derivación** (Línea 113 op.5, SALUDLINE 106, Teléfono de la Esperanza — con número grande en teal y horario).

### Vista: MI CUENTA
Avatar + chip "Psicóloga". Cards: **Tus datos** (nombre, apellido, correo institucional deshabilitado), **Cambiar contraseña** (3 inputs), **Borrar cuenta** (zona peligrosa, borde rojo, confirmación escribiendo "BORRAR").

---

## PRODUCTO 2 — Cuestionario del alumno (hoja A4)

Pantalla donde el alumno responde. Una sola **hoja tipo A4** (max-width 860px desktop / 380px móvil, blanca, sombra suave, radio 24px) sobre fondo `#F4F5F6`, con todas las preguntas en un lienzo continuo scrolleable (**no paginado, no wizard**).

### Estructura
- **Encabezado**: eyebrow "SAMI BIENESTAR", título "Cuestionario de bienestar", descripción empática, **barra de progreso** teal que se llena, contador "{n} / {total} respondidas".
- **Bloques** con separador (línea teal `#C5E1DC` + nombre cálido del bloque en teal + instrucción). Nombres cálidos (sin códigos clínicos visibles): PHQ-A→"Cómo te has sentido", GAD-7→"Preocupación y tensión", RSES→"Cómo te ves a ti mismo/a", SRQ-20→"En tu día a día", WHO-5→"Tu bienestar", UCLA-3→"Compañía y conexión", frases→"Completa las frases".
- **Tipos de pregunta**:
  - **Escala Likert con escala compartida → MATRIZ** en desktop (escala en el header una vez, una fila por ítem, un radio-círculo por celda; seleccionado = círculo teal con check; fila respondida marcada con check y número en teal). En **móvil** se apila como **pills** (botones con etiqueta completa, seleccionado teal sólido). Aplica a PHQ-A, GAD-7, RSES, WHO-5, UCLA-3.
  - **Binario Sí/No** (SRQ-20): 2 botones grandes lado a lado.
  - **Texto libre** (frases incompletas): textarea con borde inferior, auto-expandible, placeholder gris. Bloque **opcional** (no cuenta para el progreso ni para habilitar Finalizar).
- **Cierre**: hint + botón **Finalizar** (inactivo gris hasta completar lo obligatorio; teal sólido cuando está completo; al click con faltantes resalta en teal la primera pendiente y hace scroll suave a ella).
- **Flotantes**: barra inferior sticky con "Guardar y continuar luego" + mini-progreso clickeable (→ modal índice de bloques navegable); botón **SOS coral** flotante con modal de ayuda (psicóloga + Línea 113).
- **Microinteracción**: al seleccionar, anima un check (`ckpop`) y avanza el foco al siguiente ítem con `focus({preventScroll:true})` (nunca `scrollIntoView`).

### Estados a soportar
Inicial (vacío), parcial (respondida vs pendiente con diferencia sutil), completo (Finalizar activo), validación (resalta faltantes + scroll a la primera), y responsive 375px. El prototipo trae una barra superior de demo para recorrer estos estados — **NO va en producción.**

### Comportamiento / cálculo
- `pct = round(respondidas_obligatorias / total_obligatorias * 100)`. Total obligatorio = 54 (9+7+10+20+5+3). Las frases incompletas no cuentan.
- Guardar parcial (borrador) y enviar al finalizar = endpoints del backend. No calcular ni mostrar puntaje al alumno.

---

## State Management (resumen)
- **Panel**: `view` (router de vistas), `search`, `filter`, expand/colapso de grupos, toggles del builder de plantilla (`tplScales/tplCustom/tplAreas` + contador derivado), `notes` (CRUD local), `sosAttended`, `success` (toast). En producción: fetch de cohorte/resultados/citas; mutaciones para asignar, guardar plantilla/bloque/nota, marcar SOS/revisado.
- **Cuestionario**: `respuestas: Record<itemId, number|string>`, `validate`, modales (índice/SOS/enviado). Orden plano `ordenIds` + `requeridas` para progreso, foco y primera-faltante.

## Assets
- Sin imágenes propias. Íconos = SVG inline estilo **lucide** (recrear con tu set de íconos o copiar paths). **Logo: lo provee el usuario** — no recrear.
- Fuentes: **Work Sans** (400/500/600/700) y **Newsreader** (400/500) desde Google Fonts.
- Gráficos: en el prototipo son SVG generados a mano (métodos `genBars/genArea/genCitas/gauge/smooth`). En producción, recrear con una librería de charts respetando colores y ejes cuantitativos descritos arriba.

## Files
- `Panel Psicologa.dc.html` — prototipo del panel (13 vistas + datos + gráficos). Fuente de verdad visual/interacción. No portar el runtime.
- `Cuestionario Alumno.dc.html` — prototipo de la hoja del alumno (matriz/pills/binario/texto + estados).
- `README.md` — este documento.
