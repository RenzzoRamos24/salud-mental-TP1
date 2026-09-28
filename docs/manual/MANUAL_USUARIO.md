# Manual de Usuario — Sistema Sami

**Sistema de evaluación y acompañamiento en salud mental para estudiantes de educación secundaria**

| | |
|---|---|
| **Producto** | Sami |
| **Versión del manual** | 1.0 |
| **Dirigido a** | Estudiantes · Psicólogas/os · Padres y tutores · Administradores |
| **Marco legal** | Ley N° 29733 — Ley de Protección de Datos Personales (Perú) |
| **Institución piloto** | I.E.P. Miguel de Cervantes |

---

## Tabla de contenido

1. [Introducción](#1-introducción)
2. [Antes de empezar: requisitos y acceso](#2-antes-de-empezar-requisitos-y-acceso)
3. [Conceptos clave y glosario](#3-conceptos-clave-y-glosario)
4. [Roles y matriz de permisos](#4-roles-y-matriz-de-permisos)
5. [Módulos comunes a todos los usuarios](#5-módulos-comunes-a-todos-los-usuarios)
6. [Manual del Estudiante](#6-manual-del-estudiante)
7. [Manual de la Psicóloga o Psicólogo](#7-manual-de-la-psicóloga-o-psicólogo)
8. [Manual del Padre o Tutor](#8-manual-del-padre-o-tutor)
9. [Manual del Administrador](#9-manual-del-administrador)
10. [Cómo evalúa el sistema (motor de evaluación)](#10-cómo-evalúa-el-sistema-motor-de-evaluación)
11. [Documentos y reportes que genera el sistema](#11-documentos-y-reportes-que-genera-el-sistema)
12. [Protocolo de crisis](#12-protocolo-de-crisis)
13. [Privacidad, confidencialidad y seguridad](#13-privacidad-confidencialidad-y-seguridad)
14. [Preguntas frecuentes y solución de problemas](#14-preguntas-frecuentes-y-solución-de-problemas)
15. [Anexos](#15-anexos)

---

# 1. Introducción

## 1.1 Qué es Sami

Sami es una plataforma web que permite al departamento de psicología de un colegio
**construir, aplicar y evaluar cuestionarios de salud mental** a estudiantes de secundaria,
obteniendo de forma automática un tamizaje estructurado de señales de riesgo.

El sistema no reemplaza el juicio profesional. Su función es **ordenar y priorizar**: convierte
las respuestas de un estudiante en un reporte con puntajes, niveles de severidad y banderas de
atención, de modo que la psicóloga dedique su tiempo a los casos que lo requieren en lugar de a
la corrección manual de escalas.

## 1.2 Qué hace y qué no hace

| Sami **sí** hace | Sami **no** hace |
|---|---|
| Aplica escalas clínicas validadas y las califica automáticamente | Emitir un diagnóstico clínico |
| Señala banderas de atención (p. ej. ítems de ideación suicida) | Sustituir la entrevista clínica |
| Clasifica respuestas de texto libre en categorías emocionales | Decidir derivaciones por sí mismo |
| Genera reportes individuales, para padres e institucionales | Mostrar información clínica al estudiante |
| Registra trazabilidad de todos los accesos | Compartir datos con docentes o compañeros |

> **Principio rector del sistema:** *reporta señales, no diagnósticos.* La interpretación siempre
> queda en manos del profesional de psicología.

## 1.3 Estructura de este manual

Los capítulos 1 a 5 son comunes a todos los usuarios. Los capítulos 6 a 9 son manuales
independientes por rol: cada usuario puede leer únicamente el que le corresponde. Los capítulos
10 a 15 son material de referencia, orientado principalmente al equipo de psicología y a la
administración.

---

# 2. Antes de empezar: requisitos y acceso

## 2.1 Requisitos técnicos

| Elemento | Requisito |
|---|---|
| Navegador | Google Chrome, Microsoft Edge, Firefox o Safari, en versión actualizada |
| Conexión | Internet estable (el cuestionario guarda progreso, pero requiere conexión para enviar) |
| Dispositivo | Computadora, tablet o celular — la interfaz es responsiva |
| Resolución mínima recomendada | 360 px de ancho (celular) |
| Otros | No requiere instalar ningún programa ni extensión |

## 2.2 Dirección de acceso

El colegio comunica la dirección del sistema. En un entorno de desarrollo local:

- **Aplicación:** `http://localhost:5173`
- **Documentación técnica de la API:** `http://127.0.0.1:8000/docs`

## 2.3 Cómo se obtiene una cuenta

| Rol | Cómo se crea la cuenta |
|---|---|
| **Estudiante** | Registro autónomo desde `/register`, eligiendo el perfil "Estudiante" |
| **Psicólogo/a** | Registro autónomo desde `/register`, eligiendo el perfil "Psicólogo/a" |
| **Padre/Tutor** | Registro autónomo desde `/register`, eligiendo el perfil "Padre/Tutor". **Además**, la psicóloga o el administrador deben vincular la cuenta con la del hijo o hija |
| **Administrador** | **No se crea desde la interfaz.** Se genera únicamente por línea de comandos (`python -m scripts.seed_admin`), por integridad de roles |

## 2.4 Estructura general de la pantalla

Todas las pantallas comparten tres zonas:

1. **Barra superior o lateral de navegación** — cambia según el rol del usuario.
2. **Encabezado de página** — un rótulo de sección, el título y una descripción breve.
3. **Cuerpo** — tarjetas, tablas y formularios propios de cada módulo.

En los perfiles de estudiante y psicóloga, un **botón SOS** está siempre accesible.

---

# 3. Conceptos clave y glosario

Estos términos se usan de forma consistente en toda la aplicación y en este manual.

| Término | Definición operativa en Sami |
|---|---|
| **Banco clínico** | Catálogo de instrumentos disponibles. Se divide en banco fijo y banco personalizado |
| **Banco fijo** | Las 7 escalas validadas cargadas en el sistema. **No son editables**: su validez depende de la redacción literal publicada por sus autores |
| **Instrumento** | Una escala completa (p. ej. PHQ-A) con sus ítems, su rango y sus puntos de corte |
| **Ítem** | Cada pregunta individual de un instrumento |
| **Ítem inverso** | Ítem cuya puntuación se invierte antes de sumar (p. ej. ítems 6 a 10 de la RSES) |
| **Bandera de crisis** | Marca a nivel de ítem: si se responde afirmativamente, se activa el protocolo de crisis sin importar el puntaje total |
| **Frases incompletas** | 40 estímulos de completamiento de frases (adaptación SSCT), agrupados en 8 áreas temáticas |
| **Bloque personalizado** | Conjunto de preguntas propias creado por la psicóloga, con su propia escala y sus propios cortes |
| **Plantilla** | Combinación de bloques (instrumentos, bloques personalizados y áreas de frases) que conforma un cuestionario aplicable |
| **Aplicación** | La asignación concreta de una plantilla a un estudiante determinado, con su estado y sus respuestas |
| **Riesgo global** | Clasificación compuesta del resultado: SIN_RIESGO, BAJO, MEDIO, ALTO o CRÍTICO |
| **BETO** | Modelo de lenguaje en español que clasifica las respuestas de texto libre en categorías emocionales |
| **SVM** | Modelo de aprendizaje automático que emite una segunda opinión cuando la plantilla incluye la escala DASS-21 |

## 3.1 Los siete instrumentos del banco fijo

| Código | Nombre | Dominio | Ítems | Escala |
|---|---|---|---|---|
| **PHQ-A** | Patient Health Questionnaire — Adolescent | Depresión | 9 | 0 – 3 |
| **GAD-7** | Generalized Anxiety Disorder — 7 ítems | Ansiedad | 7 | 0 – 3 |
| **SRQ-20** | Self-Reporting Questionnaire 20 (OMS) | Tamizaje general | 20 | 0 – 1 |
| **RSES** | Rosenberg Self-Esteem Scale | Autoestima | 10 | 1 – 4 |
| **WHO-5** | WHO-5 Well-Being Index | Bienestar | 5 | 0 – 5 |
| **UCLA-3** | UCLA Loneliness Scale — versión breve | Soledad | 3 | 1 – 3 |
| **DASS-21** | Depresión, Ansiedad y Estrés (versión corta) | Depresión / ansiedad / estrés | 21 | 0 – 3 |

## 3.2 Las ocho áreas de frases incompletas

El banco contiene **40 frases**, distribuidas en **5 frases por área**:

`familia` · `escuela` · `pares` · `autoconcepto` · `emociones` · `miedos` · `futuro` · `identidad`

La psicóloga elige qué áreas incluir al armar una plantilla; no está obligada a usarlas todas.

---

# 4. Roles y matriz de permisos

El sistema define **cuatro roles**. Cada usuario tiene exactamente uno, y el sistema restringe
tanto las pantallas accesibles como los datos que devuelve el servidor.

## 4.1 Descripción de los roles

| Rol | Quién es | Pantalla de inicio |
|---|---|---|
| **Estudiante** | Alumno o alumna de secundaria | `/menu` |
| **Psicólogo/a** | Profesional del departamento de psicología | `/psicologo` |
| **Padre/Tutor** | Apoderado de un estudiante vinculado | `/padre` |
| **Administrador** | Responsable técnico y de gestión de la plataforma | `/admin` |

## 4.2 Matriz de permisos

| Acción o dato | Estudiante | Psicólogo/a | Padre/Tutor | Admin |
|---|:---:|:---:|:---:|:---:|
| Responder cuestionarios asignados | ✅ | — | — | — |
| Ver sus propias respuestas enviadas | Solo confirmación | — | — | — |
| **Ver puntajes y severidades clínicas** | ❌ | ✅ | ❌ | ❌ |
| Ver el reporte clínico completo de un alumno | ❌ | ✅ | ❌ | ❌ |
| Ver banderas de crisis | ❌ | ✅ | ❌ | Solo el conteo agregado |
| Crear bloques personalizados y plantillas | ❌ | ✅ | ❌ | ❌ |
| Asignar cuestionarios | ❌ | ✅ | ❌ | ❌ |
| Escribir notas clínicas privadas | ❌ | ✅ | ❌ | Solo para auditoría |
| Agendar citas | Solicitar | Crear y gestionar | ❌ | ❌ |
| **Ver las notas internas de una cita** | ❌ | ✅ | ❌ | ❌ |
| Activar el botón SOS | ✅ | — | — | — |
| Atender solicitudes SOS | ❌ | ✅ | ❌ | ✅ |
| Descargar el informe firmado del hijo/a | ❌ | ✅ | ✅ | ❌ |
| Gestionar usuarios y asignar psicólogas | ❌ | ❌ | ❌ | ✅ |
| Publicar contenidos psicoeducativos | ❌ | ❌ | ❌ | ✅ |
| Ver auditoría y logs | ❌ | ❌ | ❌ | ✅ |
| Ejecutar respaldos de base de datos | ❌ | ❌ | ❌ | ✅ |

## 4.3 Reglas de visibilidad que el sistema garantiza

1. **El estudiante nunca ve su reporte clínico.** Al terminar un cuestionario solo recibe una
   confirmación de cierre. No ve puntajes, severidades, banderas ni categorías emocionales.
2. **El padre no ve datos clínicos sensibles.** Su informe contiene identidad, actividad,
   nombre de la psicóloga responsable y el mensaje que ella redacte; nunca puntajes ni banderas.
3. **Las notas de las citas son internas.** El estudiante ve fecha, hora, modalidad, estado y el
   *resumen que la psicóloga redacta para él*, pero nunca el campo de notas internas.
4. **El administrador ve agregados, no contenido clínico.** Puede auditar quién accedió a qué,
   pero no lee respuestas ni reportes de estudiantes.

---

# 5. Módulos comunes a todos los usuarios

## 5.1 Registro de una cuenta nueva

**Ruta:** `/register`

**Pasos:**

1. Seleccionar el perfil en el bloque **"¿Quién eres?"**: Estudiante, Psicólogo/a o Padre/Tutor.
2. Completar **Nombre** y **Apellido**.
3. Ingresar el **correo institucional** (formato `tucorreo@colegio.edu.pe`).
4. Definir una **contraseña de mínimo 8 caracteres** y repetirla en *Confirmar contraseña*.
5. Confirmar el registro.

También es posible registrarse con **Google** o **Microsoft** mediante los botones superiores,
si el colegio habilitó esa integración.

> **Nota:** el perfil "Administrador" no aparece en la lista. Es intencional: se crea solo desde
> el servidor.

## 5.2 Inicio de sesión

**Ruta:** `/login`

Ingresar correo y contraseña, o usar Google / Microsoft. Tras autenticarse, el sistema redirige
automáticamente a la pantalla de inicio correspondiente al rol.

La sesión se mantiene mediante un token JWT con vigencia configurable (por defecto **24 horas**).

## 5.3 Recuperación de contraseña

**Rutas:** `/forgot-password` → `/reset-password`

1. En `/forgot-password`, ingresar el correo institucional.
2. El sistema envía un **código de 6 dígitos**.
3. En `/reset-password`, ingresar el correo, el código recibido, la nueva contraseña y su
   confirmación.

## 5.4 Consentimiento informado

**Ruta:** `/consent`

Es de **paso obligatorio**: mientras no se acepte, el sistema bloquea el acceso a cualquier otra
pantalla y redirige aquí.

La pantalla presenta tres bloques:

| Bloque | Contenido |
|---|---|
| **01 — Esto no es un diagnóstico** | Aclara que los resultados son orientativos y no reemplazan a un profesional |
| **02 — Qué pasa con lo que escribes** | Detalla el tratamiento de los datos: se guardan de forma confidencial, no los ven compañeros ni profesores, sí puede revisarlos la psicóloga del colegio, y pueden borrarse a pedido. Cita expresamente la **Ley N° 29733** |
| **03 — Tú decides** | Establece que se puede detener en cualquier momento, sin obligación de terminar |

Al pie figura de forma permanente la **Línea 113, opción 5** (MINSA, 24/7) y la indicación de
acudir a la emergencia más cercana.

Se acepta marcando *"Lo leí y entiendo. Acepto que mis respuestas se usen como se describe
arriba."* El sistema registra la versión del consentimiento aceptada.

## 5.5 Mi cuenta / Perfil

**Ruta:** `/perfil`

| Sección | Qué permite |
|---|---|
| **Datos personales** | Editar nombre y apellido. El **correo institucional no se puede modificar** |
| **Recordatorio diario** | Elegir entre: sin recordatorio, 08:00, 14:00 o 21:00 |
| **Contraseña** | Cambiarla ingresando la actual, la nueva y su confirmación |
| **Encuesta de satisfacción** | Acceso directo al cuestionario de experiencia de uso |
| **Borrar mi cuenta** | Eliminación definitiva de la cuenta y de todos sus datos |

### Borrado de cuenta

Para evitar borrados accidentales, el sistema exige una **doble confirmación**: escribir la
palabra **ELIMINAR** y además la contraseña actual. La acción es irreversible.

## 5.6 Recursos de apoyo

**Ruta:** `/recursos`

Biblioteca de material psicoeducativo publicado por la administración. Incluye:

- Contenidos publicados (artículos, enlaces, materiales) filtrables por categoría.
- **Escalas de referencia** — las escalas validadas que el sistema toma como guía.
- **Protocolos por nivel de riesgo** — pasos sugeridos según cómo aparece un estudiante en el panel.
- **Líneas de derivación** — contactos para casos fuera del horario del colegio.

## 5.7 Encuesta de satisfacción

**Ruta:** `/encuesta`

Cuestionario breve de experiencia de uso. Cada pregunta se responde en una escala de **1 a 5**
(1 = nada, 5 = mucho) y admite un **comentario opcional**.

Las respuestas son **anónimas para el equipo** y no forman parte de la evaluación clínica del
estudiante. Una vez respondida, el sistema lo indica y no vuelve a solicitarla de inmediato.

---

# 6. Manual del Estudiante

## 6.1 Navegación

El estudiante dispone de siete accesos:

| Acceso | Para qué sirve |
|---|---|
| **Inicio** | Pantalla principal con el resumen de su situación |
| **Cuestionario** | Cuestionarios pendientes y completados |
| **Reuniones** | Citas con su psicólogo/a |
| **Recursos de apoyo** | Biblioteca de materiales |
| **SOS · Ayuda** | Botón de emergencia |
| **Mi bienestar** | Evolución del estado de ánimo |
| **Mi Perfil** | Datos de la cuenta |

## 6.2 Pantalla de inicio

**Ruta:** `/menu`

Reúne en un solo lugar:

| Elemento | Qué muestra |
|---|---|
| **Estado de ánimo / Mi bienestar** | Registro de ánimo de la semana y racha de registros |
| **Cuestionarios enviados** | Total enviado e historial |
| **Pendientes por responder** | Cantidad de cuestionarios sin completar |
| **Próxima reunión** | Fecha, hora y modalidad de la siguiente cita |
| **Cuestionario de bienestar** | Acceso directo al pendiente más próximo |
| **Recursos de apoyo** | Vista previa de la biblioteca |
| **SOS · Ayuda** | Acceso de emergencia, con el recordatorio de la Línea 113 |
| **Tu proceso** | Recorrido acumulado de cuestionarios y sesiones |
| **Tu psicólogo** | Profesional asignado y acceso para agendar |

Un aviso permanente recuerda: *"100 % confidencial — solo tu psicólogo asignado puede ver tus
respuestas. Nadie más del centro tiene acceso."*

## 6.3 Responder un cuestionario

**Rutas:** `/mis-cuestionarios` → `/responder/:id`

### 6.3.1 Ver los cuestionarios asignados

La pantalla **Mis cuestionarios** separa dos listas:

- **Por responder** — con la cantidad de preguntas y la fecha de asignación.
- **Completados** — con la fecha de cierre.

### 6.3.2 Responder

1. Abrir el cuestionario desde la lista de pendientes.
2. Responder las preguntas. Una **barra de progreso** indica el porcentaje avanzado y cuántas
   preguntas se respondieron sobre el total.
3. Los bloques marcados como **opcionales** lo indican expresamente.
4. Las **frases incompletas** se responden con texto libre; el campo invita a escribir
   *"lo que sea que se te venga"*.
5. El botón **Finalizar** se habilita únicamente cuando todas las preguntas obligatorias están
   respondidas.

### 6.3.3 Guardar y continuar después

El botón **"Guardar y continuar luego"** conserva lo respondido y permite retomar más adelante.
El estado de la aplicación pasa a *en progreso*.

### 6.3.4 Qué ocurre al finalizar

Al cerrar el cuestionario, el sistema procesa las respuestas. Si incluye frases incompletas,
aparece el mensaje *"Procesando con cuidado lo que escribiste…"*; la primera ejecución del día
puede tardar algo más porque el modelo de lenguaje se carga en memoria.

Al terminar, el estudiante ve únicamente una pantalla de **"¡Listo!"** y vuelve a su lista de
cuestionarios.

> **Importante:** el estudiante **no ve puntajes, ni niveles de riesgo, ni el análisis de sus
> frases**. Esa información viaja directamente a su psicólogo/a. Es una decisión de diseño: evita
> la autointerpretación de resultados clínicos sin acompañamiento profesional.

## 6.4 Reuniones con el psicólogo

Sección **Reuniones** de la pantalla de inicio.

| Pestaña | Contenido |
|---|---|
| **Próximas** | Citas programadas, con fecha, hora, modalidad y estado |
| **Pasadas / Anteriores** | Citas ya realizadas |

Para cada cita el estudiante ve: **fecha, hora, modalidad** (presencial, virtual o telefónica),
**estado** y, cuando la psicóloga lo redacta, un **mensaje para el estudiante**.

- Si la cita es **virtual**, aparece el botón **"Unirse a la videollamada"**, que se habilita
  cerca de la hora pactada (antes muestra *"Disponible en N min"*).
- Si es **presencial**, se ofrece **"Ver ubicación"**.

### Solicitar una cita

Desde **"Agendar nueva reunión"**. El sistema propone **horarios sugeridos de la semana** para
facilitar la elección. La solicitud queda pendiente de confirmación por parte de la psicóloga.

> El estudiante **no tiene acceso a las notas internas** que la psicóloga escribe sobre la cita.

## 6.5 Botón SOS

Disponible de forma permanente desde el menú del estudiante.

**Qué ocurre al activarlo:**

1. Se registra un evento de emergencia con el origen desde el cual fue activado.
2. Se puede adjuntar un **mensaje opcional** (hasta 1000 caracteres).
3. El sistema alerta al psicólogo o psicóloga del colegio.
4. Se muestra en pantalla:

   > *"Estamos contigo. Ya registramos tu solicitud y alertamos al psicólogo/a del colegio. Por
   > favor llama AHORA a la Línea 113, opción 5. No estás solo/a."*

5. Se despliega el contacto de la **Línea 113, opción 5 — MINSA, 24/7**.

> El SOS es un canal de aviso interno; **no sustituye** una llamada a emergencias. El sistema
> siempre insiste en llamar a la línea.

## 6.6 Mi bienestar

Registro del estado de ánimo diario. Muestra el **promedio sobre 5**, la **racha de registros**
consecutivos y la evolución semanal.

La opción **Modo privado** (en Preferencias) oculta el estado de ánimo en pantallas compartidas.

---

# 7. Manual de la Psicóloga o Psicólogo

Este es el perfil con mayor alcance funcional. El flujo completo de trabajo es:

```
Crear bloque personalizado (opcional)
        ↓
Armar una plantilla  →  Asignar a un estudiante  →  El alumno responde
        ↓                                                    ↓
   Revisar el resultado  ←──────────  El sistema evalúa automáticamente
        ↓
Registrar notas · Agendar cita · Cambiar estado del caso · Descargar informe
```

## 7.1 Navegación

| Acceso | Ruta |
|---|---|
| Panel clínico | `/psicologo` |
| Estudiantes | `/psicologo/estudiantes` |
| Alertas | `/psicologo/alertas` |
| SOS | `/psicologo/sos` |
| Citas | `/psicologo/citas` |
| Banco | `/psicologo/banco` |
| Plantillas | `/psicologo/plantillas` |
| Asignar | `/psicologo/asignar` |
| Mi firma | `/psicologo/firma` |
| Recursos | `/recursos` |
| Mi cuenta | `/perfil` |

Los accesos a **Alertas** y **SOS** muestran un indicador cuando hay elementos sin atender.

## 7.2 Panel clínico

**Ruta:** `/psicologo`

Es la pantalla de inicio. Se compone de:

### 7.2.1 Indicadores superiores

| Tarjeta | Qué informa |
|---|---|
| **Estudiantes** | Evaluados sobre el total, con acceso a *Ver todos* |
| **Cuestionarios** | Completados en el mes, con acceso directo a *Asignar* |
| **En seguimiento** | Porcentaje del total de estudiantes en seguimiento, con acceso a *Ver alertas* |

### 7.2.2 Estudiantes por nivel de riesgo

Gráfico de distribución del colegio según el riesgo global calculado.

### 7.2.3 Indicadores generales

Resumen por dominio: **Depresión**, **Ansiedad** y **Bienestar**.

### 7.2.4 Evaluaciones completadas por mes

Gráfico de barras de los **últimos 12 meses**, con el total acumulado y el promedio por mes
activo. Permite alternar entre *Últimos 3 meses* y *Meses anteriores*.

### 7.2.5 Últimas evaluaciones

Tabla con **Alumno · Email · Fecha · Nivel**, y acceso directo al resultado de cada una.

## 7.3 Estudiantes

**Ruta:** `/psicologo/estudiantes`

Listado de los estudiantes a cargo, con **buscador por nombre o email**. Cada fila muestra el
nombre, el grado, la cantidad de cuestionarios y dos acciones: **Ver** (ficha completa) y
**Asignar** (nuevo cuestionario).

## 7.4 Ficha del estudiante

**Ruta:** `/psicologo/estudiante/:id`

Concentra todo lo relativo a un alumno.

### 7.4.1 Estado del caso

Selector con tres valores: **Activo**, **En seguimiento** y **Cerrado**. El cambio se guarda
automáticamente.

### 7.4.2 Acciones rápidas

- **+ Cita** — agendar una reunión.
- **+ Asignar cuestionario** — aplicar una plantilla.

### 7.4.3 Padre / Tutor vinculado

Permite vincular la cuenta de un apoderado. La pantalla advierte de forma explícita:

> *"Si vinculas a un padre, podrá ver el informe firmado del estudiante desde su propia cuenta
> (sin acceder a puntajes ni datos clínicos sensibles)."*

**Requisito:** el padre debe haberse registrado antes en `/register` con el rol "Padre/Tutor".
El vínculo se puede retirar con **Quitar vínculo**.

### 7.4.4 Historial de cuestionarios

Lista de todas las aplicaciones del alumno, con número de aplicación, fecha de asignación, fecha
de completado y acceso al resultado.

### 7.4.5 Notas clínicas privadas

Espacio de registro de observaciones, con **etiqueta opcional** por nota. La pantalla aclara:

> *"Solo tú las ves. El admin tiene acceso únicamente para auditoría."*

Las notas pueden eliminarse individualmente.

## 7.5 Banco clínico

**Ruta:** `/psicologo/banco`

Catálogo de todo el material disponible, en tres secciones:

### 7.5.1 Escalas validadas (no editables)

Las 7 escalas del banco fijo. Para cada una se muestra el número de ítems, el dominio, la cita
bibliográfica de referencia y el marcado de ítems especiales: **crisis** (bandera de atención) e
**inverso** (puntuación invertida).

> **No son editables por diseño.** Modificar la redacción de una escala validada invalida sus
> puntos de corte y su respaldo científico.

### 7.5.2 Frases incompletas — áreas disponibles

Las 8 áreas con la cantidad de frases de cada una.

### 7.5.3 Tus bloques personalizados

Los bloques creados por la psicóloga, con sus ítems, su rango y sus cortes configurados. Se
pueden **Editar** o **Eliminar**.

## 7.6 Crear un bloque personalizado

**Ruta:** `/psicologo/bloque-custom`

| Paso | Sección | Qué se define |
|---|---|---|
| 1 | **Identificación** | Nombre del bloque, dominio (opcional) e instrucción para el alumno (opcional) |
| 2 | **Escala** | Tipo — *Likert (0 a N)* o *Sí / No* — y, si es Likert, los valores mínimo y máximo |
| 3 | **Preguntas** | Las preguntas propias, agregadas una a una. Cada una puede marcarse como **inverso** |
| 4 | **Cortes** | Tres umbrales sobre el rango total: *Sin alerta máx.*, *Posible problema máx.* y *Alto máx.* |

### Sugerencia automática de cortes

El botón **"Usar tercios"** divide el rango total en tres partes iguales y propone esos valores.
Los cortes se pueden ajustar libremente, pero deben ser **crecientes** y el último debe **igualar
el rango máximo**.

## 7.7 Plantillas

**Ruta:** `/psicologo/plantillas`

Una plantilla es el cuestionario que efectivamente se aplica. Al crearla se define:

1. **Nombre** y **descripción** (opcional).
2. **Escalas validadas** a incluir — se marcan de la lista del banco fijo.
3. **Bloques personalizados** a incluir.
4. **Áreas de frases incompletas** a incluir.

El sistema muestra en todo momento el **total estimado de preguntas**, para dimensionar la
extensión antes de guardar.

Cada plantilla guardada ofrece tres acciones: **Editar**, **Asignar** y **Eliminar**.

> **Recomendación clínica:** las psicólogas que validaron el sistema sugirieron cuestionarios
> **cortos, de 15 a 20 preguntas**. Conviene vigilar el contador antes de guardar.

## 7.8 Asignar un cuestionario

**Ruta:** `/psicologo/asignar`

1. Elegir una **plantilla** del desplegable (muestra la cantidad de bloques).
2. Elegir un **estudiante** del desplegable.
3. Confirmar.

La aplicación queda en estado **pendiente** y aparece de inmediato en la lista del alumno.

## 7.9 Leer el resultado de un cuestionario

**Ruta:** `/psicologo/resultado/:id`

Es la pantalla clínica central. Se lee de arriba hacia abajo:

### 7.9.1 Aviso de crisis

Si se activó alguna bandera, aparece primero una franja destacada:

> **PROTOCOLO DE CRISIS ACTIVADO.** *Revisa de inmediato las respuestas marcadas y deriva según
> protocolo.*

### 7.9.2 Riesgo global

Clasificación general, acompañada del detalle *"N señales en zona de alerta sobre M bloques"*.

### 7.9.3 Segunda opinión — SVM sobre DASS-21

Solo aparece si la plantilla incluyó la DASS-21. Muestra:

- La clase predicha y su **nivel de confianza**.
- La **probabilidad estimada** en porcentaje.
- El **dataset** de entrenamiento.
- Un indicador de concordancia:
  - **✓ Coincide con las reglas** — el modelo y los cortes clínicos apuntan en la misma dirección.
  - **⚠ Discrepa con las reglas — revisar** — hay desacuerdo; el caso merece lectura manual.

### 7.9.4 Qué respondió el alumno — DASS-21 por subescala

Si se aplicó la DASS-21, se despliegan los 21 ítems agrupados en **Depresión**, **Ansiedad** y
**Estrés**, con la nota de que los subtotales se multiplican × 2 para equipararlos a la escala
DASS-42 (Lovibond & Lovibond, 1995).

### 7.9.5 Termómetros por bloque

Para cada bloque: el nombre, el **puntaje obtenido sobre el rango máximo**, la **etiqueta de
severidad** y, cuando corresponde, el aviso *"Bandera de crisis encendida"*.

### 7.9.6 Frases incompletas

Cada frase respondida se muestra con: el **área**, el **número**, el **estímulo**, la **respuesta
literal del alumno** y la **categoría emocional dominante** asignada por BETO. Las respuestas con
ideación detectada se marcan de forma diferenciada.

### 7.9.7 Marcar como revisado

El botón **"Marcar como revisado"** cambia el estado de la aplicación a *revisado*, dejando
constancia de que el caso fue leído por el profesional.

## 7.10 Alertas

**Ruta:** `/psicologo/alertas`

Cola de trabajo priorizada: reúne las aplicaciones con banderas de crisis o riesgo elevado. Cada
entrada indica el estudiante, si hubo **crisis activada**, y ofrece acceso directo a **Ver
resultado**.

## 7.11 Solicitudes SOS

**Ruta:** `/psicologo/sos`

Lista de las activaciones del botón SOS que siguen abiertas. Para cada una se muestra:

- Estudiante que la activó.
- Momento de activación y **pantalla de origen**.
- **Mensaje del alumno**, si lo dejó (o la indicación *"No dejó mensaje"*).

Incluye un botón **Refrescar** y el recordatorio permanente de que la **Línea 113 — opción 5**
está disponible 24/7.

Cada solicitud se cierra marcándola como **atendida**.

## 7.12 Citas

**Ruta:** `/psicologo/citas`

### Crear una cita

Con **+ Nueva cita** se completan:

| Campo | Opciones |
|---|---|
| **Estudiante** | Desplegable de alumnos a cargo |
| **Modalidad** | Presencial · Virtual · Telefónica |
| **Fecha** | Selector de fecha |
| **Hora** | Selector de hora |
| **Notas** | Texto libre, **de uso interno** |
| **Atención de crisis** | Casilla que marca la cita como alta prioridad |

### Gestionar las citas

- **Próximas** — citas programadas, con acciones **Editar** y **Completada**.
- **Histórico** — citas pasadas.

Las citas marcadas como crisis se distinguen visualmente.

> **Privacidad:** el campo **Notas** es interno. El estudiante ve fecha, hora, modalidad, estado
> y el resumen que se le redacte, pero **nunca las notas**.

## 7.13 Mi firma

**Ruta:** `/psicologo/firma`

Permite subir la **firma escaneada**, que se anexa automáticamente al pie de cada informe
clínico descargado por las familias o el equipo pedagógico.

**Requisitos del archivo:** PNG o JPG · máximo 2 MB · fondo blanco recomendado.

La pantalla incluye recomendaciones para obtener una firma nítida:

1. Firmar con lapicera o plumón negro sobre hoja blanca.
2. Fotografiar o escanear con buena luz y sin sombras.
3. Recortar dejando poco margen alrededor del trazo.
4. Guardar como PNG con fondo transparente si es posible.

La firma cargada se puede **cambiar** o **eliminar** en cualquier momento, y se previsualiza tal
como aparecerá en el informe.

---

# 8. Manual del Padre o Tutor

## 8.1 Alcance de este perfil

El perfil de padre o tutor es **de solo lectura y de alcance deliberadamente limitado**. Existe
para que la familia acompañe el proceso sin acceder a información clínica sensible.

| El padre **sí** ve | El padre **no** ve |
|---|---|
| Nombre y grado de su hijo/a | Puntajes de las escalas |
| Cantidad de cuestionarios completados | Niveles de severidad |
| Fecha de última actividad | Banderas de crisis |
| Nombre de la psicóloga responsable | Respuestas del cuestionario |
| Estado del seguimiento | Frases escritas por su hijo/a |
| Mensaje redactado por la psicóloga | Notas clínicas |
| Informe firmado descargable | Notas internas de las citas |

## 8.2 Requisito previo: la vinculación

Registrarse no basta. Después del registro, **la psicóloga o la administración deben vincular la
cuenta del padre con la del estudiante**.

Mientras no exista el vínculo, la pantalla muestra:

> *"Aún no tienes estudiantes vinculados. La administración del colegio debe vincular tu cuenta
> con tu hijo/a. Si crees que esto es un error, contacta con secretaría."*

## 8.3 Panel para padres

**Ruta:** `/padre`

Lista de los estudiantes vinculados. Para cada uno:

- Nombre y **grado** (o la indicación *"Grado no registrado"*).
- **Cantidad de cuestionarios completados**.
- **Fecha de la última actividad**.
- **Psicóloga** responsable.
- Acceso **Ver informe →**.

## 8.4 Informe del estudiante

**Ruta:** `/padre/hijo/:id`

Encabezado aclaratorio:

> *"Este informe es un resumen sin datos clínicos sensibles. Los puntajes y el detalle del
> seguimiento son confidenciales entre tu hijo/a y la psicóloga responsable."*

Contenido:

| Campo | Descripción |
|---|---|
| **Grado / curso** | Nivel del estudiante |
| **Estado del seguimiento** | Activo, en seguimiento o cerrado |
| **Cuestionarios completados** | Total |
| **Psicóloga responsable** | Profesional a cargo |
| **Mensaje de la psicóloga** | Texto redactado por la profesional. Si aún no existe, se indica que aparecerá cuando lo escriba |

## 8.5 Descargar el informe firmado

Dos formatos disponibles:

- **📄 Descargar PDF**
- **📝 Descargar Word**

Ambos incluyen la **firma escaneada de la psicóloga** responsable. La pantalla sugiere los usos
previstos: referencia familiar, respaldo para una cita externa o archivo personal.

---

# 9. Manual del Administrador

## 9.1 Alcance de este perfil

El administrador es responsable de la **gestión de usuarios, el contenido psicoeducativo, la
supervisión técnica y la auditoría**. Trabaja con **datos agregados**: no accede al contenido
clínico individual de los estudiantes.

## 9.2 Navegación

| Acceso | Ruta |
|---|---|
| Panel de administración | `/admin` |
| Configuración del sistema | `/admin/sistema` |
| Contenidos psicoeducativos | `/admin/contenidos` |
| Reportes | `/admin/reportes` |
| Auditoría y logs | `/admin/logs` |

## 9.3 Gestión de usuarios

**Ruta:** `/admin`

### 9.3.1 Indicadores

Cuatro contadores: **Total**, **Estudiantes**, **Psicólogas** y **Admins**.

### 9.3.2 Asignar estudiantes a psicólogas

Tabla con **Estudiante · Email · Psicóloga asignada**. Los alumnos sin asignar se marcan como
*"Sin asignar"*.

> **Por qué importa:** *"Cada estudiante puede tener una psicóloga responsable. Las alertas y SOS
> llegan a ella primero."* Un estudiante sin psicóloga asignada no tiene destinatario directo
> para sus alertas.

### 9.3.3 Todos los usuarios

Listado completo, filtrable por rol (Todos los roles / Estudiantes / Psicólogas /
Administradores), con el estado **activo** o **inactivo** de cada cuenta.

### 9.3.4 Vinculación de padres

Desde este módulo también se vinculan y desvinculan cuentas de padre con estudiantes.

## 9.4 Configuración del sistema

**Ruta:** `/admin/sistema`

Pantalla de monitoreo técnico, organizada en cinco bloques.

### 9.4.1 Estado de la plataforma

| Indicador | Detalle |
|---|---|
| **Plataforma** | 🟢 Operativa — Azure App Service Linux B2 |
| **Modelo NLP (BETO)** | Categorías emocionales activas |
| **Modelo SVM (DASS-21)** | 🟢 Activo — Segunda opinión clínica |
| **Último respaldo** | Backup automático diario a las 02:00 |

### 9.4.2 Resumen operativo

- **Usuarios totales**, desglosados en estudiantes, psicólogas y admins.
- **Cuestionarios aplicados**, plantillas activas y **porcentaje de completitud**.
- **Banco clínico** — 7 instrumentos: PHQ-A, GAD-7, SRQ-20, RSES, WHO-5, UCLA-3, DASS-21.

### 9.4.3 Modelo de NLP — BETO

Identificador del modelo, estado y categorías de clasificación. Desde este módulo puede
**recargarse el modelo** sin reiniciar el servidor.

### 9.4.4 Modelo de Machine Learning — SVM

| Campo | Valor |
|---|---|
| **Algoritmo** | SVC con kernel RBF + StandardScaler |
| **Dataset de entrenamiento** | DASS-42 (Open Psychometrics) · 7 269 adolescentes de 13 a 17 años |
| **Métricas (test held-out 20 %)** | F1-macro 0.92 · ROC-AUC 0.998 · Accuracy 0.97 |
| **Rol clínico** | Segunda opinión sobre la escala DASS-21 — **no reemplaza el criterio profesional** |

### 9.4.5 Tareas programadas (APScheduler)

| Tarea | Horario |
|---|---|
| 🕑 Respaldo diario de la base de datos | 02:00 (hora del servidor) |
| 🕒 Cierre automático de ciclos a los 14 días | 03:00 (hora del servidor) |
| 🧹 Purga de respaldos antiguos | Retención: 14 días |

### 9.4.6 Respaldos

Listado de los respaldos registrados (se muestran los 10 más recientes) y opción para
**ejecutar un respaldo de inmediato**.

## 9.5 Contenidos psicoeducativos

**Ruta:** `/admin/contenidos`

Lo que se publica aquí es exactamente **lo que el estudiante ve en "Recursos de apoyo"**.

### Campos de un contenido

| Campo | Obligatorio | Descripción |
|---|:---:|---|
| **Título** | Sí | Ej. *"Técnicas de respiración para momentos de ansiedad"* |
| **Descripción** | Sí | Resumen breve de para qué sirve el recurso |
| **Tipo** | Sí | Clasificación del material |
| **Categoría** | No | Agrupación temática |
| **Icono** | No | Identificador visual |
| **Enlace** | No | URL externa |
| **Autor** | No | Crédito |
| **Cuerpo del artículo** | No | Texto completo, si el recurso se lee dentro de Sami |
| **Visible para los alumnos** | Sí | Casilla que controla la publicación |

Los contenidos con la casilla desmarcada aparecen en la lista del administrador con la marca
**oculto** y no son visibles para los estudiantes. Cada contenido puede **Editarse** o
**Eliminarse**.

## 9.6 Reportes

**Ruta:** `/admin/reportes`

### 9.6.1 Métricas de cuestionarios

Cuatro indicadores: **Plantillas**, **Bloques custom**, **Asignados** y **Completitud** (%).

### 9.6.2 Reporte mensual para autoridades

Genera un **PDF agregado y anonimizado** con los totales del mes seleccionado. Se elige **Año** y
**Mes** y se descarga.

Contenido del reporte: total de aplicaciones del período, distribución por estado, distribución
por nivel de riesgo, cantidad de crisis activadas, número de alumnos activos y número de
psicólogas.

> Es un reporte **institucional**: no identifica estudiantes.

### 9.6.3 Distribución de riesgo

Visualización agregada de los niveles de riesgo del período.

### 9.6.4 Encuesta de satisfacción

Promedios sobre 5 de cada pregunta y los **últimos comentarios** recibidos. Si nadie respondió
aún, se indica expresamente.

## 9.7 Auditoría y logs

**Ruta:** `/admin/logs`

> *"Trazabilidad completa de las acciones realizadas en el sistema — cumplimiento de la Ley 29733
> de Protección de Datos Personales."*

### 9.7.1 Indicadores

| Indicador | Qué mide |
|---|---|
| **Total de peticiones** | Acumulado desde el inicio del sistema |
| **Usuarios únicos (últimos 200)** | Usuarios con actividad reciente |
| **Acciones críticas** | Eventos SOS y errores 5xx |
| **Total usuarios registrados** | Desglosado en estudiantes y psicólogas |

### 9.7.2 Directorios

Listado de **psicólogas activas** y de **estudiantes registrados**.

### 9.7.3 Tabla de logs

Columnas: **Fecha · Rol · Usuario · Método · Endpoint · Status · IP**.

**Filtros disponibles:** por rol (`estudiante` / `psicologo` / `admin`) y por endpoint
(ej. `/api/v1/auth`). Al pie se indica cuántos registros se muestran sobre el total.

---

# 10. Cómo evalúa el sistema (motor de evaluación)

Esta sección documenta la lógica de calificación. Está dirigida principalmente al equipo de
psicología y al tribunal de tesis.

Cuando un estudiante cierra un cuestionario, el sistema ejecuta **cinco capas** de análisis.

## 10.1 Capa 1 — Puntaje por bloque

Cada bloque se califica de forma independiente.

**Para instrumentos del banco fijo:**

1. Se suman los valores de los ítems respondidos.
2. Los **ítems inversos** se invierten antes de sumar, con la fórmula
   `valor_corregido = likert_max + likert_min − valor`.
3. La **WHO-5** recibe un tratamiento especial: el bruto se multiplica × 4 para estandarizarlo a
   una escala de 0 a 100.
4. El total se contrasta con la tabla de cortes del instrumento, obteniendo una **etiqueta de
   severidad** y un indicador binario de **zona de alerta**.

**Para bloques personalizados:** se aplican los tres cortes definidos por la psicóloga —
*sin alerta*, *posible problema* y *alto*. Los dos últimos cuentan como zona de alerta.

### Tablas de cortes aplicadas

**PHQ-A** (0 – 27) · *Depresión*

| Puntaje | Severidad | Zona de alerta |
|---|---|:---:|
| 0 – 4 | Mínima | — |
| 5 – 9 | Leve | — |
| 10 – 14 | Moderada | ⚠ |
| 15 – 19 | Moderadamente severa | ⚠ |
| 20 – 27 | Severa | ⚠ |

**GAD-7** (0 – 21) · *Ansiedad*

| Puntaje | Severidad | Zona de alerta |
|---|---|:---:|
| 0 – 4 | Mínima | — |
| 5 – 9 | Leve | — |
| 10 – 14 | Moderada | ⚠ |
| 15 – 21 | Severa | ⚠ |

**SRQ-20** (0 – 20) · *Tamizaje general*

| Puntaje | Severidad | Zona de alerta |
|---|---|:---:|
| 0 – 7 | Sin sospecha | — |
| 8 – 20 | Sospecha de trastorno mental común | ⚠ |

**RSES** (10 – 40) · *Autoestima*

| Puntaje | Severidad | Zona de alerta |
|---|---|:---:|
| 30 – 40 | Alta | — |
| 26 – 29 | Media | — |
| 10 – 25 | Baja | ⚠ |

**WHO-5** (0 – 100, tras × 4) · *Bienestar*

| Puntaje | Severidad | Zona de alerta |
|---|---|:---:|
| 51 – 100 | Adecuado | — |
| 29 – 50 | Posible deterioro | ⚠ |
| 0 – 28 | Probable depresión | ⚠ |

**UCLA-3** (3 – 9) · *Soledad*

| Puntaje | Severidad | Zona de alerta |
|---|---|:---:|
| 3 – 5 | No solitario | — |
| 6 – 9 | Solitario | ⚠ |

**DASS-21** (0 – 63) · *Total orientativo*

| Puntaje | Severidad | Zona de alerta |
|---|---|:---:|
| 0 – 14 | Sin sospecha | — |
| 15 – 33 | Leve | — |
| 34 – 50 | Moderado | ⚠ |
| 51 – 63 | Severo | ⚠ |

> El total de la DASS-21 es **orientativo**. La interpretación clínica se realiza por subescalas
> (Depresión: ítems 3, 5, 10, 13, 16, 17, 21 · Ansiedad: 2, 4, 7, 9, 15, 19, 20 · Estrés: 1, 6, 8,
> 11, 12, 14, 18) y se complementa con la segunda opinión del SVM.

## 10.2 Capa 2 — Banderas de crisis

Independientemente del puntaje total, ciertos ítems activan una bandera si se responden
afirmativamente:

| Origen | Condición |
|---|---|
| **PHQ-A ítem 9** | Respuesta ≥ 1 |
| **SRQ-20 ítem 17** | Respuesta = 1 |
| **Análisis BETO** | Categoría *depresión* dominante y score ≥ 0.55 |

Una sola bandera basta para elevar el caso al nivel máximo de riesgo.

## 10.3 Capa 3 — Riesgo compuesto

El riesgo global se determina contando cuántos bloques quedaron en zona de alerta:

| Condición | Riesgo global |
|---|---|
| Cualquier bandera de crisis activa | **CRÍTICO** |
| 3 o más señales en zona de alerta | **ALTO** |
| 2 señales | **MEDIO** |
| 1 señal | **BAJO** |
| 0 señales | **SIN_RIESGO** |

## 10.4 Capa 4 — Análisis de frases incompletas (BETO)

Las respuestas de texto libre se clasifican con un modelo de lenguaje en español
(`Recognai/bert-base-spanish-wwm-cased-xnli`) en modalidad *zero-shot* multi-etiqueta.

### Categorías

| Categoría | Qué captura |
|---|---|
| **depresion** | Ideas de muerte, ideación suicida, deseo de desaparecer, desesperanza total sobre el futuro, sentimientos profundos e incapacitantes de inutilidad, fracaso o vacío |
| **ansiedad** | Preocupación persistente e incontrolable, nerviosismo intenso, tensión física paralizante, miedo severo, síntomas de pánico |
| **adaptativo** | Afrontamiento saludable, resiliencia, metas, sueños, esfuerzo por superar dificultades, autoconocimiento, estrategias positivas |
| **neutral** | Actividades cotidianas, hobbies, descanso, estudios, rasgos de carácter, relaciones, agradecimiento, cansancio normal — **sin sufrimiento clínico** |

### Umbrales

| Umbral | Valor | Regla |
|---|---|---|
| **Detección** | 0.40 | La categoría debe **dominar** y superar este valor para reportarse |
| **Crisis** | 0.55 | *depresión* debe dominar **y** superar este valor para encender bandera |

> **Por qué existe la categoría "neutral":** sin ella, cualquier texto con mínima carga negativa
> disparaba simultáneamente las dos categorías patológicas, incluso en respuestas positivas o
> cotidianas. Incluirla fuerza competencia semántica y reduce drásticamente los falsos positivos.

> **Rol del modelo:** BETO funciona como **filtro semántico de priorización de lectura**, no como
> clasificador diagnóstico. Su salida siempre acompaña la respuesta literal del alumno, de modo
> que la psicóloga lee el texto original y no solo la etiqueta.

## 10.5 Capa 5 — Segunda opinión (SVM)

Se ejecuta **únicamente** cuando la plantilla incluyó la DASS-21 y las 21 respuestas están
completas.

| Característica | Detalle |
|---|---|
| **Algoritmo** | SVC con kernel RBF + StandardScaler |
| **Entrada** | Los 21 ítems crudos (valores 0 – 3) |
| **Salida** | Clase (`en_riesgo` / `sin_riesgo`), probabilidad y confianza |
| **Dataset** | DASS-42 · Open Psychometrics · 7 269 adolescentes de 13 a 17 años |
| **Etiqueta de referencia** | Cortes de Lovibond & Lovibond (1995) por subescala |
| **Métricas** | F1-macro 0.92 · ROC-AUC 0.998 · Accuracy 0.97 (test held-out) |

El sistema compara la predicción del SVM con el resultado de las reglas. Si **discrepan**, lo
señala explícitamente en pantalla como *"⚠ Discrepa con las reglas — revisar"*. La discrepancia
no cambia el riesgo global: es una invitación a la lectura manual.

## 10.6 Estados de una aplicación

```
pendiente  →  en_progreso  →  completado  →  revisado
```

| Estado | Significado |
|---|---|
| **pendiente** | Asignado, el alumno aún no lo abrió |
| **en_progreso** | El alumno guardó respuestas parciales |
| **completado** | El alumno cerró el cuestionario; el sistema ya lo evaluó |
| **revisado** | La psicóloga leyó el resultado y lo marcó como atendido |

---

# 11. Documentos y reportes que genera el sistema

| Documento | Quién lo genera | Quién lo recibe | Contenido |
|---|---|---|---|
| **Reporte clínico individual (PDF)** | Psicóloga | Uso clínico interno | Identificación del estudiante, historial de cuestionarios, citas recientes, últimas 10 notas clínicas y firma de la psicóloga |
| **Reporte clínico individual (Word)** | Psicóloga | Uso clínico interno | Mismo contenido, en formato editable |
| **Informe para padre o tutor (PDF)** | Psicóloga / Padre | Familia | Identidad del estudiante, actividad, mensaje de la psicóloga y firma. **Sin puntajes ni banderas** |
| **Informe para padre o tutor (Word)** | Psicóloga / Padre | Familia | Mismo contenido, en formato editable |
| **Reporte mensual institucional (PDF)** | Administrador | Autoridades del colegio | Totales del mes, distribución por estado y por riesgo, crisis activadas, alumnos activos y psicólogas. **Agregado y anonimizado** |

Todos los documentos individuales llevan la marca **"Documento de uso clínico — confidencial"** y
la firma escaneada de la psicóloga responsable, si la cargó previamente.

---

# 12. Protocolo de crisis

## 12.1 Cuándo se activa

El sistema activa el protocolo de crisis en dos situaciones:

1. **Automáticamente**, cuando una evaluación enciende una bandera (PHQ-A ítem 9, SRQ-20 ítem 17
   o ideación detectada por BETO).
2. **Manualmente**, cuando un estudiante pulsa el **botón SOS**.

## 12.2 Qué hace el sistema

| Momento | Acción del sistema |
|---|---|
| Al detectar la bandera | Marca el riesgo global como **CRÍTICO** |
| En el resultado | Despliega la franja *"PROTOCOLO DE CRISIS ACTIVADO"* con indicación de revisar de inmediato |
| En el panel | Coloca el caso en la cola de **Alertas** |
| Ante un SOS | Registra el evento, notifica a la psicóloga y lo lista en `/psicologo/sos` |
| Al estudiante | Muestra el mensaje de contención y el contacto de la **Línea 113, opción 5** |

## 12.3 Qué debe hacer el equipo humano

El sistema **avisa**; la respuesta es siempre humana. La secuencia recomendada:

1. **Abrir el resultado completo** y leer las respuestas marcadas, no solo las etiquetas.
2. **Contactar al estudiante** el mismo día.
3. **Agendar una cita marcada como atención de crisis** (casilla *"Esta cita es atención de crisis"*).
4. **Registrar una nota clínica** con lo observado y lo actuado.
5. **Derivar según el protocolo del colegio** cuando corresponda.
6. **Cerrar la solicitud SOS** marcándola como atendida.

## 12.4 Línea de emergencia

**Línea 113, opción 5** — MINSA, disponible 24 horas, 7 días a la semana.

El sistema la muestra de forma permanente en el consentimiento, en la pantalla de recursos, en la
respuesta al SOS y en la bandeja SOS de la psicóloga.

---

# 13. Privacidad, confidencialidad y seguridad

## 13.1 Marco legal

El tratamiento de datos se realiza conforme a la **Ley N° 29733 — Ley de Protección de Datos
Personales del Perú**. El sistema informa este marco de forma expresa en el consentimiento
informado, que todo usuario debe aceptar antes de usar la plataforma.

## 13.2 Compromisos declarados al estudiante

1. Las respuestas se guardan de forma **confidencial**.
2. **No las ven compañeros ni profesores.**
3. **Sí puede revisarlas la psicóloga** del colegio que acompañe al estudiante.
4. El estudiante puede pedir el **borrado completo** de sus datos y el sistema lo ejecuta.
5. El estudiante puede **detenerse en cualquier momento**, sin obligación de terminar.

## 13.3 Controles técnicos

| Control | Implementación |
|---|---|
| **Autenticación** | Token JWT con vigencia limitada (24 h por defecto) |
| **Autorización** | Guardas por rol en el enrutador del cliente **y** verificación de rol en cada endpoint del servidor |
| **Consentimiento obligatorio** | Guarda de ruta que impide navegar sin aceptarlo |
| **Segregación de datos por rol** | Esquemas de respuesta distintos según el rol (p. ej. las notas internas de una cita se excluyen de la respuesta al estudiante) |
| **Trazabilidad** | Middleware que registra cada petición: fecha, rol, usuario, método, endpoint, status e IP |
| **Respaldos** | Copia automática diaria a las 02:00, con retención de 14 días y purga automática |
| **Borrado de cuenta** | Doble confirmación (palabra clave + contraseña) |

## 13.4 Buenas prácticas para el equipo

- No compartir credenciales entre profesionales.
- Cerrar sesión al terminar, especialmente en equipos compartidos.
- Usar la opción **Modo privado** del estudiante en pantallas visibles a terceros.
- Recordar que las notas clínicas, aunque privadas, son **auditables por el administrador**.
- No exportar reportes individuales a servicios externos no autorizados por el colegio.

---

# 14. Preguntas frecuentes y solución de problemas

## 14.1 Acceso y cuenta

**No puedo entrar y estoy seguro de mi contraseña.**
Verificar que el correo esté escrito completo y sin espacios. Si persiste, usar
*¿Olvidaste tu contraseña?* en la pantalla de login.

**No me llega el código de recuperación.**
Revisar la carpeta de correo no deseado. El código tiene 6 dígitos y vigencia limitada; si venció,
solicitar uno nuevo.

**El sistema me devuelve siempre a la pantalla de consentimiento.**
El consentimiento no fue aceptado. Es obligatorio: hay que marcar la casilla y confirmar.

**Quiero cambiar mi correo institucional.**
No es posible desde la aplicación: el correo es el identificador de la cuenta. Debe gestionarse
con la administración.

**Me registré como Padre/Tutor pero no veo a mi hijo/a.**
El registro no crea el vínculo. La psicóloga o la administración deben vincular ambas cuentas.
Contactar con secretaría.

## 14.2 Estudiantes

**No tengo ningún cuestionario para responder.**
Los cuestionarios los asigna la psicóloga. Si no hay ninguno, no hay nada pendiente.

**Cerré el navegador a mitad del cuestionario.**
Si se usó *"Guardar y continuar luego"*, las respuestas están guardadas y el cuestionario aparece
como pendiente. Si no, puede que se hayan perdido las respuestas no guardadas.

**El botón Finalizar está deshabilitado.**
Quedan preguntas obligatorias sin responder. Los bloques opcionales lo indican expresamente; el
resto debe completarse.

**Terminé el cuestionario y no veo ningún resultado.**
Es el comportamiento esperado. Los resultados clínicos son para el psicólogo o psicóloga; el
estudiante solo ve la confirmación de envío.

**El envío está tardando mucho.**
Si el cuestionario incluía frases incompletas, el sistema las está analizando. La primera
ejecución del día carga el modelo en memoria y es más lenta; las siguientes son rápidas.

## 14.3 Psicólogas y psicólogos

**No puedo editar una escala validada.**
Es intencional. La validez de PHQ-A, GAD-7, SRQ-20, RSES, WHO-5, UCLA-3 y DASS-21 depende de su
redacción literal publicada. Para preguntas propias, hay que usar **bloques personalizados**.

**Los cortes de mi bloque personalizado no se guardan.**
Deben ser **crecientes** y el último debe **igualar el rango máximo** del bloque. El botón
*"Usar tercios"* genera una combinación válida como punto de partida.

**No aparece la segunda opinión del SVM.**
Solo se calcula si la plantilla incluyó la **DASS-21** y si las 21 respuestas están completas.

**El SVM discrepa de las reglas. ¿Cuál tiene razón?**
Ninguno tiene autoridad final. La discrepancia es una señal de que el caso es limítrofe y merece
lectura manual del detalle de respuestas.

**Un alumno no aparece en mi listado.**
Los estudiantes se asignan a psicólogas desde el panel de administración. Solicitar la asignación
al administrador.

**Mi firma no aparece en el informe.**
Verificar que esté cargada en `/psicologo/firma`. Debe ser PNG o JPG de máximo 2 MB.

## 14.4 Padres y tutores

**El informe no muestra puntajes.**
Es correcto: el informe familiar excluye deliberadamente puntajes, severidades y banderas. Para
detalle clínico hay que solicitar una reunión con la psicóloga.

**No hay mensaje de la psicóloga.**
Aún no lo redactó. Aparecerá tanto en pantalla como en el informe descargable cuando lo haga.

## 14.5 Administración

**Un estudiante no recibe alertas.**
Verificar que tenga una psicóloga asignada. Sin asignación, las alertas y los SOS no tienen
destinatario directo.

**Un contenido no le aparece a los alumnos.**
Revisar la casilla **"Visible para los alumnos"**. Si está desmarcada, el contenido figura como
*oculto*.

**Necesito un respaldo ahora.**
Desde *Configuración del sistema* → **Respaldos**, con la opción de ejecución inmediata. El
respaldo automático corre igualmente a las 02:00.

---

# 15. Anexos

## Anexo A — Índice de rutas de la aplicación

### Rutas públicas

| Ruta | Pantalla |
|---|---|
| `/login` | Inicio de sesión |
| `/register` | Registro |
| `/forgot-password` | Solicitud de recuperación de contraseña |
| `/reset-password` | Restablecimiento de contraseña |
| `/oauth-callback` | Retorno de autenticación con Google / Microsoft |

### Rutas comunes (requieren sesión y consentimiento)

| Ruta | Pantalla |
|---|---|
| `/consent` | Consentimiento informado |
| `/perfil` | Mi cuenta |
| `/recursos` | Recursos de apoyo |
| `/encuesta` | Encuesta de satisfacción |

### Rutas del estudiante

| Ruta | Pantalla |
|---|---|
| `/menu` | Inicio |
| `/mis-cuestionarios` | Mis cuestionarios |
| `/responder/:id` | Responder un cuestionario |

### Rutas de la psicóloga

| Ruta | Pantalla |
|---|---|
| `/psicologo` | Panel clínico |
| `/psicologo/estudiantes` | Listado de estudiantes |
| `/psicologo/estudiante/:id` | Ficha del estudiante |
| `/psicologo/alertas` | Alertas activas |
| `/psicologo/sos` | Solicitudes SOS |
| `/psicologo/citas` | Agenda de citas |
| `/psicologo/banco` | Banco clínico |
| `/psicologo/bloque-custom` | Crear o editar bloque personalizado |
| `/psicologo/plantillas` | Plantillas |
| `/psicologo/asignar` | Asignar cuestionario |
| `/psicologo/resultado/:id` | Resultado de una aplicación |
| `/psicologo/firma` | Mi firma |

### Rutas del padre o tutor

| Ruta | Pantalla |
|---|---|
| `/padre` | Panel para padres |
| `/padre/hijo/:id` | Informe del estudiante |

### Rutas del administrador

| Ruta | Pantalla |
|---|---|
| `/admin` | Gestión de usuarios |
| `/admin/sistema` | Configuración y monitoreo |
| `/admin/contenidos` | Contenidos psicoeducativos |
| `/admin/reportes` | Reportes de cuestionarios |
| `/admin/logs` | Auditoría y logs |

## Anexo B — Referencias de los instrumentos

| Instrumento | Referencia |
|---|---|
| **PHQ-A** | Johnson, J. G., Harris, E. S., Spitzer, R. L., & Williams, J. B. (2002). The Patient Health Questionnaire for Adolescents. *Journal of Adolescent Health*, 30(3), 196–204 |
| **GAD-7** | Spitzer, R. L., Kroenke, K., Williams, J. B., & Löwe, B. (2006). A brief measure for assessing generalized anxiety disorder. *Archives of Internal Medicine*, 166(10), 1092–1097 |
| **SRQ-20** | Harding, T. W., et al. (1980). Mental disorders in primary health care. *Psychological Medicine*, 10(2), 231–241. Organización Mundial de la Salud |
| **RSES** | Rosenberg, M. (1965). *Society and the Adolescent Self-Image*. Princeton University Press |
| **WHO-5** | World Health Organization (1998). *WHO-Five Well-Being Index*. Regional Office for Europe |
| **UCLA-3** | Hughes, M. E., Waite, L. J., Hawkley, L. C., & Cacioppo, J. T. (2004). A short scale for measuring loneliness. *Research on Aging*, 26(6), 655–672 |
| **DASS-21** | Lovibond, S. H., & Lovibond, P. F. (1995). *Manual for the Depression Anxiety Stress Scales* (2nd ed.). Psychology Foundation of Australia |
| **Frases incompletas** | Adaptación del Sacks Sentence Completion Test (SSCT). Sacks, J. M., & Levy, S. (1950) |

## Anexo C — Componentes tecnológicos

| Capa | Tecnología |
|---|---|
| **Backend** | FastAPI + SQLAlchemy |
| **Base de datos** | SQLite (desarrollo) / PostgreSQL (producción) |
| **Frontend** | Vue 3 + Vite + Tailwind CSS |
| **Autenticación** | JWT, con inicio de sesión federado opcional (Google / Microsoft) |
| **Procesamiento de lenguaje** | `Recognai/bert-base-spanish-wwm-cased-xnli` (BETO + XNLI, zero-shot multi-etiqueta) |
| **Aprendizaje automático** | scikit-learn — SVC con kernel RBF + StandardScaler |
| **Tareas programadas** | APScheduler |
| **Generación de documentos** | ReportLab (PDF) · python-docx (Word) |
| **Despliegue** | Azure App Service Linux B2 |

## Anexo D — Glosario de estados

| Entidad | Estados posibles |
|---|---|
| **Aplicación de cuestionario** | `pendiente` · `en_progreso` · `completado` · `revisado` |
| **Caso del estudiante** | `activo` · `seguimiento` · `cerrado` (rótulos en pantalla: *Activo*, *En seguimiento*, *Cerrado*) |
| **Cita** | `pendiente` · `confirmada` · `completada` · `cancelada` |
| **Evento SOS** | `abierto` · `atendido` · `cerrado` |
| **Riesgo global** | `SIN_RIESGO` · `BAJO` · `MEDIO` · `ALTO` · `CRITICO` |
| **Cuenta de usuario** | `activo` · `inactivo` |

---

*Fin del manual.*
