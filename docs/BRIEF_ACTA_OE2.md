# Brief para corregir el Acta de Conformidad OE2

> **Cómo usar esto:** copia todo este documento y pégalo en Claude junto con el archivo
> `Acta_Conformidad_OE2_Renzo_Gutierrez_Rafael_Samanez.docx`. Contiene la verdad técnica
> del sistema (Claude no tiene acceso al repositorio) y la lista exacta de correcciones.

---

## Instrucción

Eres editor técnico de una tesis de ingeniería de software. Te adjunto un **Acta de Conformidad
del Objetivo Específico 2 (OE2)** en `.docx`. El acta está desactualizada: describe una versión
anterior del sistema y contiene texto copiado de otro proyecto.

Tu tarea es **devolver el acta corregida**, respetando el formato, la numeración de figuras y el
estilo académico (APA, tercera persona, español formal). No inventes datos técnicos: usa
exclusivamente la sección "Verdad técnica del sistema" que está más abajo.

Aplica **todas** las correcciones de la sección "Correcciones requeridas". Al final, entrega
también una lista de las capturas de pantalla que el autor debe tomar y reemplazar él mismo.

---

## Verdad técnica del sistema (fuente única — no contradecir)

**Nombre del sistema:** Sami

**Propósito:** detección temprana de señales de depresión y ansiedad en estudiantes de
secundaria de un colegio privado de Lima Metropolitana. **El sistema no diagnostica**: reporta
señales y banderas; la psicóloga interpreta.

### Stack real

| Capa | Tecnología |
|------|------------|
| Frontend | Vue 3 + Vite + Tailwind (SPA única, vistas por rol) |
| Backend | **FastAPI** + SQLAlchemy (Python) — **NO Django** |
| Base de datos | SQLite en desarrollo local · Azure Database for PostgreSQL Flexible en producción |
| NLP | BETO — `Recognai/bert-base-spanish-wwm-cased-xnli` (BETO + XNLI), zero-shot multi-label, embebido en el proceso de FastAPI |
| ML | SVM (`SVC` con kernel RBF + `StandardScaler`, scikit-learn) |
| Autenticación | JWT + OAuth (Google y Microsoft) + bcrypt |
| Despliegue | Azure App Service (Linux B2) — monolito modular |

**Servicios Azure realmente usados:** Azure App Service y Azure Database for PostgreSQL
Flexible Server. **No se usan** Azure Machine Learning, Azure Databricks, Azure Functions ni
Azure Confidential Computing.

### Roles

- **Estudiante:** responde los cuestionarios que le asigna la psicóloga, consulta recursos de
  apoyo, registra su bienestar, agenda reuniones y dispone de un botón SOS.
  **Nunca ve el reporte clínico** — solo la confirmación de cierre.
- **Psicóloga:** arma el banco, crea plantillas, asigna cuestionarios, ve el panel clínico,
  las alertas, el historial y el informe de cada alumno.
- **Administrador:** gestiona usuarios, contenidos, reportes agregados y logs de acceso.

### Flujo funcional real

El sistema **no usa un chatbot ni un chat conversacional**. Ese componente fue eliminado del
diseño. El flujo actual es:

1. La psicóloga arma una **plantilla** combinando bloques del banco clínico.
2. La plantilla se **asigna** a uno o varios alumnos.
3. El alumno responde el cuestionario: bloques de escala Likert/binaria más un bloque
   opcional de **frases incompletas** (texto libre, adaptación SSCT).
4. El `EvaluatorService` evalúa las respuestas por capas y genera el reporte clínico.

### Banco clínico

**7 escalas validadas, no editables:**

| Código | Nombre | Ítems | Referencia |
|--------|--------|-------|------------|
| PHQ-A | Patient Health Questionnaire — Adolescent | 9 | Johnson, Harris, Spitzer & Williams (2002) |
| GAD-7 | Generalized Anxiety Disorder — 7 item | 7 | Spitzer, Kroenke, Williams & Löwe (2006) |
| SRQ-20 | Self-Reporting Questionnaire 20 (OMS) | 20 | Harding, de Arango, Baltazar, Climent et al. (1980) |
| RSES | Rosenberg Self-Esteem Scale | 10 | Rosenberg (1965) |
| WHO-5 | WHO-5 Well-Being Index | 5 | WHO Regional Office for Europe (1998) |
| UCLA-3 | UCLA Loneliness Scale — versión de 3 ítems | 3 | Hughes, Waite, Hawkley & Cacioppo (2004) |
| DASS-21 | Escala de Depresión, Ansiedad y Estrés | 21 | Lovibond & Lovibond (1995) |

Además: **40 frases incompletas** organizadas en 8 áreas, y **bloques personalizados** que la
psicóloga puede crear (nombre, escala, ítems y puntos de corte propios).

### Evaluación por capas — `EvaluatorService`

| Capa | Qué hace |
|------|----------|
| 1 | Puntaje por bloque con los cortes publicados de cada instrumento |
| 2 | Banderas de crisis: PHQ-A ítem 9 ≥ 1, SRQ-20 ítem 17 = 1, BETO ideación ≥ 0.40 |
| 3 | Riesgo compuesto según el número de bloques en zona de alerta |
| 4 | **BETO** clasifica cada frase incompleta en 8 categorías emocionales (zero-shot) |
| 5 | **SVM** como segunda opinión — solo si la plantilla incluye DASS-21 |

### ⚠️ Relación real entre BETO y SVM (el error más grave del acta)

El acta actual afirma que *"el SVM clasifica los vectores de BETO"*. **Eso es falso.**
BETO y SVM son **dos rutas independientes** que nunca se tocan:

```
Frases incompletas (texto libre)  ──►  BETO zero-shot  ──►  8 categorías emocionales
                                                             (Capa 4)

Respuestas DASS-21 (21 valores 0–3) ──►  SVM (RBF)     ──►  en_riesgo / sin_riesgo
                                                             (Capa 5)
```

- **BETO** recibe **texto libre** y devuelve categorías emocionales por frase. Su salida
  alimenta una bandera de crisis (ideación ≥ 0.40), **no al SVM**.
- **El SVM** recibe **21 valores numéricos** (las respuestas DASS-21 en escala 0–3), nunca
  embeddings ni vectores de BETO. Se dispara **únicamente** cuando la plantilla asignada
  incluye DASS-21; si falta cualquiera de las 21 respuestas, no opina.
- El SVM **no reemplaza a las reglas**: emite una segunda opinión y, si **discrepa** del
  resultado por reglas, el sistema levanta una bandera `discrepancia: revisar` para la
  psicóloga.

**BETO no hace lematización.** Es un modelo transformer con tokenización por subpalabras
(WordPiece); no hay stemming ni lematización en el pipeline.

### Métricas del SVM (para citar en el acta)

- Modelo: `SVC` kernel RBF + `StandardScaler`
- Dataset: DASS-21 real de Open Psychometrics, filtrado a adolescentes 13–17 años (n = 7,269)
- Features: las 21 respuestas DASS-21 (escala 0–3). Target: `at_risk` binario según los
  cortes oficiales del instrumento
- Accuracy: 0.9711 · F1-macro: 0.9215 · ROC-AUC: 0.9977 · CV F1-macro: 0.9287 ± 0.0066

---

## Correcciones requeridas

### 1. Introducción del OE2 — eliminar el "Chat inteligente"

**Texto actual (incorrecto):**

> El Objetivo Específico 2 tiene por finalidad diseñar un modelo de lenguaje de procesamiento
> natural (NLP) para la identificación de problemas mentales y el estado emocional actual de
> los estudiantes, mediante encuestas aplicadas a través de un Chat inteligente, integrando el
> clasificador SVM para la detección temprana de síntomas de ansiedad y depresión en
> estudiantes de secundaria de un colegio privado de Lima Metropolitana. Este acta deja
> constancia…

**Reemplazar por:**

> El Objetivo Específico 2 tiene por finalidad diseñar un modelo de procesamiento de lenguaje
> natural (NLP) para la identificación de señales de problemas de salud mental y del estado
> emocional de los estudiantes, mediante cuestionarios clínicos estructurados que combinan
> escalas validadas y frases incompletas de respuesta abierta, e integrando un clasificador de
> Máquinas de Vectores de Soporte (SVM) como segunda opinión para la detección temprana de
> síntomas de ansiedad y depresión en estudiantes de secundaria de un colegio privado de Lima
> Metropolitana. Esta acta deja constancia de la revisión y aprobación de los entregables del
> OE2 y del cumplimiento de sus indicadores de éxito.

### 2. Tabla de componentes de la arquitectura física — dos errores graves

**a) Django → FastAPI.** La fila "Sistema de análisis predictivo…" dice *"desarrollado el
modelo con el uso de Python y Django para el Back-end"*. Reemplazar por:

> Entorno donde se ejecuta el núcleo de la aplicación, desarrollado en Python con **FastAPI**
> para el back-end. Concentra la autenticación, el motor de evaluación por reglas, el modelo
> BETO embebido y el clasificador SVM.

**b) "Trastornos alimenticios" — texto de otro proyecto.** La fila "Servicios Azure" dice
*"para desarrollar el Machine Learning de predicción de **trastornos alimenticios** (Azure
Machine Learning, Azure Databricks, Azure Functions y Azure Confidential computing)"*.
Nada de eso corresponde a este sistema. Reemplazar por:

> Servicios de nube utilizados para el despliegue y la operación del sistema: **Azure App
> Service** (Linux B2) para alojar la aplicación web y el modelo NLP embebido, y **Azure
> Database for PostgreSQL Flexible Server** para la persistencia de los datos clínicos.

**c)** En la fila "Usuario (Alumno)", cambiar *"conversar con el sistema para obtener un
análisis predictivo"* por *"responder los cuestionarios clínicos que le asigna la psicóloga"*.

### 3. Sección 3.2.1 — eliminar el "Servicio de Chat Conversacional"

**Texto actual:**

> Servicio de Chat Conversacional: Facilita la comunicación sobre los conflictos del usuario,
> enviando los datos para su posterior análisis.

**Reemplazar por:**

> Servicio de Cuestionarios: presenta al estudiante los cuestionarios asignados, combinando
> bloques de escala validada y frases incompletas de respuesta abierta, y envía las respuestas
> al backend para su evaluación.

### 4. Sección 3.2.2 — precisar el módulo de predicción

**Texto actual:**

> Módulo de Predicción: Ejecuta el Preprocesamiento NLP para estructurar el lenguaje natural.
> Utiliza un Modelo de Machine Learning para realizar el "Análisis de texto con DSM" y la
> "Detección de salud mental".

**Reemplazar por:**

> Módulo de Evaluación: aplica los cortes clínicos publicados sobre los puntajes de cada
> escala validada y evalúa las banderas de crisis. Sobre las respuestas de texto libre ejecuta
> el modelo **BETO** en modalidad *zero-shot*, que asigna categorías emocionales a cada frase.
> De forma independiente, cuando el cuestionario incluye la escala DASS-21, el **clasificador
> SVM** emite una segunda opinión sobre las 21 respuestas numéricas y señala cualquier
> discrepancia con el resultado obtenido por reglas.

### 5. Sección 3.1 — el rol "usuario" ya no ve predicciones

El texto dice que el alumno accede a *"ver historial de predicciones de salud mental"*. Es
incorrecto: **el alumno nunca ve el reporte clínico**. Reemplazar los servicios del primer rol
por: *"responder los cuestionarios asignados"*, *"consultar recursos de apoyo"*, *"registrar
su bienestar"*, *"agendar reuniones con la psicóloga"* y *"activar el botón SOS"*. El
historial clínico y las alertas son exclusivos del rol Psicólogo.

### 6. Descripción de la Figura 13 — no corresponde a su imagen

La descripción actual habla de *"un informe clínico preliminar… el análisis de 10 respuestas
que fueron procesadas con el modelo BERT… descargar el informe en PDF y un botón para iniciar
una nueva conversación"*, pero la imagen mostrada es el **panel clínico de la psicóloga**
(indicadores generales, estudiantes por nivel de riesgo y distribución del colegio).

Además, *"iniciar una nueva conversación"* pertenece al chatbot eliminado.

**Renombrar la figura y reescribir la descripción:**

> **Figura 13.** Panel clínico de la psicóloga — Sistema de detección de salud mental
>
> Descripción: interfaz principal del rol Psicólogo. Presenta los indicadores agregados del
> colegio —número de estudiantes evaluados, cuestionarios completados y casos en seguimiento—,
> la distribución de estudiantes por nivel de riesgo (crítico, alto, medio, bajo y sin riesgo)
> y la evolución mensual de las evaluaciones cerradas. Desde este panel la psicóloga accede a
> las alertas activas, al listado de estudiantes y al banco clínico.

### 7. Numerar la última imagen (Banco clínico), hoy suelta

La última captura del documento aparece **sin número de figura y sin descripción**. Agregar:

> **Figura 14.** Banco clínico — Sistema de detección de salud mental
>
> Descripción: catálogo de instrumentos disponible para la psicóloga. Reúne las escalas
> validadas no editables —cuya validez depende de su redacción literal publicada—, los bloques
> personalizados creados por la propia profesional y las áreas de frases incompletas. Cada
> escala muestra su código, dominio clínico, número de ítems y referencia bibliográfica
> original.

### 8. Agregar dos figuras nuevas (el SVM no aparece en ninguna captura)

El objetivo del OE2 es *"integrando el clasificador SVM"*, pero **ninguna de las capturas
actuales lo muestra**. Redactar los pies y las descripciones de estas dos figuras nuevas
(las imágenes las aportará el autor):

> **Figura 15.** Informe clínico individual — Sistema de detección de salud mental
>
> Descripción: informe generado por el motor de evaluación tras el cierre de un cuestionario.
> Presenta el puntaje y el nivel de severidad de cada bloque según los cortes publicados del
> instrumento, las banderas de crisis activadas, el riesgo compuesto y la clasificación
> emocional que el modelo BETO asignó a cada frase incompleta. El informe puede descargarse en
> formato PDF y es de acceso exclusivo del rol Psicólogo.

> **Figura 16.** Segunda opinión del clasificador SVM — Sistema de detección de salud mental
>
> Descripción: bloque del informe clínico correspondiente a la quinta capa de evaluación. Se
> activa únicamente cuando el cuestionario aplicado incluye la escala DASS-21. El clasificador
> SVM recibe las 21 respuestas numéricas del instrumento y emite una predicción binaria de
> riesgo con su probabilidad asociada. Cuando esta predicción discrepa del resultado obtenido
> por el motor de reglas, el sistema levanta una bandera de revisión dirigida a la psicóloga.

### 9. Corregir el contenido de la Figura 7 (arquitectura lógica)

La figura contiene **tres afirmaciones técnicamente falsas** que deben corregirse en el
diagrama y en su nota:

| Dice la figura | Debe decir |
|---|---|
| Flecha `BETO ──vectores──► SVM` y "Clasifica los vectores de BETO" | **Eliminar la flecha.** BETO y SVM son rutas independientes; el SVM recibe las 21 respuestas numéricas del DASS-21, nunca vectores de BETO |
| "Lematización" en el bloque de BETO | Eliminar. BETO usa tokenización por subpalabras (WordPiece); no hay lematización |
| "Categoría: depresión / ansiedad · Nivel: bajo/moderado/alto" como salida del SVM | La salida real del SVM es binaria: `en_riesgo` / `sin_riesgo`, con probabilidad y flag de discrepancia |

**Nota corregida al pie de la Figura 7:**

> Nota. El alumno responde un cuestionario armado por la psicóloga a partir del banco clínico.
> Las respuestas siguen dos rutas independientes: las escalas validadas se puntúan con los
> cortes publicados de cada instrumento, mientras que las frases incompletas de texto libre son
> clasificadas por BETO en categorías emocionales mediante inferencia *zero-shot*. Cuando el
> cuestionario incluye la escala DASS-21, el clasificador SVM emite además una segunda opinión
> sobre las 21 respuestas numéricas y señala las discrepancias con el resultado por reglas. El
> informe consolidado se persiste en la base de datos y se entrega a la psicóloga a través del
> panel clínico.

### 10. Corregir el contenido de la Figura 8 (arquitectura en capas, ArchiMate)

Correcciones dentro del diagrama:

- **"Servicio de consejo estudiantil" / "Consejo de apoyo según el estado del niño"** →
  eliminar. El sistema **no da consejos**; así lo validaron las psicólogas. Reemplazar por
  **"Servicio de recursos de apoyo"** (contenido psicoeducativo publicado por la
  administración).
- **"Preprocesamiento en SVM"** → renombrar a **"Clasificación SVM (DASS-21)"** y sacarlo del
  bloque de preprocesamiento: el SVM no preprocesa, clasifica.
- **"Análisis de texto con DSM"** → renombrar a **"Clasificación emocional con BETO"**. El
  mapeo a criterios DSM-5 lo hace el motor de reglas, no el modelo de lenguaje.
- Corregir la errata **"Datos del psicoloqo"** → **"Datos del psicólogo"**.

### 11. Referencia cruzada equivocada en la sección 3.3

La sección 3.3 (capa tecnológica) cierra con *"Lo mencionado se puede ver en mejor forma en la
figura 6"*, pero está describiendo la **Figura 8**. Corregir la referencia.

### 12. Ortografía y tildes en todo el documento

Corregir de forma consistente: `atraves` → **a través** · `deteccion` → **detección** ·
`Psicologo` → **Psicólogo** · `analisis` → **análisis** · `autenticacion` → **autenticación** ·
`recopilacion` → **recopilación** · `Administracion` → **Administración** ·
`Este acta` → **Esta acta** (acta es femenino; lleva "el" solo en singular por la a tónica).

En el título de la Figura 12, quitar el sangrado irregular y unificar el formato de los pies de
figura con el resto del documento.

### 13. Firma pendiente

La celda de **Firma** del asesor especializado (Elio Jefferrson Navarrete Vilca) está vacía.
Verificar que el acta se emita con el espacio de firma correctamente formateado.

---

## Lo que Claude NO puede hacer — capturas que debe tomar el autor

Estas requieren ejecutar el sistema; Claude solo redacta los pies y descripciones:

1. **Figura 13 (reemplazo).** La tarjeta "En seguimiento" salía vacía y con "NaN%"; el bug ya
   está corregido en el código, así que basta con volver a capturar.
2. **Figura 14 (reemplazo).** La captura del banco clínico muestra solo 6 escalas y **falta
   DASS-21**, que es justamente el instrumento que activa el SVM. Recapturar con las 7.
3. **Figura 15 (nueva).** Informe clínico individual de un alumno, con puntajes, banderas y
   clasificación BETO de las frases.
4. **Figura 16 (nueva).** Bloque de segunda opinión del SVM dentro del informe, con un
   cuestionario que incluya DASS-21.

**Antes de recapturar cualquier pantalla**, sembrar datos de demostración realistas. Las
capturas actuales muestran el sistema vacío: *"Aún no hay recursos publicados"*, un solo
estudiante, una plantilla llamada *"Plantilla Test"* y el indicador de Bienestar en 0%.

El dominio de correo ya quedó unificado en `@colegio.edu.pe` en login, registro y recuperación
de contraseña (antes el registro decía `@upc.edu.pe`, que no corresponde a la población
objetivo).

---

## Checklist de entrega

- [ ] Introducción sin "Chat inteligente"
- [ ] Tabla de componentes: Django → FastAPI
- [ ] Tabla de componentes: eliminado "trastornos alimenticios" y los servicios Azure no usados
- [ ] Sección 3.1: el alumno ya no "ve predicciones"
- [ ] Sección 3.2.1: chat → cuestionarios
- [ ] Sección 3.2.2: módulo de evaluación descrito correctamente
- [ ] Figura 7: eliminada la flecha BETO → SVM, sin "lematización", salida SVM binaria
- [ ] Figura 8: sin "consejo estudiantil", SVM y BETO en su lugar, errata corregida
- [ ] Figura 13: renombrada y descripción reescrita
- [ ] Figura 14: numerada y descrita
- [ ] Figuras 15 y 16: pies y descripciones redactados
- [ ] Referencia cruzada de la sección 3.3 corregida
- [ ] Ortografía y tildes
- [ ] Espacio de firma del asesor
