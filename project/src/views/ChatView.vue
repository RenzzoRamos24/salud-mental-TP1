<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { authStore } from '../store/auth'

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
  mensajes.value.push({ autor: 'user', texto })
  inputRespuesta.value = ''
  cargando.value = true

  try {
    const res = await api.responder(sessionId.value, texto)

    if (res.completado) {
      mensajes.value.push({
        autor: 'bot',
        texto: res.mensaje || '¡Evaluación completada! Analizando con BERT…',
        tipo: 'info',
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

const progreso = () => {
  const n = Math.min(preguntaActual.value, totalPreguntas.value)
  return Math.round(((n - 1) / totalPreguntas.value) * 100)
}
</script>

<template>
  <div class="min-h-[calc(100vh-3rem)] flex flex-col bg-gradient-to-b from-slate-50 to-slate-100">
    <!-- Subheader con progreso -->
    <div class="bg-white border-b border-slate-200 sticky top-12 z-10 no-print">
      <div class="max-w-3xl mx-auto px-4 py-2 flex items-center justify-between">
        <p class="text-sm text-slate-700">
          Hola, <span class="font-medium">{{ authStore.state.user?.nombre }}</span>
        </p>
        <div class="text-right">
          <p class="text-xs font-medium text-slate-600">
            Pregunta {{ Math.min(preguntaActual, totalPreguntas) }} de {{ totalPreguntas }}
          </p>
          <div class="w-32 h-2 bg-slate-200 rounded-full mt-1 overflow-hidden">
            <div class="h-full bg-brand-600 transition-all duration-500" :style="{ width: progreso() + '%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <main ref="chatBox" class="flex-1 overflow-y-auto">
      <div class="max-w-3xl mx-auto px-4 py-6 space-y-4">
        <div v-for="(m, i) in mensajes" :key="i" class="flex fade-in-up"
             :class="m.autor === 'user' ? 'justify-end' : 'justify-start'">
          <div class="flex items-end gap-2 max-w-[80%]"
               :class="m.autor === 'user' ? 'flex-row-reverse' : ''">
            <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm"
                 :class="m.autor === 'user' ? 'bg-brand-600 text-white' : 'bg-white border border-slate-200'">
              {{ m.autor === 'user' ? '🧑' : '🤖' }}
            </div>
            <div class="rounded-2xl px-4 py-3 shadow-sm"
                 :class="[
                   m.autor === 'user'
                     ? 'bg-brand-600 text-white rounded-br-sm'
                     : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm',
                   m.tipo === 'info' ? 'italic text-slate-600 bg-amber-50 border-amber-200' : '',
                 ]">
              <p v-if="m.pregunta_numero" class="text-xs font-semibold mb-1 opacity-70">
                Pregunta {{ m.pregunta_numero }}
              </p>
              <p class="whitespace-pre-wrap leading-relaxed">{{ m.texto }}</p>
            </div>
          </div>
        </div>

        <div v-if="cargando && !analizando" class="flex justify-start fade-in-up">
          <div class="flex items-end gap-2">
            <div class="w-8 h-8 rounded-full bg-white border border-slate-200 flex items-center justify-center">🤖</div>
            <div class="bg-white border border-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
              <span class="inline-flex gap-1">
                <span class="w-2 h-2 bg-slate-400 rounded-full dot-1"></span>
                <span class="w-2 h-2 bg-slate-400 rounded-full dot-2"></span>
                <span class="w-2 h-2 bg-slate-400 rounded-full dot-3"></span>
              </span>
            </div>
          </div>
        </div>

        <div v-if="analizando" class="mx-auto max-w-md bg-brand-50 border border-brand-200 rounded-xl p-6 text-center fade-in-up">
          <div class="text-4xl mb-2">🧠</div>
          <p class="font-semibold text-brand-900 mb-1">Analizando con BERT</p>
          <p class="text-sm text-brand-700 mb-3">
            La primera vez puede tardar 1–3 minutos (carga del modelo, ~400 MB).
          </p>
          <div class="inline-flex gap-1">
            <span class="w-2 h-2 bg-brand-500 rounded-full dot-1"></span>
            <span class="w-2 h-2 bg-brand-500 rounded-full dot-2"></span>
            <span class="w-2 h-2 bg-brand-500 rounded-full dot-3"></span>
          </div>
        </div>

        <p v-if="error" class="text-red-600 text-sm text-center">{{ error }}</p>
      </div>
    </main>

    <footer v-if="!analizando" class="bg-white border-t border-slate-200 shadow-lg">
      <div class="max-w-3xl mx-auto px-4 py-4">
        <div class="flex items-end gap-2">
          <textarea v-model="inputRespuesta" @keydown="manejarTeclado"
            placeholder="Escribe tu respuesta… (Enter para enviar, Shift+Enter para nueva línea)"
            rows="2" :disabled="cargando"
            class="flex-1 px-4 py-3 border border-slate-300 rounded-xl resize-none focus:ring-2 focus:ring-brand-500 outline-none disabled:bg-slate-100" />
          <button @click="enviar" :disabled="cargando || !inputRespuesta.trim()"
            class="bg-brand-600 hover:bg-brand-700 disabled:bg-slate-300 text-white font-semibold px-6 py-3 rounded-xl shadow-md transition">
            Enviar
          </button>
        </div>
        <p class="text-xs text-slate-500 mt-2 text-center">
          Tus respuestas son confidenciales. Responde con honestidad para un análisis más preciso.
        </p>
      </div>
    </footer>
  </div>
</template>
