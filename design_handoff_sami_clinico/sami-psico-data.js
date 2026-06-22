// Sami — datos del lado clínico (psicóloga: Dra. Lucía Carrasco)
// Fecha "actual": sábado 13 de junio de 2026

window.PSICO_DATA = {
  pro: { name: "Dra. Lucía Carrasco", initials: "LC", role: "Psicóloga · Bienestar estudiantil", email: "lucia.carrasco@uni.edu" },

  today: "2026-06-13",

  // Tablas de severidad (idénticas a las del estudiante)
  sevPhqa: [
    { hasta: 4, nivel: "Mínima", accion: "Solo monitoreo" },
    { hasta: 9, nivel: "Leve", accion: "Autocuidado" },
    { hasta: 14, nivel: "Moderada", accion: "Seguimiento" },
    { hasta: 19, nivel: "Moderada-severa", accion: "Atención prioritaria" },
    { hasta: 27, nivel: "Severa", accion: "Protocolo de emergencia" },
  ],
  sevGad7: [
    { hasta: 4, nivel: "Mínima", accion: "Solo monitoreo" },
    { hasta: 9, nivel: "Leve", accion: "Autocuidado" },
    { hasta: 14, nivel: "Moderada", accion: "Seguimiento" },
    { hasta: 21, nivel: "Severa", accion: "Atención prioritaria" },
  ],

  students: [
    {
      id: "s-mateo", name: "Mateo Fuentes", initials: "MF",
      carrera: "Ingeniería Civil", anio: "3er año", email: "mateo.fuentes@uni.edu",
      ultimaActividad: "2026-06-13", entradasCompartidas: false,
      cycles: [
        { n: 1, start: "2026-04-21", end: "2026-05-04", phqa: 11, gad7: 9, crisis: false, dias: 9 },
        { n: 2, start: "2026-05-09", end: "2026-05-22", phqa: 16, gad7: 13, crisis: false, dias: 11 },
        { n: 3, start: "2026-05-30", end: "2026-06-12", phqa: 21, gad7: 16, crisis: true, dias: 13 },
      ],
      notas: [
        { fecha: "2026-05-23", autor: "LC", texto: "Refiere sobrecarga por proyecto de título y problemas para dormir. Acordamos higiene del sueño y una sesión semanal." },
      ],
    },
    {
      id: "s-diego", name: "Diego Herrera", initials: "DH",
      carrera: "Derecho", anio: "2do año", email: "diego.herrera@uni.edu",
      ultimaActividad: "2026-06-11", entradasCompartidas: false,
      cycles: [
        { n: 1, start: "2026-05-02", end: "2026-05-15", phqa: 8, gad7: 7, crisis: false, dias: 8 },
        { n: 2, start: "2026-05-20", end: "2026-06-02", phqa: 13, gad7: 12, crisis: false, dias: 10 },
        { n: 3, start: "2026-06-04", end: "2026-06-17", phqa: 17, gad7: 14, crisis: false, dias: 6, encurso: true },
      ],
      notas: [],
    },
    {
      id: "s-valentina", name: "Valentina Ríos", initials: "VR",
      carrera: "Psicología", anio: "2do año", email: "valentina.rios@uni.edu",
      ultimaActividad: "2026-06-12", entradasCompartidas: true,
      cycles: [
        { n: 1, start: "2026-04-28", end: "2026-05-11", phqa: 14, gad7: 11, crisis: false, dias: 7 },
        { n: 2, start: "2026-05-12", end: "2026-05-25", phqa: 11, gad7: 9, crisis: false, dias: 6 },
        { n: 3, start: "2026-05-30", end: "2026-06-12", phqa: 8, gad7: 6, crisis: false, dias: 8 },
      ],
      notas: [
        { fecha: "2026-05-26", autor: "LC", texto: "Buena evolución. Identifica el sueño como factor clave de su ánimo. Reforzar el hábito de escritura." },
      ],
    },
    {
      id: "s-camila", name: "Camila Soto", initials: "CS",
      carrera: "Medicina", anio: "4to año", email: "camila.soto@uni.edu",
      ultimaActividad: "2026-06-10", entradasCompartidas: false,
      cycles: [
        { n: 1, start: "2026-05-05", end: "2026-05-18", phqa: 7, gad7: 8, crisis: false, dias: 9 },
        { n: 2, start: "2026-05-26", end: "2026-06-08", phqa: 6, gad7: 7, crisis: false, dias: 10 },
      ],
      notas: [],
    },
    {
      id: "s-joaquin", name: "Joaquín Morales", initials: "JM",
      carrera: "Arquitectura", anio: "1er año", email: "joaquin.morales@uni.edu",
      ultimaActividad: "2026-05-20", entradasCompartidas: false,
      cycles: [
        { n: 1, start: "2026-04-30", end: "2026-05-13", phqa: 9, gad7: 6, crisis: false, dias: 6 },
        { n: 2, start: "2026-05-15", end: "2026-05-28", phqa: 8, gad7: 5, crisis: false, dias: 4 },
      ],
      notas: [],
    },
    {
      id: "s-antonia", name: "Antonia Vega", initials: "AV",
      carrera: "Diseño", anio: "3er año", email: "antonia.vega@uni.edu",
      ultimaActividad: "2026-06-09", entradasCompartidas: false,
      cycles: [
        { n: 1, start: "2026-05-01", end: "2026-05-14", phqa: 4, gad7: 3, crisis: false, dias: 11 },
        { n: 2, start: "2026-05-26", end: "2026-06-08", phqa: 3, gad7: 4, crisis: false, dias: 12 },
      ],
      notas: [],
    },
  ],
};
