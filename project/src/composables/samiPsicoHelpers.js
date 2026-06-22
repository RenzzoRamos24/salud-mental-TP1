// Sami clínico — helpers de severidad, tendencia, alertas, avatares.
// IMPORTANTE: todo label clínico usa "Posible …" — el diagnóstico
// es competencia exclusiva del profesional de salud mental.

import { parseIso, todayIso, MESES } from "./samiHelpers";

const SEV_PHQA = [
  { hasta: 4,  nivel: "Mínima",           accion: "Solo monitoreo",          instrumento: "PHQ-A" },
  { hasta: 9,  nivel: "Leve",             accion: "Autocuidado",             instrumento: "PHQ-A" },
  { hasta: 14, nivel: "Moderada",         accion: "Seguimiento",             instrumento: "PHQ-A" },
  { hasta: 19, nivel: "Moderada-severa",  accion: "Atención prioritaria",    instrumento: "PHQ-A" },
  { hasta: 27, nivel: "Severa",           accion: "Protocolo de emergencia", instrumento: "PHQ-A" },
];

const SEV_GAD7 = [
  { hasta: 4,  nivel: "Mínima",  accion: "Solo monitoreo",       instrumento: "GAD-7" },
  { hasta: 9,  nivel: "Leve",    accion: "Autocuidado",          instrumento: "GAD-7" },
  { hasta: 14, nivel: "Moderada",accion: "Seguimiento",          instrumento: "GAD-7" },
  { hasta: 21, nivel: "Severa",  accion: "Atención prioritaria", instrumento: "GAD-7" },
];

export function nivelPhqa(score) {
  return SEV_PHQA.find((r) => score <= r.hasta) || SEV_PHQA[SEV_PHQA.length - 1];
}
export function nivelGad7(score) {
  return SEV_GAD7.find((r) => score <= r.hasta) || SEV_GAD7[SEV_GAD7.length - 1];
}

/**
 * Retorna label clínico orientativo con prefijo "Posible" cuando corresponde.
 * Nunca afirma un diagnóstico — ese es rol del psicólogo.
 *   labelClinico("depresion", nivelPhqa(score))
 *   → "Posible depresión moderada-severa (PHQ-A · orientativo)"
 */
export function labelClinico(tipo, sev) {
  if (!sev || sev.nivel === "Mínima") return null;
  const nombres = {
    depresion: "depresión",
    ansiedad:  "ansiedad",
  };
  const nombre = nombres[tipo] || tipo;
  return `Posible ${nombre} ${sev.nivel.toLowerCase()} (${sev.instrumento} · orientativo)`;
}

export function sevClass(nivel) {
  if (!nivel) return "minima";
  if (/severa/i.test(nivel) && /moderada/i.test(nivel)) return "alta";
  if (/severa/i.test(nivel)) return "severa";
  if (/moderada/i.test(nivel)) return "moderada";
  if (/leve/i.test(nivel)) return "leve";
  return "minima";
}

// prioridad de riesgo: crisis > severa > moderada-severa > moderada > leve > mínima
export function riesgoEstudiante(s) {
  if (!s?.cycles?.length) return { rank: 0, label: "Sin datos", cls: "minima" };
  // Usar el ciclo cerrado con más días escritos (mayor confiabilidad clínica).
  // Si solo hay un ciclo en curso vacío, rank=0.
  const cerrados = s.cycles.filter((c) => !c.encurso && c.dias > 0);
  if (!cerrados.length) {
    const enc = s.cycles.find((c) => c.encurso && c.dias > 0);
    if (!enc) return { rank: 0, label: "Sin datos", cls: "minima" };
    cerrados.push(enc);
  }
  // El de mayor PHQ-A entre los ciclos cerrados (peor momento clínico conocido)
  const ref = cerrados.reduce((best, c) =>
    (c.phqa || 0) + (c.gad7 || 0) > (best.phqa || 0) + (best.gad7 || 0) ? c : best,
  );
  if (ref.crisis) return { rank: 5, label: "Crisis", cls: "severa" };
  const p = nivelPhqa(ref.phqa || 0);
  const g = nivelGad7(ref.gad7 || 0);
  const peor = p.hasta >= g.hasta ? p : g;
  const cls = sevClass(peor.nivel);
  const rank = { severa: 5, alta: 4, moderada: 3, leve: 2, minima: 1 }[cls] || 1;
  return { rank, label: peor.nivel, cls };
}

export function tendencia(s) {
  const cs = s?.cycles || [];
  if (cs.length < 2) return { dir: "flat", txt: "Primer ciclo" };
  const a = cs[cs.length - 2].phqa || 0;
  const b = cs[cs.length - 1].phqa || 0;
  const d = b - a;
  if (d >= 3) return { dir: "up", txt: `+${d} en PHQ-A` };
  if (d <= -3) return { dir: "down", txt: `${d} en PHQ-A` };
  return { dir: "flat", txt: "Estable" };
}

const AVATAR_COLORS = [
  "#0d9488", "#5b8def", "#e8883a", "#8e6fd8", "#3aa66f", "#d3792c",
];

export function avatarColor(id) {
  const s = String(id || "");
  let h = 0;
  for (const c of s) h = (h * 31 + c.charCodeAt(0)) % AVATAR_COLORS.length;
  return AVATAR_COLORS[h];
}

export function pCorto(iso) {
  if (!iso) return "—";
  const d = parseIso(iso);
  return `${d.getDate()} ${MESES[d.getMonth()].slice(0, 3)}`;
}

export function pRango(a, b) {
  return `${pCorto(a)} – ${pCorto(b)}`;
}

export function pHaceCuanto(iso) {
  if (!iso) return "—";
  const hoy = parseIso(todayIso());
  const dias = Math.round((hoy - parseIso(iso)) / 86400000);
  if (dias <= 0) return "hoy";
  if (dias === 1) return "ayer";
  if (dias < 7) return `hace ${dias} días`;
  if (dias < 14) return "hace 1 semana";
  return `hace ${Math.floor(dias / 7)} semanas`;
}

// ─── Construcción de alertas ─────────────────────────────────────────
export function buildAlerts(students) {
  const hoy = parseIso(todayIso());
  const out = [];
  for (const s of students || []) {
    const cs = s.cycles || [];
    if (!cs.length) continue;
    // Ciclo de referencia clínica: el de mayor puntaje entre los cerrados
    const cerrados = cs.filter((c) => !c.encurso && c.dias > 0);
    const ref = cerrados.length
      ? cerrados.reduce((b, c) => ((c.phqa || 0) + (c.gad7 || 0) > (b.phqa || 0) + (b.gad7 || 0) ? c : b))
      : cs[cs.length - 1];
    const r = riesgoEstudiante(s);
    if (ref.crisis) {
      out.push({
        tipo: "crit",
        studentId: s.id,
        t: `${s.name} — señal de crisis`,
        s: "Marcó pensamientos de autolesión en la encuesta de cierre. Requiere contacto hoy.",
        when: pHaceCuanto(ref.end),
        rank: 100,
      });
    } else if (r.cls === "severa" || r.cls === "alta") {
      out.push({
        tipo: "crit",
        studentId: s.id,
        t: `${s.name} — sintomatología ${r.label.toLowerCase()}`,
        s: `PHQ-A ${ref.phqa}/27 · GAD-7 ${ref.gad7}/21 en el ciclo ${ref.n}.`,
        when: pHaceCuanto(ref.end),
        rank: 80,
      });
    } else if (r.cls === "moderada") {
      out.push({
        tipo: "warn",
        studentId: s.id,
        t: `${s.name} — sintomatología moderada`,
        s: `PHQ-A ${ref.phqa}/27 · GAD-7 ${ref.gad7}/21 en el ciclo ${ref.n}. Seguimiento sugerido.`,
        when: pHaceCuanto(ref.end),
        rank: 50,
      });
    }
    if (s.ultimaActividad) {
      const dias = Math.round((hoy - parseIso(s.ultimaActividad)) / 86400000);
      if (dias >= 14) {
        out.push({
          tipo: "idle",
          studentId: s.id,
          t: `${s.name} — sin actividad`,
          s: `No escribe desde hace ${Math.floor(dias / 7)} semanas.`,
          when: pHaceCuanto(s.ultimaActividad),
          rank: 30,
        });
      }
    }
  }
  return out.sort((a, b) => b.rank - a.rank);
}

// Etiquetas para el desglose por ítem (versión abreviada de UI)
export const ITEMS_PHQA = [
  "Interés/placer",
  "Ánimo decaído",
  "Sueño",
  "Energía",
  "Apetito",
  "Autoimagen",
  "Concentración",
  "Movimiento/habla",
  "Pensamientos de daño",
];
export const ITEMS_GAD7 = [
  "Nervios",
  "No parar de preocuparse",
  "Preocupación excesiva",
  "Dificultad para relajarse",
  "Inquietud",
  "Irritabilidad",
  "Miedo a algo malo",
];

// Cuando el backend no aporta el desglose item-by-item, sintetizamos uno
// que sume el total observado (mismo enfoque del prototipo de diseño).
export function desglose(total, n, max, forzarUltimo) {
  const arr = Array(n).fill(0);
  let resto = total | 0;
  if (forzarUltimo) {
    arr[n - 1] = Math.min(2, max);
    resto -= arr[n - 1];
  }
  let i = 0;
  while (resto > 0) {
    const idx = i % (forzarUltimo ? n - 1 : n);
    if (arr[idx] < max) {
      arr[idx]++;
      resto--;
    }
    i++;
    if (i > 500) break;
  }
  return arr;
}
