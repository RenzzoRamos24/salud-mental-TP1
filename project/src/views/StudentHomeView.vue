<script setup>
import { ref, computed, onMounted, reactive } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import AppShellAlumno from "../components/AppShellAlumno.vue";

const router = useRouter();
const user = computed(() => authStore.state.user);
const view = ref("inicio");

const crumbs = {
  inicio: "Panel del Alumno",
  cuestionario: "Cuestionario",
  reuniones: "Reuniones con el psicólogo",
  recursos: "Recursos de apoyo",
  bienestar: "Mi bienestar",
  perfil: "Mi Perfil",
};
const crumb = computed(() => crumbs[view.value] || "Panel del Alumno");

function changeView(v) {
  if (crumbs[v]) view.value = v;
}

// ─── DATOS BACKEND ───
const cuestionarios = ref([]);
const citas = ref([]);
const recursos = ref([]);
const psicologo = ref(null);
const slotsBackend = ref([]);
const cargando = ref(true);

async function cargarTodo() {
  cargando.value = true;
  try {
    const [cs, ct, rs, ps, sl] = await Promise.all([
      api.misCuestionarios().catch(() => []),
      api.misCitas().catch(() => []),
      api.listarContenidos().catch(() => []),
      api.miPsicologo().catch(() => ({ asignado: false })),
      api.slotsSugeridos(4).catch(() => []),
    ]);
    cuestionarios.value = cs || [];
    citas.value = ct || [];
    recursos.value = rs || [];
    psicologo.value = ps?.asignado ? ps : null;
    slotsBackend.value = sl || [];
  } finally {
    cargando.value = false;
  }
}
onMounted(cargarTodo);

// ─── KPIs ───
const cuestEnviados = computed(
  () => cuestionarios.value.filter((c) => c.estado === "completado" || c.estado === "revisado").length,
);
const cuestPendientes = computed(
  () => cuestionarios.value.filter((c) => c.estado === "pendiente" || c.estado === "en_progreso"),
);

const ahora = new Date();
const proximaCita = computed(() => {
  const futuras = citas.value
    .filter((c) => c.estado !== "cancelada" && c.estado !== "completada")
    .filter((c) => {
      const dt = new Date(`${c.fecha}T${c.hora || "00:00"}:00`);
      return dt >= new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate());
    })
    .sort((a, b) => {
      const da = `${a.fecha} ${a.hora}`, db = `${b.fecha} ${b.hora}`;
      return da < db ? -1 : 1;
    });
  return futuras[0] || null;
});

const citasFuturas = computed(() => {
  const hoy = new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate());
  return citas.value
    .filter((c) => c.estado !== "cancelada")
    .filter((c) => new Date(`${c.fecha}T00:00:00`) >= hoy)
    .sort((a, b) => (`${a.fecha} ${a.hora}` < `${b.fecha} ${b.hora}` ? -1 : 1));
});
const citasPasadas = computed(() => {
  const hoy = new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate());
  return citas.value
    .filter((c) => new Date(`${c.fecha}T00:00:00`) < hoy || c.estado === "completada")
    .sort((a, b) => (`${a.fecha} ${a.hora}` < `${b.fecha} ${b.hora}` ? 1 : -1));
});

const proximaEnMin = computed(() => {
  if (!proximaCita.value) return null;
  const dt = new Date(`${proximaCita.value.fecha}T${proximaCita.value.hora || "00:00"}:00`);
  const diff = Math.round((dt - new Date()) / 60000);
  if (diff < 0 || diff > 60) return null;
  return diff;
});

// Habilitamos "Unirse" sólo dentro de la ventana [-5, +15] minutos.
function puedeUnirseACita(c) {
  if (!c || c.modalidad !== "online") return false;
  const dt = new Date(`${c.fecha}T${c.hora || "00:00"}:00`);
  const diff = Math.round((dt - new Date()) / 60000);
  return diff >= -5 && diff <= 15;
}
const puedeUnirse = computed(() => puedeUnirseACita(citasFuturas.value[0]));
const tiempoParaUnirse = computed(() => {
  const c = citasFuturas.value[0];
  if (!c) return null;
  const dt = new Date(`${c.fecha}T${c.hora || "00:00"}:00`);
  const diff = Math.round((dt - new Date()) / 60000);
  if (diff < -5) return "Sesión finalizada";
  if (diff <= 15) return "Listo para unirse";
  if (diff < 60) return `Disponible en ${diff} min`;
  const hrs = Math.round(diff / 60);
  if (hrs < 24) return `Disponible en ${hrs} h`;
  return `Disponible el día de la cita`;
});

// ─── BIENESTAR (mood en localStorage) ───
const moodKey = computed(() => `sami_mood_${user.value?.id || "anon"}`);
const moodMap = { muy_mal: 1, mal: 2, regular: 3, bien: 4, muy_bien: 5 };
const moodLabel = { muy_mal: "Muy mal", mal: "Mal", regular: "Regular", bien: "Bien", muy_bien: "Muy bien" };
const moodHistory = reactive(JSON.parse(localStorage.getItem(`mood_history`) || "{}"));
function readMood() {
  try {
    const raw = localStorage.getItem(moodKey.value);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}
const moodData = reactive(readMood());

function todayKey() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function pickMood(k) {
  moodData[todayKey()] = k;
  localStorage.setItem(moodKey.value, JSON.stringify(moodData));
}
const moodHoy = computed(() => moodData[todayKey()] || null);

// últimos 7 días (Lun→Dom de la semana en curso)
const semanaDias = computed(() => {
  const out = [];
  const d = new Date();
  const dow = (d.getDay() + 6) % 7; // 0=Lun
  const inicio = new Date(d);
  inicio.setDate(d.getDate() - dow);
  for (let i = 0; i < 7; i++) {
    const x = new Date(inicio);
    x.setDate(inicio.getDate() + i);
    const key = `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`;
    const m = moodData[key];
    out.push({
      key,
      level: m ? moodMap[m] : 0,
      label: ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][i],
      isToday: key === todayKey(),
    });
  }
  return out;
});

const animoPromedio = computed(() => {
  const vals = semanaDias.value.map((d) => d.level).filter((v) => v > 0);
  if (!vals.length) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
});
const animoTexto = computed(() => {
  const p = animoPromedio.value;
  if (p == null) return "—";
  if (p >= 4.3) return "Muy bien";
  if (p >= 3.5) return "Bien";
  if (p >= 2.5) return "Regular";
  if (p >= 1.5) return "Mal";
  return "Muy mal";
});
const racha = computed(() => {
  let n = 0;
  for (let i = 6; i >= 0; i--) {
    if (semanaDias.value[i].level > 0) n++;
    else break;
  }
  return n;
});

// ─── MENSAJE DEL PSICÓLOGO (último resumen_para_estudiante) ───
const mensajePsicologo = computed(() => {
  const citaConMsg = citas.value
    .filter((c) => c.resumen_para_estudiante)
    .sort((a, b) => {
      const da = a.completada_at || `${a.fecha}T${a.hora || "00:00"}`;
      const db = b.completada_at || `${b.fecha}T${b.hora || "00:00"}`;
      return da < db ? 1 : -1;
    })[0];
  if (!citaConMsg) return null;
  return {
    texto: citaConMsg.resumen_para_estudiante,
    fecha: citaConMsg.completada_at || citaConMsg.fecha,
    psicologo: psicologo.value
      ? `Psic. ${psicologo.value.nombre} ${psicologo.value.apellido}`
      : "Tu psicólogo",
  };
});

// ─── TIMELINE "TU PROCESO" — hitos reales del backend ───
const timeline = computed(() => {
  const items = [];

  // próxima cita
  if (citasFuturas.value[0]) {
    const c = citasFuturas.value[0];
    items.push({
      tipo: "cita_proxima",
      fecha: `${c.fecha}T${c.hora || "00:00"}:00`,
      titulo: "Próxima sesión",
      detalle: `${fmtFechaSimple(c.fecha)} · ${c.hora} · ${c.modalidad === "online" ? "Videollamada" : "Presencial"}`,
      icono: "session",
      futuro: true,
    });
  }

  // citas completadas
  citas.value
    .filter((c) => c.estado === "completada" || c.completada_at)
    .slice(0, 3)
    .forEach((c) => {
      items.push({
        tipo: "cita_completada",
        fecha: c.completada_at || `${c.fecha}T${c.hora || "00:00"}:00`,
        titulo: "Sesión realizada",
        detalle: psicologo.value
          ? `Con Psic. ${psicologo.value.nombre} · ${fmtFechaSimple(c.fecha)}`
          : fmtFechaSimple(c.fecha),
        icono: "session",
      });
    });

  // cuestionarios completados/revisados
  cuestionarios.value
    .filter((c) => c.estado === "completado" || c.estado === "revisado")
    .slice(0, 3)
    .forEach((c) => {
      items.push({
        tipo: "cuestionario",
        fecha: c.completada_at || c.asignada_at,
        titulo: c.estado === "revisado" ? "Tu psicólogo revisó tu cuestionario" : "Cuestionario completado",
        detalle: c.plantilla_nombre || "Bienestar",
        icono: "doc",
      });
    });

  // primer registro (cuenta)
  if (user.value?.created_at && items.length < 4) {
    items.push({
      tipo: "inicio",
      fecha: user.value.created_at,
      titulo: "Comenzaste tu proceso en Sami",
      detalle: "Bienvenida/o a tu espacio de bienestar",
      icono: "spark",
    });
  }

  return items
    .sort((a, b) => (a.fecha < b.fecha ? 1 : -1))
    .slice(0, 6);
});

// ─── ANIMO TENDENCIA (para KPI) ───
const animoTendencia = computed(() => {
  const vals = semanaDias.value.map((d) => d.level).filter((v) => v > 0);
  if (vals.length < 2) return null;
  const mid = Math.floor(vals.length / 2);
  const a = vals.slice(0, mid).reduce((x, y) => x + y, 0) / Math.max(1, mid);
  const b = vals.slice(mid).reduce((x, y) => x + y, 0) / Math.max(1, vals.length - mid);
  if (b - a > 0.3) return "↑ mejor";
  if (a - b > 0.3) return "↓ atención";
  return "→ estable";
});

// ─── FILTROS RECURSOS ───
const filtroRecurso = ref("todos");
const filtros = ["Todos", "Estrés", "Sueño", "Ansiedad", "Mindfulness"];
const recursosFiltrados = computed(() => {
  if (filtroRecurso.value === "todos") return recursos.value;
  const k = filtroRecurso.value.toLowerCase();
  return recursos.value.filter(
    (r) =>
      (r.categoria || "").toLowerCase().includes(k) ||
      (r.titulo || "").toLowerCase().includes(k),
  );
});

// ─── SOLICITAR CITA ───
const slots = computed(() => slotsBackend.value);
const agendando = ref(false);
const agendaMsg = ref("");
async function agendar(slot) {
  agendando.value = true;
  agendaMsg.value = "";
  try {
    await api.solicitarCita({
      fecha: slot.fecha,
      hora: slot.hora,
      modalidad: slot.modalidad_sugerida || "online",
      motivo: "Solicitud desde Mi Panel",
    });
    agendaMsg.value = "¡Listo! Tu psicólogo confirmará pronto.";
    await cargarTodo();
  } catch (e) {
    agendaMsg.value = e?.response?.data?.detail || "No se pudo agendar.";
  } finally {
    agendando.value = false;
  }
}

// ─── COMENZAR CUESTIONARIO ───
function comenzarCuestionario() {
  if (cuestPendientes.value.length > 0) {
    router.push({ name: "responder", params: { id: cuestPendientes.value[0].id } });
  } else {
    router.push({ name: "mis-cuestionarios" });
  }
}

// ─── SOS ───
const sosEnviando = ref(false);
const sosMsg = ref("");
async function activarSOS(origen = "panel") {
  if (sosEnviando.value) return;
  sosEnviando.value = true;
  sosMsg.value = "";
  try {
    await api.activarSOS({ origen, mensaje: "Solicitud de apoyo desde el panel" });
    sosMsg.value = "Tu psicólogo fue alertado. Te contactará pronto.";
  } catch {
    sosMsg.value = "No se pudo enviar el SOS. Llama a la línea 113.";
  } finally {
    sosEnviando.value = false;
  }
}

// ─── PREFERENCIAS (localStorage) ───
const prefsKey = computed(() => `sami_prefs_${user.value?.id || "anon"}`);
const prefs = reactive(
  JSON.parse(
    localStorage.getItem(`sami_prefs_${user.value?.id || "anon"}`) ||
      '{"recordatorios":true,"correo":true,"privado":false}',
  ),
);
function togglePref(k) {
  prefs[k] = !prefs[k];
  localStorage.setItem(prefsKey.value, JSON.stringify(prefs));
}

// ─── CERRAR SESIÓN ───
async function cerrarSesion() {
  await api.logout().catch(() => {});
  authStore.clear();
  router.push("/login");
}

// ─── UTILIDADES ───
function fmtFecha(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric" });
}
function fmtFechaSimple(yyyymmdd) {
  if (!yyyymmdd) return "";
  const [y, m, d] = yyyymmdd.split("-");
  const dt = new Date(+y, +m - 1, +d);
  return dt.toLocaleDateString("es-PE", { weekday: "short", day: "2-digit", month: "short" });
}
function diaCorto(yyyymmdd) {
  if (!yyyymmdd) return "";
  const [y, m, d] = yyyymmdd.split("-");
  const dt = new Date(+y, +m - 1, +d);
  return {
    dia: dt.toLocaleDateString("es-PE", { weekday: "short" }),
    num: d,
    mes: dt.toLocaleDateString("es-PE", { month: "short" }),
  };
}
function moodEmojiForHistory(estado) {
  if (estado === "revisado") return { bg: "#e6f5f0", color: "#1aa896" };
  if (estado === "completado") return { bg: "#e6f5f0", color: "#1aa896" };
  if (estado === "en_progreso") return { bg: "#fbf7e6", color: "#c2a02a" };
  return { bg: "#f4f6f6", color: "#7c8b90" };
}

// label dinámico del KPI próxima reunión
const kpiProxima = computed(() => {
  if (!proximaCita.value) return { titulo: "—", sub: "Sin reuniones", chip: "—" };
  const dt = new Date(`${proximaCita.value.fecha}T${proximaCita.value.hora || "00:00"}:00`);
  const hoy = new Date();
  const esHoy = dt.toDateString() === hoy.toDateString();
  const titulo = esHoy
    ? "Hoy"
    : dt.toLocaleDateString("es-PE", { day: "2-digit", month: "short" });
  const psicNombre = proximaCita.value.psicologo_nombre || psicologo.value?.nombre || "Psicóloga";
  return { titulo, sub: `Psic. ${psicNombre}`, chip: proximaCita.value.hora || "--:--" };
});

const recursosPorTipo = (categoria) => {
  const map = {
    pdf:   { bg: "#fdecec", color: "#e0524c", icon: "doc" },
    video: { bg: "#eaf0fb", color: "#3a78b3", icon: "play" },
    audio: { bg: "#efeafa", color: "#7a5cc4", icon: "wave" },
    actividad: { bg: "#fef3e2", color: "#d98a1f", icon: "book" },
    articulo:  { bg: "#e3f3ef", color: "#0e8d7e", icon: "page" },
  };
  const k = (categoria || "").toLowerCase();
  if (k.includes("video")) return map.video;
  if (k.includes("audio")) return map.audio;
  if (k.includes("activ")) return map.actividad;
  if (k.includes("pdf") || k.includes("guía") || k.includes("guia")) return map.pdf;
  return map.articulo;
};
</script>

<template>
  <AppShellAlumno :view="view" :crumb="crumb" @change-view="changeView">
    <!-- ═════════ INICIO ═════════ -->
    <div v-if="view === 'inicio'" class="al-grid-main">
      <div class="al-col-left">
        <!-- KPIs -->
        <div class="al-kpis">
          <div class="al-card al-kpi">
            <div class="al-kpi__head">
              <div class="al-kpi__icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/></svg>
              </div>
              <div>
                <div class="al-kpi__num">{{ animoTexto }}</div>
                <div class="al-kpi__lbl">Estado de ánimo</div>
              </div>
            </div>
            <div class="al-kpi__foot">
              <a class="al-link" @click="changeView('bienestar')">
                Mi bienestar
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
              </a>
              <div class="al-kpi__right">
                <div class="al-kpi__trend">{{ animoTendencia || "registra hoy" }}</div>
                <div class="al-chip-soft">esta semana</div>
              </div>
            </div>
          </div>

          <div class="al-card al-kpi">
            <div class="al-kpi__head">
              <div class="al-kpi__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>
              </div>
              <div>
                <div class="al-kpi__num">{{ cuestEnviados }}</div>
                <div class="al-kpi__lbl">Cuestionarios enviados</div>
              </div>
            </div>
            <div class="al-kpi__foot">
              <a class="al-link" @click="changeView('cuestionario')">
                Historial
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
              </a>
              <div class="al-kpi__right">
                <div class="al-kpi__trend">{{ cuestPendientes.length }} pend.</div>
                <div class="al-chip-soft">por responder</div>
              </div>
            </div>
          </div>

          <div class="al-card al-kpi">
            <div class="al-kpi__head">
              <div class="al-kpi__icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M15 10l5-3v10l-5-3v-4z"/><rect x="3" y="6" width="12" height="12" rx="2"/></svg>
              </div>
              <div>
                <div class="al-kpi__num">{{ kpiProxima.titulo }}</div>
                <div class="al-kpi__lbl">Próxima reunión</div>
              </div>
            </div>
            <div class="al-kpi__foot">
              <a class="al-link" @click="changeView('reuniones')">
                Ver agenda
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
              </a>
              <div class="al-kpi__right">
                <div class="al-kpi__trend">{{ kpiProxima.chip }}</div>
                <div class="al-chip-soft">{{ kpiProxima.sub }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Acceso cuestionario -->
        <div class="al-card al-quizcta">
          <div class="al-quizcta__icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>
          </div>
          <div class="al-quizcta__txt">
            <div class="al-quizcta__title">Cuestionario de bienestar</div>
            <div class="al-quizcta__sub">
              <template v-if="cuestPendientes.length">
                Tienes {{ cuestPendientes.length }} pendiente{{ cuestPendientes.length === 1 ? '' : 's' }}. Te toma poco tiempo.
              </template>
              <template v-else>
                No tienes cuestionarios pendientes. Mira tu historial.
              </template>
            </div>
          </div>
          <button class="al-btn-primary" @click="comenzarCuestionario">
            {{ cuestPendientes.length ? "Comenzar cuestionario" : "Ver historial" }}
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </button>
        </div>

        <!-- Recursos -->
        <div class="al-card">
          <div class="al-section-head">
            <div class="al-section-title">Recursos de apoyo</div>
            <a class="al-link" @click="changeView('recursos')">Ver todos</a>
          </div>
          <div v-if="recursos.length === 0" class="al-empty">
            Aún no hay recursos publicados.
          </div>
          <div v-else class="al-recursos-grid-mini">
            <a
              v-for="r in recursos.slice(0, 4)"
              :key="r.id"
              href="#"
              class="al-recurso-mini"
              @click.prevent="r.url ? window.open(r.url, '_blank') : null"
            >
              <div
                class="al-recurso-mini__icon"
                :style="{ background: recursosPorTipo(r.categoria).bg, color: recursosPorTipo(r.categoria).color }"
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
              </div>
              <div class="al-recurso-mini__txt">
                <div class="al-recurso-mini__title">{{ r.titulo }}</div>
                <div class="al-recurso-mini__sub">{{ r.categoria || "Recurso" }}</div>
              </div>
            </a>
          </div>
        </div>
      </div>

      <div class="al-col-right">
        <!-- SOS — sólo emergencia -->
        <div id="sos-card" class="al-sos">
          <div class="al-sos__bubble"></div>
          <div class="al-sos__head">
            <div class="al-sos__icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V7l8-4z"/><path d="M12 9v4M12 16h.01"/></svg>
            </div>
            <div>
              <div class="al-sos__title">SOS · Ayuda</div>
              <div class="al-sos__sub">Sólo en casos de emergencia</div>
            </div>
          </div>
          <a href="tel:113" class="al-sos__main">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3.1-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.4-1.2a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>
            Llamar a la línea 113
          </a>
        </div>

        <!-- Reuniones -->
        <div class="al-card">
          <div class="al-section-head">
            <div class="al-section-title">Reuniones con el psicólogo</div>
            <a class="al-link" @click="changeView('reuniones')">Agenda</a>
          </div>

          <div v-if="proximaCita" class="al-live">
            <div class="al-live__badge">
              <span class="al-live__dot"></span>
              {{ proximaEnMin != null ? `EN VIVO EN ${proximaEnMin} MIN` : "PRÓXIMA" }}
            </div>
            <div class="al-live__title">Sesión con tu psicólogo</div>
            <div class="al-live__meta">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>
              {{ fmtFechaSimple(proximaCita.fecha) }} · {{ proximaCita.hora }} · {{ proximaCita.modalidad }}
            </div>
            <button
              class="al-btn-primary al-btn-full"
              :class="{ 'al-btn-disabled': !puedeUnirseACita(proximaCita) }"
              :disabled="!puedeUnirseACita(proximaCita)"
              @click="puedeUnirseACita(proximaCita) ? null : null"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 10l5-3v10l-5-3v-4z"/><rect x="3" y="6" width="12" height="12" rx="2"/></svg>
              {{ puedeUnirseACita(proximaCita) ? "Unirse a la videollamada" : (proximaEnMin != null ? `Disponible en ${proximaEnMin} min` : "Aún no disponible") }}
            </button>
          </div>
          <div v-else class="al-empty">
            No tienes reuniones próximas. Agenda una desde la vista Reuniones.
          </div>

          <div class="al-meeting-list">
            <div
              v-for="c in citasFuturas.slice(proximaCita ? 1 : 0, proximaCita ? 3 : 2)"
              :key="c.id"
              class="al-meeting-row"
            >
              <div class="al-mini-avatar">
                {{ (c.estudiante_nombre || psicologo?.nombre || "P")[0] }}
              </div>
              <div class="al-meeting-row__txt">
                <div class="al-meeting-row__title">{{ c.notas || "Sesión" }}</div>
                <div class="al-meeting-row__sub">
                  {{ fmtFechaSimple(c.fecha) }} · {{ c.hora }}
                </div>
              </div>
              <span
                class="al-chip"
                :class="c.modalidad === 'online' ? 'al-chip--teal' : 'al-chip--amber'"
              >
                {{ c.modalidad === "online" ? "Online" : "Presencial" }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Tu proceso (timeline horizontal) -->
      <div class="al-card al-fullwidth">
        <div class="al-section-head">
          <div class="al-section-title">Tu proceso</div>
          <a class="al-link" @click="changeView('bienestar')">Ver completo</a>
        </div>
        <div v-if="timeline.length === 0" class="al-empty">
          Cuando respondas tu primer cuestionario o tengas una sesión, vas a ver tu recorrido acá.
        </div>
        <div v-else class="al-htimeline">
          <div
            v-for="(t, i) in timeline.slice(0, 5)"
            :key="i"
            class="al-htl-step"
            :class="{ 'al-htl-step--future': t.futuro }"
          >
            <div class="al-htl-dot">
              <svg v-if="t.icono === 'session'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 10l5-3v10l-5-3v-4z"/><rect x="3" y="6" width="12" height="12" rx="2"/></svg>
              <svg v-else-if="t.icono === 'doc'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l2.4 5.6L20 8l-4.5 4.3L17 18l-5-3-5 3 1.5-5.7L4 8l5.6-.4z"/></svg>
            </div>
            <div class="al-htl-line" v-if="i < Math.min(timeline.length, 5) - 1"></div>
            <div class="al-htl-body">
              <div class="al-htl-title">{{ t.titulo }}</div>
              <div class="al-htl-detail">{{ t.detalle }}</div>
              <div class="al-htl-date">{{ fmtFecha(t.fecha) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═════════ CUESTIONARIO ═════════ -->
    <div v-else-if="view === 'cuestionario'" class="al-grid-2col">
      <div class="al-col-left">
        <div class="al-hero">
          <div class="al-hero__title">¿Tienes alguna novedad?</div>
          <div class="al-hero__txt">
            Responde el cuestionario que te asignó tu psicólogo. Es confidencial y te ayuda a contarle cómo te sientes.
          </div>
        </div>
        <div class="al-card al-cta-center">
          <div class="al-cta-center__icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>
          </div>
          <div class="al-cta-center__title">Cuestionario de bienestar</div>
          <div class="al-cta-center__sub">
            <template v-if="cuestPendientes.length">
              Tienes {{ cuestPendientes.length }} pendiente{{ cuestPendientes.length === 1 ? '' : 's' }}. Responde cuando estés listo/a.
            </template>
            <template v-else>
              No tienes cuestionarios pendientes en este momento.
            </template>
          </div>
          <button class="al-btn-primary al-btn-lg" @click="comenzarCuestionario">
            {{ cuestPendientes.length ? "Comenzar cuestionario" : "Ver historial" }}
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </button>
        </div>
      </div>

      <div class="al-col-right">
        <div class="al-card">
          <div class="al-side-title">Cuestionarios enviados</div>
          <div v-if="cuestionarios.length === 0" class="al-empty">
            Todavía no has respondido cuestionarios.
          </div>
          <div v-else class="al-history-list">
            <div v-for="c in cuestionarios.slice(0, 6)" :key="c.id" class="al-history-row">
              <div
                class="al-history-row__icon"
                :style="{ background: moodEmojiForHistory(c.estado).bg, color: moodEmojiForHistory(c.estado).color }"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/></svg>
              </div>
              <div class="al-history-row__txt">
                <div class="al-history-row__title">{{ c.plantilla_nombre || "Cuestionario" }}</div>
                <div class="al-history-row__sub">
                  {{ c.completada_at ? fmtFecha(c.completada_at) : fmtFecha(c.asignada_at) }}
                </div>
              </div>
              <span class="al-chip al-chip--teal">{{
                c.estado === "revisado"
                  ? "Revisado"
                  : c.estado === "completado"
                    ? "Completado"
                    : c.estado === "en_progreso"
                      ? "En curso"
                      : "Pendiente"
              }}</span>
            </div>
          </div>
        </div>
        <div class="al-card al-confid">
          <div class="al-confid__head">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0e8d7e" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>
            100% confidencial
          </div>
          <div class="al-confid__txt">
            Solo tu psicólogo asignado puede ver tus respuestas. Nadie más del centro tiene acceso.
          </div>
        </div>
      </div>
    </div>

    <!-- ═════════ REUNIONES ═════════ -->
    <div v-else-if="view === 'reuniones'" class="al-grid-2col">
      <div class="al-col-left">
        <div class="al-tabs-row">
          <div class="al-tabs">
            <button class="al-tab al-tab--active">Próximas</button>
            <button class="al-tab" @click="view = 'reuniones'">Pasadas</button>
          </div>
        </div>

        <div v-if="!citasFuturas.length" class="al-card al-empty">
          Aún no tienes reuniones programadas. Pídele una a tu psicólogo abajo.
        </div>

        <div v-if="citasFuturas[0]" class="al-card al-featured">
          <div class="al-featured__head">
            <div class="al-featured__badge">
              <span class="al-live__dot"></span>
              {{ proximaEnMin != null && proximaEnMin <= 60 ? `EN VIVO EN ${proximaEnMin} MIN` : "PRÓXIMA SESIÓN" }}
            </div>
            <div class="al-featured__title-row">
              <div class="al-featured__avatar">{{ (psicologo?.nombre || "P")[0] }}</div>
              <div>
                <div class="al-featured__title">Sesión con tu psicólogo</div>
                <div class="al-featured__sub">
                  {{ psicologo ? `Psic. ${psicologo.nombre} ${psicologo.apellido}` : "Bienestar estudiantil" }}
                </div>
              </div>
            </div>
          </div>
          <div class="al-featured__body">
            <div class="al-featured__grid">
              <div class="al-info-cell">
                <div class="al-info-cell__icon"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/></svg></div>
                <div><div class="al-info-cell__lbl">Fecha</div><div class="al-info-cell__val">{{ fmtFechaSimple(citasFuturas[0].fecha) }}</div></div>
              </div>
              <div class="al-info-cell">
                <div class="al-info-cell__icon"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></div>
                <div><div class="al-info-cell__lbl">Hora</div><div class="al-info-cell__val">{{ citasFuturas[0].hora }}</div></div>
              </div>
              <div class="al-info-cell">
                <div class="al-info-cell__icon"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 10l5-3v10l-5-3v-4z"/><rect x="3" y="6" width="12" height="12" rx="2"/></svg></div>
                <div><div class="al-info-cell__lbl">Modalidad</div><div class="al-info-cell__val">{{ citasFuturas[0].modalidad === 'online' ? 'Videollamada' : 'Presencial' }}</div></div>
              </div>
              <div class="al-info-cell">
                <div class="al-info-cell__icon"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1"/></svg></div>
                <div><div class="al-info-cell__lbl">Estado</div><div class="al-info-cell__val" style="color:#0e8d7e;">{{ citasFuturas[0].estado }}</div></div>
              </div>
            </div>
            <div v-if="citasFuturas[0].notas" class="al-objective">
              <div class="al-objective__lbl">Notas de la sesión</div>
              <div class="al-objective__txt">{{ citasFuturas[0].notas }}</div>
            </div>
            <div class="al-actions-row">
              <button
                v-if="citasFuturas[0].modalidad === 'online'"
                class="al-btn-primary"
                :class="{ 'al-btn-disabled': !puedeUnirse }"
                :disabled="!puedeUnirse"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 10l5-3v10l-5-3v-4z"/><rect x="3" y="6" width="12" height="12" rx="2"/></svg>
                {{ puedeUnirse ? "Unirse a la videollamada" : "Unirse a la videollamada" }}
              </button>
              <button v-else class="al-btn-primary">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/></svg>
                Ver ubicación
              </button>
              <span class="al-status-pill" :class="{ 'al-status-pill--ok': puedeUnirse }">{{ tiempoParaUnirse }}</span>
            </div>
          </div>
        </div>

        <div v-for="c in citasFuturas.slice(1)" :key="c.id" class="al-card al-meeting">
          <div class="al-meeting__date" :class="c.modalidad !== 'online' ? 'al-meeting__date--amber' : ''">
            <div class="al-meeting__day">{{ diaCorto(c.fecha).dia }}</div>
            <div class="al-meeting__num">{{ diaCorto(c.fecha).num }}</div>
            <div class="al-meeting__mes">{{ diaCorto(c.fecha).mes }}</div>
          </div>
          <div class="al-meeting__body">
            <div class="al-meeting__title-row">
              <div class="al-meeting__title">{{ c.notas || "Sesión" }}</div>
              <span class="al-chip" :class="c.modalidad === 'online' ? 'al-chip--teal' : 'al-chip--amber'">
                {{ c.modalidad === "online" ? "Online" : "Presencial" }}
              </span>
            </div>
            <div class="al-meeting__meta">
              <div class="al-meeting__avatar-mini">{{ (psicologo?.nombre || "P")[0] }}</div>
              <span>{{ psicologo ? `Psic. ${psicologo.nombre}` : "Psicóloga" }}</span>
              <span class="al-meeting__dot">·</span>
              <span>{{ c.hora }}</span>
            </div>
          </div>
        </div>

        <div v-if="citasPasadas.length" class="al-section-title-line">Anteriores</div>
        <div v-for="c in citasPasadas.slice(0, 4)" :key="'p' + c.id" class="al-card al-meeting al-meeting--past">
          <div class="al-meeting__date al-meeting__date--past">
            <div class="al-meeting__day">{{ diaCorto(c.fecha).dia }}</div>
            <div class="al-meeting__num">{{ diaCorto(c.fecha).num }}</div>
            <div class="al-meeting__mes">{{ diaCorto(c.fecha).mes }}</div>
          </div>
          <div class="al-meeting__body">
            <div class="al-meeting__title-row">
              <div class="al-meeting__title" style="color:#5a6a70;">{{ c.notas || "Sesión" }}</div>
              <span class="al-chip al-chip--soft">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
                Realizada
              </span>
            </div>
            <div class="al-meeting__meta">
              <span>{{ psicologo ? `Psic. ${psicologo.nombre}` : "Psicóloga" }}</span>
              <span class="al-meeting__dot">·</span>
              <span>{{ c.hora }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="al-col-right">
        <div class="al-card al-psy-card">
          <div class="al-psy-card__avatar">{{ (psicologo?.nombre || "P")[0] }}</div>
          <div class="al-psy-card__name">
            {{ psicologo ? `Psic. ${psicologo.nombre} ${psicologo.apellido}` : "Sin psicólogo asignado" }}
          </div>
          <div class="al-psy-card__role">Bienestar estudiantil</div>
          <div v-if="psicologo" class="al-psy-card__chip">
            <span class="al-psy-card__chip-dot"></span>
            Disponible
          </div>
          <div class="al-psy-card__actions">
            <a v-if="psicologo" :href="`mailto:${psicologo.email}`" class="al-btn-primary al-btn-full">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z"/></svg>
              Enviar mensaje
            </a>
            <button v-else class="al-btn-ghost" disabled>
              Sin asignar
            </button>
          </div>
        </div>

        <div class="al-card">
          <div class="al-side-title">Agendar nueva reunión</div>
          <div class="al-side-sub">Horarios sugeridos esta semana</div>
          <div class="al-slots">
            <button
              v-for="(s, idx) in slots"
              :key="idx"
              class="al-slot"
              :disabled="agendando"
              @click="agendar(s)"
            >
              <span class="al-slot__date">{{ s.label }}</span>
              <span class="al-slot__hour">{{ s.hora }}</span>
            </button>
          </div>
          <div v-if="agendaMsg" class="al-agenda-msg">{{ agendaMsg }}</div>
        </div>
      </div>
    </div>

    <!-- ═════════ RECURSOS ═════════ -->
    <div v-else-if="view === 'recursos'" class="al-recursos-wrap">
      <div class="al-filters">
        <button
          v-for="f in filtros"
          :key="f"
          class="al-filter"
          :class="{ active: filtroRecurso === f.toLowerCase() || (f === 'Todos' && filtroRecurso === 'todos') }"
          @click="filtroRecurso = f === 'Todos' ? 'todos' : f.toLowerCase()"
        >
          {{ f }}
        </button>
      </div>

      <div v-if="recursosFiltrados.length === 0" class="al-card al-empty">
        No hay recursos con ese filtro todavía.
      </div>

      <div v-else class="al-recursos-grid">
        <a
          v-for="r in recursosFiltrados"
          :key="r.id"
          :href="r.url || '#'"
          target="_blank"
          rel="noopener"
          class="al-recurso"
        >
          <div
            class="al-recurso__hero"
            :style="{ background: recursosPorTipo(r.categoria).bg, color: recursosPorTipo(r.categoria).color }"
          >
            <svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
          </div>
          <div class="al-recurso__body">
            <div class="al-recurso__cat">{{ r.categoria || "Recurso" }}</div>
            <div class="al-recurso__title">{{ r.titulo }}</div>
            <div class="al-recurso__cta">
              {{ r.url ? "Abrir" : "Ver" }}
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </div>
          </div>
        </a>
      </div>
    </div>

    <!-- ═════════ MI BIENESTAR ═════════ -->
    <div v-else-if="view === 'bienestar'" class="al-grid-2col">
      <div class="al-col-left">
        <div class="al-card">
          <div class="al-section-title">¿Cómo te sientes hoy?</div>
          <div class="al-side-sub">Registra tu ánimo para ver tu evolución.</div>
          <div class="al-mood-row">
            <button
              v-for="(lbl, k) in moodLabel"
              :key="k"
              class="al-mood"
              :class="{ active: moodHoy === k }"
              @click="pickMood(k)"
            >
              <span class="al-mood__face" :data-mood="k">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="9"/>
                  <path v-if="k === 'muy_mal'" d="M8 16q4-3 8 0"/>
                  <path v-else-if="k === 'mal'" d="M8.5 15.5q3.5-1.5 7 0"/>
                  <path v-else-if="k === 'regular'" d="M8 15h8"/>
                  <path v-else-if="k === 'bien'" d="M8.5 14q3.5 2.5 7 0"/>
                  <path v-else d="M8 13q4 4 8 0"/>
                  <path d="M9 9h.01M15 9h.01"/>
                </svg>
              </span>
              <span class="al-mood__lbl">{{ lbl }}</span>
            </button>
          </div>
        </div>

        <!-- MENSAJE DEL PSICÓLOGO -->
        <div class="al-msgcard" :class="{ 'al-msgcard--empty': !mensajePsicologo }">
          <div class="al-msgcard__head">
            <div class="al-msgcard__avatar">{{ (psicologo?.nombre || "P")[0] }}</div>
            <div>
              <div class="al-msgcard__lbl">Mensaje de tu psicólogo</div>
              <div class="al-msgcard__from">
                {{ mensajePsicologo?.psicologo || (psicologo ? `Psic. ${psicologo.nombre} ${psicologo.apellido}` : "Aún no asignado") }}
              </div>
            </div>
            <span v-if="mensajePsicologo" class="al-msgcard__date">
              {{ fmtFecha(mensajePsicologo.fecha) }}
            </span>
          </div>
          <div v-if="mensajePsicologo" class="al-msgcard__txt">
            <svg class="al-msgcard__quote" width="22" height="22" viewBox="0 0 24 24" fill="#0e8d7e"><path d="M7 7h4v4H8c0 2 1 3 3 3v3c-4 0-6-2-6-6V7zm9 0h4v4h-3c0 2 1 3 3 3v3c-4 0-6-2-6-6V7z"/></svg>
            {{ mensajePsicologo.texto }}
          </div>
          <div v-else class="al-msgcard__empty">
            Tu psicólogo te dejará una nota después de tu próxima sesión.
            Mientras tanto, podés solicitar una cita o responder los cuestionarios pendientes.
          </div>
          <div v-if="!mensajePsicologo" class="al-msgcard__cta">
            <button class="al-btn-ghost al-btn-sm" @click="changeView('reuniones')">Agendar sesión</button>
            <button class="al-btn-ghost al-btn-sm" @click="changeView('cuestionario')">Mis cuestionarios</button>
          </div>
        </div>
      </div>

      <div class="al-col-right">
        <div class="al-card">
          <div class="al-side-title">Resumen</div>
          <div class="al-resume-list">
            <div class="al-resume">
              <div class="al-resume__icon al-resume__icon--teal">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/></svg>
              </div>
              <div>
                <div class="al-resume__num">{{ animoTexto }}</div>
                <div class="al-resume__lbl">Promedio ({{ animoPromedio ? animoPromedio.toFixed(1) : "—" }}/5)</div>
              </div>
            </div>
            <div class="al-resume">
              <div class="al-resume__icon al-resume__icon--amber">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3c1.5 3 4 4 4 7a4 4 0 0 1-8 0c0-1 .5-2 1-2.5"/></svg>
              </div>
              <div>
                <div class="al-resume__num">{{ racha }} día{{ racha === 1 ? "" : "s" }}</div>
                <div class="al-resume__lbl">Racha de registros</div>
              </div>
            </div>
            <div class="al-resume">
              <div class="al-resume__icon al-resume__icon--teal-soft">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>
              </div>
              <div>
                <div class="al-resume__num">{{ cuestEnviados }}</div>
                <div class="al-resume__lbl">Cuestionarios enviados</div>
              </div>
            </div>
          </div>
        </div>
        <div class="al-card">
          <div class="al-side-title">Tu proceso</div>
          <div v-if="timeline.length === 0" class="al-empty">
            Cuando respondas tu primer cuestionario o tengas una sesión, vas a ver tu recorrido acá.
          </div>
          <ul v-else class="al-timeline">
            <li
              v-for="(t, i) in timeline"
              :key="i"
              class="al-tl-item"
              :class="{ 'al-tl-item--future': t.futuro }"
            >
              <span class="al-tl-icon">
                <svg v-if="t.icono === 'session'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 10l5-3v10l-5-3v-4z"/><rect x="3" y="6" width="12" height="12" rx="2"/></svg>
                <svg v-else-if="t.icono === 'doc'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>
                <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l2.4 5.6L20 8l-4.5 4.3L17 18l-5-3-5 3 1.5-5.7L4 8l5.6-.4z"/></svg>
              </span>
              <div class="al-tl-body">
                <div class="al-tl-title">{{ t.titulo }}</div>
                <div class="al-tl-detail">{{ t.detalle }}</div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- ═════════ MI PERFIL ═════════ -->
    <div v-else-if="view === 'perfil'" class="al-grid-2col">
      <div class="al-col-left">
        <div class="al-card al-profile-head">
          <div class="al-profile-head__avatar">{{ user?.nombre?.[0] || "?" }}{{ user?.apellido?.[0] || "" }}</div>
          <div class="al-profile-head__info">
            <div class="al-profile-head__name">{{ user?.nombre }} {{ user?.apellido }}</div>
            <div class="al-profile-head__role">Alumno{{ user?.grado ? ` · ${user.grado}` : "" }}</div>
          </div>
        </div>

        <div class="al-card">
          <div class="al-side-title">Información personal</div>
          <div class="al-info-grid">
            <div class="al-info-cell-card">
              <div class="al-info-cell__lbl">Nombre completo</div>
              <div class="al-info-cell__val">{{ user?.nombre }} {{ user?.apellido }}</div>
            </div>
            <div class="al-info-cell-card">
              <div class="al-info-cell__lbl">Correo</div>
              <div class="al-info-cell__val">{{ user?.email }}</div>
            </div>
            <div class="al-info-cell-card">
              <div class="al-info-cell__lbl">Año / Curso</div>
              <div class="al-info-cell__val">{{ user?.grado || "—" }}</div>
            </div>
            <div class="al-info-cell-card">
              <div class="al-info-cell__lbl">Rol</div>
              <div class="al-info-cell__val">Estudiante</div>
            </div>
            <div class="al-info-cell-card">
              <div class="al-info-cell__lbl">Cuenta desde</div>
              <div class="al-info-cell__val">{{ fmtFecha(user?.created_at) }}</div>
            </div>
            <div class="al-info-cell-card">
              <div class="al-info-cell__lbl">Estado caso</div>
              <div class="al-info-cell__val">{{ user?.estado_caso || "Activo" }}</div>
            </div>
          </div>
        </div>

        <div class="al-card">
          <div class="al-side-title">Preferencias</div>
          <div class="al-pref-row">
            <div>
              <div class="al-pref-row__title">Recordatorios de reunión</div>
              <div class="al-pref-row__sub">Avísame 30 min antes de cada sesión</div>
            </div>
            <button class="al-toggle" :class="{ on: prefs.recordatorios }" @click="togglePref('recordatorios')">
              <span class="al-toggle__dot"></span>
            </button>
          </div>
          <div class="al-pref-row">
            <div>
              <div class="al-pref-row__title">Notificaciones por correo</div>
              <div class="al-pref-row__sub">Resúmenes y respuestas del psicólogo</div>
            </div>
            <button class="al-toggle" :class="{ on: prefs.correo }" @click="togglePref('correo')">
              <span class="al-toggle__dot"></span>
            </button>
          </div>
          <div class="al-pref-row al-pref-row--last">
            <div>
              <div class="al-pref-row__title">Modo privado</div>
              <div class="al-pref-row__sub">Oculta tu ánimo en pantallas compartidas</div>
            </div>
            <button class="al-toggle" :class="{ on: prefs.privado }" @click="togglePref('privado')">
              <span class="al-toggle__dot"></span>
            </button>
          </div>
        </div>
      </div>

      <div class="al-col-right">
        <div class="al-card">
          <div class="al-side-title">Tu psicólogo</div>
          <div v-if="psicologo" class="al-psy-mini">
            <div class="al-psy-mini__avatar">{{ psicologo.nombre[0] }}</div>
            <div>
              <div class="al-psy-mini__name">Psic. {{ psicologo.nombre }} {{ psicologo.apellido }}</div>
              <div class="al-psy-mini__role">Bienestar estudiantil</div>
            </div>
          </div>
          <div v-else class="al-empty">Aún no tienes un psicólogo asignado.</div>
          <button class="al-btn-ghost al-btn-full" @click="changeView('reuniones')">
            Agendar reunión
          </button>
        </div>

        <div class="al-card">
          <div class="al-side-title">Cuenta</div>
          <a class="al-account-link" href="#" @click.prevent="router.push('/perfil')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c8b90" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            Cambiar contraseña
          </a>
          <a class="al-account-link al-account-link--danger" href="#" @click.prevent="cerrarSesion">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5M21 12H9"/></svg>
            Cerrar sesión
          </a>
        </div>
      </div>
    </div>
  </AppShellAlumno>
</template>

<style scoped>
/* ── grids ── */
.al-grid-main {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 372px;
  gap: 20px;
  align-items: start;
}
.al-grid-2col {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 20px;
  align-items: start;
}
.al-col-left { display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.al-col-right { display: flex; flex-direction: column; gap: 20px; }
.al-fullwidth { grid-column: 1 / -1; margin-top: 0; }

/* ── card base ── */
.al-card {
  background: #fff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 6px 20px rgba(35, 80, 95, 0.05);
}
.al-empty {
  padding: 18px;
  text-align: center;
  color: #8b999e;
  font-size: 14px;
}

.al-section-head {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}
.al-section-title {
  font-size: 18px;
  font-weight: 700;
  color: #243239;
}
.al-section-title-line {
  font-size: 13px;
  font-weight: 700;
  color: #9aa7ab;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-top: 6px;
}
.al-side-title {
  font-size: 16px;
  font-weight: 700;
  color: #243239;
  margin-bottom: 14px;
}
.al-side-sub {
  font-size: 13px;
  color: #9aa7ab;
  margin-top: 4px;
  margin-bottom: 12px;
}

/* ── KPI ── */
.al-kpis { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.al-kpi { padding: 22px; }
.al-kpi__head { display: flex; align-items: flex-start; gap: 16px; }
.al-kpi__icon {
  width: 56px; height: 56px; border-radius: 50%;
  border: 1.5px solid #d3e8e3;
  display: flex; align-items: center; justify-content: center;
  flex: 0 0 56px; color: #0e8d7e;
}
.al-kpi__num {
  font-size: 30px; font-weight: 800; color: #243239; line-height: 1.05;
}
.al-kpi__lbl { margin-top: 6px; font-size: 14px; color: #8b999e; }
.al-kpi__foot {
  display: flex; align-items: flex-end; justify-content: space-between; margin-top: 20px;
}
.al-kpi__right { text-align: right; }
.al-kpi__trend { color: #1aa896; font-weight: 700; font-size: 13px; }

.al-chip-soft {
  display: inline-block;
  margin-top: 5px;
  background: #e3f3ef;
  color: #0e8d7e;
  font-weight: 600;
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 7px;
}

.al-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #0e8d7e;
  font-weight: 600;
  font-size: 14px;
  text-decoration: none;
  cursor: pointer;
}

/* ── botones ── */
.al-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #1aa896, #0c8475);
  color: #fff;
  border: none;
  border-radius: 11px;
  padding: 12px 22px;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  box-shadow: 0 6px 14px rgba(15, 130, 115, 0.3);
}
.al-btn-primary:disabled { opacity: 0.7; cursor: wait; }
.al-btn-lg { padding: 14px 28px; font-size: 15px; }
.al-btn-full { width: 100%; justify-content: center; margin-top: 12px; }
.al-btn-ghost {
  background: #fff;
  color: #0e8d7e;
  border: 1px solid #d3e8e3;
  border-radius: 11px;
  padding: 12px;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
}

/* ── quiz cta ── */
.al-quizcta {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 22px 24px;
}
.al-quizcta__icon {
  width: 52px; height: 52px; border-radius: 14px;
  background: #e3f3ef; color: #0e8d7e;
  flex: 0 0 52px;
  display: flex; align-items: center; justify-content: center;
}
.al-quizcta__txt { flex: 1; min-width: 0; }
.al-quizcta__title { font-size: 17px; font-weight: 700; color: #243239; }
.al-quizcta__sub { font-size: 13.5px; color: #8b999e; margin-top: 3px; }

/* ── recursos mini ── */
.al-recursos-grid-mini {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
.al-recurso-mini {
  display: flex;
  gap: 14px;
  padding: 16px;
  border: 1px solid #eef1f2;
  border-radius: 14px;
  text-decoration: none;
  align-items: center;
  transition: border-color 0.15s, background 0.15s;
}
.al-recurso-mini:hover {
  border-color: #bfe3db;
  background: #fafdfc;
}
.al-recurso-mini__icon {
  width: 46px;
  height: 46px;
  border-radius: 11px;
  flex: 0 0 46px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-recurso-mini__title { font-weight: 700; font-size: 14px; color: #33424a; }
.al-recurso-mini__sub { margin-top: 4px; font-size: 12px; color: #9aa7ab; }

/* ── SOS ── */
.al-sos {
  border-radius: 18px;
  padding: 24px;
  background: linear-gradient(150deg, #ff6b6b, #e0413c);
  box-shadow: 0 12px 26px rgba(224, 65, 60, 0.32);
  color: #fff;
  position: relative;
  overflow: hidden;
}
.al-sos__bubble {
  position: absolute;
  right: -30px;
  top: -30px;
  width: 130px;
  height: 130px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
}
.al-sos__head {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}
.al-sos__icon {
  width: 48px;
  height: 48px;
  border-radius: 13px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-sos__title { font-weight: 800; font-size: 18px; }
.al-sos__sub { font-size: 12.5px; color: rgba(255, 255, 255, 0.85); margin-top: 2px; }
.al-sos__main {
  width: 100%;
  margin-top: 18px;
  background: #fff;
  color: #e0413c;
  border: none;
  border-radius: 12px;
  padding: 13px;
  font-size: 15px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.al-sos__main:disabled { opacity: 0.7; cursor: wait; }
.al-sos__msg {
  margin-top: 10px;
  font-size: 12.5px;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.16);
  border-radius: 8px;
  padding: 8px 12px;
}
.al-sos__actions {
  display: flex;
  flex-direction: column;
  gap: 9px;
  margin-top: 14px;
}
.al-sos__alt {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.14);
  border-radius: 11px;
  padding: 11px 13px;
  text-decoration: none;
  color: #fff;
  font-size: 13.5px;
  font-weight: 600;
}
.al-sos__alt:hover { background: rgba(255, 255, 255, 0.22); }

/* ── reuniones panel (inicio) ── */
.al-live {
  border: 1.5px solid #cfeae3;
  background: #f4fbf9;
  border-radius: 14px;
  padding: 16px;
}
.al-live__badge {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0e8d7e;
  font-size: 12px;
  font-weight: 700;
}
.al-live__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1fbf75;
  display: inline-block;
  box-shadow: 0 0 0 4px rgba(31, 191, 117, 0.18);
}
.al-live__title {
  font-weight: 700;
  font-size: 15px;
  color: #243239;
  margin-top: 8px;
}
.al-live__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 13px;
  color: #8b999e;
}

.al-meeting-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}
.al-meeting-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 4px;
  border-bottom: 1px solid #f1f4f4;
}
.al-meeting-row:last-child { border-bottom: none; }
.al-mini-avatar {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 38px;
}
.al-meeting-row__txt { min-width: 0; flex: 1; }
.al-meeting-row__title {
  font-weight: 600;
  font-size: 13.5px;
  color: #33424a;
}
.al-meeting-row__sub {
  font-size: 12px;
  color: #9aa7ab;
}

.al-chip {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 9px;
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.al-chip--teal { color: #0e8d7e; background: #e3f3ef; }
.al-chip--amber { color: #d98a1f; background: #fef3e2; }
.al-chip--soft { color: #1aa896; background: #eef7f4; }

/* ── chart ── */
.al-chart {
  display: flex;
  gap: 12px;
  height: 220px;
  align-items: stretch;
}
.al-chart__yaxis {
  flex: 0 0 76px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 0 4px 30px 0;
  font-size: 11px;
  color: #8b999e;
  text-align: right;
  line-height: 1;
}
.al-chart__ylabel {
  white-space: nowrap;
  font-weight: 600;
}
.al-chart__plot {
  position: relative;
  flex: 1;
  min-width: 0;
}
.al-chart__grid {
  position: absolute;
  inset: 0 0 26px 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.al-chart__line { border-top: 1px dashed #eef1f2; height: 0; }
.al-chart__base { border-top: 1px solid #e7ecec; height: 0; }
.al-chart__bars {
  position: absolute;
  inset: 0 0 26px 0;
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 0 4px;
}
.al-chart__col {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  height: 100%;
}
.al-chart__bar {
  width: 56%;
  min-height: 6px;
  background: rgba(26, 168, 150, 0.3);
  border-radius: 6px 6px 0 0;
}
.al-chart__bar--today {
  background: linear-gradient(180deg, #22b8a6, #0e8d7e);
  box-shadow: 0 4px 10px rgba(20, 150, 135, 0.25);
}
.al-chart__bar--empty {
  width: 56%;
  height: 4px;
  background: repeating-linear-gradient(90deg, #e7ecec 0 4px, transparent 4px 8px);
  border-radius: 4px;
  align-self: flex-end;
  opacity: 0.7;
}
.al-chart__labels {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  gap: 10px;
  padding: 0 4px;
}
.al-chart__labels div {
  flex: 1;
  text-align: center;
  font-size: 12px;
  color: #9aa7ab;
}

/* botón deshabilitado y pill de estado */
.al-btn-disabled {
  background: #e7ecec !important;
  color: #9aa7ab !important;
  box-shadow: none !important;
  cursor: not-allowed !important;
}
.al-status-pill {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  background: #f4f5f6;
  color: #6b7b80;
  font-size: 12px;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 8px;
}
.al-status-pill--ok { background: #e3f3ef; color: #0e8d7e; }
.al-chart-legend {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #8b999e;
}
.al-chart-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  background: #1aa896;
}

/* ── cuestionario vista ── */
.al-hero {
  background: linear-gradient(120deg, #e7f6f1, #f4fbf9);
  border: 1px solid #e0f0ea;
  border-radius: 18px;
  padding: 22px 24px;
}
.al-hero__title { font-size: 20px; font-weight: 800; color: #243239; }
.al-hero__txt {
  font-size: 14px;
  color: #56666c;
  margin-top: 6px;
  line-height: 1.5;
  max-width: 560px;
}
.al-cta-center {
  padding: 40px 28px;
  text-align: center;
}
.al-cta-center__icon {
  width: 68px;
  height: 68px;
  border-radius: 18px;
  background: #e3f3ef;
  color: #0e8d7e;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}
.al-cta-center__title {
  font-size: 19px;
  font-weight: 800;
  color: #243239;
  margin-top: 18px;
}
.al-cta-center__sub {
  font-size: 14px;
  color: #8b999e;
  margin-top: 8px;
  line-height: 1.5;
  max-width: 420px;
  margin-left: auto;
  margin-right: auto;
}
.al-cta-center .al-btn-primary { margin-top: 22px; }

.al-history-list { display: flex; flex-direction: column; }
.al-history-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f4f4;
}
.al-history-row:last-child { border-bottom: none; }
.al-history-row__icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  flex: 0 0 38px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-history-row__txt { flex: 1; min-width: 0; }
.al-history-row__title { font-size: 13.5px; font-weight: 700; color: #33424a; }
.al-history-row__sub { font-size: 12px; color: #9aa7ab; }

.al-confid {
  background: #f7faf9;
  border: 1px solid #eef3f1;
}
.al-confid__head {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #243239;
}
.al-confid__txt {
  font-size: 13px;
  color: #6b7b80;
  line-height: 1.5;
  margin-top: 8px;
}

/* ── reuniones vista detalle ── */
.al-tabs-row { display: flex; align-items: center; gap: 12px; }
.al-tabs {
  display: flex;
  gap: 6px;
  background: #fff;
  padding: 5px;
  border-radius: 12px;
  box-shadow: 0 6px 20px rgba(35, 80, 95, 0.05);
}
.al-tab {
  border: none;
  background: transparent;
  color: #5a6a70;
  font-weight: 600;
  font-size: 13px;
  padding: 8px 16px;
  border-radius: 9px;
  cursor: pointer;
  font-family: inherit;
}
.al-tab--active { background: #0e8d7e; color: #fff; font-weight: 700; }

.al-featured { padding: 0; overflow: hidden; }
.al-featured__head {
  background: linear-gradient(120deg, #e7f6f1, #f4fbf9);
  padding: 20px 24px;
  border-bottom: 1px solid #eaf3ef;
}
.al-featured__badge {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0e8d7e;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.3px;
}
.al-featured__title-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 14px;
}
.al-featured__avatar {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  font-weight: 800;
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-featured__title { font-weight: 800; font-size: 18px; color: #243239; }
.al-featured__sub { font-size: 13px; color: #6b7b80; margin-top: 2px; }
.al-featured__body { padding: 20px 24px; }
.al-featured__grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.al-info-cell { display: flex; gap: 10px; align-items: flex-start; }
.al-info-cell__icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: #e3f3ef;
  color: #0e8d7e;
  flex: 0 0 34px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-info-cell__lbl { font-size: 12px; color: #9aa7ab; }
.al-info-cell__val {
  font-size: 14px;
  font-weight: 700;
  color: #33424a;
  margin-top: 2px;
  text-transform: capitalize;
}
.al-objective {
  margin-top: 18px;
  background: #f7faf9;
  border: 1px solid #eef3f1;
  border-radius: 12px;
  padding: 14px 16px;
}
.al-objective__lbl {
  font-size: 12px;
  color: #9aa7ab;
  font-weight: 600;
  margin-bottom: 4px;
}
.al-objective__txt {
  font-size: 14px;
  color: #33424a;
  line-height: 1.5;
}
.al-actions-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
  flex-wrap: wrap;
}

.al-meeting {
  padding: 20px 22px;
  display: flex;
  gap: 18px;
}
.al-meeting--past { opacity: 0.9; }
.al-meeting__date {
  width: 64px;
  flex: 0 0 64px;
  text-align: center;
  background: #f4fbf9;
  border: 1px solid #e3f0ec;
  border-radius: 12px;
  padding: 10px 0;
  height: fit-content;
}
.al-meeting__date--amber {
  background: #fef7ee;
  border-color: #f3e6d2;
}
.al-meeting__date--past {
  background: #f4f6f6;
  border-color: #eaeeee;
}
.al-meeting__day {
  font-size: 11px;
  font-weight: 700;
  color: #0e8d7e;
  text-transform: uppercase;
}
.al-meeting__date--amber .al-meeting__day { color: #d98a1f; }
.al-meeting__date--past .al-meeting__day { color: #9aa7ab; }
.al-meeting__num {
  font-size: 24px;
  font-weight: 800;
  color: #243239;
  line-height: 1.1;
}
.al-meeting__date--past .al-meeting__num { color: #7c8b90; }
.al-meeting__mes { font-size: 11px; color: #9aa7ab; text-transform: capitalize; }
.al-meeting__body { flex: 1; min-width: 0; }
.al-meeting__title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.al-meeting__title {
  font-weight: 700;
  font-size: 16px;
  color: #243239;
}
.al-meeting .al-chip { margin-left: auto; }
.al-meeting__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 9px;
  font-size: 13px;
  color: #6b7b80;
}
.al-meeting__avatar-mini {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  font-weight: 700;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-meeting__dot { color: #cfd8d6; }

.al-psy-card { padding: 24px 22px; text-align: center; }
.al-psy-card__avatar {
  width: 74px;
  height: 74px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  font-weight: 800;
  font-size: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #eaf5f2;
}
.al-psy-card__name { font-weight: 800; font-size: 16px; color: #243239; margin-top: 12px; }
.al-psy-card__role { font-size: 12.5px; color: #9aa7ab; margin-top: 2px; }
.al-psy-card__chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  background: #eef7f4;
  color: #1aa896;
  font-size: 12px;
  font-weight: 700;
  padding: 5px 12px;
  border-radius: 20px;
}
.al-psy-card__chip-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #1fbf75;
  display: inline-block;
}
.al-psy-card__actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 18px;
}

.al-slots {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 16px;
}
.al-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  border: 1px solid #e3f0ec;
  background: #f7faf9;
  border-radius: 10px;
  padding: 11px;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  color: #33424a;
  transition: background 0.15s, border-color 0.15s;
}
.al-slot:hover { background: #ecf6f3; border-color: #b9dfd6; }
.al-slot:disabled { opacity: 0.6; cursor: wait; }
.al-slot__date { color: #0e8d7e; font-weight: 700; text-transform: capitalize; }
.al-slot__hour { color: #33424a; }
.al-agenda-msg {
  margin-top: 14px;
  background: #ecf6f3;
  border: 1px solid #d3e8e3;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 13px;
  color: #0e8d7e;
}

/* ── recursos ── */
.al-recursos-wrap { display: flex; flex-direction: column; gap: 18px; }
.al-filters { display: flex; gap: 8px; flex-wrap: wrap; }
.al-filter {
  border: 1px solid #e7ecec;
  background: #fff;
  color: #5a6a70;
  font-weight: 600;
  font-size: 13px;
  padding: 9px 16px;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
}
.al-filter.active {
  background: #0e8d7e;
  color: #fff;
  font-weight: 700;
  border-color: #0e8d7e;
}
.al-recursos-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}
.al-recurso {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(35, 80, 95, 0.05);
  overflow: hidden;
  text-decoration: none;
  color: inherit;
}
.al-recurso__hero {
  height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-recurso__body { padding: 16px 18px 18px; }
.al-recurso__cat {
  font-size: 11px;
  color: #9aa7ab;
  font-weight: 600;
  text-transform: capitalize;
}
.al-recurso__title {
  font-size: 15px;
  font-weight: 700;
  color: #33424a;
  margin-top: 5px;
}
.al-recurso__cta {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-top: 10px;
  color: #0e8d7e;
  font-weight: 600;
  font-size: 13px;
}

/* ── bienestar ── */
.al-mood-row {
  display: flex;
  gap: 10px;
  margin-top: 18px;
}
.al-mood {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  border: none;
  background: none;
  cursor: pointer;
  font-family: inherit;
}
.al-mood__face {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-mood__face[data-mood="muy_mal"] { background: #fdecec; color: #e0524c; }
.al-mood__face[data-mood="mal"] { background: #fef3e2; color: #d98a1f; }
.al-mood__face[data-mood="regular"] { background: #fbf7e6; color: #c2a02a; }
.al-mood__face[data-mood="bien"] { background: #e6f5f0; color: #1aa896; }
.al-mood__face[data-mood="muy_bien"] { background: #def0ea; color: #0e8d7e; }
.al-mood.active .al-mood__face {
  outline: 2.5px solid #1aa896;
  outline-offset: 2px;
}
.al-mood__lbl { font-size: 12px; color: #8b999e; }
.al-mood.active .al-mood__lbl { color: #1aa896; font-weight: 700; }

.al-resume-list { display: flex; flex-direction: column; gap: 14px; }
.al-resume { display: flex; align-items: center; gap: 12px; }
.al-resume__icon {
  width: 42px; height: 42px; border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  flex: 0 0 42px;
}
.al-resume__icon--teal { background: #e6f5f0; color: #1aa896; }
.al-resume__icon--amber { background: #fef3e2; color: #d98a1f; }
.al-resume__icon--teal-soft { background: #e3f3ef; color: #0e8d7e; }
.al-resume__num { font-size: 18px; font-weight: 800; color: #243239; }
.al-resume__lbl { font-size: 12px; color: #9aa7ab; }

/* ── Mensaje del psicólogo ── */
.al-msgcard {
  background: linear-gradient(135deg, #e3f3ef, #f7faf9);
  border: 1px solid #cfeae3;
  border-radius: 18px;
  padding: 22px 24px;
  box-shadow: 0 6px 20px rgba(35, 80, 95, 0.05);
}
.al-msgcard--empty { background: #fff; }
.al-msgcard__head {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}
.al-msgcard__avatar {
  width: 44px; height: 44px; border-radius: 13px;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff; font-weight: 800; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  flex: 0 0 44px;
}
.al-msgcard__lbl {
  font-size: 12px; font-weight: 700; color: #0e8d7e;
  text-transform: uppercase; letter-spacing: 0.4px;
}
.al-msgcard__from { font-size: 15px; font-weight: 700; color: #243239; margin-top: 2px; }
.al-msgcard__date {
  margin-left: auto;
  font-size: 12px; color: #8b999e; font-weight: 600;
  text-transform: capitalize;
}
.al-msgcard__txt {
  position: relative;
  font-size: 15px;
  line-height: 1.65;
  color: #33424a;
  padding: 12px 0 4px 32px;
  font-style: italic;
}
.al-msgcard__quote { position: absolute; left: 0; top: 8px; opacity: 0.4; }
.al-msgcard__empty {
  font-size: 14px;
  color: #6b7b80;
  line-height: 1.55;
  padding: 6px 0;
}
.al-msgcard__cta {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}
.al-btn-sm { padding: 8px 14px !important; font-size: 13px !important; }

/* ── Timeline vertical (Mi bienestar) ── */
.al-timeline {
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}
.al-timeline::before {
  content: "";
  position: absolute;
  left: 13px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: #e3f3ef;
  border-radius: 2px;
}
.al-tl-item {
  display: flex;
  gap: 14px;
  position: relative;
  padding: 10px 0;
}
.al-tl-icon {
  width: 28px; height: 28px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #1aa896;
  color: #0e8d7e;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 28px;
  position: relative;
  z-index: 1;
}
.al-tl-item--future .al-tl-icon {
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  border-color: #0e8d7e;
}
.al-tl-body { flex: 1; min-width: 0; padding-top: 2px; }
.al-tl-title {
  font-size: 14px;
  font-weight: 700;
  color: #243239;
}
.al-tl-item--future .al-tl-title { color: #0e8d7e; }
.al-tl-detail {
  font-size: 12.5px;
  color: #6b7b80;
  margin-top: 2px;
  text-transform: capitalize;
}

/* ── Timeline horizontal (Inicio) ── */
.al-htimeline {
  display: flex;
  align-items: stretch;
  gap: 0;
  overflow-x: auto;
  padding: 8px 4px 4px;
}
.al-htl-step {
  position: relative;
  flex: 1;
  min-width: 160px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 12px;
}
.al-htl-dot {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #1aa896;
  color: #0e8d7e;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}
.al-htl-step--future .al-htl-dot {
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  box-shadow: 0 6px 14px rgba(15, 130, 115, 0.3);
}
.al-htl-line {
  position: absolute;
  top: 18px;
  left: 50%;
  right: -50%;
  height: 2px;
  background: #e3f3ef;
  z-index: 0;
}
.al-htl-body { margin-top: 12px; }
.al-htl-title {
  font-size: 13.5px;
  font-weight: 700;
  color: #243239;
  line-height: 1.3;
}
.al-htl-step--future .al-htl-title { color: #0e8d7e; }
.al-htl-detail {
  font-size: 12px;
  color: #6b7b80;
  margin-top: 4px;
  text-transform: capitalize;
}
.al-htl-date {
  font-size: 11px;
  color: #9aa7ab;
  margin-top: 4px;
  font-weight: 600;
  text-transform: capitalize;
}

/* ── perfil ── */
.al-profile-head {
  display: flex;
  align-items: center;
  gap: 18px;
}
.al-profile-head__avatar {
  width: 78px;
  height: 78px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  font-weight: 800;
  font-size: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #eaf5f2;
}
.al-profile-head__info { flex: 1; min-width: 0; }
.al-profile-head__name { font-size: 20px; font-weight: 800; color: #243239; }
.al-profile-head__role { font-size: 13px; color: #9aa7ab; margin-top: 3px; }

.al-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.al-info-cell-card {
  border: 1px solid #eef1f2;
  border-radius: 12px;
  padding: 14px 16px;
}
.al-info-cell-card .al-info-cell__val { text-transform: none; }

.al-pref-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f1f4f4;
}
.al-pref-row--last { border-bottom: none; }
.al-pref-row__title { font-size: 14px; font-weight: 600; color: #33424a; }
.al-pref-row__sub { font-size: 12px; color: #9aa7ab; }
.al-toggle {
  margin-left: auto;
  width: 42px;
  height: 24px;
  border-radius: 13px;
  background: #e1e6e6;
  position: relative;
  border: none;
  cursor: pointer;
  transition: background 0.18s;
}
.al-toggle.on { background: #1aa896; }
.al-toggle__dot {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  transition: left 0.18s, right 0.18s;
}
.al-toggle.on .al-toggle__dot { left: 21px; }

.al-psy-mini {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.al-psy-mini__avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  font-weight: 800;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.al-psy-mini__name { font-size: 14.5px; font-weight: 700; color: #243239; }
.al-psy-mini__role { font-size: 12px; color: #9aa7ab; }

.al-account-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f1f4f4;
  text-decoration: none;
  color: #33424a;
  font-size: 14px;
  font-weight: 600;
}
.al-account-link:last-child { border-bottom: none; }
.al-account-link--danger { color: #e0524c; }

/* ── RESPONSIVE ── */
@media (max-width: 1200px) {
  .al-grid-main,
  .al-grid-2col {
    grid-template-columns: 1fr !important;
  }
  .al-kpis {
    grid-template-columns: repeat(2, 1fr);
  }
  .al-recursos-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .al-fullwidth { grid-column: auto; }
}
@media (max-width: 800px) {
  .al-kpis { grid-template-columns: 1fr; }
  .al-recursos-grid-mini { grid-template-columns: 1fr; }
  .al-recursos-grid { grid-template-columns: 1fr; }
  .al-info-grid { grid-template-columns: 1fr; }
  .al-featured__grid { grid-template-columns: 1fr; }
  .al-quizcta { flex-direction: column; align-items: stretch; text-align: left; }
  .al-quizcta .al-btn-primary { width: 100%; justify-content: center; }
  .al-mood-row { flex-wrap: wrap; gap: 6px; }
  .al-mood { flex: 1 1 30%; }
  .al-htimeline { flex-direction: column; align-items: stretch; }
  .al-htl-step { flex-direction: row; text-align: left; gap: 12px; padding: 8px 4px; }
  .al-htl-line { display: none; }
  .al-htl-body { margin-top: 0; flex: 1; }
  .al-tabs-row { flex-wrap: wrap; gap: 10px; }
  .al-actions-row { gap: 8px; }
  .al-actions-row .al-btn-primary { width: 100%; justify-content: center; }
  .al-status-pill { margin-left: 0; }
  .al-slots { grid-template-columns: 1fr; }
  .al-profile-head { flex-wrap: wrap; }
  .al-meeting { flex-direction: column; }
  .al-meeting__date { width: 100%; flex: 0 0 auto; display: flex; gap: 8px; justify-content: flex-start; align-items: center; padding: 8px 12px; }
  .al-meeting__date .al-meeting__day,
  .al-meeting__date .al-meeting__num,
  .al-meeting__date .al-meeting__mes { display: inline; line-height: 1.2; }
  .al-meeting__num { font-size: 18px; }
  .al-featured__title-row { flex-wrap: wrap; }
  .al-featured__title { font-size: 16px; }
  .al-msgcard__head { flex-wrap: wrap; }
  .al-msgcard__date { margin-left: 0; flex-basis: 100%; }
}
</style>
