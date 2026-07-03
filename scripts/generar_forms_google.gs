/**
 * Sami · Piloto colegio — generador de Google Forms
 *
 * Crea 3 formularios (Pack A, B, C) con el mismo contenido de los PDFs
 * de `docs/piloto_colegio/`. Anónimos, sin login, con "Código de
 * participante" para poder cruzar los 3 packs del mismo alumno.
 *
 * Cómo usarlo:
 *   1. Ir a https://script.google.com  →  Nuevo proyecto.
 *   2. Pegar TODO este archivo dentro del editor.
 *   3. Guardar (Ctrl+S), ponerle un nombre al proyecto.
 *   4. En el selector de funciones elegir `main` → Ejecutar.
 *   5. Aceptar los permisos que pide (Forms, Drive).
 *   6. Al terminar, mirar el "Registro de ejecución" (View → Logs):
 *      imprime la URL pública de cada uno de los 3 formularios.
 *
 * Los formularios quedan en tu Google Drive (carpeta raíz).
 * Cada uno tiene su propia Google Sheet de respuestas (se genera al
 * abrir Respuestas → icono verde en el form).
 */

// ── Contenido clínico (idéntico a scripts/generar_packs_piloto.py) ──────
const PHQA = [
  "Poco interés o placer en hacer cosas.",
  "Sentirte triste, decaído/a o sin esperanza.",
  "Problemas para dormir, dormir demasiado, o despertarte mucho durante la noche.",
  "Sentirte cansado/a o con poca energía.",
  "Falta de apetito o comer en exceso.",
  "Sentirte mal contigo mismo/a, sentir que eres un/a fracasado/a, o que has fallado a tu familia.",
  "Dificultad para concentrarte en cosas como tareas escolares, leer o ver televisión.",
  "Moverte o hablar tan lento que otras personas lo notan, o estar tan inquieto/a que te mueves mucho más de lo habitual.",
  "Pensar que estarías mejor muerto/a o tener pensamientos de hacerte daño de alguna manera.",
];

const GAD7 = [
  "Sentirte nervioso/a, ansioso/a o con los nervios de punta.",
  "No poder dejar de preocuparte o no poder controlar tus preocupaciones.",
  "Preocuparte demasiado por diferentes cosas.",
  "Tener dificultad para relajarte.",
  "Estar tan inquieto/a que te resulta difícil quedarte quieto/a.",
  "Irritarte o enojarte con facilidad.",
  "Sentir miedo como si algo terrible fuera a pasar.",
];

const DASS21 = [
  "Me costó mucho relajarme.",
  "Me di cuenta que tenía la boca seca.",
  "No podía sentir ningún sentimiento positivo.",
  "Se me hizo difícil respirar.",
  "Se me hizo difícil tomar la iniciativa para hacer cosas.",
  "Reaccioné exageradamente en ciertas situaciones.",
  "Sentí que mis manos temblaban.",
  "Sentí que tenía muchos nervios.",
  "Estaba preocupado por situaciones en las que podría tener pánico.",
  "Sentí que no tenía nada por que esperar.",
  "Noté que me agitaba.",
  "Se me hizo difícil relajarme.",
  "Me sentí triste y deprimido.",
  "No toleré nada que no me permitiera continuar con lo que hacía.",
  "Sentí que estaba al punto del pánico.",
  "No me pude entusiasmar por nada.",
  "Sentí que valía muy poco como persona.",
  "Sentí que estaba muy irritable.",
  "Sentí los latidos de mi corazón sin haber hecho esfuerzo físico.",
  "Tuve miedo sin razón.",
  "Sentí que la vida no tenía ningún sentido.",
];

const FRASES_SSCT = [
  "En mi casa yo…",
  "Mis hermanos…",
  "Yo soy…",
  "Lo que más me gusta de mí es…",
  "Cuando me miro al espejo…",
  "El colegio para mí…",
  "Estudiar es…",
  "Mis amigos…",
  "Cuando estoy con otros chicos/as…",
  "Cuando me enojo…",
  "Cuando estoy triste yo…",
  "Cuando algo me preocupa…",
  "Lo que más me da miedo es…",
  "Cuando estoy solo/a…",
  "Dentro de 5 años…",
  "Mi mayor sueño es…",
  "El futuro me…",
  "Si pudiera cambiar algo de mí…",
  "Cuando pienso en quién soy…",
  "Lo que define quién soy es…",
];

const LABELS_03   = ["Nunca", "Algunos días", "Más de la mitad", "Casi todos los días"];
const LABELS_DASS = ["No me aplicó", "Un poco", "Bastante", "Mucho"];

// ── Helpers ─────────────────────────────────────────────────────────────
/**
 * Configura un formulario como anónimo:
 * - Sin recolectar email
 * - Sin login requerido (público, cualquiera con el enlace)
 * - Sin límite de 1 respuesta por cuenta
 */
function configurarAnonimo_(form) {
  form.setCollectEmail(false);
  form.setAllowResponseEdits(false);
  form.setAcceptingResponses(true);
  form.setShowLinkToRespondAgain(false);
  form.setProgressBar(true);
  // Estas dos SOLO funcionan en cuentas Google Workspace (dominio propio).
  // En Gmail personal tiran "This operation is not supported" — y no hace
  // falta llamarlas porque el form ya es público sin login por defecto.
  try { form.setRequireLogin(false); } catch (e) {}
  try { form.setLimitOneResponsePerUser(false); } catch (e) {}
}

/**
 * Demografía mínima: solo edad. El "código de participante" se genera
 * automáticamente en la Sheet vía trigger `alRecibirRespuesta_` según el
 * orden en que llegan los envíos (P001, P002, …).
 */
function agregarDemografia_(form) {
  form.addSectionHeaderItem()
      .setTitle("Antes de empezar")
      .setHelpText(
        "Estas respuestas son completamente anónimas. No pedimos tu nombre " +
        "ni tu correo — solo tu edad."
      );

  form.addTextItem()
      .setTitle("Edad")
      .setRequired(true);
}

/**
 * Agrega un bloque tipo escala Likert como una "cuadrícula de opción múltiple"
 * (grid) con una fila por ítem y columnas = etiquetas.
 */
function agregarBloqueLikert_(form, titulo, instruccion, items, labels) {
  form.addPageBreakItem().setTitle(titulo).setHelpText(instruccion);

  // Un GridItem por bloque — más rápido de responder y más limpio en móvil.
  const grid = form.addGridItem();
  grid.setTitle(titulo);
  grid.setHelpText(instruccion);
  grid.setRows(items);
  grid.setColumns(labels);
  grid.setRequired(true);
}

/**
 * Bloque de frases incompletas — texto libre por cada estímulo.
 */
function agregarBloqueFrases_(form, titulo, instruccion, items) {
  form.addPageBreakItem().setTitle(titulo).setHelpText(instruccion);
  items.forEach((frase) => {
    form.addParagraphTextItem()
        .setTitle(frase)
        .setRequired(false); // frases pueden dejarse en blanco si no sale nada
  });
}

/**
 * Versión "inline" de la grilla Likert — SIN page break inicial.
 * Se usa en el form con selector A/B/C, donde varias grillas conviven
 * dentro de la misma sección sin romperla.
 */
function agregarGrillaInline_(form, titulo, instruccion, items, labels) {
  form.addSectionHeaderItem()
      .setTitle(titulo)
      .setHelpText(instruccion);
  const grid = form.addGridItem();
  grid.setTitle(titulo);
  grid.setHelpText(instruccion);
  grid.setRows(items);
  grid.setColumns(labels);
  grid.setRequired(true);
}

/**
 * Versión "inline" de las frases — SIN page break inicial.
 */
function agregarFrasesInline_(form, items) {
  items.forEach((frase) => {
    form.addParagraphTextItem()
        .setTitle(frase)
        .setRequired(false);
  });
}

// ── Constructores por pack ─────────────────────────────────────────────
function crearPackA_() {
  const form = FormApp.create("Sami · Pack A — Bienestar (PHQ-A + GAD-7)");
  form.setDescription(
    "Lee con calma y elige lo que más se acerca a cómo te has sentido. " +
    "No hay respuestas correctas o incorrectas. Tus respuestas son anónimas."
  );
  configurarAnonimo_(form);
  agregarDemografia_(form);

  agregarBloqueLikert_(
    form,
    "Cómo te has sentido",
    "Durante las últimas dos semanas, ¿con qué frecuencia te ha molestado lo siguiente?",
    PHQA,
    LABELS_03
  );
  agregarBloqueLikert_(
    form,
    "Preocupación y tensión",
    "Durante las últimas dos semanas, ¿con qué frecuencia te has sentido así?",
    GAD7,
    LABELS_03
  );

  return form;
}

function crearPackB_() {
  const form = FormApp.create("Sami · Pack B — Bienestar (DASS-21)");
  form.setDescription(
    "Lee con calma y marca cuánto te aplicó cada frase esta semana. " +
    "No hay respuestas correctas o incorrectas. Tus respuestas son anónimas."
  );
  configurarAnonimo_(form);
  agregarDemografia_(form);

  agregarBloqueLikert_(
    form,
    "Cómo te ha ido esta semana",
    "Por favor lee cada frase y marca cuánto te aplicó esta semana.",
    DASS21,
    LABELS_DASS
  );

  return form;
}

function crearPackC_() {
  const form = FormApp.create("Sami · Pack C — Completa las frases");
  form.setDescription(
    "Completa cada frase con lo primero que se te venga a la mente. " +
    "No hay respuestas correctas o incorrectas. Tus respuestas son anónimas."
  );
  configurarAnonimo_(form);
  agregarDemografia_(form);

  agregarBloqueFrases_(
    form,
    "Completa las frases",
    "Completa cada frase con lo primero que se te venga a la mente. No hay respuestas correctas.",
    FRASES_SSCT
  );

  return form;
}

// ── Sheet destino + trigger de código automático ───────────────────────
/**
 * Vincula el form a una Google Sheet nueva (si no tiene una) e instala
 * el trigger `alRecibirRespuesta_` que va a escribir "P001", "P002", …
 * en la columna "Participante" según orden de envío.
 */
function conectarSheetYTrigger_(form) {
  // 1. Crear Sheet destino si no existe.
  //    Ojo: form.getDestinationId() tira una excepción cuando el form no
  //    tiene destino asignado (no devuelve null). Por eso el try/catch.
  let ssId = null;
  try { ssId = form.getDestinationId(); } catch (e) { ssId = null; }
  if (!ssId) {
    const ss = SpreadsheetApp.create("Respuestas — " + form.getTitle());
    form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());
    ssId = ss.getId();
  }

  // 2. Instalar trigger onFormSubmit si no está ya
  const triggers = ScriptApp.getProjectTriggers();
  const yaInstalado = triggers.some(
    (t) =>
      t.getHandlerFunction() === "alRecibirRespuesta_" &&
      t.getTriggerSourceId() === form.getId()
  );
  if (!yaInstalado) {
    ScriptApp.newTrigger("alRecibirRespuesta_")
      .forForm(form)
      .onFormSubmit()
      .create();
  }

  return SpreadsheetApp.openById(ssId);
}

/**
 * Trigger onFormSubmit — se ejecuta CADA vez que un alumno aprieta enviar.
 * Escribe "P001", "P002", … en la columna "Participante" de la fila recién
 * agregada, según el orden en que llegaron los envíos.
 *
 * OJO — este trigger tiene que existir como función global (no privada con
 * guión bajo) para que Google la reconozca al momento de disparar el evento.
 */
function alRecibirRespuesta_(e) {
  const form = e.source;
  let ssId = null;
  try { ssId = form.getDestinationId(); } catch (err) { return; }
  if (!ssId) return; // no hay sheet destino — nada que hacer
  const ss = SpreadsheetApp.openById(ssId);
  const sheet = ss.getSheets()[0];

  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow < 2) return;

  // Encontrar (o crear) la columna "Participante"
  const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  let codeCol = -1;
  for (let i = 0; i < headers.length; i++) {
    if (headers[i] === "Participante") { codeCol = i + 1; break; }
  }
  if (codeCol === -1) {
    codeCol = lastCol + 1;
    sheet.getRange(1, codeCol).setValue("Participante");
  }

  // Código = "P" + número de fila de datos, con padding a 4 dígitos
  // (sobra para 40 por pack, y aguanta hasta 9999 sin cortarse).
  const nro = lastRow - 1;
  const codigo = "P" + ("0000" + nro).slice(-4);
  sheet.getRange(lastRow, codeCol).setValue(codigo);
}

// ── Entry point ────────────────────────────────────────────────────────
/**
 * Crea UN solo formulario con selector A/B/C.
 *   1. Alumno abre el link (uno solo para toda el aula).
 *   2. Pone su edad y elige "Encuesta A", "B" o "C" (según le indiquen).
 *   3. Ve solo las preguntas de la encuesta elegida.
 *   4. Envía.
 * En la Sheet queda una fila por alumno con edad + qué encuesta hizo +
 * respuestas del pack + código automático (P0001, P0002, …).
 */
function main() {
  const form = FormApp.create("Sami · Cuestionario de bienestar");
  form.setDescription(
    "Este cuestionario dura entre 5 y 15 minutos según cuál te toque. " +
    "Elige lo que más se acerca a cómo te has sentido. No hay respuestas " +
    "correctas o incorrectas — tus respuestas son completamente anónimas."
  );
  configurarAnonimo_(form);

  // ── Sección 0 · Intro + Edad + Selector ─────────────────────────────
  form.addSectionHeaderItem()
      .setTitle("Antes de empezar")
      .setHelpText(
        "Estas respuestas son completamente anónimas. No pedimos tu nombre " +
        "ni tu correo — solo tu edad y qué encuesta te tocó hacer."
      );

  form.addTextItem()
      .setTitle("Edad")
      .setRequired(true);

  const selector = form.addMultipleChoiceItem()
      .setTitle("¿Qué encuesta te tocó?")
      .setHelpText("Tu profesor/a te dice cuál elegir.")
      .setRequired(true);

  // ── Sección A · PHQ-A + GAD-7 ───────────────────────────────────────
  const pageA = form.addPageBreakItem()
      .setTitle("Encuesta A · Cómo te has sentido")
      .setHelpText(
        "Lee con calma y elige lo que más se acerca a cómo te has sentido. " +
        "No hay respuestas correctas o incorrectas."
      );
  pageA.setGoToPage(FormApp.PageNavigationType.SUBMIT);

  agregarGrillaInline_(
    form,
    "Cómo te has sentido",
    "Durante las últimas dos semanas, ¿con qué frecuencia te ha molestado lo siguiente?",
    PHQA,
    LABELS_03
  );
  agregarGrillaInline_(
    form,
    "Preocupación y tensión",
    "Durante las últimas dos semanas, ¿con qué frecuencia te has sentido así?",
    GAD7,
    LABELS_03
  );

  // ── Sección B · DASS-21 ─────────────────────────────────────────────
  const pageB = form.addPageBreakItem()
      .setTitle("Encuesta B · Cómo te ha ido esta semana")
      .setHelpText(
        "Lee con calma y marca cuánto te aplicó cada frase esta semana. " +
        "No hay respuestas correctas o incorrectas."
      );
  pageB.setGoToPage(FormApp.PageNavigationType.SUBMIT);

  agregarGrillaInline_(
    form,
    "Cómo te ha ido esta semana",
    "Por favor lee cada frase y marca cuánto te aplicó esta semana.",
    DASS21,
    LABELS_DASS
  );

  // ── Sección C · Frases incompletas ──────────────────────────────────
  const pageC = form.addPageBreakItem()
      .setTitle("Encuesta C · Completa las frases")
      .setHelpText(
        "Completa cada frase con lo primero que se te venga a la mente. " +
        "No hay respuestas correctas o incorrectas."
      );
  pageC.setGoToPage(FormApp.PageNavigationType.SUBMIT);

  agregarFrasesInline_(form, FRASES_SSCT);

  // ── Conectar el selector con las 3 secciones ────────────────────────
  selector.setChoices([
    selector.createChoice("Encuesta A", pageA),
    selector.createChoice("Encuesta B", pageB),
    selector.createChoice("Encuesta C", pageC),
  ]);

  // ── Vincular Sheet + trigger de código automático ───────────────────
  const ss = conectarSheetYTrigger_(form);

  Logger.log("=== Formulario único con selector A/B/C creado ===");
  Logger.log("URL pública (para los alumnos): %s", form.getPublishedUrl());
  Logger.log("Editor: %s", form.getEditUrl());
  Logger.log("Sheet:  %s", ss.getUrl());
  Logger.log(
    "Cada envío queda en la misma Sheet con código automático (P0001, " +
    "P0002, …). La columna '¿Qué encuesta te tocó?' te dice si esa fila " +
    "es A, B o C."
  );
}

// ── Form unificado PILOTO 15 MIN (A + B, sin frases) ──────────────────
/**
 * Versión recortada del cuestionario para entrar en una sola clase de 15 min
 * con 120 alumnos simultáneos. Contiene:
 *   - Edad (demografía mínima)
 *   - Pack A: PHQ-A (16 items) + GAD-7 (7 items)
 *   - Pack B: DASS-21 (21 items)
 * Total: ~10 min de llenado + 5 min de colchón.
 *
 * Se dejaron FUERA las 20 frases del Pack C — con texto libre no entra
 * en 15 min. Correrlas en una segunda sesión corta para BETO.
 */
function crearFormPiloto15min() {
  const form = FormApp.create("Sami · Cuestionario de bienestar");
  form.setDescription(
    "Este cuestionario dura unos 10 minutos. Lee con calma y elige lo que " +
    "más se acerca a cómo te has sentido. No hay respuestas correctas o " +
    "incorrectas — tus respuestas son completamente anónimas."
  );
  configurarAnonimo_(form);
  agregarDemografia_(form);

  // Parte 1 — PHQ-A + GAD-7
  agregarBloqueLikert_(
    form,
    "Parte 1 · Cómo te has sentido",
    "Durante las últimas dos semanas, ¿con qué frecuencia te ha molestado lo siguiente?",
    PHQA,
    LABELS_03
  );
  agregarBloqueLikert_(
    form,
    "Parte 1 · Preocupación y tensión",
    "Durante las últimas dos semanas, ¿con qué frecuencia te has sentido así?",
    GAD7,
    LABELS_03
  );

  // Parte 2 — DASS-21
  agregarBloqueLikert_(
    form,
    "Parte 2 · Cómo te ha ido esta semana",
    "Por favor lee cada frase y marca cuánto te aplicó esta semana.",
    DASS21,
    LABELS_DASS
  );

  const ss = conectarSheetYTrigger_(form);

  Logger.log("=== Formulario piloto 15 min creado ===");
  Logger.log(
    "Sami · Cuestionario de bienestar (A + B, sin frases)\n" +
    "  Público (para alumnos): %s\n  Editor:  %s\n  Sheet:   %s",
    form.getPublishedUrl(),
    form.getEditUrl(),
    ss.getUrl()
  );
  Logger.log(
    "Un solo enlace/QR para toda el aula. Estimado: ~10 min de llenado."
  );
}

// ── Form unificado COMPLETO (los 3 packs, ~22 min) ─────────────────────
/**
 * Crea UN solo form con los 3 packs seguidos como secciones. Usá esta si
 * tenés más de 20 min por sesión — para 15 min mirá `crearFormPiloto15min`.
 */
function crearFormUnificado() {
  const form = FormApp.create("Sami · Cuestionario de bienestar");
  form.setDescription(
    "Este cuestionario tiene 3 partes cortas (unos 20 minutos en total). " +
    "Lee con calma y elige lo que más se acerca a cómo te has sentido. " +
    "No hay respuestas correctas o incorrectas — tus respuestas son " +
    "completamente anónimas."
  );
  configurarAnonimo_(form);
  agregarDemografia_(form);

  // Parte 1 — PHQ-A + GAD-7
  agregarBloqueLikert_(
    form,
    "Parte 1 · Cómo te has sentido",
    "Durante las últimas dos semanas, ¿con qué frecuencia te ha molestado lo siguiente?",
    PHQA,
    LABELS_03
  );
  agregarBloqueLikert_(
    form,
    "Parte 1 · Preocupación y tensión",
    "Durante las últimas dos semanas, ¿con qué frecuencia te has sentido así?",
    GAD7,
    LABELS_03
  );

  // Parte 2 — DASS-21
  agregarBloqueLikert_(
    form,
    "Parte 2 · Cómo te ha ido esta semana",
    "Por favor lee cada frase y marca cuánto te aplicó esta semana.",
    DASS21,
    LABELS_DASS
  );

  // Parte 3 — Frases incompletas
  agregarBloqueFrases_(
    form,
    "Parte 3 · Completa las frases",
    "Completa cada frase con lo primero que se te venga a la mente. No hay respuestas correctas.",
    FRASES_SSCT
  );

  const ss = conectarSheetYTrigger_(form);

  Logger.log("=== Formulario unificado creado ===");
  Logger.log(
    "Sami · Cuestionario de bienestar\n" +
    "  Público (para alumnos): %s\n  Editor:  %s\n  Sheet:   %s",
    form.getPublishedUrl(),
    form.getEditUrl(),
    ss.getUrl()
  );
  Logger.log(
    "Un solo enlace / QR para toda el aula. Cada fila de la Sheet será " +
    "un alumno completo (edad + Pack A + Pack B + Pack C)."
  );
}

/**
 * Arregla los 3 forms que ya creaste sin cambiar sus URLs.
 *
 * Qué hace por cada form:
 *   1. Borra el campo "Código de participante" (si sigue existiendo).
 *   2. Borra respuestas de prueba (opcional — mirá el parámetro abajo).
 *   3. Le vincula una Google Sheet si aún no tiene.
 *   4. Instala el trigger `alRecibirRespuesta_` para autonumerar.
 *
 * PEGÁ ABAJO los 3 IDs de tus forms actuales (los sacás del log de main()).
 * El ID es la parte entre `/d/` y `/edit` de la URL del EDITOR.
 */
function actualizarFormsExistentes() {
  const formIds = [
    "1UH5Pr4uztX59lKSgWd2XVDSpX-bwAENgv3W4cARY1L4", // Pack A
    "1rKKTIVV9O9CD8_A1JPgoobVtuJlZ9gszYLlROiDwn44", // Pack B
    "12kcu4Yiqv2VEinEut6CtCZ42E6cRpLUiUIgNGAq9dT8", // Pack C
  ];
  const borrarRespuestasDePrueba = true; // ponelo en false si querés conservar respuestas ya recibidas

  Logger.log("=== Actualizando forms existentes ===");
  formIds.forEach((id) => {
    const form = FormApp.openById(id);

    // 1. Borrar los ítems que ya no queremos (código, género, y la sección
    //    vieja "Datos del participante"). Se conserva solo "Edad".
    const camposABorrar = [
      "Código de participante",
      "Género",
      "Datos del participante",
    ];
    form.getItems().forEach((item) => {
      if (camposABorrar.indexOf(item.getTitle()) !== -1) {
        form.deleteItem(item);
      }
    });

    // 2. Limpiar respuestas de prueba (para que P001 sea el primer alumno real)
    if (borrarRespuestasDePrueba) {
      form.deleteAllResponses();
    }

    // 3 + 4. Vincular Sheet + instalar trigger
    const ss = conectarSheetYTrigger_(form);

    Logger.log(
      "OK — %s\n  Público (para alumnos): %s\n  Sheet: %s",
      form.getTitle(),
      form.getPublishedUrl(),
      ss.getUrl()
    );
  });
  Logger.log(
    "Listo. Los 3 forms ahora piden solo 'Edad' + los ítems, y las Sheets " +
    "van a autonumerar P001, P002, … por orden de envío."
  );
}
