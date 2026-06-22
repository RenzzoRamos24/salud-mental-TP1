// Sami — datos de ejemplo (estudiante: Valentina Ríos)
// Fecha "actual" del prototipo: jueves 12 de junio de 2026

window.SAMI_DATA = {
  user: { name: "Valentina Ríos", initials: "VR", email: "valentina.rios@uni.edu" },

  today: "2026-06-12",

  // Pregunta del día (rota; el prototipo usa la primera)
  prompts: [
    "¿Qué fue lo que más espacio ocupó en tu cabeza hoy?",
    "¿Hubo algún momento del día en que te sentiste tranquila?",
    "Si pudieras repetir una hora de hoy, ¿cuál sería?",
    "¿Qué te gustaría soltar antes de dormir?",
  ],

  tags: {
    universidad: { label: "Universidad", color: "#5b8def" },
    animo:       { label: "Ánimo",       color: "#e8883a" },
    sueno:       { label: "Sueño",       color: "#8e6fd8" },
    gratitud:    { label: "Gratitud",    color: "#3aa66f" },
  },

  // Ciclo de diario de 14 días (el ciclo 3 cierra hoy)
  cycle: {
    number: 3,
    start: "2026-05-30",
    length: 14,
    questions: [
      { id: "animo",  q: "¿Cómo estuvo tu ánimo hoy?",        opts: ["Muy bajo", "Bajo", "Normal", "Bien", "Muy bien"] },
      { id: "sueno",  q: "¿Qué tal dormiste anoche?",          opts: ["Muy mal", "Mal", "Regular", "Bien", "Muy bien"] },
      { id: "carga",  q: "¿Qué tan pesado se sintió el día?",  opts: ["Nada", "Poco", "Algo", "Bastante", "Mucho"] },
    ],
  },

  entries: [
    {
      id: "e12", date: "2026-06-11", tag: "universidad",
      title: "Entrega de Métodos, por fin",
      body: "Subimos el informe a las 11:48, doce minutos antes del cierre. Sofi encontró un error en la tabla de resultados a última hora y casi me da algo, pero lo arreglamos entre las dos.\n\nDespués nos quedamos en la cafetería de la facultad sin hablar de la materia ni una vez. Hacía semanas que no hacíamos eso. Me di cuenta de cuánto lo extrañaba.",
    },
    {
      id: "e11", date: "2026-06-09", tag: "sueno",
      title: "Tres de la mañana otra vez",
      body: "Me desperté a las 3 y ya no pude volver a dormirme. Me quedé repasando mentalmente la entrega del miércoles, que no depende de mí a esa hora, obviamente.\n\nTerminé escuchando un podcast hasta que aclaró. Mañana voy a intentar dejar el teléfono fuera de la pieza, a ver si es eso.",
    },
    {
      id: "e10", date: "2026-06-08", tag: "animo",
      title: "Lunes gris pero manejable",
      body: "Día plano. No pasó nada malo, pero tampoco nada que me levantara. Caminé hasta la universidad en vez de tomar el bus y eso ayudó un poco; el barrio estaba tranquilo y olía a pan.\n\nNoto que los lunes me cuestan más desde que empezó el semestre. Lo dejo anotado para verlo después.",
    },
    {
      id: "e09", date: "2026-06-06", tag: "gratitud",
      title: "La llamada con mamá",
      body: "Hablamos casi una hora. Le conté lo del laboratorio y se rió tanto que terminé riéndome yo también. No me había dado cuenta de cuánto necesitaba contarle las cosas a alguien que no estuviera dentro del problema.\n\nAnoto esto para releerlo cuando esté insoportable conmigo misma.",
    },
    {
      id: "e08", date: "2026-06-04", tag: "universidad",
      title: "Pequeña victoria con la beca",
      body: "Por fin salió el trámite de la beca. Tres semanas de idas y vueltas por un sello que faltaba.\n\nMe lo anoto como victoria del día porque las cosas de papeles me agotan más que cualquier parcial. Y porque la próxima vez que piense que no avanzo, quiero acordarme de que esto también costó y salió.",
    },
    {
      id: "e07", date: "2026-05-30", tag: "animo",
      title: "Sábado en cámara lenta",
      body: "Me quedé en casa casi todo el día y no me sentí culpable, que ya es un avance. Ordené la pieza, cociné de verdad (no fideos) y vi una película entera sin mirar el teléfono.\n\nA veces se me olvida que descansar también cuenta como hacer algo.",
    },
    {
      id: "e06", date: "2026-05-27", tag: "universidad",
      title: "El parcial de Estadística",
      body: "Salí del parcial sin saber si me fue bien o mal, que es la peor sensación. Dos preguntas las dejé a medias por administrar mal el tiempo.\n\nLo que sí: no me bloqueé como en marzo. Respiré, salté la pregunta y volví después. Eso antes no me salía.",
    },
    {
      id: "e05", date: "2026-05-24", tag: "gratitud",
      title: "Domingo de feria",
      body: "Fui a la feria con Agus y compramos frutillas que estaban absurdamente buenas. Caminamos sin rumbo como dos horas.\n\nNo todo tiene que ser productivo. Hoy fue un buen día y no hice nada importante.",
    },
    {
      id: "e04", date: "2026-05-21", tag: "sueno",
      title: "Semana de dormir mejor",
      body: "Tres noches seguidas durmiendo antes de la una. La diferencia en el humor es ridícula: hoy un compañero dijo algo que el martes pasado me habría arruinado la mañana y hoy ni me rozó.\n\nQuiero acordarme de esto la próxima vez que 'una serie más' parezca buena idea.",
    },
    {
      id: "e03", date: "2026-05-18", tag: "animo",
      title: "Hablé en clase",
      body: "Levanté la mano en Teoría Social y di mi opinión delante de todos. Me tembló un poco la voz al principio pero la terminé. El profesor retomó mi punto después, así que tan mal no estuvo.\n\nHace un año esto era impensable. Lo escribo para no olvidarlo.",
    },
    {
      id: "e02", date: "2026-05-15", tag: "universidad",
      title: "Demasiadas cosas a la vez",
      body: "Hoy sentí que el semestre se me venía encima: dos entregas, el parcial, y encima el trámite de la beca. Hice una lista y la verdad es que en papel parece menos que en mi cabeza.\n\nVoy a partirlo por días. Mañana solo existe el informe, lo demás no.",
    },
    {
      id: "e01", date: "2026-05-12", tag: "gratitud",
      title: "Primera entrada",
      body: "Probando esto del diario. La psicóloga del campus me lo recomendó y le tengo poca fe, pero bueno, acá estoy.\n\nSi funciona la mitad de lo que promete, me conformo.",
    },
  ],

  // Encuesta de cierre de ciclo: 9 ítems PHQ-A + 7 ítems GAD-7
  closeSurvey: {
    likert: [
      { v: 0, label: "Nunca", desc: "Ningún día" },
      { v: 1, label: "Algunos días", desc: "Varios días" },
      { v: 2, label: "Más de la mitad de los días", desc: "Mayoría de días" },
      { v: 3, label: "Casi todos los días", desc: "Casi a diario" },
    ],
    questions: [
      { mod: "PHQ-A", n: 1, q: "Cuéntame, en estas últimas semanas ¿cómo has estado con las cosas que antes te gustaban —música, salir, hobbies, estudiar—? ¿Sigues disfrutándolas como antes?" },
      { mod: "PHQ-A", n: 2, q: "¿Y tu ánimo cómo ha estado? Quiero saber si te has sentido decaído/a, triste o sin esperanza estos días." },
      { mod: "PHQ-A", n: 3, q: "Hablemos un poco de tu sueño. ¿Has estado durmiendo bien, te cuesta conciliarlo, o quizás duermes más de la cuenta?" },
      { mod: "PHQ-A", n: 4, q: "¿Y la energía? ¿Sientes que tienes fuerzas para tu día a día, o has estado más cansado/a de lo normal, incluso después de descansar?" },
      { mod: "PHQ-A", n: 5, q: "Cuéntame, ¿cómo va tu apetito? ¿Comes parecido a siempre, o has notado que comes menos —o más— de lo normal?" },
      { mod: "PHQ-A", n: 6, q: "A veces uno se siente mal consigo mismo —como si no fuera suficiente, o como si le hubiera fallado a alguien importante. ¿Te ha pasado algo así estas semanas?" },
      { mod: "PHQ-A", n: 7, q: "¿Cómo va tu concentración? Por ejemplo, cuando lees algo, ves una serie o estás en clase, ¿logras mantenerte enfocado/a?" },
      { mod: "PHQ-A", n: 8, q: "Cuéntame si has notado algo distinto en cómo te mueves o hablas: ¿alguien te ha dicho que estás más lento/a de lo usual, o tú sientes que no puedes parar de moverte?" },
      { mod: "PHQ-A", n: 9, q: "Esta pregunta la hago con cuidado, porque me importa cómo estás. ¿En estas semanas has tenido pensamientos de hacerte daño, de no estar, o de que sería mejor desaparecer? Puedes responder con confianza, esto es para cuidarte." },
      { mod: "GAD-7", n: 1, q: "Cuéntame cómo has estado con los nervios. ¿Te has sentido más ansioso/a o con los nervios de punta últimamente?" },
      { mod: "GAD-7", n: 2, q: "Y cuando empiezas a preocuparte, ¿logras parar de pensar en eso, o sientes que la preocupación se te escapa de las manos?" },
      { mod: "GAD-7", n: 3, q: "¿Te ha pasado que te preocupas por muchas cosas a la vez —los estudios, la familia, el futuro, la salud— y todo se junta en tu cabeza?" },
      { mod: "GAD-7", n: 4, q: "Hablemos del cuerpo: ¿logras relajarte, o sientes que estás todo el tiempo tenso/a, con el cuerpo rígido o sin poder desconectar?" },
      { mod: "GAD-7", n: 5, q: "¿Has sentido como una inquietud por dentro, como si no pudieras quedarte quieto/a, ni siquiera cuando intentas descansar?" },
      { mod: "GAD-7", n: 6, q: "Cuéntame, ¿has estado más irritable o de mal humor estos días? Como si las cosas pequeñas te fastidiaran más de lo normal." },
      { mod: "GAD-7", n: 7, q: "A veces uno tiene la sensación de que algo malo va a pasar, sin saber muy bien qué. ¿Te ha pasado algo así últimamente?" },
    ],
    sevPhqa: [
      { hasta: 4, nivel: "Mínima", accion: "Solo monitoreo" },
      { hasta: 9, nivel: "Leve", accion: "Recomendaciones de autocuidado" },
      { hasta: 14, nivel: "Moderada", accion: "Alerta al psicólogo" },
      { hasta: 19, nivel: "Moderada-severa", accion: "Alerta urgente" },
      { hasta: 27, nivel: "Severa", accion: "Protocolo de emergencia" },
    ],
    sevGad7: [
      { hasta: 4, nivel: "Mínima", accion: "Solo monitoreo" },
      { hasta: 9, nivel: "Leve", accion: "Recomendaciones de autocuidado" },
      { hasta: 14, nivel: "Moderada", accion: "Alerta al psicólogo" },
      { hasta: 21, nivel: "Severa", accion: "Alerta urgente" },
    ],
  },

  resources: {
    urgent: [
      { name: "Línea de apoyo universitaria", desc: "Atención psicológica para estudiantes, gratuita y confidencial.", phone: "0800 222 5462", hours: "Lun–Vie · 8 a 20 h" },
      { name: "Línea de la vida", desc: "Contención en crisis, cualquier día a cualquier hora.", phone: "135", hours: "24 horas, todos los días" },
      { name: "Emergencias", desc: "Si vos o alguien más está en peligro inmediato.", phone: "911", hours: "24 horas" },
    ],
    tips: [
      { title: "Cómo releer tu diario sin juzgarte", read: "4 min", desc: "Releer entradas viejas puede ser incómodo. Algunas ideas para hacerlo con un poco más de amabilidad." },
      { title: "Dormir mal una semana no es 'no saber dormir'", read: "6 min", desc: "Qué dice la evidencia sobre el sueño en época de exámenes, y qué probar primero." },
      { title: "Tres líneas también cuentan", read: "3 min", desc: "Por qué las entradas cortas sostienen el hábito mejor que las largas." },
      { title: "Cuándo conviene pedir una cita", read: "5 min", desc: "Señales de que hablar con alguien del equipo de bienestar puede ayudarte más que seguir solo." },
    ],
  },
};
