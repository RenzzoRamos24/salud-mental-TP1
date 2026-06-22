<script setup>
import { computed, ref, watch } from "vue";
import { api } from "../api";

const props = defineProps({
  encuesta: { type: Object, required: true },
});
const emit = defineEmits(["cerrada", "volver"]);

const items = computed(() => props.encuesta?.items || []);
const opciones = computed(() => props.encuesta?.opciones || []);
const respuestas = ref({ ...(props.encuesta?.respuestas || {}) });
const idx = ref(0);
const enviando = ref(false);
const error = ref("");
const cerrando = ref(false);
const resumen = ref(null);
const timer = ref(null);

watch(
  () => props.encuesta?.id,
  () => {
    respuestas.value = { ...(props.encuesta?.respuestas || {}) };
    const pendiente = items.value.findIndex(
      (it) => respuestas.value[it.id] === undefined,
    );
    idx.value = pendiente >= 0 ? pendiente : 0;
    resumen.value = null;
  },
  { immediate: true },
);

const total = computed(() => items.value.length);
const itemActual = computed(() => items.value[idx.value] || null);
const ultima = computed(() => idx.value === total.value - 1);
const valorActual = computed(() =>
  itemActual.value ? respuestas.value[itemActual.value.id] : undefined,
);
const todasRespondidas = computed(
  () =>
    items.value.filter((it) => respuestas.value[it.id] !== undefined).length ===
    total.value,
);

const moduloLabel = computed(() => {
  if (!itemActual.value) return "";
  return itemActual.value.modulo === "PHQ-9" ? "PHQ-A" : "GAD-7";
});
const moduloNumero = computed(() =>
  itemActual.value ? itemActual.value.numero : 0,
);

async function elegir(v) {
  if (enviando.value || !itemActual.value) return;
  error.value = "";
  const itId = itemActual.value.id;
  respuestas.value = { ...respuestas.value, [itId]: v };
  enviando.value = true;
  try {
    await api.encuestaResponder(itId, v);
    if (!ultima.value) {
      if (timer.value) clearTimeout(timer.value);
      timer.value = setTimeout(() => {
        idx.value = Math.min(idx.value + 1, total.value - 1);
      }, 260);
    }
  } catch (e) {
    error.value =
      e.response?.data?.detail ||
      "No pudimos guardar tu respuesta. Intenta de nuevo.";
  } finally {
    enviando.value = false;
  }
}

function atras() {
  if (idx.value > 0) idx.value -= 1;
}
function siguiente() {
  if (!ultima.value) idx.value += 1;
}

async function terminar() {
  if (!todasRespondidas.value || cerrando.value) return;
  error.value = "";
  cerrando.value = true;
  try {
    const data = await api.encuestaCerrar();
    resumen.value = data.resumen;
  } catch (e) {
    error.value = e.response?.data?.detail || "No pudimos cerrar la encuesta.";
  } finally {
    cerrando.value = false;
  }
}

function exit() {
  emit("cerrada", resumen.value);
}
function volver() {
  emit("volver");
}

function lvlClass(nivel) {
  if (/severa/i.test(nivel || "")) return "lvl bad";
  if (/moderada/i.test(nivel || "")) return "lvl warn";
  return "lvl";
}
</script>

<template>
  <div class="survey" data-screen-label="Encuesta de cierre">
    <!-- ─── RESUMEN final ────────────────────────────────────────── -->
    <div
      v-if="resumen"
      class="survey-col"
      data-screen-label="Encuesta de cierre · Resumen"
    >
      <div class="q-mod">Encuesta de cierre</div>
      <h1
        style="
          font-size: 26px;
          font-weight: 700;
          letter-spacing: -0.02em;
          margin: 0 0 8px;
        "
      >
        Gracias por responder.
      </h1>
      <p
        style="
          font-size: 14.5px;
          color: var(--ink-2);
          line-height: 1.6;
          margin: 0;
        "
      >
        Estos son los puntajes de tu ciclo {{ encuesta.ciclo_numero }}. Quedan
        guardados para que los conversen con tu psicóloga.
      </p>
      <div class="score-grid">
        <div class="score-card">
          <div class="name">PHQ-A · Depresión</div>
          <div class="num">
            {{ resumen.phq9_total }}<small>/27</small>
          </div>
          <span :class="lvlClass(resumen.phq9_severidad)">{{
            resumen.phq9_severidad
          }}</span>
          <div class="act">{{ resumen.phq9_accion }}</div>
        </div>
        <div class="score-card">
          <div class="name">GAD-7 · Ansiedad</div>
          <div class="num">
            {{ resumen.gad7_total }}<small>/21</small>
          </div>
          <span :class="lvlClass(resumen.gad7_severidad)">{{
            resumen.gad7_severidad
          }}</span>
          <div class="act">{{ resumen.gad7_accion }}</div>
        </div>
      </div>
      <div v-if="resumen.crisis_protocolo" class="crisis-card">
        <h3>Pide ayuda ahora.</h3>
        <p>
          Marcaste tener pensamientos de hacerte daño. Por favor llama a la
          <strong>Línea 113, opción 5</strong>. Es gratuita, confidencial y
          atiende 24/7. También avisa a tu psicóloga o a alguien de tu casa
          hoy mismo.
        </p>
      </div>
      <button class="btn primary" type="button" @click="exit">
        Volver al diario
      </button>
    </div>

    <!-- ─── PREGUNTAS ────────────────────────────────────────────── -->
    <div
      v-else
      class="survey-col"
      data-screen-label="Encuesta de cierre · Pregunta"
    >
      <div class="survey-top">
        <span>Cierre del ciclo {{ encuesta.ciclo_numero }}</span>
        <span>{{ idx + 1 }}/{{ total }}</span>
      </div>
      <div class="seg-progress">
        <i
          v-for="(it, i) in items"
          :key="it.id"
          :class="
            i === idx
              ? 'cur'
              : respuestas[it.id] !== undefined
                ? 'done'
                : ''
          "
        ></i>
      </div>

      <div v-if="itemActual">
        <div class="q-mod">{{ moduloLabel }} · pregunta {{ moduloNumero }}</div>
        <p class="q-text">{{ itemActual.texto }}</p>
        <p class="q-sub">Pensando en los últimos 14 días</p>

        <div class="likert">
          <button
            v-for="o in opciones"
            :key="o.valor"
            type="button"
            :class="valorActual === o.valor ? 'on' : ''"
            :disabled="enviando"
            @click="elegir(o.valor)"
          >
            <span class="val">{{ o.valor }}</span>
            <span>
              <span class="lab">{{ o.etiqueta }}</span>
              <span class="des">{{ o.descripcion }}</span>
            </span>
          </button>
        </div>

        <div class="survey-nav">
          <button
            class="btn"
            type="button"
            :disabled="idx === 0 || enviando"
            :style="idx === 0 ? 'opacity:.45' : ''"
            @click="atras"
          >
            Atrás
          </button>
          <button
            v-if="ultima"
            class="btn primary"
            type="button"
            :disabled="cerrando || !todasRespondidas"
            @click="terminar"
          >
            {{ cerrando ? "Enviando…" : "Terminar" }}
          </button>
          <button v-else class="btn" type="button" @click="siguiente">
            Saltar
          </button>
        </div>

        <div v-if="error" class="err-card">{{ error }}</div>

        <p class="survey-foot">
          Tus respuestas son confidenciales. Solo las ve tu psicóloga.
        </p>
        <p style="text-align: center; margin-top: 14px">
          <button class="linkbtn" type="button" @click="volver">
            ← Volver al diario
          </button>
        </p>
      </div>
    </div>
  </div>
</template>
