<script setup>
import { computed, ref, watch } from "vue";
import { api } from "../api";

const props = defineProps({
  encuesta: { type: Object, required: true },
});
const emit = defineEmits(["cerrada", "cancelada"]);

const items = computed(() => props.encuesta?.items || []);
const opciones = computed(() => props.encuesta?.opciones || []);
const respuestas = ref({ ...(props.encuesta?.respuestas || {}) });
const indice = ref(0);
const enviando = ref(false);
const error = ref("");
const cerrando = ref(false);
const resumen = ref(null);

watch(
  () => props.encuesta?.id,
  () => {
    respuestas.value = { ...(props.encuesta?.respuestas || {}) };
    const pendiente = items.value.findIndex(
      (it) => respuestas.value[it.id] === undefined,
    );
    indice.value = pendiente >= 0 ? pendiente : 0;
    resumen.value = null;
  },
  { immediate: true },
);

const itemActual = computed(() => items.value[indice.value] || null);
const total = computed(() => items.value.length);
const respondidas = computed(
  () =>
    items.value.filter((it) => respuestas.value[it.id] !== undefined).length,
);
const todasRespondidas = computed(() => respondidas.value === total.value);
const valorActual = computed(() =>
  itemActual.value ? respuestas.value[itemActual.value.id] : undefined,
);

async function elegir(valor) {
  if (enviando.value || !itemActual.value) return;
  error.value = "";
  enviando.value = true;
  const item_id = itemActual.value.id;
  try {
    await api.encuestaResponder(item_id, valor);
    respuestas.value = { ...respuestas.value, [item_id]: valor };
    setTimeout(() => {
      if (indice.value < total.value - 1) indice.value += 1;
    }, 180);
  } catch (e) {
    error.value =
      e.response?.data?.detail || "No pudimos guardar tu respuesta. Intenta de nuevo.";
  } finally {
    enviando.value = false;
  }
}

function atras() {
  if (indice.value > 0) indice.value -= 1;
}
function siguiente() {
  if (indice.value < total.value - 1) indice.value += 1;
}

async function cerrar() {
  if (!todasRespondidas.value || cerrando.value) return;
  error.value = "";
  cerrando.value = true;
  try {
    const data = await api.encuestaCerrar();
    resumen.value = data.resumen;
  } catch (e) {
    error.value =
      e.response?.data?.detail || "No pudimos cerrar la encuesta.";
  } finally {
    cerrando.value = false;
  }
}

function terminar() {
  emit("cerrada", resumen.value);
}

const moduloLabel = computed(() => {
  if (!itemActual.value) return "";
  return itemActual.value.modulo === "PHQ-9" ? "PHQ-A" : "GAD-7";
});
const moduloNumero = computed(() =>
  itemActual.value ? itemActual.value.numero : 0,
);
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center px-4 py-6 overflow-y-auto"
    style="background: #edf1e8"
  >
    <div class="w-full max-w-[720px] mx-auto fade-in-up">
      <!-- ─── RESUMEN final ────────────────────────────────────────── -->
      <div v-if="resumen" class="card-hero p-8">
        <p class="eyebrow mb-2">Encuesta de cierre</p>
        <h1 class="hero-serif text-[28px] sm:text-[34px] mb-5">
          Gracias por <span class="hero-mint">responder.</span>
        </h1>
        <p class="text-[15px] text-ink-700 leading-relaxed mb-6">
          Estos son los puntajes de tu ciclo {{ encuesta.ciclo_numero }}.
          Quedan guardados para que los conversen con tu psicóloga.
        </p>

        <div class="grid sm:grid-cols-2 gap-3 mb-6">
          <div class="card-flat p-5">
            <p class="label-kicker">PHQ-A · Depresión</p>
            <p
              class="gb text-[28px] font-bold text-green-900 mt-1.5 tabular leading-none"
            >
              {{ resumen.phq9_total }}<span class="text-ink-300 text-[18px]">/27</span>
            </p>
            <p class="text-[13px] text-ink-700 font-semibold mt-2">
              {{ resumen.phq9_severidad }}
            </p>
            <p class="text-[12.5px] text-ink-500 mt-1 leading-relaxed">
              {{ resumen.phq9_accion }}
            </p>
          </div>
          <div class="card-flat p-5">
            <p class="label-kicker">GAD-7 · Ansiedad</p>
            <p
              class="gb text-[28px] font-bold text-green-900 mt-1.5 tabular leading-none"
            >
              {{ resumen.gad7_total }}<span class="text-ink-300 text-[18px]">/21</span>
            </p>
            <p class="text-[13px] text-ink-700 font-semibold mt-2">
              {{ resumen.gad7_severidad }}
            </p>
            <p class="text-[12.5px] text-ink-500 mt-1 leading-relaxed">
              {{ resumen.gad7_accion }}
            </p>
          </div>
        </div>

        <div
          v-if="resumen.crisis_protocolo"
          class="banner-danger mb-5"
        >
          <div>
            <p class="gb font-semibold mb-1">Pide ayuda ahora.</p>
            <p class="text-[14px]">
              Marcaste tener pensamientos de hacerte daño. Por favor llama
              a la <strong>Línea 113, opción 5</strong>. Es gratuita,
              confidencial y atiende 24/7. También avisa a tu psicóloga o a
              alguien de tu casa hoy mismo.
            </p>
          </div>
        </div>

        <button @click="terminar" type="button" class="btn-primary w-full">
          Volver al diario
        </button>
      </div>

      <!-- ─── PREGUNTAS ────────────────────────────────────────────── -->
      <div v-else class="card-hero p-7 sm:p-9">
        <div class="flex items-center justify-between mb-1">
          <p class="eyebrow">Cierre del ciclo {{ encuesta.ciclo_numero }}</p>
          <span class="text-[12.5px] text-ink-400 tabular">
            {{ respondidas }}/{{ total }}
          </span>
        </div>

        <div class="flex items-center gap-[6px] mt-2 mb-7">
          <span
            v-for="(it, i) in items"
            :key="it.id"
            class="flex-1 h-[5px] rounded-full transition"
            :style="{
              background:
                respuestas[it.id] !== undefined
                  ? '#4C6B53'
                  : i === indice
                    ? '#E08763'
                    : '#E4EBDE',
            }"
          ></span>
        </div>

        <div v-if="itemActual" class="mb-7">
          <p class="label-kicker">
            {{ moduloLabel }} · pregunta {{ moduloNumero }}
          </p>
          <h2
            class="gb text-[22px] sm:text-[26px] font-semibold text-green-900 leading-snug mt-2"
          >
            {{ itemActual.texto }}
          </h2>
        </div>

        <p
          class="label-kicker mb-3"
        >
          Pensando en los últimos 14 días
        </p>
        <div class="grid sm:grid-cols-2 gap-2.5">
          <button
            v-for="op in opciones"
            :key="op.valor"
            type="button"
            @click="elegir(op.valor)"
            :disabled="enviando"
            :class="[
              'flex items-center gap-3 px-4 py-4 rounded-[16px] transition text-left shadow-subtle border-[1.5px] border-transparent',
              valorActual === op.valor
                ? 'bg-green-600 text-white'
                : 'bg-white text-ink-800 hover:-translate-y-0.5 hover:shadow-lift',
            ]"
          >
            <span
              class="w-7 h-7 rounded-full flex items-center justify-center text-[13px] font-bold tabular shrink-0"
              :style="
                valorActual === op.valor
                  ? 'background: rgba(255,255,255,0.18); color: #fff;'
                  : 'background: #E2EADC; color: #3F5D4B;'
              "
            >
              {{ op.valor }}
            </span>
            <div class="min-w-0">
              <p class="font-semibold text-[14.5px] leading-tight">
                {{ op.etiqueta }}
              </p>
              <p
                class="text-[12.5px] leading-tight mt-0.5"
                :class="
                  valorActual === op.valor ? 'opacity-80' : 'text-ink-500'
                "
              >
                {{ op.descripcion }}
              </p>
            </div>
          </button>
        </div>

        <p v-if="error" class="field-error mt-4">{{ error }}</p>

        <div class="flex items-center justify-between gap-3 mt-7 flex-wrap">
          <button
            type="button"
            @click="atras"
            :disabled="indice === 0"
            class="btn-ghost"
          >
            Atrás
          </button>
          <div class="flex items-center gap-2">
            <button
              v-if="indice < total - 1"
              type="button"
              @click="siguiente"
              class="btn-secondary"
            >
              Saltar
            </button>
            <button
              v-if="todasRespondidas"
              type="button"
              @click="cerrar"
              :disabled="cerrando"
              class="btn-primary"
            >
              {{ cerrando ? "Enviando…" : "Terminar" }}
            </button>
          </div>
        </div>

        <p class="text-[12px] text-ink-400 text-center mt-5">
          Tus respuestas son confidenciales. Solo las ve tu psicóloga.
        </p>
      </div>
    </div>
  </div>
</template>
