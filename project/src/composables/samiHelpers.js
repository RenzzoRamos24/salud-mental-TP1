// Sami — utilidades compartidas para vistas del estudiante (Inicio, Diario,
// Mi historial). El backend almacena la entrada como un único `texto`; el
// diseño separa título y cuerpo. Aquí concentramos esa traducción.

export const MESES = [
  "enero", "febrero", "marzo", "abril", "mayo", "junio",
  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
];
export const DIAS = [
  "domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado",
];
export const DIAS_AB = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"];

export const TAGS = {
  universidad: { label: "Universidad", color: "#5b8def" },
  animo: { label: "Ánimo", color: "#e8883a" },
  sueno: { label: "Sueño", color: "#8e6fd8" },
  gratitud: { label: "Gratitud", color: "#3aa66f" },
};

export function parseIso(iso) {
  if (!iso) return new Date(NaN);
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function todayIso() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function fmtLong(iso) {
  const d = parseIso(iso);
  const s = `${DIAS[d.getDay()]} ${d.getDate()} de ${MESES[d.getMonth()]} de ${d.getFullYear()}`;
  return s[0].toUpperCase() + s.slice(1);
}

export function fmtMonth(iso) {
  const d = parseIso(iso);
  const m = MESES[d.getMonth()];
  return `${m[0].toUpperCase()}${m.slice(1)} ${d.getFullYear()}`;
}

export function dayNum(iso) {
  return parseIso(iso).getDate();
}

export function dowAb(iso) {
  return DIAS_AB[parseIso(iso).getDay()];
}

export function isoDeFecha(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function daysBetween(a, b) {
  return Math.round((parseIso(b) - parseIso(a)) / 86400000);
}

export function wordCount(s) {
  return (s || "").trim() ? s.trim().split(/\s+/).length : 0;
}

// El backend guarda texto único. Convención Sami: la primera línea, si
// es corta (≤ 80 chars), se trata como título; el resto, como cuerpo.
// Etiqueta opcional: si la entrada termina con `\n#tag`, se extrae.
export function splitEntry(rawText) {
  const text = (rawText || "").trim();
  if (!text) return { title: "", body: "", tag: null };

  let body = text;
  let tag = null;
  const m = body.match(/\n#(universidad|animo|sueno|gratitud)\s*$/);
  if (m) {
    tag = m[1];
    body = body.slice(0, m.index).trimEnd();
  }

  const firstBreak = body.indexOf("\n");
  if (firstBreak === -1) {
    if (body.length <= 80) return { title: body, body: "", tag };
    return { title: "", body, tag };
  }
  const firstLine = body.slice(0, firstBreak).trim();
  if (firstLine && firstLine.length <= 80) {
    return { title: firstLine, body: body.slice(firstBreak + 1).trimStart(), tag };
  }
  return { title: "", body, tag };
}

export function joinEntry({ title, body, tag }) {
  let out = "";
  if (title && title.trim()) out += title.trim() + "\n\n";
  out += (body || "").trim();
  if (tag && TAGS[tag]) out += `\n#${tag}`;
  return out.trim();
}

// Convierte una entrada del backend al modelo Sami.
export function fromBackend(e) {
  const raw = e.texto != null ? e.texto : e.preview || "";
  const parts = splitEntry(raw);
  return {
    id: String(e.id),
    date: e.fecha,
    estado_animo: e.estado_animo || null,
    title: parts.title,
    body: parts.body,
    tag: parts.tag,
    _raw: raw,
    timestamp: e.timestamp || null,
  };
}

export function saludo() {
  const h = new Date().getHours();
  if (h < 12) return "Buenos días";
  if (h < 19) return "Buenas tardes";
  return "Buenas noches";
}
