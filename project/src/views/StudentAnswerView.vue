<script setup>
import { ref, reactive, computed, onMounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

const route = useRoute();
const router = useRouter();
const aplicacionId = computed(() => Number(route.params.id));

const cargando = ref(true);
const error = ref("");
const detalle = ref(null);
// Usamos reactive en lugar de ref({}) para que la asignación por clave dinámica
// (respuestas[origen] = ...) dispare reactividad inmediata en los computed.
const respuestas = reactive({});
const enviando = ref(false);
const finalizado = ref(false);
const mensajeFinal = ref("");
const intentoFinalizar = ref(false);
// Cuántos segundos lleva esperando — para mostrar mensaje friendly si tarda mucho
const segundosEsperando = ref(0);
let timerEsperando = null;

// ── Etiquetas cálidas por bloque (sin códigos clínicos visibles) ─────
const BLOQUE_NOMBRES = {
  "PHQ-A": "Cómo te has sentido",
  "GAD-7": "Preocupación y tensión",
  RSES: "Cómo te ves a ti mismo/a",
  "SRQ-20": "En tu día a día",
  "WHO-5": "Tu bienestar",
  "UCLA-3": "Compañía y conexión",
  FRASES: "Completa las frases",
};
const BLOQUE_INSTRUCCIONES = {
  "PHQ-A": "Durante las últimas dos semanas, ¿con qué frecuencia te ha molestado lo siguiente?",
  "GAD-7": "Durante las últimas dos semanas, ¿con qué frecuencia te has sentido así?",
  RSES: "Indica cuán de acuerdo estás con cada afirmación.",
  "SRQ-20": "Pensando en los últimos 30 días, responde sí o no.",
  "WHO-5": "Cómo te has sentido durante las últimas dos semanas.",
  "UCLA-3": "Indica con qué frecuencia te sientes así.",
  FRASES: "Completa cada frase con lo primero que se te venga a la mente. No hay respuestas correctas.",
};

// ── Escalas Likert (etiquetas por opción) ────────────────────────────
const OPCIONES = {
  "0-3": [
    { v: 0, label: "Nunca" },
    { v: 1, label: "Algunos días" },
    { v: 2, label: "Más de la mitad" },
    { v: 3, label: "Casi todos los días" },
  ],
  "1-4": [
    { v: 1, label: "Muy en desacuerdo" },
    { v: 2, label: "En desacuerdo" },
    { v: 3, label: "De acuerdo" },
    { v: 4, label: "Muy de acuerdo" },
  ],
  "0-5": [
    { v: 0, label: "En ningún momento" },
    { v: 1, label: "Algunos días" },
    { v: 2, label: "Menos de la mitad" },
    { v: 3, label: "Más de la mitad" },
    { v: 4, label: "La mayor parte" },
    { v: 5, label: "Todo el tiempo" },
  ],
  "1-3": [
    { v: 1, label: "Casi nunca" },
    { v: 2, label: "A veces" },
    { v: 3, label: "A menudo" },
  ],
  binaria: [
    { v: 1, label: "Sí" },
    { v: 0, label: "No" },
  ],
};

function escalaKey(p) {
  if (p.tipo === "binaria") return "binaria";
  return `${p.likert_min}-${p.likert_max}`;
}
function opciones(p) {
  return OPCIONES[escalaKey(p)] || [];
}

// ── Carga ────────────────────────────────────────────────────────────
async function cargar() {
  cargando.value = true;
  try {
    detalle.value = await api.detalleParaResponder(aplicacionId.value);
    for (const p of detalle.value.preguntas) {
      if (!(p.origen in respuestas)) {
        respuestas[p.origen] =
          p.tipo === "texto" ? { valor_texto: "" } : { valor_num: null };
      }
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || "No pude cargar el cuestionario.";
  } finally {
    cargando.value = false;
  }
}
onMounted(cargar);

// ── Agrupar preguntas por bloque ─────────────────────────────────────
const bloques = computed(() => {
  if (!detalle.value) return [];
  const map = new Map();
  for (const p of detalle.value.preguntas) {
    const key = p.bloque_codigo.startsWith("FRASES") || p.origen.startsWith("FRASE:") ? "FRASES" : p.bloque_codigo;
    if (!map.has(key)) {
      map.set(key, {
        codigo: key,
        titulo: BLOQUE_NOMBRES[key] || p.bloque_nombre,
        instruccion: BLOQUE_INSTRUCCIONES[key] || "",
        preguntas: [],
        tipo: p.tipo,
        opcional: key === "FRASES",
      });
    }
    map.get(key).preguntas.push(p);
  }
  return Array.from(map.values());
});

// ── Progreso (solo preguntas obligatorias) ───────────────────────────
const obligatorias = computed(() =>
  (detalle.value?.preguntas || []).filter((p) => p.tipo !== "texto"),
);
const respondidasObl = computed(() =>
  obligatorias.value.filter(
    (p) =>
      respuestas[p.origen]?.valor_num !== null &&
      respuestas[p.origen]?.valor_num !== undefined,
  ).length,
);
const pct = computed(() =>
  obligatorias.value.length
    ? Math.round((respondidasObl.value / obligatorias.value.length) * 100)
    : 0,
);
const completa = computed(
  () =>
    obligatorias.value.length &&
    respondidasObl.value === obligatorias.value.length,
);
const total = computed(() => detalle.value?.preguntas?.length || 0);

function estaRespondida(p) {
  const r = respuestas[p.origen];
  if (!r) return false;
  if (p.tipo === "texto") return (r.valor_texto || "").trim().length > 0;
  return r.valor_num !== null && r.valor_num !== undefined;
}

function pendienteParaValidar(p) {
  return intentoFinalizar.value && p.tipo !== "texto" && !estaRespondida(p);
}

// ── Marcar respuesta ─────────────────────────────────────────────────
function setNum(p, v) {
  respuestas[p.origen] = { valor_num: v };
  intentoFinalizar.value = false;
}
function setTexto(p, v) {
  respuestas[p.origen] = { valor_texto: v };
}

// ── Guardar parcial (sin tocar enviando, eso lo controla finalizar) ─
async function guardarParcial(silent = false) {
  try {
    if (!silent) enviando.value = true;
    const arr = Object.entries(respuestas)
      .filter(
        ([_, r]) =>
          (r && r.valor_num !== null && r.valor_num !== undefined) ||
          (r && (r.valor_texto || "").trim().length),
      )
      .map(([origen, r]) => ({
        origen,
        valor_num: r.valor_num ?? null,
        valor_texto: r.valor_texto ?? null,
      }));
    await api.guardarRespuestas(aplicacionId.value, arr);
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo guardar.";
  } finally {
    if (!silent) enviando.value = false;
  }
}

function arrancarTimerEspera() {
  segundosEsperando.value = 0;
  if (timerEsperando) clearInterval(timerEsperando);
  timerEsperando = setInterval(() => {
    segundosEsperando.value += 1;
  }, 1000);
}
function pararTimerEspera() {
  if (timerEsperando) clearInterval(timerEsperando);
  timerEsperando = null;
}

async function finalizar() {
  // Anti doble-click: si ya estamos enviando, ignoramos.
  if (enviando.value) return;

  intentoFinalizar.value = true;
  if (!completa.value) {
    const primera = obligatorias.value.find((p) => !estaRespondida(p));
    if (primera) {
      await nextTick();
      const el = document.querySelector(
        `[data-q="${CSS.escape(primera.origen)}"]`,
      );
      if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    return;
  }

  enviando.value = true;
  arrancarTimerEspera();
  try {
    await guardarParcial(true);
    const res = await api.cerrarCuestionario(aplicacionId.value);
    finalizado.value = true;
    mensajeFinal.value =
      res?.mensaje || "Gracias por completar el cuestionario.";
  } catch (e) {
    error.value =
      e?.response?.data?.detail || "No se pudo cerrar el cuestionario.";
  } finally {
    pararTimerEspera();
    enviando.value = false;
  }
}

function volverInicio() {
  router.push("/mis-cuestionarios");
}
</script>

<template>
  <div class="sami-bg">
    <!-- estado vacío / cargando -->
    <div v-if="cargando" class="sami-status">Preparando tu cuestionario…</div>
    <div v-else-if="error && !detalle" class="sami-status sami-status--err">{{ error }}</div>

    <!-- finalizado -->
    <div v-else-if="finalizado" class="sami-sheet sami-sheet--end">
      <div class="sami-check">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="11" fill="#45988C" />
          <path d="M7 12.5l3.5 3.5L17 8" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" fill="none" />
        </svg>
      </div>
      <h2>¡Listo!</h2>
      <p>{{ mensajeFinal }}</p>
      <button class="sami-btn sami-btn--primary" @click="volverInicio">
        Volver a mis cuestionarios
      </button>
    </div>

    <!-- hoja A4 -->
    <div v-else class="sami-sheet">
      <header class="sami-head">
        <p class="sami-eyebrow">Sami · Bienestar</p>
        <h1 class="sami-title">{{ detalle.plantilla_nombre || "Cuestionario de bienestar" }}</h1>
        <p class="sami-desc">
          {{ detalle.descripcion || "Lee con calma y elige lo que más se acerca a cómo te has sentido. No hay respuestas correctas o incorrectas." }}
        </p>

        <div class="sami-progress">
          <div class="sami-progress__track">
            <div class="sami-progress__fill" :style="{ width: pct + '%' }" />
          </div>
          <div class="sami-progress__meta">
            <span class="sami-progress__count">{{ respondidasObl }} / {{ obligatorias.length }} respondidas</span>
            <span class="sami-progress__pct">{{ pct }}%</span>
          </div>
        </div>
      </header>

      <div v-if="error" class="sami-error">{{ error }}</div>

      <!-- Bloques -->
      <section
        v-for="b in bloques"
        :key="b.codigo"
        class="sami-block"
      >
        <div class="sami-block__sep">
          <span class="sami-block__line"></span>
          <span class="sami-block__title">{{ b.titulo }}</span>
          <span class="sami-block__line"></span>
        </div>
        <p v-if="b.instruccion" class="sami-block__instr">{{ b.instruccion }}</p>
        <p v-if="b.opcional" class="sami-block__opt">Este bloque es opcional.</p>

        <!-- Texto libre -->
        <div v-if="b.preguntas[0]?.tipo === 'texto'" class="sami-frases">
          <div
            v-for="p in b.preguntas"
            :key="p.origen"
            :data-q="p.origen"
            class="sami-frase"
          >
            <p class="sami-frase__stem">{{ p.texto }}</p>
            <textarea
              class="sami-frase__input"
              :value="respuestas[p.origen]?.valor_texto"
              @input="setTexto(p, $event.target.value)"
              rows="2"
              placeholder="Lo que sea que se te venga…"
            ></textarea>
          </div>
        </div>

        <!-- Binario Sí/No -->
        <div v-else-if="b.preguntas[0]?.tipo === 'binaria'" class="sami-binarias">
          <div
            v-for="(p, idx) in b.preguntas"
            :key="p.origen"
            :data-q="p.origen"
            class="sami-binaria"
            :class="{ 'is-pending': pendienteParaValidar(p), 'is-done': estaRespondida(p) }"
          >
            <div class="sami-binaria__head">
              <span class="sami-binaria__num">{{ idx + 1 }}</span>
              <span class="sami-binaria__text">{{ p.texto }}</span>
            </div>
            <div class="sami-binaria__opts">
              <button
                v-for="op in opciones(p)"
                :key="op.v"
                class="sami-binaria__btn"
                :class="{ 'is-on': respuestas[p.origen]?.valor_num === op.v }"
                @click="setNum(p, op.v)"
              >
                {{ op.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- Likert matriz (desktop) -->
        <div v-else class="sami-matriz">
          <!-- escala header -->
          <div class="sami-matriz__head">
            <div class="sami-matriz__qcol"></div>
            <div
              v-for="op in opciones(b.preguntas[0])"
              :key="op.v"
              class="sami-matriz__opt-label"
            >
              {{ op.label }}
            </div>
          </div>

          <!-- filas -->
          <div
            v-for="(p, idx) in b.preguntas"
            :key="p.origen"
            :data-q="p.origen"
            class="sami-matriz__row"
            :class="{ 'is-pending': pendienteParaValidar(p), 'is-done': estaRespondida(p) }"
          >
            <div class="sami-matriz__qcol">
              <span class="sami-matriz__num">{{ idx + 1 }}</span>
              <span class="sami-matriz__text">{{ p.texto }}</span>
            </div>
            <button
              v-for="op in opciones(p)"
              :key="op.v"
              class="sami-matriz__cell"
              :class="{ 'is-on': respuestas[p.origen]?.valor_num === op.v }"
              @click="setNum(p, op.v)"
              :title="op.label"
            >
              <span class="sami-radio">
                <span class="sami-radio__check">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M5 12.5l4 4L19 7"
                      stroke="#fff"
                      stroke-width="2.6"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                </span>
              </span>
              <span class="sami-matriz__cell-label">{{ op.label }}</span>
            </button>
          </div>
        </div>
      </section>

      <!-- Cierre -->
      <footer class="sami-foot">
        <p class="sami-foot__hint" v-if="!completa">
          Cuando termines todas las preguntas obligatorias, se habilita Finalizar.
        </p>
        <button
          class="sami-btn sami-btn--primary"
          :class="{ 'is-disabled': !completa }"
          :disabled="!completa || enviando"
          @click="finalizar"
          type="button"
        >
          {{ enviando ? "Enviando…" : "Finalizar" }}
        </button>
      </footer>

      <!-- Overlay durante el envío -->
      <div v-if="enviando" class="sami-overlay">
        <div class="sami-overlay__card">
          <div class="sami-overlay__spinner">
            <svg width="48" height="48" viewBox="0 0 50 50">
              <circle
                cx="25"
                cy="25"
                r="20"
                fill="none"
                stroke="#e3f3ef"
                stroke-width="5"
              />
              <circle
                cx="25"
                cy="25"
                r="20"
                fill="none"
                stroke="#45988c"
                stroke-width="5"
                stroke-linecap="round"
                stroke-dasharray="40 100"
                transform="rotate(-90 25 25)"
              >
                <animateTransform
                  attributeName="transform"
                  type="rotate"
                  from="0 25 25"
                  to="360 25 25"
                  dur="1.1s"
                  repeatCount="indefinite"
                />
              </circle>
            </svg>
          </div>
          <p class="sami-overlay__title">Estamos guardando tus respuestas</p>
          <p class="sami-overlay__sub" v-if="segundosEsperando < 8">
            Esto suele tomar unos segundos.
          </p>
          <p class="sami-overlay__sub" v-else-if="segundosEsperando < 30">
            Procesando con cuidado lo que escribiste…
          </p>
          <p class="sami-overlay__sub" v-else-if="segundosEsperando < 90">
            Estamos preparando el análisis de tus frases. La primera vez puede tardar un poco más.
          </p>
          <p class="sami-overlay__sub" v-else>
            Ya casi. Esta es la primera vez en el día que el sistema analiza
            frases; la próxima será mucho más rápida.
          </p>
          <p class="sami-overlay__timer">
            {{ segundosEsperando }}s
          </p>
        </div>
      </div>
    </div>

    <!-- Sticky bar -->
    <div v-if="!cargando && !finalizado" class="sami-sticky">
      <div class="sami-sticky__inner">
        <span class="sami-sticky__count">{{ respondidasObl }} / {{ obligatorias.length }} respondidas</span>
        <button class="sami-btn sami-btn--ghost" :disabled="enviando" @click="guardarParcial">
          Guardar y continuar luego
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sami-bg {
  min-height: 100vh;
  background: #f4f5f6;
  font-family: "Work Sans", system-ui, sans-serif;
  color: #1f2937;
  padding: 36px 16px 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sami-status {
  background: #fff;
  border-radius: 18px;
  padding: 40px 32px;
  text-align: center;
  color: #667085;
  margin-top: 20vh;
}
.sami-status--err {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

/* ── Hoja A4 ───────────────────────────────────────────────── */
.sami-sheet {
  width: 100%;
  max-width: 860px;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 6px 30px rgba(35, 80, 95, 0.06);
  padding: 48px 56px;
  position: relative;
}
.sami-sheet--end {
  text-align: center;
  padding: 64px 56px;
  max-width: 560px;
}
.sami-check {
  display: flex;
  justify-content: center;
  margin-bottom: 18px;
}
.sami-sheet--end h2 {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 30px;
  color: #0a0a0a;
  margin-bottom: 12px;
}
.sami-sheet--end p {
  color: #475467;
  margin-bottom: 28px;
  line-height: 1.6;
}

/* ── Encabezado ────────────────────────────────────────────── */
.sami-head {
  margin-bottom: 36px;
}
.sami-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #0e8d7e;
  margin-bottom: 12px;
}
.sami-title {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 30px;
  line-height: 1.1;
  color: #0a0a0a;
  letter-spacing: -0.01em;
  margin-bottom: 10px;
}
.sami-desc {
  color: #475467;
  font-size: 15px;
  line-height: 1.55;
  margin-bottom: 24px;
}

.sami-progress {
  margin-top: 24px;
}
.sami-progress__track {
  height: 6px;
  background: #eef1f2;
  border-radius: 99px;
  overflow: hidden;
}
.sami-progress__fill {
  height: 100%;
  background: linear-gradient(90deg, #22b8a6, #0e8d7e);
  border-radius: 99px;
  transition: width 0.4s ease-out;
}
.sami-progress__meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  font-size: 12.5px;
}
.sami-progress__count {
  color: #667085;
}
.sami-progress__pct {
  color: #0e8d7e;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.sami-error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  padding: 12px 16px;
  border-radius: 12px;
  margin: 12px 0;
  font-size: 13px;
}

/* ── Bloques ──────────────────────────────────────────────── */
.sami-block {
  margin-top: 40px;
}
.sami-block__sep {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 14px;
}
.sami-block__line {
  flex: 1;
  height: 1px;
  background: #c5e1dc;
}
.sami-block__title {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 19px;
  color: #0e8d7e;
  letter-spacing: -0.01em;
  white-space: nowrap;
}
.sami-block__instr {
  text-align: center;
  color: #667085;
  font-size: 13.5px;
  margin-bottom: 22px;
  line-height: 1.5;
}
.sami-block__opt {
  text-align: center;
  font-size: 12px;
  color: #98a2b3;
  font-style: italic;
  margin-bottom: 16px;
}

/* ── Matriz Likert ────────────────────────────────────────── */
.sami-matriz__head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) repeat(var(--opts, 4), minmax(72px, 90px));
  gap: 4px;
  padding: 0 0 14px;
  margin-bottom: 6px;
  border-bottom: 1px solid #eef1f2;
}
.sami-matriz__opt-label {
  font-size: 11px;
  color: #667085;
  text-align: center;
  line-height: 1.2;
  padding: 0 4px;
}
.sami-matriz__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) repeat(var(--opts, 4), minmax(72px, 90px));
  gap: 4px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f4f5f6;
  transition: background 0.15s;
}
.sami-matriz__row.is-pending {
  background: #fff7ed;
  margin: 0 -16px;
  padding: 12px 16px;
  border-radius: 12px;
  border-bottom: 1px solid transparent;
}
.sami-matriz__qcol {
  display: flex;
  gap: 10px;
  padding-right: 14px;
  align-items: flex-start;
}
.sami-matriz__num {
  flex: none;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: #f4f5f6;
  color: #667085;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
  font-variant-numeric: tabular-nums;
}
.sami-matriz__row.is-done .sami-matriz__num {
  background: #e3f3ef;
  color: #0e8d7e;
}
.sami-matriz__text {
  font-size: 14px;
  line-height: 1.45;
  color: #344054;
}
.sami-matriz__cell {
  background: transparent;
  border: 0;
  cursor: pointer;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-family: inherit;
}
.sami-matriz__cell-label {
  display: none;
}
.sami-radio {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1.6px solid #d1d5db;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, border-color 0.15s;
}
.sami-matriz__cell:hover .sami-radio {
  border-color: #9ecfc6;
}
.sami-radio__check {
  width: 14px;
  height: 14px;
  opacity: 0;
  transform: scale(0.5);
  transition: opacity 0.15s, transform 0.15s;
}
.sami-matriz__cell.is-on .sami-radio {
  background: #45988c;
  border-color: #45988c;
}
.sami-matriz__cell.is-on .sami-radio__check {
  opacity: 1;
  transform: scale(1);
}

/* dinámico: cols opts */
.sami-matriz {
  --opts: 4;
}
.sami-matriz:has(.sami-matriz__cell:nth-child(8)) {
  --opts: 6;
}
.sami-matriz:has(.sami-matriz__head .sami-matriz__opt-label:nth-child(7)) {
  --opts: 6;
}

/* ── Binarias ─────────────────────────────────────────────── */
.sami-binarias {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.sami-binaria {
  border: 1px solid #eef1f2;
  border-radius: 14px;
  padding: 16px 18px;
  transition: background 0.15s;
}
.sami-binaria.is-pending {
  background: #fff7ed;
  border-color: #fed7aa;
}
.sami-binaria.is-done {
  border-color: #c5e1dc;
}
.sami-binaria__head {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}
.sami-binaria__num {
  flex: none;
  width: 22px;
  height: 22px;
  border-radius: 7px;
  background: #f4f5f6;
  color: #667085;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-variant-numeric: tabular-nums;
}
.sami-binaria.is-done .sami-binaria__num {
  background: #e3f3ef;
  color: #0e8d7e;
}
.sami-binaria__text {
  font-size: 14.5px;
  line-height: 1.45;
  color: #1f2937;
}
.sami-binaria__opts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.sami-binaria__btn {
  padding: 12px;
  background: #ffffff;
  border: 1.6px solid #d1d5db;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  color: #475467;
  cursor: pointer;
  transition: all 0.15s;
}
.sami-binaria__btn:hover {
  border-color: #9ecfc6;
}
.sami-binaria__btn.is-on {
  background: #45988c;
  border-color: #45988c;
  color: #ffffff;
}

/* ── Frases incompletas ───────────────────────────────────── */
.sami-frases {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.sami-frase {
  display: flex;
  flex-direction: column;
}
.sami-frase__stem {
  font-size: 14.5px;
  color: #1f2937;
  margin-bottom: 6px;
  line-height: 1.45;
}
.sami-frase__input {
  border: 0;
  border-bottom: 1.6px solid #e5e7eb;
  background: transparent;
  padding: 8px 4px;
  font-family: inherit;
  font-size: 14.5px;
  color: #1f2937;
  resize: vertical;
  outline: none;
  transition: border-color 0.15s;
}
.sami-frase__input:focus {
  border-color: #45988c;
}
.sami-frase__input::placeholder {
  color: #9ca3af;
}

/* ── Cierre ───────────────────────────────────────────────── */
.sami-foot {
  margin-top: 48px;
  padding-top: 32px;
  border-top: 1px solid #eef1f2;
  text-align: center;
}
.sami-foot__hint {
  font-size: 13px;
  color: #98a2b3;
  margin-bottom: 16px;
}

/* ── Botones ──────────────────────────────────────────────── */
.sami-btn {
  font-family: inherit;
  font-size: 14.5px;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 12px;
  cursor: pointer;
  border: 0;
  transition: all 0.15s;
}
.sami-btn--primary {
  background: #45988c;
  color: #ffffff;
  box-shadow: 0 6px 14px -6px rgba(69, 152, 140, 0.5);
}
.sami-btn--primary:hover:not(.is-disabled):not(:disabled) {
  background: #0e8d7e;
}
.sami-btn--primary.is-disabled,
.sami-btn--primary:disabled {
  background: #e5e7eb;
  color: #9ca3af;
  cursor: not-allowed;
  box-shadow: none;
}
.sami-btn--ghost {
  background: transparent;
  color: #475467;
  padding: 8px 14px;
}
.sami-btn--ghost:hover {
  color: #0a0a0a;
}

/* ── Overlay envío ────────────────────────────────────────── */
.sami-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 28, 0.42);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}
.sami-overlay__card {
  background: #fff;
  border-radius: 18px;
  padding: 32px 36px;
  max-width: 380px;
  text-align: center;
  box-shadow: 0 18px 48px rgba(15, 60, 70, 0.25);
}
.sami-overlay__spinner {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}
.sami-overlay__title {
  font-family: "Newsreader", Georgia, serif;
  font-size: 19px;
  font-weight: 500;
  color: #0a0a0a;
  margin-bottom: 8px;
}
.sami-overlay__sub {
  font-size: 13px;
  color: #667085;
  line-height: 1.55;
  min-height: 36px;
  transition: opacity 0.2s;
}
.sami-overlay__timer {
  margin-top: 14px;
  font-size: 12px;
  color: #98a2b3;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.04em;
}

/* ── Sticky bar ───────────────────────────────────────────── */
.sami-sticky {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #ffffff;
  border-top: 1px solid #eef1f2;
  padding: 12px 16px;
  box-shadow: 0 -6px 20px rgba(35, 80, 95, 0.04);
  z-index: 10;
}
.sami-sticky__inner {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.sami-sticky__count {
  font-size: 13px;
  color: #667085;
  font-variant-numeric: tabular-nums;
}

/* ── Responsive mobile ────────────────────────────────────── */
@media (max-width: 720px) {
  .sami-sheet {
    padding: 28px 22px;
    border-radius: 18px;
  }
  .sami-title {
    font-size: 24px;
  }
  /* Matriz colapsa a pills */
  .sami-matriz__head {
    display: none;
  }
  .sami-matriz__row {
    grid-template-columns: 1fr;
    gap: 8px;
    padding: 14px 12px;
    border-bottom: 1px solid #f4f5f6;
  }
  .sami-matriz__qcol {
    padding-right: 0;
    padding-bottom: 6px;
  }
  .sami-matriz__cell {
    flex-direction: row;
    justify-content: flex-start;
    gap: 10px;
    padding: 10px 14px;
    border: 1.6px solid #e5e7eb;
    border-radius: 12px;
    width: 100%;
  }
  .sami-matriz__cell-label {
    display: inline;
    font-size: 13px;
    color: #344054;
  }
  .sami-matriz__cell.is-on {
    background: #45988c;
    border-color: #45988c;
  }
  .sami-matriz__cell.is-on .sami-matriz__cell-label {
    color: #ffffff;
  }
}
</style>
