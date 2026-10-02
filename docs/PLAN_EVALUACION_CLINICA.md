# Plan de evaluación clínica — cómo el psicólogo valida el SVM y BETO

Documento de diseño. Estado: propuesta, pendiente de tu decisión en los
puntos marcados **[decidir]**.

Acompaña a lo ya implementado en esta rama:

- `POST /api/v1/admin/psicologo/generar-codigo` — emite un código `SAMI-PSI-NN`.
- `GET /api/v1/psychologist/evaluaciones-recientes` — todas las evaluaciones.
- `/psicologo/evaluaciones` — la bandeja en el frontend.

Todos los números de este documento salen de la base del piloto
(`mental_health.db`, 105 aplicaciones evaluadas), no de estimaciones.

---

## 1. Antes del diseño: tres cosas que encontré y que lo condicionan

### 1.1 La validación actual del SVM es circular

`docs/piloto_colegio/RESULTADOS_VALIDACION.md` reporta **100 % en todas las
métricas** sobre los 38 alumnos del Pack B. Ese número no es evidencia de
validez clínica, y conviene saberlo antes de la defensa:

- El SVM se **entrenó** con etiquetas derivadas de aplicar los cortes de
  Lovibond & Lovibond a las 3 subescalas del DASS-21.
- El *ground truth* del piloto se **calculó con los mismos cortes**, sobre las
  mismas 21 respuestas.

Es decir: se le pidió al modelo reproducir una fórmula aritmética, y la
reproduce perfecto. Un `if` de tres líneas saca el mismo 100 %. Si un jurado
tira de ese hilo, el argumento se cae.

Lo que lo arregla es exactamente lo que estás pidiendo: **un criterio humano
independiente como patrón de oro**. Contra un psicólogo, el 100 % se convierte
en un κ real, y el aporte del SVM pasa a ser demostrable.

### 1.2 BETO ya no tiene 8 categorías, tiene 4 — y la documentación no lo dice

El código vigente (`app/services/nlp_service.py`) clasifica en:

```
depresion · ansiedad · adaptativo · neutral
```

y la bandera de crisis es `dominante == "depresion" AND score >= 0.55`.

Pero `CLAUDE.md`, `METRICAS_VALIDACION.md` y el docstring de
`evaluator_service.py` siguen describiendo **8 categorías emocionales** y una
regla `ideación ≥ 0.40`. Eso ya no existe. Consecuencias concretas:

| Dónde | Qué pasa |
|---|---|
| Base del piloto | 520 de las 535 frases ya están evaluadas con el modelo de 4 categorías. Solo 15 (aplicación #1, de prueba) quedaron con los scores viejos de 8 categorías. |
| `scripts/eval_beto_emoevent.py` | Filtra los scores a `["ira","miedo","tristeza","esperanza","neutral"]`. Con el modelo actual la única etiqueta que sobrevive al filtro es `neutral`, así que si lo corres hoy predice `neutral` para los 1,526 tweets. El F1-macro 0.1246 de `reports/beto_emoevent.md` describe una versión retirada del clasificador. |
| Diseño de etiquetado | No se le puede pedir al psicólogo etiquetar 8 emociones: el sistema no las produce. El formulario tiene que hablar el idioma de las 4 categorías actuales. |

**[decidir]** Tres opciones, y recomiendo la (a):

- **(a)** Aceptar las 4 categorías como definitivas, actualizar los 3
  documentos, y medir *eso*. Es lo que corre en producción.
- **(b)** Volver a 8 categorías para que coincida con lo escrito. Significa
  recalibrar umbrales y re-evaluar las 520 frases.
- **(c)** Dejar la discrepancia. No lo recomiendo: es la primera cosa que
  encuentra quien compare el código con el documento.

### 1.3 Los packs del piloto son disjuntos

Ningún alumno rindió la batería completa:

| Pack | n | Qué respondió | Qué se puede validar con él |
|---|---|---|---|
| A | 37 | PHQ-A + GAD-7 | Reglas y cortes |
| B | 39 | DASS-21 | Reglas **y SVM** — el único pack donde el SVM opina. Opinó en 38: uno tiene un ítem ilegible y el servicio no predice con respuestas faltantes |
| C | 26 | 20 frases SSCT | **BETO** |
| sueltas | 3 | plantillas de prueba y demo, con frases | descartables |

Esto importa: la concordancia a nivel de caso hay que reportarla **por pack**,
no agrupada. Un psicólogo que solo ve 20 frases no está emitiendo el mismo
juicio que uno que ve un PHQ-A completo, y promediar los dos κ produce un
número que no significa nada. Es una limitación del piloto, no del sistema, y
se declara como tal.

---

## 2. Qué puede hacer el psicólogo hoy (ya implementado)

El admin emite un código:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/admin/psicologo/generar-codigo \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Lucía","apellido":"Ramírez",
       "hereda_alumnos_de_email":"psicologa@demo.pe"}'
# → {"codigo_acceso": "SAMI-PSI-01", "alumnos_heredados": 105, ...}
```

El psicólogo entra en `/codigo` con `SAMI-PSI-01`, acepta el acuerdo de
confidencialidad, y cae en `/psicologo/evaluaciones` con las 105 evaluaciones:
puntaje por escala, severidad, bandera de crisis, riesgo compuesto, veredicto
del SVM (y si discrepa de las reglas) y cuántas frases marcó BETO. Puede
filtrar por riesgo, por crisis, por "solo donde el SVM discrepa", y abrir
cualquier caso en el panel de resultado que ya existe.

**Eso es revisión clínica, no validación.** Sirve para que trabaje; no produce
ninguna métrica defendible, porque ve la salida del modelo antes de opinar. Lo
que sigue es la parte que sí produce métricas.

---

## 3. El principio que sostiene todo: ciego

El único mecanismo de juicio que existe hoy es `ResultadoFeedback`:
`aceptado` / `rechazado` sobre el análisis completo. Tiene dos problemas que
lo hacen inservible como validación:

1. **No es ciego.** La psicóloga lee "CRÍTICO, crisis activada" y después
   dice si está de acuerdo. Eso mide anclaje, no concordancia. Un jurado lo
   descarta en una pregunta.
2. **Es un solo bit sobre todo el caso.** No se puede derivar κ, ni
   sensibilidad, ni especificidad, ni nada por clase. Y del SVM no dice nada.

El rediseño es: el psicólogo **emite su juicio primero, sin ver nada del
modelo**, y el sistema compara después. Eso convierte su criterio en patrón
de oro y habilita todas las métricas de la dimensión 4 de
`METRICAS_VALIDACION.md`.

`ResultadoFeedback` se queda como está — es útil como "precisión percibida en
uso real" — pero no es la validación.

---

## 4. Pista A — evaluación a nivel de caso (valida reglas + SVM)

### 4.1 Qué ve el psicólogo

Una pantalla por caso, identificado como `CASO-017` (sin nombre: reduce sesgo
y protege al alumno frente a un evaluador externo). Contiene:

- Grado y pack aplicado.
- **Las respuestas crudas, ítem por ítem, con su etiqueta verbal**
  ("Varios días", "Más de la mitad de los días"…). Sin sumas.
- Las frases incompletas transcritas literal, si el pack las tiene.

### 4.2 Qué NO ve (se filtra en el servidor, no con CSS)

Puntajes, subtotales, severidades, banderas de crisis, riesgo compuesto,
salida del SVM, categorías de BETO. El endpoint ciego **no incluye
`resultado_json` en la respuesta**. Si está en el payload, un evaluador curioso
abre el inspector y la ceguedad se perdió.

### 4.3 Qué responde

| Campo | Valores | Para qué |
|---|---|---|
| `riesgo_clinico` | `SIN_RIESGO` · `BAJO` · `MEDIO` · `ALTO` · `CRITICO` | κ y κ ponderado contra las reglas |
| `requiere_derivacion_inmediata` | sí / no | sensibilidad y especificidad en la decisión que de verdad importa |
| `ideacion_presente` | sí / no / no evaluable | compara contra la bandera de crisis |
| `confianza` | alta / media / baja | permite reportar κ solo en los casos de confianza alta como análisis de sensibilidad |
| `comentario` | texto libre | para los casos discrepantes; es lo que explica el número |

### 4.4 Las tres comparaciones que salen de ahí

1. **Reglas vs. psicólogo** — valida `EvaluatorService` (capas 1-3). Es la
   dimensión 4 de `METRICAS_VALIDACION.md`, tal como está preregistrada.
2. **SVM vs. psicólogo** — sobre los 38 del Pack B. Esta es la que rompe la
   circularidad del §1.1. Por primera vez el SVM se mide contra algo que no
   es la fórmula con la que se entrenó.
3. **SVM vs. reglas, con el psicólogo como árbitro** — hay **14
   discrepancias** en los 38 casos, y están repartidas así:

   - **13 casos**: el SVM dice `en_riesgo` (11 de ellos con probabilidad
     ≥ 0.94, y 7 con probabilidad 1.00) y las reglas dicen `SIN_RIESGO`.
   - **1 caso** (aplicación #38): el SVM dice `sin_riesgo` con probabilidad
     0.018 y las reglas dicen `CRITICO` con crisis activada.

   Esos 14 casos son el material de más valor de todo el piloto. Si el
   psicólogo le da la razón al SVM en los 13, tienes el argumento del aporte
   del modelo escrito con datos: *las reglas por total 0-63 pierden casos que
   el SVM recupera*. Y el caso #38 es el que hay que mirar con lupa: un
   `sin_riesgo` con probabilidad 0.018 frente a una bandera de crisis es
   exactamente el falso negativo que la tesis promete que no ocurre.

### 4.5 Cuántos casos

| Opción | Casos a etiquetar | Esfuerzo (~3 min/caso) | Qué cuesta |
|---|---|---|---|
| **Censo** (recomendada) | 105 | ~5 h, repartible en sesiones | Nada que explicar al jurado |
| Estratificada | 39 CRÍTICO + 4 MEDIO + 6 BAJO + 25 de los 56 SIN_RIESGO = **74** | ~3.7 h | Hay que ponderar la especificidad por el muestreo |

**Recomiendo el censo.** 105 casos dan un κ con intervalo de confianza
estrecho, y no hay que explicar ninguna corrección. Si el tiempo del
psicólogo es el cuello de botella, el mínimo irrenunciable son **los 38 del
Pack B** (los únicos donde el SVM habla).

**[decidir]** Censo de 105, o los 38 del Pack B primero y el resto después.

---

## 5. Pista B — evaluación a nivel de frase (valida BETO)

### 5.1 Qué ve

Una frase por pantalla, mezcladas, **sin agrupar por alumno** (si ve 20
frases seguidas del mismo chico, etiqueta el caso y no la frase). Solo el
estímulo y lo que el alumno escribió. Ninguna predicción.

El criterio ya está redactado y es bueno:
`docs/piloto_colegio/etiquetado_ideacion/INSTRUCCIONES_ETIQUETADO.md`. Se
reusa tal cual.

### 5.2 Qué responde

| Campo | Valores |
|---|---|
| `ideacion_presente` | 0 / 1 — **la etiqueta crítica** |
| `categoria` | `depresion` · `ansiedad` · `adaptativo` · `neutral` (las 4 que el modelo produce) |
| `sufrimiento_clinico_grave` | 0 / 1 |
| `confianza` | alta / media / baja |

El campo `sufrimiento_clinico_grave` existe por una razón técnica: la
hipótesis que BETO evalúa para `depresion` dice literalmente *"ideas de
muerte, ideación suicida, deseo de desaparecer, desesperanza total sobre el
futuro, o sentimientos profundos e incapacitantes de inutilidad, fracaso o
vacío"*. Es una hipótesis **compuesta**: más amplia que ideación sola. Si
mides la bandera de crisis solo contra "ideación suicida", vas a contar como
falso positivo cada frase de desesperanza severa que el modelo marcó
correctamente según su propia definición.

Entonces se reportan las dos cosas, separadas y honestas:

- **Bandera de crisis vs. ideación suicida** → es la métrica ética, la del
  recall ≥ 0.90 que ya está preregistrado.
- **Bandera de crisis vs. (ideación ∨ sufrimiento grave)** → es la métrica
  que mide si el clasificador hace lo que su propia hipótesis declara.

Esa distinción es defendible y además te protege: cualquier precisión baja en
la primera queda explicada por la segunda.

### 5.3 Muestreo — acá sí hay una decisión fina

535 frases con texto; 520 con el modelo vigente. La ideación es **rara**: la
bandera de crisis se activó en **14 de 520 (2.7 %)**. Un muestreo aleatorio
simple de 200 frases traería ~5 positivos, y con 5 positivos no se puede
estimar un recall. Por eso hay que estratificar por el score de `depresion`:

| Estrato | Frases | A etiquetar | Por qué |
|---|---|---|---|
| Marcadas (`dep ≥ 0.55`, domina) | 14 | **14 (censo)** | Mide precisión y tasa de falsos positivos directo, sin ponderar |
| Frontera (`0.35 ≤ dep < 0.55`) | 46 | **46 (censo)** | Son los *casi*. Los falsos negativos se concentran acá |
| Resto (`dep < 0.35`) | 460 | **140 al azar** | Acota los falsos negativos lejanos; peso 460/140 = 3.29 |
| | **520** | **200** | ~1.5 h a 20 s/frase |

Precisión y FP se leen directo del primer estrato. El recall se estima
ponderando el tercero:

```
VP_ponderado = VP_estrato1 + VP_estrato2 + 0 · 3.29
FN_ponderado = FN_estrato1 + FN_estrato2 + FN_estrato3 · 3.29
recall       = VP_ponderado / (VP_ponderado + FN_ponderado)
```

(Un VP en el estrato 3 es imposible por construcción: si `dep < 0.35` la
bandera no se activó.)

**Alternativa sin estadística que explicar: censo de las 520** (~3 h). Si
preferís que el capítulo de métricas no tenga ni una ponderación, es el
camino. Es más trabajo humano y menos trabajo de redacción.

**[decidir]** Estratificado 200 con ponderación, o censo de 520.

### 5.4 Las 15 frases del modelo viejo

La aplicación #1 tiene 15 frases con scores de 8 categorías. O se re-evalúan
con `POST /api/v1/admin/piloto/re-evaluar-beto` (ya existe), o se excluyen.
Re-evaluarlas es un comando; recomiendo eso y dejar el set homogéneo.

---

## 6. Qué tiene que tener el sistema

### 6.1 Requisitos no negociables

Cada uno existe porque sin él la métrica resultante es impugnable:

1. **Ceguera en el servidor.** El endpoint ciego no serializa `resultado_json`.
2. **Orden mezclado pero determinista** (semilla = `evaluador_id`): el
   psicólogo puede parar y seguir mañana sin repetir ni saltarse frases.
3. **Etiquetas append-only.** Si corrige, se guarda la corrección y se
   conserva la primera. El κ primario se calcula con la primera emisión.
4. **Tiempo por ítem.** Detecta etiquetado apresurado y, al revés, documenta
   que el trabajo fue serio.
5. **Pseudonimización.** `CASO-017`, `F-1042`. El evaluador externo no
   necesita nombres.
6. **Set de calibración.** 5 casos y 10 frases de entrenamiento, con
   devolución, antes de los reales. No entran en las métricas. Sube
   muchísimo la fiabilidad.
7. **Umbrales preregistrados.** Ya están en `METRICAS_VALIDACION.md`. Las
   métricas se calculan **recién al cerrar** el etiquetado, nunca durante:
   mirar el κ a mitad de camino y seguir etiquetando es tocar el resultado.
8. **Salida de emergencia.** Botón "este caso es urgente" que avisa a la
   psicóloga titular sin mostrar nada del modelo. Si el evaluador ve una
   frase grave, no puede quedarse callado esperando que termine el estudio.
   Esto es obligación ética, no una feature.

### 6.2 Esquema (2 tablas nuevas)

```python
class EvaluacionCiegaCaso(Base):          # Pista A
    id, aplicacion_id (FK), evaluador_id (FK)
    riesgo_clinico            # 5 clases
    requiere_derivacion       # bool
    ideacion_presente         # bool | None
    confianza                 # alta|media|baja
    comentario                # text
    segundos                  # int
    es_correccion             # bool  (append-only)
    created_at
    # UNIQUE(aplicacion_id, evaluador_id, es_correccion=False)


class EtiquetaCiegaFrase(Base):           # Pista B
    id, aplicacion_id (FK), frase_numero, texto_hash
    evaluador_id (FK)
    ideacion_presente         # bool
    categoria                 # depresion|ansiedad|adaptativo|neutral
    sufrimiento_grave         # bool
    confianza, segundos, es_correccion, created_at
```

`texto_hash` permite verificar que la frase etiquetada es exactamente la que
se comparó, aunque después se re-evalúe el modelo.

Las dos llevan `evaluador_id`: con **dos** psicólogos sobre un subconjunto
común sale el **κ inter-evaluador**, que es la referencia contra la cual se
interpreta el κ del sistema. Sin él, `METRICAS_VALIDACION.md` ya anticipa la
limitación ("un solo evaluador clínico"). Con 30 casos y 80 frases
solapadas se resuelve.

### 6.3 Endpoints

```
GET  /api/v1/validacion/casos/siguiente      → el próximo caso ciego (o 204)
POST /api/v1/validacion/casos/{id}           → guarda el juicio
GET  /api/v1/validacion/frases/siguiente     → la próxima frase ciega
POST /api/v1/validacion/frases/{id}          → guarda la etiqueta
GET  /api/v1/validacion/progreso             → n etiquetados / n totales
POST /api/v1/validacion/urgente/{caso}       → alerta a la psicóloga titular
POST /api/v1/validacion/cerrar               → congela el set (solo admin)
GET  /api/v1/validacion/metricas             → κ, sens, esp… (solo tras cerrar)
GET  /api/v1/validacion/export.csv           → tablas crudas para la tesis
```

### 6.4 Pantallas (3)

- `/validacion/casos` — un caso por vez, respuestas crudas, formulario de 5
  campos, barra de progreso, botón "urgente".
- `/validacion/frases` — una frase por vez, 4 campos, atajos de teclado
  (etiquetar 200 frases con mouse es tortura; con `1`/`2`/`3`/`4` + Enter se
  hace en 1.5 h).
- `/validacion/metricas` — tablas finales, habilitadas solo tras cerrar.
  Esta es la pantalla de la que salen las tablas del capítulo de resultados.

---

## 7. Lo que se calcula al cerrar

Todos los umbrales ya están preregistrados en `METRICAS_VALIDACION.md` §2 y
§4. No se tocan.

### Reglas vs. psicólogo (por pack)

| Métrica | Umbral | Nota |
|---|---|---|
| κ de Cohen (5 clases) | ≥ 0.60 | con IC 95 % por bootstrap |
| κ ponderado lineal | ≥ 0.70 | penaliza menos confundir ALTO con CRÍTICO |
| Sensibilidad (binarizado ≥ MEDIO) | ≥ 0.85 | |
| Especificidad | ≥ 0.75 | |
| VPP / VPN | ≥ 0.70 / ≥ 0.85 | |
| FN en CRÍTICO | ≤ 0.05, ideal 0 | la métrica ética |
| Matriz 5×5 | — | reporte completo |

### SVM vs. psicólogo (n = 38, Pack B)

Mismas métricas en binario (`en_riesgo` / `sin_riesgo`), más:

- ROC-AUC usando `probabilidad` contra la etiqueta humana. **Este es el
  número que reemplaza al 0.9977 circular.**
- Curva de calibración: la probabilidad del SVM, ¿predice la frecuencia real
  de riesgo clínico? Con n=38 son 4 bins; se reporta como exploratorio.
- Adjudicación de las 14 discrepancias, caso por caso, con el comentario del
  psicólogo. Media página de la tesis, y vale más que cualquier tabla.

### BETO vs. psicólogo (n = 200 frases)

| Métrica | Umbral |
|---|---|
| **Recall de la bandera en ideación** | **≥ 0.90** |
| Tasa de falsos positivos | ≤ 0.10 |
| Precisión de la bandera | reporte |
| κ por categoría (4 categorías) | ≥ 0.60 |
| F1-macro sobre las 4 categorías | ≥ 0.65 |
| Curva recall/precisión variando el umbral 0.55 | reporte |

Lo último es gratis y rinde mucho: con las 200 frases etiquetadas se puede
barrer el umbral y mostrar **que 0.55 es la elección correcta** (o corregirlo
con evidencia). Hoy el 0.55 está "calibrado" sin un número detrás.

### κ inter-evaluador (si hay 2 psicólogos)

Sobre el subconjunto solapado. Es el techo: el sistema no puede concordar con
el criterio clínico mejor de lo que dos clínicos concuerdan entre sí.

---

## 8. Esfuerzo

| Trabajo | Quién | Cuánto |
|---|---|---|
| Implementar las 2 tablas + 8 endpoints + servicio de métricas | yo | ~1 sesión |
| 3 pantallas Vue con atajos de teclado | yo | ~1 sesión |
| Calibración (5 casos + 10 frases) | psicólogo | 20 min |
| Pista A — 105 casos | psicólogo | ~5 h, en 3-4 sesiones |
| Pista B — 200 frases | psicólogo | ~1.5 h |
| Segundo evaluador (30 casos + 80 frases) | psicólogo 2 | ~2 h |
| Cerrar, calcular, exportar tablas | automático | minutos |

---

## 9. Limitaciones a declarar en la tesis

Escritas de antemano, para que no las encuentre el jurado primero:

1. Los packs son disjuntos: ningún alumno rindió la batería completa, así que
   la concordancia se reporta por pack y no refleja un juicio clínico sobre
   un cuadro completo.
2. El SVM solo se valida sobre 38 casos, los únicos con DASS-21.
3. Las frases vienen de 29 aplicaciones (26 del Pack C + 3 sueltas): hay
   correlación dentro del alumno, y los
   IC de las métricas por frase son algo optimistas. Se puede corregir con
   bootstrap por alumno (agrupando) — barato de implementar y queda prolijo.
4. Las respuestas del piloto se transcribieron de papel: hay error de
   transcripción no cuantificado.
5. Con un solo evaluador no hay κ inter-evaluador y el patrón de oro es un
   criterio individual.
6. El patrón de oro es juicio clínico sobre respuestas escritas, no
   entrevista diagnóstica. No es un diagnóstico, y el sistema tampoco lo
   pretende.

---

## 10. Plan de implementación

Por etapas, cada una utilizable sola:

1. ~~Código de psicólogo + bandeja de últimas evaluaciones~~ — **hecho en esta rama**.
2. Decidir §1.2 (4 vs 8 categorías) y actualizar los 3 documentos
   desactualizados. Bloquea a la pista B: sin eso el formulario no se puede
   escribir.
3. Re-evaluar las 15 frases viejas de la aplicación #1.
4. Pista A: tablas, endpoints, pantalla de casos, calibración. Arrancar por
   los 38 del Pack B — es donde está el valor.
5. Pista B: pantalla de frases con atajos + muestreo estratificado.
6. Servicio de métricas + pantalla + export CSV.
7. Segundo evaluador, si se consigue.

El orden no es negociable en un punto: **primero etiquetar, después calcular**.
