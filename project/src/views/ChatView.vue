<script setup>
import { ref, nextTick, onMounted, watch, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import SOSButton from "../components/SOSButton.vue";

const router = useRouter();

const sessionId = ref(null);
const totalPreguntas = ref(16);
const preguntaActual = ref(0);
const fase = ref("apertura");
const itemActual = ref(null);

const mensajes = ref([]);
const inputRespuesta = ref("");
const cargando = ref(false);
const analizando = ref(false);
const error = ref("");
const chatBox = ref(null);

onMounted(async () => {
  try {
    const data = await api.iniciarSesion();
    sessionId.value = data.session_id;
    totalPreguntas.value = data.total_preguntas;
    preguntaActual.value = data.pregunta_numero;
    fase.value = data.fase || "apertura";

    mensajes.value.push({ autor: "bot", texto: data.mensaje, tipo: "saludo" });
    scrollAbajo();
  } catch (e) {
    error.value = e.response?.data?.detail || e.message;
  }
});

watch(mensajes, () => scrollAbajo(), { deep: true });

async function scrollAbajo() {
  await nextTick();
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight;
}

function aplicarRespuestaBot(res) {
  itemActual.value = null;

  if (res.completado) {
    mensajes.value.push({
      autor: "bot",
      texto: res.mensaje || "Evaluación completada. Procesando análisis…",
      tipo: "completado",
    });
    analizando.value = true;
    return iniciarAnalisis();
  }

  const faseAnterior = fase.value;
  fase.value = res.fase || fase.value;
  preguntaActual.value = res.pregunta_numero;

  // Acuse del bot (una sola vez):
  //   - Si veníamos de apertura → este `mensaje` es el triage. Lo mostramos
  //     como "info" antes de la primera pregunta.
  //   - Si ya estábamos en evaluación → es un acuse breve ("Gracias por
  //     contarme", "Te entiendo…"). Solo lo mostramos si la respuesta no
  //     pide aclaración (en ese caso, el `mensaje` reemplaza al acuse).
  if (res.mensaje && faseAnterior === "apertura") {
    mensajes.value.push({ autor: "bot", texto: res.mensaje, tipo: "info" });
  } else if (res.mensaje && !res.requiere_seleccion) {
    mensajes.value.push({ autor: "bot", texto: res.mensaje, tipo: "ack" });
  }

  if (res.requiere_seleccion) {
    // El bot pide aclarar frecuencia con botones, sin repetir la pregunta.
    mensajes.value.push({
      autor: "bot",
      texto: res.mensaje || "¿Con qué frecuencia te pasa esto?",
      tipo: "aclaracion",
      modulo: res.modulo,
      item_codigo: res.item_codigo,
      criterio_dsm5: res.criterio_dsm5,
    });
  } else {
    // Pregunta nueva (PHQ-9 o GAD-7)
    mensajes.value.push({
      autor: "bot",
      texto: res.pregunta,
      tipo: "pregunta",
      pregunta_numero: res.pregunta_numero,
      modulo: res.modulo,
      item_codigo: res.item_codigo,
      criterio_dsm5: res.criterio_dsm5,
    });
  }

  itemActual.value = {
    item_codigo: res.item_codigo,
    modulo: res.modulo,
    criterio_dsm5: res.criterio_dsm5,
    opciones_likert: res.opciones_likert,
    requiere_seleccion: !!res.requiere_seleccion,
    score_propuesto: res.score_propuesto,
  };
}

async function enviarTexto() {
  const texto = inputRespuesta.value.trim();
  if (!texto || cargando.value) return;

  error.value = "";
  mensajes.value.push({ autor: "user", texto });
  inputRespuesta.value = "";
  cargando.value = true;

  try {
    const res = await api.responder(sessionId.value, texto);
    await aplicarRespuestaBot(res);
  } catch (e) {
    error.value = e.response?.data?.detail || e.message;
  } finally {
    cargando.value = false;
  }
}

async function enviarScore(score) {
  if (cargando.value) return;
  const opcion = (itemActual.value?.opciones_likert || []).find(
    (o) => o.valor === score,
  );
  const etiqueta = opcion?.etiqueta || `Opción ${score}`;

  error.value = "";
  mensajes.value.push({ autor: "user", texto: etiqueta });
  cargando.value = true;

  try {
    const res = await api.responder(sessionId.value, etiqueta, score);
    await aplicarRespuestaBot(res);
  } catch (e) {
    error.value = e.response?.data?.detail || e.message;
  } finally {
    cargando.value = false;
  }
}

async function iniciarAnalisis() {
  try {
    const resultado = await api.analizar(sessionId.value);
    sessionStorage.setItem("sm_upc_resultado", JSON.stringify(resultado));
    router.push("/resultados");
  } catch (e) {
    error.value = `Error analizando: ${e.response?.data?.detail || e.message}`;
    analizando.value = false;
  }
}

function manejarTeclado(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    enviarTexto();
  }
}

const progreso = computed(() => {
  const n = Math.min(preguntaActual.value, totalPreguntas.value);
  return Math.round((100 * n) / totalPreguntas.value);
});

const inicialUser = computed(() => {
  const u = authStore.state.user;
  return (u?.nombre || "·").charAt(0).toUpperCase();
});

const moduloChip = (modulo) => {
  if (modulo === "PHQ-9") return "PHQ-9";
  if (modulo === "GAD-7") return "GAD-7";
  return modulo || "Inicio";
};

// En fase evaluación SIEMPRE mostramos los 4 botones Likert (clinímetricamente
// es lo correcto: el score lo elige el usuario, no el modelo). El textarea
// queda como vía para explicar con texto si quiere.
const mostrarBotonera = computed(
  () =>
    fase.value === "evaluacion" &&
    !!itemActual.value?.opciones_likert?.length &&
    !analizando.value &&
    !cargando.value,
);

const escalaActiva = computed(() => {
  if (fase.value !== "evaluacion") return "PHQ-9 + GAD-7";
  return itemActual.value?.modulo || "PHQ-9 + GAD-7";
});
</script>

<template>
  <div class="min-h-[calc(100vh-3.5rem)] flex flex-col bg-white">
    <div class="bg-white border-b border-ink-100 sticky top-14 z-10 no-print">
      <div
        class="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between gap-4"
      >
        <div class="flex items-center gap-3 min-w-0">
          <div class="avatar-md">S</div>
          <div class="min-w-0">
            <p class="font-semibold text-ink-900 text-sm">Sami</p>
            <p class="text-xs text-ink-500">En línea</p>
          </div>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <span class="dass-tag">{{ escalaActiva }}</span>
          <div class="text-right">
            <p class="text-[11px] text-ink-500 uppercase tracking-wider">
              Evaluación
            </p>
            <div class="flex items-center gap-2 mt-1">
              <div class="w-28 h-1.5 bg-ink-100 rounded overflow-hidden">
                <div
                  class="h-full bg-green-600 transition-all duration-500"
                  :style="{ width: progreso + '%' }"
                ></div>
              </div>
              <p class="text-xs font-semibold text-ink-700">
                {{ Math.min(preguntaActual, totalPreguntas)
                }}<span class="text-ink-400">/{{ totalPreguntas }}</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <main ref="chatBox" class="flex-1 overflow-y-auto">
      <div class="max-w-3xl mx-auto px-4 py-6 space-y-4">
        <template v-for="(m, i) in mensajes" :key="i">
          <div
            v-if="m.autor === 'bot'"
            class="flex items-start gap-3 fade-in-up"
          >
            <div class="avatar-sm shrink-0">S</div>
            <div class="flex flex-col gap-1.5 max-w-[80%]">
              <span v-if="m.tipo === 'saludo'" class="opinion-tag">
                Apertura — cuéntame
              </span>
              <span v-else-if="m.modulo" class="dass-tag">
                {{ moduloChip(m.modulo)
                }}<span v-if="m.criterio_dsm5" class="opacity-70">
                  · {{ m.criterio_dsm5 }}</span
                >
              </span>
              <span v-else-if="m.tipo === 'completado'" class="opinion-tag">
                Evaluación — completada
              </span>
              <div
                :class="
                  m.tipo === 'completado' || m.tipo === 'info'
                    ? 'bubble-info'
                    : 'bubble-bot'
                "
              >
                <p class="whitespace-pre-wrap leading-relaxed text-sm">
                  {{ m.texto }}
                </p>
              </div>
            </div>
          </div>

          <div
            v-else
            class="flex items-start gap-3 flex-row-reverse fade-in-up"
          >
            <div class="avatar-sm shrink-0 bg-ink-100 text-ink-900">
              {{ inicialUser }}
            </div>
            <div class="bubble-user">
              <p class="whitespace-pre-wrap leading-relaxed text-sm">
                {{ m.texto }}
              </p>
            </div>
          </div>
        </template>

        <!-- Botonera Likert: siempre visible en fase evaluación -->
        <div
          v-if="mostrarBotonera"
          class="flex items-start gap-3 fade-in-up pl-12"
        >
          <div class="w-full max-w-xl">
            <p
              class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold mb-2"
            >
              Elige con qué frecuencia te ha pasado
            </p>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                v-for="op in itemActual.opciones_likert"
                :key="op.valor"
                @click="enviarScore(op.valor)"
                class="card p-3 text-left hover:border-green-500 transition"
              >
                <p
                  class="text-[10px] uppercase tracking-wider text-ink-400 font-semibold"
                >
                  {{ op.valor }}
                </p>
                <p
                  class="text-sm font-semibold text-ink-900 mt-0.5 leading-tight"
                >
                  {{ op.etiqueta }}
                </p>
                <p class="text-[11px] text-ink-500 mt-0.5">
                  {{ op.descripcion }}
                </p>
              </button>
            </div>
          </div>
        </div>

        <div
          v-if="cargando && !analizando"
          class="flex items-start gap-3 fade-in-up"
        >
          <div class="avatar-sm shrink-0">S</div>
          <div class="bubble-bot">
            <span class="inline-flex gap-1.5 py-1">
              <span class="w-2 h-2 bg-green-600 rounded-full dot-1"></span>
              <span class="w-2 h-2 bg-green-600 rounded-full dot-2"></span>
              <span class="w-2 h-2 bg-green-600 rounded-full dot-3"></span>
            </span>
          </div>
        </div>

        <div
          v-if="analizando"
          class="mx-auto max-w-md p-6 bg-white border border-ink-200 rounded-xl shadow-soft"
        >
          <p class="font-semibold text-ink-900">Analizando tu conversación</p>
          <p class="text-sm text-ink-600 mt-1.5 leading-relaxed">
            Calculando PHQ-9 y GAD-7 y revisando con BERT. Puede tardar
            1–3 minutos la primera vez (~400 MB de modelo).
          </p>
          <div class="inline-flex gap-1.5 mt-3">
            <span class="w-2 h-2 bg-green-600 rounded-full dot-1"></span>
            <span class="w-2 h-2 bg-green-600 rounded-full dot-2"></span>
            <span class="w-2 h-2 bg-green-600 rounded-full dot-3"></span>
          </div>
        </div>

        <p v-if="error" class="banner-danger">{{ error }}</p>
      </div>
    </main>

    <footer v-if="!analizando" class="bg-white border-t border-ink-100">
      <div class="max-w-3xl mx-auto px-4 py-3">
        <div class="flex items-end gap-2">
          <textarea
            v-model="inputRespuesta"
            @keydown="manejarTeclado"
            :placeholder="
              mostrarBotonera
                ? '¿Quieres contar algo más? (opcional)'
                : 'Escribe tu respuesta… (Enter para enviar)'
            "
            rows="2"
            :disabled="cargando"
            class="input resize-none flex-1"
          ></textarea>
          <button
            @click="enviarTexto"
            :disabled="cargando || !inputRespuesta.trim()"
            class="btn-primary px-5 py-3"
          >
            Enviar
          </button>
        </div>
        <p class="text-xs text-ink-500 mt-2 text-center">
          Tus respuestas son confidenciales. Responde con honestidad.
        </p>
      </div>
    </footer>

    <SOSButton />
  </div>
</template>
