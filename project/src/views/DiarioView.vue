<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import SamiEncuestaCierre from "../components/SamiEncuestaCierre.vue";
import {
  TAGS,
  fmtLong,
  fmtMonth,
  dowAb,
  dayNum,
  fromBackend,
  joinEntry,
  todayIso,
  wordCount,
} from "../composables/samiHelpers";

const route = useRoute();
const router = useRouter();

const mode = ref("diary"); // 'diary' | 'encuesta'
const filter = ref("all"); // 'all' | 'hoy' | tag id
const selectedId = ref(null);
const entries = ref([]); // sami-shape entries (id, date, title, body, tag…)
const ciclo = ref(null);
const encuesta = ref(null);
const toast = ref("");
let toastTimer = null;
let saveTimer = null;
let saveCounter = 0;

const hoy = todayIso();

// ─── Cycle daily survey (localStorage) ────────────────────────────────
const CYCLE_KEY = "sami-cycle-v1";
const cycleAnswers = ref({});
try {
  cycleAnswers.value = JSON.parse(localStorage.getItem(CYCLE_KEY)) || {};
} catch (_) {
  cycleAnswers.value = {};
}

function submitCycleDaily(date, values) {
  cycleAnswers.value = { ...cycleAnswers.value, [date]: values };
  localStorage.setItem(CYCLE_KEY, JSON.stringify(cycleAnswers.value));
  showToast("Encuesta del día enviada");
}

const cycleQuestions = [
  { id: "animo", q: "¿Cómo estuvo tu ánimo hoy?", opts: ["Muy bajo", "Bajo", "Normal", "Bien", "Muy bien"] },
  { id: "sueno", q: "¿Qué tal dormiste anoche?", opts: ["Muy mal", "Mal", "Regular", "Bien", "Muy bien"] },
  { id: "carga", q: "¿Qué tan pesado se sintió el día?", opts: ["Nada", "Poco", "Algo", "Bastante", "Mucho"] },
];
const cycleValues = ref({});
const cycleDayDone = computed(() => !!cycleAnswers.value[hoy]);
const cycleDayListo = computed(() =>
  cycleQuestions.every((q) => cycleValues.value[q.id] != null),
);

// ─── Carga inicial ────────────────────────────────────────────────────
async function cargarEntradas() {
  try {
    const data = await api.listarMisEntradasDiario();
    // Backend devuelve preview (recortado). Para edición necesitamos el
    // texto completo de la entrada de hoy. La traemos por separado.
    let list = (data || []).map(fromBackend);
    const hoyServer = list.find((e) => e.date === hoy);
    if (hoyServer) {
      try {
        const full = await api.obtenerEntradaDiario(hoyServer.id);
        const parsed = fromBackend(full);
        list = list.map((e) => (e.id === hoyServer.id ? parsed : e));
      } catch (_) {}
    }
    entries.value = list;
  } catch (_) {
    entries.value = [];
  }
}

async function cargarCiclo() {
  try {
    ciclo.value = await api.miCiclo();
  } catch (_) {
    ciclo.value = null;
  }
}

async function cargarEncuesta() {
  try {
    const data = await api.encuestaPendiente();
    encuesta.value = data?.pendiente ? data.encuesta : null;
  } catch (_) {
    encuesta.value = null;
  }
}

// ─── Vida del componente ──────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([cargarEntradas(), cargarCiclo(), cargarEncuesta()]);

  // Intent desde query string
  const q = route.query;
  if (q.encuesta === "1" && encuesta.value) {
    mode.value = "encuesta";
  } else if (q.compose === "1") {
    nuevaEntrada();
  } else if (q.entry) {
    const id = String(q.entry);
    if (entries.value.find((e) => e.id === id)) {
      selectedId.value = id;
      filter.value = "all";
    }
  } else {
    // Selección por defecto: entrada de hoy si existe, sino primera
    const hoyEntry = entries.value.find((e) => e.date === hoy);
    selectedId.value = hoyEntry?.id || entries.value[0]?.id || null;
  }
});

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
  if (saveTimer) clearTimeout(saveTimer);
});

function showToast(msg) {
  toast.value = msg;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.value = ""), 2400);
}

// ─── Listado filtrado y agrupado ─────────────────────────────────────
const visibles = computed(() => {
  if (filter.value === "all") return entries.value;
  if (filter.value === "hoy") return entries.value.filter((e) => e.date === hoy);
  return entries.value.filter((e) => e.tag === filter.value);
});

const grupos = computed(() => {
  const out = [];
  for (const e of visibles.value) {
    const m = fmtMonth(e.date);
    if (!out.length || out[out.length - 1].month !== m) {
      out.push({ month: m, items: [] });
    }
    out[out.length - 1].items.push(e);
  }
  return out;
});

const selected = computed(
  () => entries.value.find((e) => e.id === selectedId.value) || null,
);

const countAll = computed(() => entries.value.length);
const countHoy = computed(
  () => entries.value.filter((e) => e.date === hoy).length,
);
function countTag(tagId) {
  return entries.value.filter((e) => e.tag === tagId).length;
}

// ─── Edición de entrada ───────────────────────────────────────────────
function nuevaEntrada() {
  const existente = entries.value.find((e) => e.date === hoy);
  if (existente) {
    selectedId.value = existente.id;
    filter.value = "all";
    return;
  }
  // Stub local sin POST. Se POSTea cuando el usuario escriba algo.
  const stub = {
    id: "u-" + Date.now(),
    date: hoy,
    title: "",
    body: "",
    tag: null,
    _raw: "",
    _unsaved: true,
  };
  entries.value = [stub, ...entries.value];
  selectedId.value = stub.id;
  filter.value = "all";
}

function patchEntry(id, patch) {
  entries.value = entries.value.map((e) =>
    e.id === id ? { ...e, ...patch } : e,
  );
}

function onEditTitle(e) {
  if (!selected.value) return;
  patchEntry(selected.value.id, { title: e.target.value });
  scheduleSave(selected.value.id);
}
function onEditBody(e) {
  if (!selected.value) return;
  patchEntry(selected.value.id, { body: e.target.value });
  scheduleSave(selected.value.id);
}
function onToggleTag(tagId) {
  if (!selected.value) return;
  const cur = selected.value.tag === tagId ? null : tagId;
  patchEntry(selected.value.id, { tag: cur });
  scheduleSave(selected.value.id);
}

function scheduleSave(id) {
  saveCounter += 1;
  const mine = saveCounter;
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    if (mine !== saveCounter) return;
    persistir(id);
  }, 700);
}

async function persistir(id) {
  const e = entries.value.find((x) => x.id === id);
  if (!e) return;
  const texto = joinEntry({ title: e.title, body: e.body, tag: e.tag });
  if (!texto) return; // backend no permite vacío

  try {
    if (e._unsaved || String(e.id).startsWith("u-")) {
      const data = await api.crearEntradaDiario({ texto });
      const nuevoId = String(data.id);
      entries.value = entries.value.map((x) =>
        x.id === e.id
          ? { ...x, id: nuevoId, _unsaved: false, _raw: data.texto }
          : x,
      );
      if (selectedId.value === e.id) selectedId.value = nuevoId;
      // refresca ciclo (puede haber empezado uno nuevo)
      cargarCiclo();
    } else {
      // PUT: solo permitido para hoy
      if (e.date !== hoy) return;
      await api.actualizarEntradaDiario(e.id, { texto });
    }
  } catch (err) {
    // Silencioso: el siguiente cambio lo reintenta.
    console.warn("No pude guardar la entrada:", err?.response?.data || err);
  }
}

// ─── Ciclo strip ──────────────────────────────────────────────────────
const cicloLength = 14;
const cicloDia = computed(() => {
  if (!ciclo.value?.ciclo_actual) return 0;
  return Math.min(ciclo.value.ciclo_actual.dia_actual || 0, cicloLength);
});
const cicloDone = computed(() => cicloDia.value >= cicloLength);

// ─── Modo encuesta ────────────────────────────────────────────────────
function abrirEncuesta() {
  if (encuesta.value) mode.value = "encuesta";
}

async function onEncuestaCerrada() {
  mode.value = "diary";
  await Promise.all([cargarCiclo(), cargarEncuesta()]);
}

function onEncuestaVolver() {
  mode.value = "diary";
}

// ─── Watch: actualizar cycleValues cuando cambia hoy ──────────────────
watch(
  () => cycleAnswers.value[hoy],
  (v) => {
    if (v) cycleValues.value = { ...v };
  },
  { immediate: true },
);

const wordsEntry = computed(() =>
  wordCount((selected.value?.title || "") + " " + (selected.value?.body || "")),
);
</script>

<template>
  <div v-if="mode === 'encuesta' && encuesta" class="sami-shell">
    <SamiEncuestaCierre
      :encuesta="encuesta"
      @cerrada="onEncuestaCerrada"
      @volver="onEncuestaVolver"
    />
  </div>

  <div v-else class="diary" data-screen-label="Diario">
    <!-- ── Panel 1 — Sidebar ──────────────────────────────────────── -->
    <aside class="d-side">
      <div class="group">
        <button
          class="row"
          :class="filter === 'hoy' ? 'on' : ''"
          type="button"
          @click="filter = 'hoy'"
        >
          Hoy
          <span class="count">{{ countHoy }}</span>
        </button>
        <button
          class="row"
          :class="filter === 'all' ? 'on' : ''"
          type="button"
          @click="filter = 'all'"
        >
          Todas las entradas
          <span class="count">{{ countAll }}</span>
        </button>
      </div>
      <div class="group">
        <div class="group-label">Etiquetas</div>
        <button
          v-for="(t, id) in TAGS"
          :key="id"
          class="row"
          :class="filter === id ? 'on' : ''"
          type="button"
          @click="filter = id"
        >
          <span class="dot" :style="{ background: t.color }"></span>
          {{ t.label }}
          <span class="count">{{ countTag(id) }}</span>
        </button>
      </div>
    </aside>

    <!-- ── Panel 2 — Lista de entradas ────────────────────────────── -->
    <div class="d-list">
      <div class="d-list-head">
        <span class="month">Diario</span>
        <button
          class="newbtn"
          type="button"
          title="Nueva entrada"
          @click="nuevaEntrada"
        >
          +
        </button>
      </div>
      <div v-for="g in grupos" :key="g.month">
        <div class="month-label">{{ g.month }}</div>
        <button
          v-for="e in g.items"
          :key="e.id"
          class="entry-row"
          :class="e.id === selectedId ? 'on' : ''"
          type="button"
          @click="selectedId = e.id"
        >
          <span class="datebox">
            <span class="dow">{{ dowAb(e.date) }}</span>
            <span class="num">{{ dayNum(e.date) }}</span>
          </span>
          <span class="meta">
            <span class="t">{{ e.title || "Sin título" }}</span>
            <span class="x">{{
              (e.body || "").split("\n")[0] || "Todavía no escribiste nada."
            }}</span>
            <span v-if="e.tag && TAGS[e.tag]" class="tagline">
              <span class="dot" :style="{ background: TAGS[e.tag].color }"></span>
              {{ TAGS[e.tag].label }}
            </span>
          </span>
        </button>
      </div>
      <p
        v-if="!visibles.length"
        style="
          padding: 28px 16px;
          font-size: 13px;
          color: var(--ink-3);
          text-align: center;
        "
      >
        No hay entradas con este filtro.
      </p>
    </div>

    <!-- ── Panel 3 — Editor ───────────────────────────────────────── -->
    <div class="d-editor">
      <template v-if="selected">
        <div class="ed-head">
          <span class="when">{{ fmtLong(selected.date) }}</span>
          <span
            v-if="selected.date === hoy"
            style="font-size: 12px; color: var(--accent); font-weight: 600"
            >Hoy</span
          >
        </div>

        <!-- Banner de encuesta de cierre -->
        <div v-if="cicloDone && encuesta" class="invite">
          <div style="min-width: 0; flex: 1">
            <div style="font-size: 13.5px; font-weight: 700">
              Cerraste tu ciclo de 14 días.
            </div>
            <div
              style="
                font-size: 12.5px;
                color: var(--ink-2);
                margin-top: 2px;
                line-height: 1.5;
              "
            >
              Cuéntale a Sami cómo te sentiste estas dos semanas. Son 16
              preguntas, te toma 5 minutos.
            </div>
          </div>
          <button class="btn primary" type="button" @click="abrirEncuesta">
            Empezar encuesta
          </button>
        </div>

        <div class="ed-body">
          <input
            class="ed-title"
            :value="selected.title"
            placeholder="Ponle un título (o no)"
            @input="onEditTitle"
          />
          <textarea
            class="ed-text"
            :value="selected.body"
            :rows="Math.max(10, (selected.body || '').split('\n').length + 3)"
            placeholder="Cuéntale a Sami cómo te has sentido…"
            @input="onEditBody"
          ></textarea>
        </div>

        <!-- Encuesta del ciclo (3 preguntas), solo en la entrada de hoy y
             si el ciclo no terminó. -->
        <div
          v-if="selected.date === hoy && !cicloDone"
          class="cycle-card"
          data-comment-anchor="cycle-survey"
        >
          <template v-if="cycleDayDone">
            <h3>Encuesta del ciclo · día {{ cicloDia }} de {{ cicloLength }}</h3>
            <p class="hint" style="margin-bottom: 0">
              Listo por hoy. Gracias por tomarte el minuto — esto le da contexto
              a tus entradas.
            </p>
          </template>
          <template v-else>
            <h3>Encuesta del ciclo · día {{ cicloDia }} de {{ cicloLength }}</h3>
            <p class="hint">Un minuto, tres preguntas. Acompaña tu entrada de hoy.</p>
            <div v-for="q in cycleQuestions" :key="q.id" class="scale-q">
              <div class="q">{{ q.q }}</div>
              <div class="opts">
                <button
                  v-for="(o, i) in q.opts"
                  :key="o"
                  type="button"
                  :class="cycleValues[q.id] === i ? 'on' : ''"
                  @click="cycleValues[q.id] = i"
                >
                  {{ o }}
                </button>
              </div>
            </div>
            <button
              class="btn primary"
              type="button"
              :disabled="!cycleDayListo"
              @click="submitCycleDaily(hoy, { ...cycleValues })"
            >
              Enviar
            </button>
          </template>
        </div>

        <div class="ed-foot">
          <span class="tagpick">
            <button
              v-for="(t, id) in TAGS"
              :key="id"
              type="button"
              :class="selected.tag === id ? 'on' : ''"
              @click="onToggleTag(id)"
            >
              <span class="dot" :style="{ background: t.color }"></span>
              {{ t.label }}
            </button>
          </span>
          <span style="margin-left: auto">
            {{ wordsEntry }}
            {{ wordsEntry === 1 ? "palabra" : "palabras" }} · guardado
          </span>
        </div>
      </template>

      <template v-else>
        <div v-if="cicloDone && encuesta" class="invite">
          <div style="min-width: 0; flex: 1">
            <div style="font-size: 13.5px; font-weight: 700">
              Cerraste tu ciclo de 14 días.
            </div>
            <div
              style="
                font-size: 12.5px;
                color: var(--ink-2);
                margin-top: 2px;
                line-height: 1.5;
              "
            >
              Cuéntale a Sami cómo te sentiste estas dos semanas. Son 16
              preguntas, te toma 5 minutos.
            </div>
          </div>
          <button class="btn primary" type="button" @click="abrirEncuesta">
            Empezar encuesta
          </button>
        </div>
        <div style="flex: 1; display: grid; place-items: center">
          <p style="color: var(--ink-3); font-size: 13.5px">
            Elegí una entrada, o creá una nueva con el botón +
          </p>
        </div>
      </template>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="toast" class="toast">{{ toast }}</div>
  </Teleport>
</template>
