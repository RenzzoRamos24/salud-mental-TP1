// Etiquetas verbales de las escalas Likert, indexadas por su rango.
//
// Viven acá y no en una vista porque las usan dos pantallas que tienen que
// decir exactamente lo mismo: la del alumno respondiendo y la del psicólogo
// etiquetando a ciegas. Si divergen, el psicólogo juzgaría un texto distinto
// del que leyó el alumno y la comparación dejaría de ser válida.
//
// Las redacciones son las de los instrumentos validados; no se tocan sin
// revisar la fuente (ver BANCO_INSTRUMENTOS.md).

export const OPCIONES = {
  // PHQ-A, GAD-7, DASS-21
  "0-3": [
    { v: 0, label: "Nunca" },
    { v: 1, label: "Algunos días" },
    { v: 2, label: "Más de la mitad" },
    { v: 3, label: "Casi todos los días" },
  ],
  // RSES
  "1-4": [
    { v: 1, label: "Muy en desacuerdo" },
    { v: 2, label: "En desacuerdo" },
    { v: 3, label: "De acuerdo" },
    { v: 4, label: "Muy de acuerdo" },
  ],
  // WHO-5
  "0-5": [
    { v: 0, label: "En ningún momento" },
    { v: 1, label: "Algunos días" },
    { v: 2, label: "Menos de la mitad" },
    { v: 3, label: "Más de la mitad" },
    { v: 4, label: "La mayor parte" },
    { v: 5, label: "Todo el tiempo" },
  ],
  // UCLA-3
  "1-3": [
    { v: 1, label: "Casi nunca" },
    { v: 2, label: "A veces" },
    { v: 3, label: "A menudo" },
  ],
  // SRQ-20
  binaria: [
    { v: 1, label: "Sí" },
    { v: 0, label: "No" },
  ],
};

export function escalaKey(p) {
  if (p.tipo === "binaria") return "binaria";
  return `${p.likert_min}-${p.likert_max}`;
}

export function opciones(p) {
  return OPCIONES[escalaKey(p)] || [];
}

// Etiqueta verbal de un valor concreto. Si la escala no está registrada,
// devuelve el número crudo en vez de mentir con una etiqueta inventada.
export function etiquetaValor(p, valor) {
  const op = opciones(p).find((o) => o.v === valor);
  return op ? op.label : String(valor);
}
