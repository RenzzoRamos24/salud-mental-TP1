<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../store/auth'
import { api } from '../api'
import SOSButton from '../components/SOSButton.vue'

const router = useRouter()
const user = computed(() => authStore.state.user)
const rol = computed(() => authStore.rol.value)

const totalSesiones = ref(0)
const ultimaEvaluacion = ref(null)

onMounted(async () => {
  if (rol.value !== 'estudiante') return
  try {
    const h = await api.miHistorial()
    totalSesiones.value = h?.total_sesiones || 0
    ultimaEvaluacion.value = h?.ultima_evaluacion || null
  } catch (_) { /* no-op */ }
})

const opcionesEstudiante = [
  { titulo: 'Iniciar evaluación',       desc: 'Conversa con Sami sobre cómo te has sentido', icon: '💬', tone: 'mint',  destino: '/chat' },
  { titulo: 'Mi historial',             desc: 'Revisa tus evaluaciones anteriores',          icon: '📊', tone: 'sky',   destino: '/mi-historial' },
  { titulo: 'Recursos y aprendizaje',   desc: 'Artículos y consejos psicoeducativos',         icon: '💡', tone: 'brand', destino: '/recursos' },
  { titulo: 'Encuesta de satisfacción', desc: 'Cuéntanos cómo te fue con Sami',               icon: '⭐', tone: 'peach', destino: '/encuesta' },
  { titulo: 'Mi perfil',                desc: 'Edita tus datos y privacidad',                 icon: '👤', tone: 'peach', destino: '/perfil' },
]

const opcionesPsicologo = [
  { titulo: 'Panel de estudiantes', desc: 'Métricas, alertas tempranas y agenda de citas.', icon: '👥', tone: 'mint',  destino: '/psicologo' },
  { titulo: 'Recursos UPC',         desc: 'Material clínico y líneas de apoyo.',            icon: '💡', tone: 'brand', destino: '/recursos' },
  { titulo: 'Mi perfil',            desc: 'Actualiza tus datos y contraseña.',              icon: '👤', tone: 'peach', destino: '/perfil' },
]

const opcionesAdmin = [
  { titulo: 'Usuarios del sistema', desc: 'Listado de estudiantes, psicólogos y admins.', icon: '👥', tone: 'mint',  destino: '/admin' },
  { titulo: 'Configuración',        desc: 'Preguntas del chatbot, umbrales BERT, respaldos.', icon: '⚙️', tone: 'sky',   destino: '/admin/sistema' },
  { titulo: 'Contenidos educativos',desc: 'Publicar y editar recursos visibles para estudiantes.', icon: '📚', tone: 'brand', destino: '/admin/contenidos' },
  { titulo: 'Mensajes del chatbot', desc: 'Plantillas conversacionales de Sami.',             icon: '💬', tone: 'peach', destino: '/admin/mensajes-chatbot' },
  { titulo: 'Reportes',             desc: 'Estadísticas globales del sistema.',               icon: '📊', tone: 'sky',   destino: '/admin/reportes' },
  { titulo: 'Auditoría de accesos', desc: 'Logs detallados de cada llamada a la API.',        icon: '🛡️', tone: 'brand', destino: '/admin/logs' },
]

const opciones = computed(() => {
  if (rol.value === 'admin') return opcionesAdmin
  if (rol.value === 'psicologo') return opcionesPsicologo
  return opcionesEstudiante
})

const esEstudiante = computed(() => rol.value === 'estudiante')

const tituloHero = computed(() => {
  if (rol.value === 'admin') return ['Bienvenido al', 'panel de administración']
  if (rol.value === 'psicologo') return ['Bienvenido a', 'tu panel clínico']
  return ['Bienvenido a', 'tu espacio de bienestar']
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-6 py-10">
    <!-- Hero -->
    <section class="mb-10 fade-in-up">
      <p class="text-sm text-mint-500 font-medium mb-2">
        Hola, {{ user?.nombre }} <span class="not-italic">👋</span>
      </p>
      <h1 class="hero-serif text-4xl sm:text-5xl">
        {{ tituloHero[0] }} <span class="hero-mint">{{ tituloHero[1] }}</span>
      </h1>
    </section>

    <!-- Grid 2 columnas -->
    <div class="grid sm:grid-cols-2 gap-5">
      <button
        v-for="(op, i) in opciones"
        :key="i"
        @click="router.push(op.destino)"
        class="group menu-card text-left fade-in-up"
        :style="{ animationDelay: (i * 60) + 'ms' }"
      >
        <span class="menu-card-arrow">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </span>
        <div
          class="icon-box mb-5"
          :class="{
            'icon-box-mint':  op.tone === 'mint',
            'icon-box-sky':   op.tone === 'sky',
            'icon-box-brand': op.tone === 'brand',
            'icon-box-peach': op.tone === 'peach',
          }"
        >{{ op.icon }}</div>
        <h3 class="font-serif text-xl font-semibold text-ink-900">{{ op.titulo }}</h3>
        <p class="text-sm text-ink-500 mt-1.5 leading-relaxed">{{ op.desc }}</p>
      </button>
    </div>

    <!-- Banner crisis solo estudiantes -->
    <div
      v-if="esEstudiante"
      class="mt-8 rounded-3xl bg-peach-50 border border-peach-100 p-6 flex items-start gap-4 fade-in-up"
    >
      <div class="w-12 h-12 rounded-full bg-peach-200 text-peach-600 flex items-center justify-center text-xl shrink-0">
        ♥
      </div>
      <div>
        <p class="font-serif text-lg font-semibold text-ink-900">¿Estás pasando por un momento difícil?</p>
        <p class="text-sm text-ink-600 mt-1 leading-relaxed">
          Llama gratis a la <strong>Línea 113 (MINSA), opción 5</strong> — atención 24/7 en salud mental,
          o habla con la psicóloga del colegio o tu tutor de aula.
        </p>
      </div>
    </div>

    <SOSButton v-if="esEstudiante" />
  </div>
</template>
