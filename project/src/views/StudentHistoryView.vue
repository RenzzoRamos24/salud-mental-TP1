<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import { api } from '../api'

Chart.register(...registerables)

const route = useRoute()
const router = useRouter()

const cargando = ref(true)
const error = ref('')
const data = ref(null)
const sesionAbierta = ref(null)
const chartCanvas = ref(null)
let chartInstance = null

const colorRiesgo = {
  'CRÍTICO': 'bg-red-100 text-red-800 border-red-300',
  'ALTO':    'bg-orange-100 text-orange-800 border-orange-300',
  'MEDIO':   'bg-amber-100 text-amber-800 border-amber-300',
  'BAJO':    'bg-emerald-100 text-emerald-800 border-emerald-300',
}

const nivelANumero = { 'BAJO': 1, 'MEDIO': 2, 'ALTO': 3, 'CRÍTICO': 4 }
const numeroANivel = { 1: 'BAJO', 2: 'MEDIO', 3: 'ALTO', 4: 'CRÍTICO' }

function fechaCorta(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PE', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

function fechaLarga(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PE', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function toggleSesion(id) {
  sesionAbierta.value = sesionAbierta.value === id ? null : id
}

const tieneSerie = computed(() => data.value?.serie_temporal?.length > 0)

function dibujarGrafico() {
  if (!chartCanvas.value || !tieneSerie.value) return

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  const serie = data.value.serie_temporal
  const labels = serie.map(p => fechaCorta(p.fecha))
  const valores = serie.map(p => nivelANumero[p.nivel] || 0)
  const colores = serie.map(p => {
    if (p.nivel === 'CRÍTICO') return '#dc2626'
    if (p.nivel === 'ALTO') return '#ea580c'
    if (p.nivel === 'MEDIO') return '#d97706'
    return '#059669'
  })

  chartInstance = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Nivel de riesgo',
        data: valores,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.3,
        pointBackgroundColor: colores,
        pointBorderColor: colores,
        pointRadius: 6,
        pointHoverRadius: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const p = serie[ctx.dataIndex]
              return `${p.nivel} (score: ${p.score?.toFixed(2) ?? '—'})`
            },
          },
        },
      },
      scales: {
        y: {
          min: 0,
          max: 4,
          ticks: {
            stepSize: 1,
            callback: (v) => numeroANivel[v] || '',
          },
          grid: { color: '#e2e8f0' },
        },
        x: {
          grid: { display: false },
        },
      },
    },
  })
}

onMounted(async () => {
  try {
    data.value = await api.historialEstudiante(route.params.id)
    await nextTick()
    dibujarGrafico()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div class="min-h-[calc(100vh-3rem)] bg-slate-50 py-8 px-4">
    <div class="max-w-5xl mx-auto">
      <button @click="router.push('/psicologo')"
        class="text-sm text-slate-600 hover:text-brand-700 mb-4 inline-flex items-center gap-1">
        ← Volver a estudiantes
      </button>

      <div v-if="cargando" class="text-center text-slate-500 py-12">Cargando historial…</div>
      <p v-else-if="error" class="text-red-600">{{ error }}</p>

      <div v-else-if="data" class="space-y-6">
        <!-- Encabezado del estudiante -->
        <header class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 fade-in-up">
          <div class="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <p class="text-sm text-slate-500">Historial emocional · HU-20</p>
              <h1 class="text-2xl font-bold text-slate-900 mt-1">
                {{ data.estudiante.nombre }} {{ data.estudiante.apellido }}
              </h1>
              <p class="text-slate-600 font-mono text-sm mt-1">{{ data.estudiante.email }}</p>
            </div>
            <div class="text-right">
              <p class="text-xs text-slate-500 mb-1">Último riesgo</p>
              <span v-if="data.estudiante.ultimo_riesgo"
                :class="['inline-block px-3 py-1 rounded-full text-sm font-bold border',
                  colorRiesgo[data.estudiante.ultimo_riesgo]]">
                {{ data.estudiante.ultimo_riesgo }}
              </span>
              <span v-else class="text-slate-400">Sin evaluaciones</span>
              <p class="text-xs text-slate-500 mt-1">
                {{ fechaCorta(data.estudiante.ultima_evaluacion) }}
              </p>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-slate-100">
            <div>
              <p class="text-xs text-slate-500 uppercase">Sesiones totales</p>
              <p class="text-2xl font-bold text-slate-900">{{ data.estudiante.total_sesiones }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 uppercase">Completadas</p>
              <p class="text-2xl font-bold text-emerald-700">{{ data.estudiante.sesiones_completadas }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 uppercase">Score actual</p>
              <p class="text-2xl font-bold text-slate-900">
                {{ data.estudiante.ultimo_score?.toFixed(2) ?? '—' }}
              </p>
            </div>
          </div>
        </header>

        <!-- Gráfico de evolución -->
        <section v-if="tieneSerie" class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 fade-in-up">
          <h2 class="text-lg font-bold text-slate-900 mb-4">Evolución del nivel de riesgo</h2>
          <div class="h-64">
            <canvas ref="chartCanvas"></canvas>
          </div>
        </section>

        <!-- Lista de sesiones -->
        <section class="bg-white rounded-2xl shadow-sm border border-slate-200 fade-in-up overflow-hidden">
          <h2 class="text-lg font-bold text-slate-900 p-6 pb-4">Sesiones</h2>

          <p v-if="data.sesiones.length === 0" class="text-slate-500 text-center py-8">
            Este estudiante aún no ha realizado evaluaciones.
          </p>

          <ul v-else class="divide-y divide-slate-100">
            <li v-for="s in data.sesiones" :key="s.session_id" class="px-6 py-4">
              <button @click="toggleSesion(s.session_id)"
                class="w-full text-left flex items-center justify-between gap-4 hover:bg-slate-50 -mx-2 px-2 py-1 rounded">
                <div class="flex items-center gap-3 flex-wrap">
                  <span v-if="s.nivel_riesgo"
                    :class="['inline-block px-2 py-1 rounded-full text-xs font-bold border',
                      colorRiesgo[s.nivel_riesgo]]">
                    {{ s.nivel_riesgo }}
                  </span>
                  <span v-else class="text-xs text-slate-400 italic">Sin análisis</span>
                  <span class="text-sm text-slate-700">{{ fechaLarga(s.fecha_inicio) }}</span>
                  <span class="text-xs text-slate-400">·</span>
                  <span class="text-xs"
                    :class="s.estado === 'completada' ? 'text-emerald-600' : 'text-amber-600'">
                    {{ s.estado }}
                  </span>
                </div>
                <span class="text-slate-400 text-sm">
                  {{ sesionAbierta === s.session_id ? '▲' : '▼' }}
                </span>
              </button>

              <div v-if="sesionAbierta === s.session_id" class="mt-4 space-y-4 pl-2">
                <div v-if="s.explicacion"
                  class="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                  <p class="text-xs font-bold text-indigo-900 uppercase mb-1">Explicación clínica</p>
                  <p class="text-sm text-indigo-900 whitespace-pre-wrap">{{ s.explicacion }}</p>
                </div>

                <div>
                  <p class="text-xs font-bold text-slate-700 uppercase mb-2">
                    Conversación ({{ s.conversacion.length }} preguntas)
                  </p>
                  <ol class="space-y-3">
                    <li v-for="c in s.conversacion" :key="c.numero"
                      class="bg-slate-50 border border-slate-200 rounded-lg p-3">
                      <p class="text-xs text-slate-500 mb-1">Pregunta {{ c.numero }}</p>
                      <p class="text-sm font-medium text-slate-900 mb-2">{{ c.pregunta }}</p>
                      <p class="text-sm text-slate-700 italic border-l-2 border-brand-300 pl-3">
                        {{ c.respuesta }}
                      </p>
                    </li>
                  </ol>
                </div>
              </div>
            </li>
          </ul>
        </section>
      </div>
    </div>
  </div>
</template>
