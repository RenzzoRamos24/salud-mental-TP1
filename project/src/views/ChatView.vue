<script setup>
import { ref, nextTick, onMounted, watch, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import SOSButton from "../components/SOSButton.vue";

const router = useRouter();

const sessionId = ref(null);
const totalPreguntas = ref(10);
const preguntaActual = ref(1);

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

    mensajes.value.push({ autor: "bot", texto: data.mensaje, tipo: "saludo" });
    mensajes.value.push({
      autor: "bot",
      texto: data.pregunta,
      pregunta_numero: data.pregunta_numero,
      tipo: "pregunta",
    });
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

async function enviar() {
  const texto = inputRespuesta.value.trim();
  if (!texto || cargando.value) return;

  error.value = "";
  mensajes.value.push({
    autor: "user",
    texto,
    pregunta_numero: preguntaActual.value,
  });
  inputRespuesta.value = "";
  cargando.value = true;

  try {
    const res = await api.responder(sessionId.value, texto);

    if (res.completado) {
      mensajes.value.push({
        autor: "bot",
        texto: res.mensaje || "Evaluación completada. Procesando análisis…",
        tipo: "completado",
      });
      analizando.value = true;
      await iniciarAnalisis();
    } else {
      preguntaActual.value = res.pregunta_numero;
      mensajes.value.push({
        autor: "bot",
        texto: res.pregunta,
        pregunta_numero: res.pregunta_numero,
        tipo: "pregunta",
        necesita_contexto: res.necesita_mas_contexto || false,
      });
    }
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
    enviar();
  }
}

const progreso = computed(() => {
  const n = Math.min(preguntaActual.value, totalPreguntas.value);
  return Math.round(((n - 1) / totalPreguntas.value) * 100);
});

const inicialUser = computed(() => {
  const u = authStore.state.user;
  return (u?.nombre || "·").charAt(0).toUpperCase();
});

const tituloPregunta = (n) => {
  const titulos = [
    "Estado de ánimo general",
    "Estado de ánimo deprimido",
    "Necesito un poco de contexto",
    "Alteración del sueño",
    "Necesito un poco más de contexto",
    "Pérdida de interés o placer",
    "Energía y fatiga",
    "Concentración",
    "Apetito",
    "Pensamientos sobre ti mismo",
  ];
  return titulos[(n - 1) % titulos.length];
};
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
          <span class="dass-tag">DASS-{{ totalPreguntas }}</span>
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
              <span v-if="m.tipo === 'saludo'" class="opinion-tag"
                >Opinion-BERT — análisis inicial</span
              >
              <span v-else-if="m.pregunta_numero" class="dass-tag">
                DASS-{{ m.pregunta_numero }} —
                {{ tituloPregunta(m.pregunta_numero) }}
              </span>
              <span v-else-if="m.tipo === 'completado'" class="opinion-tag"
                >Evaluación — completada</span
              >
              <div
                :class="m.tipo === 'completado' ? 'bubble-info' : 'bubble-bot'"
              >
                <p class="whitespace-pre-wrap leading-relaxed text-sm">
                  {{ m.texto }}
                </p>
              </div>
              <div
                v-if="m.necesita_contexto"
                class="inline-flex items-center text-[11px] font-medium uppercase tracking-wider text-ink-500"
              >
                Necesito un poco más de contexto
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

        <div
          v-if="cargando && !analizando"
          class="flex items-start gap-3 fade-in-up"
        >
          <div class="avatar-sm shrink-0">S</div>
          <div class="bubble-bot">
            <span class="inline-flex gap-1.5 py-1"> </span>
          </div>
        </div>

        <div
          v-if="analizando"
          class="mx-auto max-w-md p-6 bg-white border border-ink-200 rounded-xl"
        >
          <p class="font-semibold text-ink-900">Analizando con Opinion-BERT</p>
          <p class="text-sm text-ink-600 mt-1.5 leading-relaxed">
            La primera vez puede tardar 1–3 minutos (carga del modelo, ~400 MB).
          </p>
          <div class="inline-flex gap-1.5 mt-3"></div>
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
            placeholder="Escribe tu respuesta… (Enter para enviar)"
            rows="2"
            :disabled="cargando"
            class="input resize-none flex-1"
          ></textarea>
          <button
            @click="enviar"
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
