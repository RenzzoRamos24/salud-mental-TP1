<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'
import RiskBadge from '../components/RiskBadge.vue'
import StatCard from '../components/StatCard.vue'

Chart.register(...registerables)

const router = useRouter()
const cargando = ref(true)
const error = ref('')
const data = ref(null)
const sesionAbierta = ref(null)
const chartCanvas = ref(null)
let chartInstance = null

const nivelANumero = { 'BAJO': 1, 'MEDIO': 2, 'ALTO': 3, 'CRÍTICO': 4 }
const numeroANivel = { 1: 'BAJO', 2: 'MEDIO', 3: 'ALTO', 4: 'CRÍTICO' }

function normalizarNivel(n) { return n ? n.toUpperCase().trim() : null }
function fechaCorta(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PE', { year: 'numeric', month: 'short', day: 'numeric' })
}
function fechaLarga(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PE', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function toggleSesion(id) { sesionAbierta.value = sesionAbierta.value === id ? null : id }

const sesionesCompletadas = computed(() => (data.value?.sesiones || []).filter(s => s.estado === 'completada'))
const tieneSerie = computed(() => (data.value?.serie_temporal?.length || 0) > 0)
const ultimoNivel = computed(() => normalizarNivel(data.value?.estudiante?.ultimo_riesgo))

function dibujarGrafico() {
  if (!chartCanvas.value || !tieneSerie.value) return
  if (chartInstance) { chartInstance.destroy(); chartInstance = null }
  const serie = data.value.serie_temporal
  const labels = serie.map(p => fechaCorta(p.fecha))
  const valores = serie.map(p => nivelANumero[normalizarNivel(p.nivel)] || 0)
  const colores = serie.map(p => {
    const n = normalizarNivel(p.nivel)
    if (n === 'CRÍTICO') return '#E0413A'
    if (n === 'ALTO') return '#F2754F'
    if (n === 'MEDIO') return '#F2A93B'
    return '#3DC57E'
  })

  chartInstance = new Chart(chartCanvas.value.getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [{
      label: 'Nivel de riesgo', data: valores,
      borderColor: '#8B6CF0', backgroundColor: 'rgba(139, 108, 240, 0.10)',
      borderWidth: 2.5, fill: true, tension: 0.35,
      pointBackgroundColor: colores, pointBorderColor: '#fff',
      pointBorderWidth: 2, pointRadius: 7, pointHoverRadius: 9,
    }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => {
          const p = serie[ctx.dataIndex]
          return `${normalizarNivel(p.nivel)} (score: ${p.score?.toFixed(2) ?? '—'})`
        } } } },
      scales: {
        y: { min: 0, max: 4, ticks: { stepSize: 1, callback: (v) => numeroANivel[v] || '' }, grid: { color: '#EDEAF0' } },
        x: { grid: { display: false } },
      },
    },
  })
}

onMounted(async () => {
  try {
    data.value = await api.miHistorial()
    const primeraCompleta = (data.value?.sesiones || []).find(s => s.estado === 'completada')
    if (primeraCompleta) sesionAbierta.value = primeraCompleta.session_id
  } catch (e) { error.value = e.response?.data?.detail || e.message }
  finally { cargando.value = false }
  await nextTick()
  dibujarGrafico()
})
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">← Volver al menú</button>

    <div v-if="cargando" class="text-center text-ink-500 py-16">Cargando tu historial…</div>
    <p v-else-if="error" class="banner-danger">⚠️ {{ error }}</p>

    <div v-else-if="data" class="space-y-6">
      <PageHeader
        title="Mi historial"
        accent="emocional"
        :subtitle="`${data.estudiante.nombre} ${data.estudiante.apellido} · ${data.estudiante.email}`"
        icon="📊"
        tone="sky"
      >
        <template #aside>
          <div class="text-right">
            <p class="text-xs text-ink-400 uppercase tracking-wider font-semibold">Último nivel</p>
            <div class="mt-1.5"><RiskBadge :nivel="ultimoNivel" :score="data.estudiante.ultimo_score" /></div>
            <p class="text-xs text-ink-500 mt-1.5">{{ fechaCorta(data.estudiante.ultima_evaluacion) }}</p>
          </div>
        </template>
      </PageHeader>

      <!-- Stats -->
      <section class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Sesiones totales"  :value="data.estudiante.total_sesiones"       icon="📋" tone="brand" />
        <StatCard label="Completadas"       :value="data.estudiante.sesiones_completadas" icon="✅" tone="mint" />
        <StatCard label="Score actual"      :value="data.estudiante.ultimo_score?.toFixed(2) ?? '—'" icon="🎯" tone="peach" />
      </section>

      <!-- Gráfico evolución -->
      <section class="card p-6 fade-in-up">
        <h2 class="section-title">📊 Mi evolución emocional</h2>
        <p class="section-subtitle mb-4">Nivel de riesgo registrado en cada evaluación completada.</p>
        <div v-if="tieneSerie" class="h-72"><canvas ref="chartCanvas"></canvas></div>
        <div v-else class="text-center py-12 bg-cream-50 rounded-2xl border border-dashed border-ink-200">
          <p class="text-4xl mb-2">📊</p>
          <p class="text-sm text-ink-500">Todavía no tienes evaluaciones completadas.</p>
          <button @click="router.push('/chat')" class="btn-mint mt-4">Iniciar evaluación</button>
        </div>
      </section>

      <!-- Sesiones -->
      <section class="card overflow-hidden fade-in-up">
        <div class="px-6 pt-6 pb-4 flex items-baseline justify-between">
          <h2 class="section-title !mb-0">Mis sesiones</h2>
          <p class="text-xs text-ink-400">
            {{ sesionesCompletadas.length }} completada(s) de {{ data.sesiones.length }} total
          </p>
        </div>

        <p v-if="data.sesiones.length === 0" class="text-ink-500 text-center py-10 mx-6 mb-6 bg-cream-50 rounded-2xl border border-dashed border-ink-200">
          Aún no has iniciado ninguna evaluación.
        </p>

        <ul v-else class="divide-y divide-ink-100 border-t border-ink-100">
          <li v-for="s in data.sesiones" :key="s.session_id">
            <button @click="toggleSesion(s.session_id)" class="w-full text-left px-6 py-4 flex items-center justify-between gap-4 hover:bg-brand-50 transition">
              <div class="flex items-center gap-3 flex-wrap min-w-0">
                <RiskBadge :nivel="normalizarNivel(s.nivel_riesgo)" />
                <span class="text-sm text-ink-700">{{ fechaLarga(s.fecha_inicio) }}</span>
                <span class="chip" :class="s.estado === 'completada' ? 'chip-mint' : 'chip-peach'">
                  {{ s.estado }}
                </span>
              </div>
              <span class="text-brand-600 text-xs font-semibold whitespace-nowrap">
                {{ sesionAbierta === s.session_id ? '▲ Ocultar' : '▼ Ver detalle' }}
              </span>
            </button>

            <div v-if="sesionAbierta === s.session_id" class="px-6 pb-6 bg-cream-50 border-t border-ink-100 fade-in-up">
              <div v-if="s.nivel_riesgo" class="mt-4 flex items-center gap-3 flex-wrap">
                <RiskBadge :nivel="normalizarNivel(s.nivel_riesgo)" :score="s.score" />
              </div>

              <div v-if="s.conversacion.length > 0" class="mt-4">
                <p class="text-xs font-bold text-ink-500 uppercase tracking-wider mb-3">Conversación ({{ s.conversacion.length }} preguntas)</p>
                <ol class="space-y-3">
                  <li v-for="c in s.conversacion" :key="c.numero" class="card p-4">
                    <p class="text-xs text-ink-400 mb-1 font-semibold uppercase tracking-wider">Pregunta {{ c.numero + 1 }}</p>
                    <p class="text-sm font-medium text-ink-900 mb-2">{{ c.pregunta }}</p>
                    <p class="text-xs text-ink-400 mb-1 font-semibold uppercase tracking-wider">Tu respuesta</p>
                    <p class="text-sm text-ink-700 italic border-l-4 border-brand-400 pl-3 py-1 bg-brand-50/60 rounded">{{ c.respuesta }}</p>
                  </li>
                </ol>
              </div>
            </div>
          </li>
        </ul>
      </section>

      <div class="banner-brand flex items-center justify-between gap-4 flex-wrap">
        <div class="flex items-center gap-3">
          <span class="text-2xl">🩺</span>
          <div>
            <p class="font-semibold">¿Necesitas apoyo profesional?</p>
            <p class="text-sm text-ink-600">Consulta los recursos disponibles en la UPC y líneas de crisis.</p>
          </div>
        </div>
        <button @click="router.push('/recursos')" class="btn-mint btn-sm">Ver recursos</button>
      </div>
    </div>
  </div>
</template>
