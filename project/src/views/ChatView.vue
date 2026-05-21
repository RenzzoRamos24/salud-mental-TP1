<script setup>
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { authStore } from '../store/auth'
import SOSButton from '../components/SOSButton.vue'

const router = useRouter()

const sessionId = ref(null)
const totalPreguntas = ref(10)
const preguntaActual = ref(1)

const mensajes = ref([])
const inputRespuesta = ref('')
const cargando = ref(false)
const analizando = ref(false)
const error = ref('')
const chatBox = ref(null)

onMounted(async () => {
  try {
    const data = await api.iniciarSesion()
    sessionId.value = data.session_id
    totalPreguntas.value = data.total_preguntas
    preguntaActual.value = data.pregunta_numero

    mensajes.value.push({ autor: 'bot', texto: data.mensaje, tipo: 'saludo' })
    mensajes.value.push({
      autor: 'bot',
      texto: data.pregunta,
      pregunta_numero: data.pregunta_numero,
      tipo: 'pregunta',
    })
    scrollAbajo()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  }
})

watch(mensajes, () => scrollAbajo(), { deep: true })

async function scrollAbajo() {
  await nextTick()
  if (chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight
}

async function enviar() {
  const texto = inputRespuesta.value.trim()
  if (!texto || cargando.value) return

  error.value = ''
  mensajes.value.push({ autor: 'user', texto, pregunta_numero: preguntaActual.value })
  inputRespuesta.value = ''
  cargando.value = true

  try {
    const res = await api.responder(sessionId.value, texto)

    if (res.completado) {
      mensajes.value.push({
        autor: 'bot',
        texto: res.mensaje || '¡Evaluación completada! Procesando análisis…',
        tipo: 'completado',
      })
      analizando.value = true
      await iniciarAnalisis()
    } else {
      preguntaActual.value = res.pregunta_numero
      mensajes.value.push({
        autor: 'bot',
        texto: res.pregunta,
        pregunta_numero: res.pregunta_numero,
        tipo: 'pregunta',
        necesita_contexto: res.necesita_mas_contexto || false,
      })
    }
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    cargando.value = false
  }
}

async function iniciarAnalisis() {
  try {
    const resultado = await api.analizar(sessionId.value)
    sessionStorage.setItem('sm_upc_resultado', JSON.stringify(resultado))
    router.push('/resultados')
  } catch (e) {
    error.value = `Error analizando: ${e.response?.data?.detail || e.message}`
    analizando.value = false
  }
}

function manejarTeclado(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    enviar()
  }
}

const progreso = computed(() => {
  const n = Math.min(preguntaActual.value, totalPreguntas.value)
  return Math.round(((n - 1) / totalPreguntas.value) * 100)
})

const inicialUser = computed(() => {
  const u = authStore.state.user
  return ((u?.nombre || '?').charAt(0)).toUpperCase()
})

// Etiqueta clínica por pregunta — secuencia conceptual DASS-x
const tituloPregunta = (n) => {
  const titulos = [
    'Estado de ánimo general',
    'Estado de ánimo deprimido',
    'Necesito un poco de contexto',
    'Alteración del sueño',
    'Necesito un poco más de contexto',
    'Pérdida de interés o placer',
    'Energía y fatiga',
    'Concentración',
    'Apetito',
    'Pensamientos sobre ti mismo',
  ]
  return titulos[(n - 1) % titulos.length]
}
</script>

<template>
  <div class="min-h-[calc(100vh-4rem)] flex flex-col">
    <!-- Sub-header del chat -->
    <div class="bg-cream-50/85 backdrop-blur-md border-b border-cream-200 sticky top-16 z-10 no-print">
      <div class="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3 min-w-0">
          <div class="relative shrink-0">
            <div class="w-10 h-10 rounded-full bg-mint-200 text-mint-600 flex items-center justify-center text-base font-semibold">S</div>
            <span class="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-mint-400 border-2 border-cream-50"></span>
          </div>
          <div class="min-w-0">
            <p class="font-semibold text-ink-900 text-sm">Sami</p>
            <p class="text-xs text-ink-500">En línea · Opinion-BERT activo</p>
          </div>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <span class="dass-tag">DASS-{{ totalPreguntas }}</span>
          <div class="text-right">
            <p class="text-[11px] text-ink-500 uppercase tracking-wider">Evaluación</p>
            <div class="flex items-center gap-2 mt-0.5">
              <div class="w-32 h-1.5 bg-cream-200 rounded-full overflow-hidden">
                <div class="h-full bg-mint-400 transition-all duration-500" :style="{ width: progreso + '%' }"></div>
              </div>
              <p class="text-xs font-semibold text-ink-700">
                {{ Math.min(preguntaActual, totalPreguntas) }}<span class="text-ink-400">/{{ totalPreguntas }}</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Conversación -->
    <main ref="chatBox" class="flex-1 overflow-y-auto">
      <div class="max-w-3xl mx-auto px-4 py-6 space-y-5">
        <template v-for="(m, i) in mensajes" :key="i">
          <!-- Mensaje bot -->
          <div v-if="m.autor === 'bot'" class="flex items-start gap-3 fade-in-up">
            <div class="shrink-0 w-9 h-9 rounded-full bg-mint-200 text-mint-600 flex items-center justify-center text-sm font-semibold">S</div>
            <div class="flex flex-col gap-1.5 max-w-[80%]">
              <span v-if="m.tipo === 'saludo'" class="opinion-tag">Opinion-BERT · Análisis inicial</span>
              <span v-else-if="m.pregunta_numero" class="dass-tag">
                DASS-{{ m.pregunta_numero }} · {{ tituloPregunta(m.pregunta_numero) }}
              </span>
              <span v-else-if="m.tipo === 'completado'" class="opinion-tag">Evaluación · completada</span>
              <div :class="m.tipo === 'completado' ? 'bubble-info' : 'bubble-bot'">
                <p class="whitespace-pre-wrap leading-relaxed text-sm">{{ m.texto }}</p>
              </div>
              <div
                v-if="m.necesita_contexto"
                class="inline-flex items-center gap-2 text-[11px] font-bold uppercase tracking-wider text-peach-600"
              >
                <span>🔁</span> Necesito un poco más de contexto
              </div>
            </div>
          </div>

          <!-- Mensaje usuario -->
          <div v-else class="flex items-start gap-3 flex-row-reverse fade-in-up">
            <div class="shrink-0 w-9 h-9 rounded-full bg-peach-200 text-peach-600 flex items-center justify-center text-sm font-bold">{{ inicialUser }}</div>
            <div class="bubble-user">
              <p class="whitespace-pre-wrap leading-relaxed text-sm">{{ m.texto }}</p>
            </div>
          </div>
        </template>

        <!-- Typing indicator -->
        <div v-if="cargando && !analizando" class="flex items-start gap-3 fade-in-up">
          <div class="w-9 h-9 rounded-full bg-mint-200 text-mint-600 flex items-center justify-center text-sm font-semibold">S</div>
          <div class="bubble-bot">
            <span class="inline-flex gap-1.5 py-1">
              <span class="w-2 h-2 bg-mint-400 rounded-full dot-1"></span>
              <span class="w-2 h-2 bg-mint-400 rounded-full dot-2"></span>
              <span class="w-2 h-2 bg-mint-400 rounded-full dot-3"></span>
            </span>
          </div>
        </div>

        <!-- Card Analizando -->
        <div v-if="analizando" class="mx-auto max-w-md p-7 text-center bg-white border border-cream-200 rounded-3xl shadow-soft fade-in-up">
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-mint-100 text-mint-600 text-2xl mb-3">🧠</div>
          <p class="font-serif font-semibold text-ink-900 text-lg">Analizando con Opinion-BERT</p>
          <p class="text-sm text-ink-500 mt-2 leading-relaxed">
            La primera vez puede tardar 1–3 minutos (carga del modelo, ~400 MB).
          </p>
          <div class="inline-flex gap-1.5 mt-4">
            <span class="w-2 h-2 bg-mint-400 rounded-full dot-1"></span>
            <span class="w-2 h-2 bg-mint-400 rounded-full dot-2"></span>
            <span class="w-2 h-2 bg-mint-400 rounded-full dot-3"></span>
          </div>
        </div>

        <p v-if="error" class="banner-danger">
          <span>⚠️</span><span>{{ error }}</span>
        </p>
      </div>
    </main>

    <!-- Input -->
    <footer v-if="!analizando" class="bg-cream-50/95 backdrop-blur-md border-t border-cream-200">
      <div class="max-w-3xl mx-auto px-4 py-4">
        <div class="flex items-end gap-2">
          <textarea
            v-model="inputRespuesta"
            @keydown="manejarTeclado"
            placeholder="Escribe tu respuesta… (Enter para enviar, Shift+Enter para nueva línea)"
            rows="2"
            :disabled="cargando"
            class="input resize-none flex-1 bg-white"
          ></textarea>
          <button
            @click="enviar"
            :disabled="cargando || !inputRespuesta.trim()"
            class="px-6 py-3 rounded-2xl bg-mint-400 hover:bg-mint-500 text-white font-semibold transition disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
        <p class="text-xs text-ink-500 mt-2 text-center">
          🔒 Tus respuestas son confidenciales · Responde con honestidad para un análisis más preciso
        </p>
      </div>
    </footer>

    <SOSButton />
  </div>
</template>
