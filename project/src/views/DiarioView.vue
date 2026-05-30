<script setup>
import { computed, reactive, ref, onMounted } from "vue";
import { authStore } from "../store/auth";
import { api } from "../api";

// ─────────────────────────────────────────────────────────────────────────
// Estado de la vista
// ─────────────────────────────────────────────────────────────────────────
const tab = ref("escribir"); // "escribir" | "diario" | "proceso" | "apoyo"

// ─── Ciclo de 14 días (día N, sesiones cerradas, próxima cita) ──────
const ciclo = ref(null);
const cargandoCiclo = ref(false);

async function cargarCiclo() {
  cargandoCiclo.value = true;
  try {
    ciclo.value = await api.miCiclo();
  } catch (_) {
    ciclo.value = null;
  } finally {
    cargandoCiclo.value = false;
  }
}

function formatFechaCiclo(iso) {
  if (!iso) return "—";
  return new Date(iso + "T00:00:00").toLocaleDateString("es-PE", {
    day: "numeric",
    month: "long",
  });
}

// ─── Calendario de mes ───────────────────────────────────────────────
const NOMBRES_MES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];
// Lunes-domingo (formato español)
const DIAS_SEMANA = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];

// Mes que está viendo el alumno (por defecto el actual)
const mesVisible = ref({
  year: new Date().getFullYear(),
  month: new Date().getMonth(), // 0-11
});

const tituloMes = computed(
  () => `${NOMBRES_MES[mesVisible.value.month]} ${mesVisible.value.year}`,
);

function cambiarMes(delta) {
  let { year, month } = mesVisible.value;
  month += delta;
  if (month < 0) {
    month = 11;
    year -= 1;
  } else if (month > 11) {
    month = 0;
    year += 1;
  }
  mesVisible.value = { year, month };
}

function irAHoy() {
  const ahora = new Date();
  mesVisible.value = { year: ahora.getFullYear(), month: ahora.getMonth() };
}

function tituloCelda(c) {
  const partes = [formatFechaCiclo(c.iso)];
  if (c.tieneEntrada) partes.push("Escribiste");
  if (c.esSesionCerrada) partes.push(`Sesión #${c.sesionNumero}`);
  if (c.esProximaCita) partes.push("Próxima cita");
  if (c.esHoy) partes.push("Hoy");
  return partes.join(" · ");
}

const matrizCalendario = computed(() => {
  // Devuelve filas de 7 días, cada celda { iso, num, mesActual, ...flags }.
  const { year, month } = mesVisible.value;
  const primerDia = new Date(year, month, 1);
  // En JS getDay() devuelve 0=Dom, 1=Lun, ... 6=Sáb. Lo convertimos a
  // "offset desde lunes" (lunes=0, ..., domingo=6).
  const offsetLunes = (primerDia.getDay() + 6) % 7;
  const diasEnMes = new Date(year, month + 1, 0).getDate();

  const hoyIso = new Date().toISOString().slice(0, 10);
  const fechasEntradas = new Set(
    ciclo.value?.ciclo_actual?.fechas_con_entrada || [],
  );
  const sesionesPorFecha = new Map(
    (ciclo.value?.sesiones_cerradas || []).map((s) => [s.fecha, s.numero]),
  );
  const proxima = ciclo.value?.proxima_cita;
  const inicioCiclo = ciclo.value?.ciclo_actual?.inicio;
  const limiteCiclo = ciclo.value?.ciclo_actual?.fecha_limite;

  const celdas = [];
  // Padding izquierdo: días del mes anterior (vacíos)
  for (let i = 0; i < offsetLunes; i++) {
    celdas.push(null);
  }
  for (let d = 1; d <= diasEnMes; d++) {
    const iso = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    celdas.push({
      iso,
      num: d,
      esHoy: iso === hoyIso,
      tieneEntrada: fechasEntradas.has(iso),
      esSesionCerrada: sesionesPorFecha.has(iso),
      sesionNumero: sesionesPorFecha.get(iso),
      esProximaCita: proxima && proxima.fecha === iso,
      enCicloActual:
        inicioCiclo && limiteCiclo && iso >= inicioCiclo && iso <= limiteCiclo,
    });
  }
  // Padding derecho hasta completar la última fila
  while (celdas.length % 7 !== 0) {
    celdas.push(null);
  }
  // Divido en filas de 7
  const filas = [];
  for (let i = 0; i < celdas.length; i += 7) {
    filas.push(celdas.slice(i, i + 7));
  }
  return filas;
});

const usuario = computed(() => authStore.state.user);
const primerNombre = computed(() => {
  const n = (usuario.value?.nombre || "").trim();
  return n.split(" ")[0] || "";
});

// ─────────────────────────────────────────────────────────────────────────
// Saludo + fecha
// ─────────────────────────────────────────────────────────────────────────
const hoy = new Date();
const fechaLarga = hoy.toLocaleDateString("es-PE", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

const saludoTiempo = computed(() => {
  const h = hoy.getHours();
  if (h < 12) return "Buenos días";
  if (h < 19) return "Buenas tardes";
  return "Buenas noches";
});

// ─────────────────────────────────────────────────────────────────────────
// Prompts rotativos (uno por día del mes)
// ─────────────────────────────────────────────────────────────────────────
const PROMPTS = [
  "¿Hubo algo que disfrutaste hoy, o algo que ya no te llama como antes?",
  "Si pudieras nombrar cómo te sentiste hoy con una palabra, ¿cuál sería?",
  "¿Qué fue lo más difícil del día? No tiene que ser grande.",
  "¿Hubo un momento en que respiraste tranquilo/a? Cuéntalo.",
  "¿Hay algo que te quedaste sin decir hoy?",
  "¿Cómo dormiste anoche y cómo se notó en tu día?",
  "Si tuvieras que escribirle a tu yo de la próxima semana, ¿qué le contarías?",
  "¿Hubo alguien que te hiciera bien hoy?",
  "¿Qué te dio energía? ¿Qué te la quitó?",
  "Si hoy fuera una canción, ¿cuál sería?",
  "¿Qué cosa pequeña te gustó del día de hoy?",
  "¿Hay algo que estás postergando por miedo a sentirlo?",
];
const promptDelDia = computed(() => PROMPTS[hoy.getDate() % PROMPTS.length]);

// ─────────────────────────────────────────────────────────────────────────
// Pantalla "Escribir"
// ─────────────────────────────────────────────────────────────────────────
const texto = ref("");
const moodSeleccionado = ref(null); // "soleado" | "mixto" | "nublado" | "lluvioso"
const guardando = ref(false);
const guardado = ref(false);

// ─── Modal post-guardado ──────────────────────────────────────────────
const FRASES_VALIDADORAS = [
  "Guardado ✓ Gracias por escribir hoy.",
  "Guardado ✓ Tomarte este momento para ti cuenta mucho.",
  "Guardado ✓ Cada entrada es un paso hacia conocerte mejor.",
  "Guardado ✓ Hoy escribiste. Eso ya es algo importante.",
];

const modalGuardado = reactive({
  abierto: false,
  frase: "",
  consejo: "",
});

let timerCierreModal = null;

function cerrarModalGuardado() {
  modalGuardado.abierto = false;
  if (timerCierreModal) {
    clearTimeout(timerCierreModal);
    timerCierreModal = null;
  }
}

function abrirModalGuardado() {
  modalGuardado.frase =
    FRASES_VALIDADORAS[Math.floor(Math.random() * FRASES_VALIDADORAS.length)];
  modalGuardado.consejo = "";
  modalGuardado.abierto = true;

  // Cargamos el consejo del día sin bloquear; si falla, el modal se ve
  // bien sin él.
  api
    .consejoDelDia()
    .then((data) => {
      if (modalGuardado.abierto) modalGuardado.consejo = data.consejo;
    })
    .catch(() => {});

  // Auto-cierre a los 4s si el alumno no toca nada.
  if (timerCierreModal) clearTimeout(timerCierreModal);
  timerCierreModal = setTimeout(() => {
    if (modalGuardado.abierto) cerrarModalGuardado();
  }, 4000);
}

function verMiDiario() {
  cerrarModalGuardado();
  irA("diario");
}

const palabras = computed(() => {
  const t = texto.value.trim();
  return t ? t.split(/\s+/).length : 0;
});

// Feedback dinámico y alentador según cuánto lleva escrito.
const palabrasFeedback = computed(() => {
  const n = palabras.value;
  if (n === 0) return "Empieza cuando quieras…";
  if (n <= 10) return "Vas bien, sigue…";
  if (n <= 30) return "Sigue, lo estás haciendo bien 💬";
  if (n <= 60) return "Genial, ya vas tomando ritmo ✍️";
  return "Excelente entrada de hoy 🌟";
});

// ─── Racha de días consecutivos ──────────────────────────────────────
// Cuenta hacia atrás desde hoy (o desde ayer si hoy todavía no escribió)
// mientras haya entradas en días consecutivos.
function _isoLocal(d) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

const rachaDias = computed(() => {
  if (!entradasMock.value.length) return 0;
  const fechas = new Set(entradasMock.value.map((e) => e.fecha));
  const hoy = new Date();
  const hoyIso = _isoLocal(hoy);
  const ayer = new Date(hoy);
  ayer.setDate(ayer.getDate() - 1);
  const ayerIso = _isoLocal(ayer);

  // Punto de inicio: si escribió hoy, contamos desde hoy. Si solo ayer,
  // contamos desde ayer. Si ni hoy ni ayer, la racha está rota.
  const cursor = new Date(hoy);
  if (!fechas.has(hoyIso)) {
    if (!fechas.has(ayerIso)) return 0;
    cursor.setDate(cursor.getDate() - 1);
  }

  let count = 0;
  while (fechas.has(_isoLocal(cursor))) {
    count++;
    cursor.setDate(cursor.getDate() - 1);
  }
  return count;
});

const rachaTexto = computed(() => {
  const n = rachaDias.value;
  if (n === 0) return "Retoma hoy tu racha";
  if (n === 1) return "Día 1 — ¡Buen comienzo!";
  if (n <= 4) return `🔥 ${n} días seguidos`;
  if (n <= 9) return `🔥🔥 ${n} días seguidos — ¡Sigue así!`;
  if (n <= 14) return `🔥🔥🔥 ${n} días — ¡Eres constante!`;
  return `⭐ ${n} días — ¡Increíble constancia!`;
});

const MOODS = [
  { id: "soleado", label: "Buen día" },
  { id: "mixto", label: "Mezclado" },
  { id: "nublado", label: "Apagado" },
  { id: "lluvioso", label: "Difícil" },
];

async function guardarEntrada() {
  if (!texto.value.trim() || guardando.value) return;
  guardando.value = true;
  try {
    await api.crearEntradaDiario({
      texto: texto.value.trim(),
      estado_animo: moodSeleccionado.value,
      prompt_del_dia: promptDelDia.value,
    });

    // Recargamos el historial + ciclo para reflejar la entrada nueva
    await Promise.all([cargarEntradas(), cargarCiclo()]);

    texto.value = "";
    moodSeleccionado.value = null;
    abrirModalGuardado();
  } catch (e) {
    // Sin pantalla de error clínico — solo aviso suave
    alert(
      e.response?.data?.detail ||
        "No pudimos guardar tu entrada. Inténtalo de nuevo.",
    );
  } finally {
    guardando.value = false;
  }
}

// ─────────────────────────────────────────────────────────────────────────
// Pantalla "Mi diario" — entradas reales
// ─────────────────────────────────────────────────────────────────────────
// El backend devuelve { id, fecha, timestamp, estado_animo, preview }.
// El template las consume como { id, fecha, mood, texto } (texto = preview),
// así no tocamos el diseño.
const entradasMock = ref([]); // (nombre conservado para no tocar el template)
const cargandoEntradas = ref(false);

async function cargarEntradas() {
  cargandoEntradas.value = true;
  try {
    const data = await api.listarMisEntradasDiario();
    entradasMock.value = (data || []).map((e) => ({
      id: e.id,
      fecha: e.fecha, // "YYYY-MM-DD"
      mood: e.estado_animo,
      texto: e.preview,
    }));
  } catch (_) {
    entradasMock.value = [];
  } finally {
    cargandoEntradas.value = false;
  }
}

const entradaAbierta = ref(null);

async function abrirEntrada(e) {
  // Carga la entrada completa por id para mostrar el texto íntegro en el modal.
  try {
    const completa = await api.obtenerEntradaDiario(e.id);
    entradaAbierta.value = {
      id: completa.id,
      fecha: completa.fecha,
      mood: completa.estado_animo,
      texto: completa.texto,
    };
  } catch (_) {
    // Fallback: abrir con el preview que ya tenemos.
    entradaAbierta.value = e;
  }
}
function cerrarEntrada() {
  entradaAbierta.value = null;
}

function formatearFechaCorta(iso) {
  const d = new Date(iso + "T00:00:00");
  const hoyMs = new Date(
    hoy.toISOString().slice(0, 10) + "T00:00:00",
  ).getTime();
  const diff = Math.round((hoyMs - d.getTime()) / 86400000);
  if (diff === 0) return "Hoy";
  if (diff === 1) return "Ayer";
  if (diff < 7) return `Hace ${diff} días`;
  return d.toLocaleDateString("es-PE", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

function previewTexto(t, n = 140) {
  if (!t) return "";
  return t.length > n ? t.slice(0, n).trimEnd() + "…" : t;
}

// ─────────────────────────────────────────────────────────────────────────
// Pantalla "Apoyo" — recomendaciones, mensaje del psi, próxima cita
// ─────────────────────────────────────────────────────────────────────────
const recomendaciones = ref(null);
const mensajesPsi = ref([]);
const citasPropias = ref([]);
const cargandoApoyo = ref(false);

async function cargarApoyo() {
  cargandoApoyo.value = true;
  try {
    const [r, m, c] = await Promise.all([
      api.misRecomendaciones().catch(() => null),
      api.misMensajesPsicologo().catch(() => []),
      api.misCitas().catch(() => []),
    ]);
    recomendaciones.value = r;
    mensajesPsi.value = m || [];
    citasPropias.value = c || [];
  } finally {
    cargandoApoyo.value = false;
  }
}

const mensajesNoLeidos = computed(
  () => mensajesPsi.value.filter((m) => !m.leido).length,
);

const proximaCita = computed(() => {
  // Backend ordena ascendente por fecha+hora. Tomamos la primera no cancelada.
  return (
    citasPropias.value.find(
      (c) => c.estado !== "cancelada" && c.estado !== "completada",
    ) || null
  );
});

async function marcarMensajeLeido(id) {
  try {
    await api.marcarMensajePsicologoLeido(id);
    const m = mensajesPsi.value.find((x) => x.id === id);
    if (m) {
      m.leido = true;
      m.leido_at = new Date().toISOString();
    }
  } catch (_) {
    // silencioso — no es bloqueante
  }
}

function formatFechaHoraCita(fecha, hora) {
  if (!fecha) return "—";
  try {
    const d = new Date(`${fecha}T${hora || "00:00"}`);
    return d.toLocaleDateString("es-PE", {
      weekday: "long",
      day: "numeric",
      month: "long",
    }) + (hora ? ` · ${hora.slice(0, 5)}` : "");
  } catch (_) {
    return `${fecha} · ${hora || ""}`;
  }
}

function formatFechaCortaIso(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ─────────────────────────────────────────────────────────────────────────
// Cambiar de tab y resetear estados visuales
// ─────────────────────────────────────────────────────────────────────────
function irA(t) {
  tab.value = t;
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (t === "apoyo" && !recomendaciones.value) {
    cargarApoyo();
  }
  if (t === "proceso" && !ciclo.value) {
    cargarCiclo();
  }
}

onMounted(async () => {
  const params = new URLSearchParams(window.location.search);
  const t = params.get("tab");
  if (t && ["escribir", "diario", "proceso", "apoyo"].includes(t)) tab.value = t;

  // Pre-cargamos las entradas y el ciclo en paralelo.
  await Promise.all([cargarEntradas(), cargarCiclo()]);

  // Apoyo se carga en background para tenerlo listo al abrirlo.
  cargarApoyo();
});
</script>

<template>
  <div class="min-h-[calc(100vh-3.5rem)] bg-white pb-24">
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- TAB: ESCRIBIR                                                       -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section v-if="tab === 'escribir'" class="page-shell fade-in-up">
      <header class="mb-6">
        <p class="text-sm text-green-700 mb-1">
          {{ saludoTiempo }}, {{ primerNombre || "tú" }}.
        </p>
        <h1 class="hero-serif text-2xl sm:text-3xl">
          Hoy es <span class="hero-mint">{{ fechaLarga }}</span>
        </h1>
      </header>

      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <!-- DÍA N del ciclo de seguimiento                                       -->
      <!-- ═══════════════════════════════════════════════════════════════════ -->
      <div
        v-if="ciclo && ciclo.ciclo_actual"
        class="card p-4 mb-5"
        :class="{
          'border-l-4 border-l-amber-500 bg-amber-50/40':
            ciclo.estado === 'vencido',
          'border-l-4 border-l-green-600': ciclo.estado === 'en_curso',
        }"
      >
        <div class="flex items-baseline justify-between gap-3 flex-wrap">
          <div>
            <p
              class="text-[11px] uppercase tracking-wider font-semibold"
              :class="
                ciclo.estado === 'vencido' ? 'text-amber-700' : 'text-green-700'
              "
            >
              Ciclo de seguimiento #{{ ciclo.ciclo_actual.numero }}
            </p>
            <h2 class="text-xl font-bold text-ink-900 mt-0.5">
              {{ ciclo.mensaje }}
            </h2>
          </div>
          <div class="text-right">
            <p
              class="text-3xl font-bold"
              :class="
                ciclo.estado === 'vencido' ? 'text-amber-600' : 'text-green-700'
              "
            >
              {{ ciclo.ciclo_actual.dia_actual }}/{{ ciclo.dias_por_ciclo }}
            </p>
            <p class="text-[11px] text-ink-500">
              {{ ciclo.ciclo_actual.entradas_escritas }} entrada{{
                ciclo.ciclo_actual.entradas_escritas === 1 ? "" : "s"
              }}
              escrita{{ ciclo.ciclo_actual.entradas_escritas === 1 ? "" : "s" }}
            </p>
          </div>
        </div>

        <!-- Barra de progreso -->
        <div class="mt-3 h-2 bg-ink-100 rounded-full overflow-hidden">
          <div
            class="h-full transition-all duration-500"
            :class="
              ciclo.estado === 'vencido' ? 'bg-amber-500' : 'bg-green-600'
            "
            :style="`width: ${Math.min(ciclo.ciclo_actual.porcentaje, 100)}%`"
          ></div>
        </div>

        <p class="text-xs text-ink-500 mt-2">
          Empezó el {{ formatFechaCiclo(ciclo.ciclo_actual.inicio) }} ·
          hasta el {{ formatFechaCiclo(ciclo.ciclo_actual.fecha_limite) }}
        </p>
      </div>

      <!-- Prompt suave del día -->
      <div class="card-mint p-4 mb-5">
        <p
          class="text-[11px] uppercase tracking-wider text-green-700 font-semibold mb-1"
        >
          Si no sabes por dónde empezar
        </p>
        <p class="text-ink-800 leading-relaxed">{{ promptDelDia }}</p>
      </div>

      <!-- Racha de días consecutivos -->
      <div class="flex items-center justify-end mb-2">
        <span
          class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition"
          :class="
            rachaDias === 0
              ? 'bg-ink-100 text-ink-600'
              : 'bg-green-50 text-green-700 border border-green-200'
          "
          :title="rachaDias === 0 ? 'Escribe hoy para empezar una racha' : `Llevas ${rachaDias} día(s) consecutivo(s)`"
        >
          {{ rachaTexto }}
        </span>
      </div>

      <!-- Caja de escritura -->
      <div class="card p-0 overflow-hidden">
        <textarea
          v-model="texto"
          placeholder="Escribe lo que te pase por la cabeza. Esto es solo para ti."
          rows="14"
          class="w-full resize-none px-5 py-5 text-base leading-relaxed text-ink-900 placeholder:text-ink-400 bg-white focus:outline-none"
          :disabled="guardando"
        ></textarea>

        <!-- Contador + feedback -->
        <div
          class="border-t border-ink-100 px-5 py-3 flex items-center justify-end gap-3"
        >
          <p class="text-xs text-ink-500 transition-opacity duration-200">
            <span class="font-semibold text-ink-600">{{ palabras }}</span>
            {{ palabras === 1 ? "palabra" : "palabras" }} ·
            <span class="text-green-700">{{ palabrasFeedback }}</span>
          </p>
        </div>
      </div>

      <!-- ¿Cómo te sentiste hoy? — selector de mood destacado -->
      <div class="mt-5 mb-4">
        <p
          class="text-[11px] uppercase tracking-wider text-green-700 font-semibold mb-3"
        >
          ¿Cómo te sentiste hoy?
        </p>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <button
            v-for="m in MOODS"
            :key="m.id"
            type="button"
            @click="
              moodSeleccionado = moodSeleccionado === m.id ? null : m.id
            "
            :class="[
              'flex flex-col items-center justify-center gap-2 px-3 py-4 rounded-xl border-2 transition text-sm font-medium',
              moodSeleccionado === m.id
                ? 'bg-green-600 border-green-600 text-white shadow-green'
                : 'bg-white border-ink-200 text-ink-700 hover:border-green-500',
            ]"
          >
            <!-- Ícono climático -->
            <svg
              v-if="m.id === 'soleado'"
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="12" cy="12" r="4" />
              <line x1="12" y1="2" x2="12" y2="4" />
              <line x1="12" y1="20" x2="12" y2="22" />
              <line x1="4.93" y1="4.93" x2="6.34" y2="6.34" />
              <line x1="17.66" y1="17.66" x2="19.07" y2="19.07" />
              <line x1="2" y1="12" x2="4" y2="12" />
              <line x1="20" y1="12" x2="22" y2="12" />
              <line x1="4.93" y1="19.07" x2="6.34" y2="17.66" />
              <line x1="17.66" y1="6.34" x2="19.07" y2="4.93" />
            </svg>
            <svg
              v-else-if="m.id === 'mixto'"
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <circle cx="7" cy="9" r="3" />
              <path
                d="M11 18a4 4 0 0 0 0-8 6 6 0 0 0-11.6 1.5A4 4 0 0 0 4 18"
                transform="translate(6 0)"
              />
            </svg>
            <svg
              v-else-if="m.id === 'nublado'"
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M17 18a5 5 0 0 0 0-10 7 7 0 0 0-13.5 2A5 5 0 0 0 5 18z"
              />
            </svg>
            <svg
              v-else
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M17 14a5 5 0 0 0 0-10 7 7 0 0 0-13.5 2A5 5 0 0 0 5 14"
              />
              <line x1="8" y1="19" x2="8" y2="21" />
              <line x1="12" y1="19" x2="12" y2="22" />
              <line x1="16" y1="19" x2="16" y2="21" />
            </svg>
            <span>{{ m.label }}</span>
          </button>
        </div>
      </div>

      <!-- Sello de privacidad -->
      <div
        class="mt-4 flex items-center gap-2 text-xs text-ink-500 justify-center"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect x="3" y="11" width="18" height="11" rx="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
        Solo tú ves lo que escribes aquí.
      </div>

      <!-- Guardar -->
      <div class="mt-5 flex items-center justify-between gap-3 flex-wrap">
        <span class="text-xs text-ink-400">
          Puedes guardar cuando quieras. No hay forma "correcta".
        </span>
        <button
          @click="guardarEntrada"
          :disabled="!texto.trim() || guardando"
          class="btn-primary"
        >
          {{ guardando ? "Guardando…" : "Guardar entrada" }}
        </button>
      </div>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- TAB: MI DIARIO                                                      -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section v-else-if="tab === 'diario'" class="page-shell fade-in-up">
      <header class="mb-6">
        <h1 class="hero-serif text-2xl sm:text-3xl">
          Mi <span class="hero-mint">diario</span>
        </h1>
        <p class="mt-2 text-ink-600 text-sm">
          Lo que has escrito hasta ahora. Solo tú lo ves.
        </p>
      </header>

      <p
        v-if="!entradasMock.length"
        class="text-ink-500 text-sm text-center py-12"
      >
        Todavía no has escrito nada. Pásate por "Escribir" cuando quieras.
      </p>

      <ul v-else class="space-y-3">
        <li
          v-for="e in entradasMock"
          :key="e.id"
          @click="abrirEntrada(e)"
          class="card p-5 cursor-pointer hover:border-green-500 transition"
        >
          <div class="flex items-start justify-between gap-3 mb-2">
            <p
              class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
            >
              {{ formatearFechaCorta(e.fecha) }}
            </p>
            <span
              v-if="e.mood"
              class="text-xs text-green-700 inline-flex items-center gap-1"
            >
              <svg
                v-if="e.mood === 'soleado'"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              >
                <circle cx="12" cy="12" r="4" />
                <line x1="12" y1="2" x2="12" y2="4" />
                <line x1="12" y1="20" x2="12" y2="22" />
                <line x1="4.93" y1="4.93" x2="6.34" y2="6.34" />
                <line x1="17.66" y1="17.66" x2="19.07" y2="19.07" />
                <line x1="2" y1="12" x2="4" y2="12" />
                <line x1="20" y1="12" x2="22" y2="12" />
              </svg>
              <svg
                v-else-if="e.mood === 'mixto'"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle cx="7" cy="9" r="3" />
                <path
                  d="M11 18a4 4 0 0 0 0-8 6 6 0 0 0-11.6 1.5A4 4 0 0 0 4 18"
                  transform="translate(6 0)"
                />
              </svg>
              <svg
                v-else-if="e.mood === 'nublado'"
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M17 18a5 5 0 0 0 0-10 7 7 0 0 0-13.5 2A5 5 0 0 0 5 18z"
                />
              </svg>
              <svg
                v-else
                width="12"
                height="12"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M17 14a5 5 0 0 0 0-10 7 7 0 0 0-13.5 2A5 5 0 0 0 5 14"
                />
                <line x1="8" y1="19" x2="8" y2="21" />
                <line x1="12" y1="19" x2="12" y2="22" />
                <line x1="16" y1="19" x2="16" y2="21" />
              </svg>
              {{ MOODS.find((m) => m.id === e.mood)?.label }}
            </span>
          </div>
          <p class="text-sm text-ink-800 leading-relaxed">
            {{ previewTexto(e.texto) }}
          </p>
        </li>
      </ul>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- TAB: APOYO                                                          -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section v-else-if="tab === 'apoyo'" class="page-shell fade-in-up">
      <header class="mb-6">
        <h1 class="hero-serif text-2xl sm:text-3xl">
          Tu espacio de <span class="hero-mint">apoyo</span>
        </h1>
        <p class="mt-2 text-ink-600 text-sm">
          Consejos pensados para vos, lo que tu psicólogo te quiere decir, y
          tus próximas citas.
        </p>
      </header>

      <!-- ─────────────────────────────────────────────────────────────── -->
      <!-- 1) MENSAJE DEL PSICÓLOGO                                         -->
      <!-- ─────────────────────────────────────────────────────────────── -->
      <div v-if="mensajesPsi.length" class="card p-5 mb-5">
        <div class="flex items-baseline justify-between mb-3">
          <p
            class="text-[11px] uppercase tracking-wider text-green-700 font-semibold"
          >
            Mensaje de tu psicólogo
          </p>
          <span
            v-if="mensajesNoLeidos"
            class="text-[11px] bg-green-600 text-white px-2 py-0.5 rounded-full font-semibold"
          >
            {{ mensajesNoLeidos }} nuevo{{ mensajesNoLeidos > 1 ? "s" : "" }}
          </span>
        </div>
        <ul class="space-y-3">
          <li
            v-for="m in mensajesPsi.slice(0, 3)"
            :key="m.id"
            class="border-l-4 pl-4 py-1"
            :class="m.leido ? 'border-l-ink-200' : 'border-l-green-600'"
          >
            <p
              class="text-sm text-ink-900 leading-relaxed whitespace-pre-wrap"
            >
              {{ m.mensaje }}
            </p>
            <div
              class="flex items-center justify-between gap-3 mt-2 text-[11px] text-ink-500"
            >
              <span>{{ formatFechaCortaIso(m.created_at) }}</span>
              <button
                v-if="!m.leido"
                @click="marcarMensajeLeido(m.id)"
                class="text-green-700 font-semibold hover:underline"
              >
                Marcar leído
              </button>
              <span v-else class="text-ink-400">Leído</span>
            </div>
          </li>
        </ul>
      </div>

      <!-- ─────────────────────────────────────────────────────────────── -->
      <!-- 2) PRÓXIMA CITA                                                  -->
      <!-- ─────────────────────────────────────────────────────────────── -->
      <div v-if="proximaCita" class="card p-5 mb-5 border-l-4 border-l-green-600">
        <p
          class="text-[11px] uppercase tracking-wider text-green-700 font-semibold mb-1"
        >
          Próxima cita
        </p>
        <p class="text-lg font-semibold text-ink-900">
          {{ formatFechaHoraCita(proximaCita.fecha, proximaCita.hora) }}
        </p>
        <p class="text-sm text-ink-600 mt-1 capitalize">
          Modalidad: <strong>{{ proximaCita.modalidad }}</strong>
          <span
            class="ml-2 text-[11px] uppercase tracking-wider font-semibold"
            :class="
              proximaCita.estado === 'confirmada'
                ? 'text-green-700'
                : 'text-amber-700'
            "
          >
            · {{ proximaCita.estado }}
          </span>
        </p>
        <p
          v-if="proximaCita.notas"
          class="text-sm text-ink-600 mt-2 italic border-t border-ink-100 pt-2"
        >
          "{{ proximaCita.notas }}"
        </p>
      </div>

      <!-- ─────────────────────────────────────────────────────────────── -->
      <!-- 3) RECOMENDACIONES PERSONALIZADAS                                -->
      <!-- ─────────────────────────────────────────────────────────────── -->
      <div v-if="cargandoApoyo" class="text-center text-ink-500 py-6">
        Preparando tu espacio…
      </div>

      <div v-else-if="recomendaciones && recomendaciones.tiene_datos" class="mb-5">
        <p
          class="text-[11px] uppercase tracking-wider text-green-700 font-semibold mb-1"
        >
          Pensado para vos
        </p>
        <p class="text-sm text-ink-600 mb-4 leading-relaxed">
          {{ recomendaciones.mensaje }}
        </p>

        <div class="space-y-4">
          <article
            v-for="r in recomendaciones.recomendaciones"
            :key="r.clave"
            class="card p-5"
            :class="{
              'border-l-4 border-l-red-600': r.tono === 'urgente',
              'border-l-4 border-l-green-600 bg-green-50/40':
                r.tono === 'refuerzo',
            }"
          >
            <div class="flex items-start gap-2 mb-3">
              <span
                v-if="r.tono === 'refuerzo'"
                class="text-[10px] uppercase tracking-wider font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded mt-0.5"
              >
                Lo que estás haciendo bien
              </span>
            </div>
            <h3 class="text-base font-semibold text-ink-900 mb-2">
              {{ r.titulo }}
            </h3>
            <p
              v-if="r.validacion"
              class="text-sm text-ink-700 leading-relaxed mb-3 italic"
            >
              {{ r.validacion }}
            </p>
            <ul class="space-y-2">
              <li
                v-for="(c, i) in r.consejos"
                :key="i"
                class="text-sm text-ink-700 leading-relaxed flex gap-3"
              >
                <span
                  class="text-green-600 font-bold shrink-0 select-none mt-0.5"
                  >·</span
                >
                <span>{{ c }}</span>
              </li>
            </ul>
          </article>
        </div>
      </div>

      <div
        v-else-if="recomendaciones && !recomendaciones.tiene_datos"
        class="card-mint p-5 mb-5"
      >
        <p class="text-ink-900 font-medium">Aún no escribiste en tu diario.</p>
        <p class="text-sm text-ink-700 mt-1.5 leading-relaxed">
          {{ recomendaciones.mensaje }}
        </p>
      </div>

      <!-- Validación cálida -->
      <div class="card-mint p-5 mb-5">
        <p class="text-ink-900 font-medium">Gracias por escribir hoy.</p>
        <p class="text-sm text-ink-700 mt-1.5 leading-relaxed">
          Poner en palabras lo que sientes ya es un acto importante. Si te
          quedaste con ganas de hablar con alguien, aquí tienes opciones.
        </p>
      </div>

      <!-- Línea 113 -->
      <a
        href="tel:113"
        class="card p-5 mb-3 block hover:border-green-500 transition"
      >
        <p
          class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
        >
          Línea 113 — MINSA · opción 5
        </p>
        <p class="text-2xl font-semibold text-ink-900 mt-1 tracking-tight">
          113
        </p>
        <p class="text-sm text-ink-600 mt-1.5 leading-relaxed">
          Gratuito, confidencial y atiende a cualquier hora. Puedes hablar con
          alguien aunque no sea una emergencia.
        </p>
      </a>

      <!-- Departamento psicopedagógico -->
      <div class="card p-5 mb-3">
        <p
          class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
        >
          Departamento psicopedagógico
        </p>
        <p class="text-lg font-semibold text-ink-900 mt-1">
          La psicóloga del colegio
        </p>
        <p class="text-sm text-ink-600 mt-1.5 leading-relaxed">
          Pasa por su oficina o avísale a tu tutor/a si quieres hablar. Lo que
          conversen queda entre ustedes.
        </p>
      </div>

      <!-- Línea 106 SAMU -->
      <a
        href="tel:106"
        class="card p-5 block hover:border-green-500 transition"
      >
        <p
          class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
        >
          Línea 106 — SAMU · emergencias
        </p>
        <p class="text-2xl font-semibold text-ink-900 mt-1 tracking-tight">
          106
        </p>
        <p class="text-sm text-ink-600 mt-1.5 leading-relaxed">
          Solo si lo necesitas ahora, si te sientes en peligro o si alguien
          cerca tuyo lo está. Atienden 24/7.
        </p>
      </a>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- TAB: PROCESO — calendario del ciclo + sesiones cerradas              -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <section v-if="tab === 'proceso'" class="page-shell fade-in-up">
      <header class="mb-6">
        <h1 class="hero-serif text-2xl sm:text-3xl">
          Tu <span class="hero-mint">proceso</span>
        </h1>
        <p class="mt-2 text-ink-600 text-sm">
          Acá ves cómo va tu ciclo actual, qué viene y qué quedó de las
          sesiones anteriores.
        </p>
      </header>

      <div v-if="cargandoCiclo" class="text-center text-ink-500 py-6">
        Cargando tu proceso…
      </div>

      <div v-else-if="ciclo && ciclo.estado === 'sin_iniciar'" class="card-mint p-5">
        <p class="text-ink-900 font-medium">Tu primer ciclo empieza cuando escribas.</p>
        <p class="text-sm text-ink-700 mt-1.5 leading-relaxed">
          {{ ciclo.mensaje }}
        </p>
      </div>

      <template v-else-if="ciclo && ciclo.ciclo_actual">
        <!-- ── Ciclo actual ───────────────────────────────────────── -->
        <div
          class="card p-5 mb-5"
          :class="
            ciclo.estado === 'vencido'
              ? 'border-l-4 border-l-amber-500'
              : 'border-l-4 border-l-green-600'
          "
        >
          <p
            class="text-[11px] uppercase tracking-wider font-semibold mb-1"
            :class="
              ciclo.estado === 'vencido' ? 'text-amber-700' : 'text-green-700'
            "
          >
            Ciclo de seguimiento #{{ ciclo.ciclo_actual.numero }}
          </p>
          <p class="text-lg font-semibold text-ink-900">
            {{ ciclo.mensaje }}
          </p>
          <p class="text-xs text-ink-500 mt-1">
            Empezó el {{ formatFechaCiclo(ciclo.ciclo_actual.inicio) }} ·
            hasta el {{ formatFechaCiclo(ciclo.ciclo_actual.fecha_limite) }}
          </p>

        </div>

        <!-- ── Calendario de mes ───────────────────────────────────── -->
        <div class="card p-5 mb-5">
          <div class="flex items-center justify-between mb-4">
            <button
              @click="cambiarMes(-1)"
              class="btn-ghost btn-sm"
              aria-label="Mes anterior"
            >
              ‹
            </button>
            <div class="text-center">
              <h3 class="text-base font-semibold text-ink-900 capitalize">
                {{ tituloMes }}
              </h3>
              <button
                @click="irAHoy"
                class="text-xs text-green-700 font-semibold hover:underline"
              >
                Ir a hoy
              </button>
            </div>
            <button
              @click="cambiarMes(1)"
              class="btn-ghost btn-sm"
              aria-label="Mes siguiente"
            >
              ›
            </button>
          </div>

          <!-- Encabezado días de semana -->
          <div class="grid grid-cols-7 gap-1.5 mb-2">
            <div
              v-for="d in DIAS_SEMANA"
              :key="d"
              class="text-center text-[11px] uppercase tracking-wider font-semibold text-ink-500 py-1"
            >
              {{ d }}
            </div>
          </div>

          <!-- Filas del mes -->
          <div class="space-y-1.5">
            <div
              v-for="(fila, i) in matrizCalendario"
              :key="i"
              class="grid grid-cols-7 gap-1.5"
            >
              <div
                v-for="(celda, j) in fila"
                :key="j"
                class="aspect-square rounded-lg flex flex-col items-center justify-center text-sm relative transition"
                :class="
                  !celda
                    ? 'bg-transparent'
                    : celda.tieneEntrada
                      ? 'bg-green-600 text-white font-semibold'
                      : celda.esSesionCerrada
                        ? 'bg-green-100 text-green-800 ring-2 ring-green-600'
                        : celda.esProximaCita
                          ? 'bg-amber-100 text-amber-800 ring-2 ring-amber-500'
                          : celda.esHoy
                            ? 'bg-green-50 text-green-800 ring-2 ring-green-500'
                            : celda.enCicloActual
                              ? 'bg-green-50/40 text-ink-700'
                              : 'bg-ink-50/40 text-ink-400'
                "
                :title="celda ? tituloCelda(celda) : ''"
              >
                <template v-if="celda">
                  <span>{{ celda.num }}</span>
                  <span
                    v-if="celda.esSesionCerrada"
                    class="absolute bottom-0.5 text-[9px] font-bold leading-none"
                  >
                    S{{ celda.sesionNumero }}
                  </span>
                  <span
                    v-else-if="celda.esProximaCita"
                    class="absolute bottom-0.5 text-[9px] font-bold leading-none"
                  >
                    cita
                  </span>
                </template>
              </div>
            </div>
          </div>

          <!-- Leyenda -->
          <div class="flex items-center gap-4 mt-4 text-[11px] text-ink-500 flex-wrap">
            <span class="inline-flex items-center gap-1.5">
              <span class="w-3 h-3 rounded bg-green-600"></span>
              Escribiste
            </span>
            <span class="inline-flex items-center gap-1.5">
              <span class="w-3 h-3 rounded bg-green-50 ring-2 ring-green-500"></span>
              Hoy
            </span>
            <span class="inline-flex items-center gap-1.5">
              <span class="w-3 h-3 rounded bg-green-100 ring-2 ring-green-600"></span>
              Sesión cerrada
            </span>
            <span class="inline-flex items-center gap-1.5">
              <span class="w-3 h-3 rounded bg-amber-100 ring-2 ring-amber-500"></span>
              Próxima cita
            </span>
            <span class="inline-flex items-center gap-1.5">
              <span class="w-3 h-3 rounded bg-green-50/40 ring-1 ring-green-200"></span>
              Ciclo actual
            </span>
          </div>
        </div>

        <!-- ── Próxima cita ───────────────────────────────────────── -->
        <div
          v-if="ciclo.proxima_cita"
          class="card p-5 mb-5 border-l-4 border-l-green-600"
        >
          <p
            class="text-[11px] uppercase tracking-wider text-green-700 font-semibold mb-1"
          >
            Próxima sesión
          </p>
          <p class="text-lg font-semibold text-ink-900">
            {{ formatFechaCiclo(ciclo.proxima_cita.fecha) }} ·
            {{ ciclo.proxima_cita.hora.slice(0, 5) }}
          </p>
          <p class="text-sm text-ink-600 mt-1 capitalize">
            Modalidad: <strong>{{ ciclo.proxima_cita.modalidad }}</strong>
            <span
              class="ml-2 text-[11px] uppercase tracking-wider font-semibold"
              :class="
                ciclo.proxima_cita.estado === 'confirmada'
                  ? 'text-green-700'
                  : 'text-amber-700'
              "
            >
              · {{ ciclo.proxima_cita.estado }}
            </span>
          </p>
        </div>

        <div
          v-else
          class="card p-5 mb-5 border-l-4 border-l-ink-200"
        >
          <p
            class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold mb-1"
          >
            Próxima sesión
          </p>
          <p class="text-sm text-ink-700">
            Aún no tienes una cita agendada. Tu psicólogo coordinará una
            cuando estés cerca de terminar este ciclo.
          </p>
        </div>

        <!-- ── Sesiones cerradas ──────────────────────────────────── -->
        <div v-if="ciclo.sesiones_cerradas.length" class="space-y-3">
          <h2 class="section-title !mb-1">Sesiones anteriores</h2>
          <p class="text-sm text-ink-500 mb-3">
            Lo que conversaste con tu psicólogo en cada cierre de ciclo.
          </p>
          <article
            v-for="s in [...ciclo.sesiones_cerradas].reverse()"
            :key="s.numero"
            class="card p-5"
          >
            <div class="flex items-baseline justify-between gap-3 mb-2">
              <p class="text-base font-semibold text-ink-900">
                Sesión #{{ s.numero }}
              </p>
              <p class="text-xs text-ink-500">
                {{ formatFechaCiclo(s.fecha) }}
              </p>
            </div>
            <p class="text-xs text-ink-500 mb-3">
              Ciclo del {{ formatFechaCiclo(s.inicio_ciclo) }} al
              {{ formatFechaCiclo(s.fecha_cierre) }} · {{ s.entradas_escritas }}
              entradas escritas
            </p>
            <div v-if="s.resumen_para_estudiante" class="card-mint p-4">
              <p
                class="text-[11px] uppercase tracking-wider text-green-700 font-semibold mb-1"
              >
                Lo que quedó de la sesión
              </p>
              <p
                class="text-sm text-ink-900 leading-relaxed whitespace-pre-wrap"
              >
                {{ s.resumen_para_estudiante }}
              </p>
            </div>
            <p v-else class="text-sm text-ink-500 italic">
              Tu psicólogo todavía no escribió un resumen de esta sesión.
            </p>
          </article>
        </div>
      </template>
    </section>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- MODAL: confirmación post-guardado                                    -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div
        v-if="modalGuardado.abierto"
        @click.self="cerrarModalGuardado"
        class="fixed inset-0 z-50 bg-ink-900/40 flex items-center justify-center p-4 fade-in-up"
      >
        <div
          class="bg-white rounded-2xl border border-ink-200 shadow-card w-full max-w-md p-6 text-center"
        >
          <!-- Ícono de check verde -->
          <div
            class="mx-auto w-16 h-16 rounded-full bg-green-100 text-green-700 flex items-center justify-center mb-4"
          >
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>

          <h2 class="text-lg font-semibold text-ink-900 leading-snug">
            {{ modalGuardado.frase }}
          </h2>

          <!-- Consejo del día (cargado del backend) -->
          <div
            v-if="modalGuardado.consejo"
            class="card-mint p-4 mt-5 text-left"
          >
            <p
              class="text-[11px] uppercase tracking-wider text-green-700 font-semibold mb-1"
            >
              Para llevar de hoy
            </p>
            <p class="text-sm text-ink-800 leading-relaxed">
              {{ modalGuardado.consejo }}
            </p>
          </div>

          <div class="flex gap-2 mt-5">
            <button @click="verMiDiario" class="btn-secondary flex-1">
              Ver mi diario
            </button>
            <button @click="cerrarModalGuardado" class="btn-primary flex-1">
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- MODAL: ver entrada completa                                          -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <Teleport to="body">
      <div
        v-if="entradaAbierta"
        @click.self="cerrarEntrada"
        class="fixed inset-0 z-50 bg-ink-900/40 flex items-center justify-center p-4 fade-in-up"
      >
        <div
          class="bg-white rounded-xl border border-ink-200 shadow-card w-full max-w-2xl p-6 max-h-[85vh] overflow-y-auto"
        >
          <div class="flex items-start justify-between gap-3 mb-4">
            <div>
              <p
                class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
              >
                {{ formatearFechaCorta(entradaAbierta.fecha) }}
              </p>
              <p v-if="entradaAbierta.mood" class="text-xs text-green-700 mt-1">
                {{ MOODS.find((m) => m.id === entradaAbierta.mood)?.label }}
              </p>
            </div>
            <button
              @click="cerrarEntrada"
              class="text-ink-500 hover:text-ink-900 transition"
              aria-label="Cerrar"
            >
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              >
                <line x1="6" y1="6" x2="18" y2="18" />
                <line x1="6" y1="18" x2="18" y2="6" />
              </svg>
            </button>
          </div>
          <p class="text-ink-900 leading-relaxed whitespace-pre-wrap">
            {{ entradaAbierta.texto }}
          </p>
        </div>
      </div>
    </Teleport>

    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <!-- TABBAR inferior                                                     -->
    <!-- ═══════════════════════════════════════════════════════════════════ -->
    <nav
      class="fixed bottom-0 left-0 right-0 bg-white border-t border-ink-100 shadow-soft z-30"
    >
      <div class="max-w-3xl mx-auto grid grid-cols-4">
        <button
          type="button"
          @click="irA('escribir')"
          :class="[
            'flex flex-col items-center justify-center gap-1 py-3 transition',
            tab === 'escribir'
              ? 'text-green-700'
              : 'text-ink-500 hover:text-ink-900',
          ]"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M12 20h9" />
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
          </svg>
          <span class="text-xs font-medium">Escribir</span>
        </button>

        <button
          type="button"
          @click="irA('diario')"
          :class="[
            'flex flex-col items-center justify-center gap-1 py-3 transition',
            tab === 'diario'
              ? 'text-green-700'
              : 'text-ink-500 hover:text-ink-900',
          ]"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path
              d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"
            />
          </svg>
          <span class="text-xs font-medium">Mi diario</span>
        </button>

        <button
          type="button"
          @click="irA('proceso')"
          :class="[
            'flex flex-col items-center justify-center gap-1 py-3 transition',
            tab === 'proceso'
              ? 'text-green-700'
              : 'text-ink-500 hover:text-ink-900',
          ]"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span class="text-xs font-medium">Proceso</span>
        </button>

        <button
          type="button"
          @click="irA('apoyo')"
          :class="[
            'flex flex-col items-center justify-center gap-1 py-3 transition',
            tab === 'apoyo'
              ? 'text-green-700'
              : 'text-ink-500 hover:text-ink-900',
          ]"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"
            />
          </svg>
          <span class="text-xs font-medium">Apoyo</span>
        </button>
      </div>
    </nav>
  </div>
</template>
