<script setup>
import { ref, onMounted, nextTick, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'
import StatCard from '../components/StatCard.vue'
import RiskBadge from '../components/RiskBadge.vue'

Chart.register(...registerables)

const route = useRoute()
const router = useRouter()

const cargando = ref(true)
const error = ref('')
const data = ref(null)
const sesionAbierta = ref(null)
const chartCanvas = ref(null)
let chartInstance = null

const nivelANumero = { 'BAJO': 1, 'MEDIO': 2, 'ALTO': 3, 'CRÍTICO': 4 }
const numeroANivel = { 1: 'BAJO', 2: 'MEDIO', 3: 'ALTO', 4: 'CRÍTICO' }

function fechaCorta(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PE', { year: 'numeric', month: 'short', day: 'numeric' })
}
function fechaLarga(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PE', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
function toggleSesion(id) { sesionAbierta.value = sesionAbierta.value === id ? null : id }

const tieneSerie = computed(() => data.value?.serie_temporal?.length > 0)

function dibujarGrafico() {
  if (!chartCanvas.value || !tieneSerie.value) return
  if (chartInstance) { chartInstance.destroy(); chartInstance = null }
  const serie = data.value.serie_temporal
  const labels = serie.map(p => fechaCorta(p.fecha))
  const valores = serie.map(p => nivelANumero[p.nivel] || 0)
  const colores = serie.map(p => {
    if (p.nivel === 'CRÍTICO') return '#E0413A'
    if (p.nivel === 'ALTO') return '#F2754F'
    if (p.nivel === 'MEDIO') return '#F2A93B'
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
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => {
          const p = serie[ctx.dataIndex]
          return `${p.nivel} (score: ${p.score?.toFixed(2) ?? '—'})`
        } } },
      },
      scales: {
        y: { min: 0, max: 4, ticks: { stepSize: 1, callback: (v) => numeroANivel[v] || '' }, grid: { color: '#EDEAF0' } },
        x: { grid: { display: false } },
      },
    },
  })
}

onMounted(async () => {
  try {
    data.value = await api.historialEstudiante(route.params.id)
    await nextTick()
    dibujarGrafico()
  } catch (e) { error.value = e.response?.data?.detail || e.message }
  finally { cargando.value = false }
})

// Modal cita
const modalCita = reactive({ abierto: false, fecha: '', hora: '', modalidad: 'presencial', notas: '', guardando: false, error: '', exito: false })
function abrirModalCita() { Object.assign(modalCita, { abierto: true, fecha: '', hora: '', modalidad: 'presencial', notas: '', error: '', exito: false }) }
function cerrarModal() { modalCita.abierto = false }
async function guardarCita() {
  modalCita.error = ''
  if (!modalCita.fecha || !modalCita.hora) { modalCita.error = 'Fecha y hora son obligatorias'; return }
  modalCita.guardando = true
  try {
    await api.crearCita({
      estudiante_id: parseInt(route.params.id),
      fecha: modalCita.fecha, hora: modalCita.hora,
      modalidad: modalCita.modalidad,
      notas: modalCita.notas || null,
    })
    modalCita.exito = true
    setTimeout(cerrarModal, 1500)
  } catch (e) { modalCita.error = e.response?.data?.detail || e.message }
  finally { modalCita.guardando = false }
}
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/psicologo')" class="btn-ghost btn-sm mb-3">← Volver a estudiantes</button>

    <div v-if="cargando" class="text-center text-ink-500 py-16">Cargando historial…</div>
    <p v-else-if="error" class="banner-danger">⚠️ {{ error }}</p>

    <div v-else-if="data" class="space-y-6">
      <PageHeader
        :title="`${data.estudiante.nombre} ${data.estudiante.apellido}`"
        :subtitle="`${data.estudiante.email} · Historial emocional clínico`"
        icon="📋"
        tone="brand"
      >
        <template #actions>
          <button @click="abrirModalCita" class="btn-primary btn-sm mt-3">+ Agendar cita</button>
        </template>
        <template #aside>
          <div class="text-right">
            <p class="text-xs uppercase tracking-wider text-ink-400 font-semibold">Último riesgo</p>
            <div class="mt-1.5"><RiskBadge :nivel="data.estudiante.ultimo_riesgo" :score="data.estudiante.ultimo_score" /></div>
            <p class="text-xs text-ink-500 mt-1.5">{{ fechaCorta(data.estudiante.ultima_evaluacion) }}</p>
          </div>
        </template>
      </PageHeader>

      <section class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Sesiones totales" :value="data.estudiante.total_sesiones"       icon="📋" tone="brand" />
        <StatCard label="Completadas"      :value="data.estudiante.sesiones_completadas" icon="✅" tone="mint" />
        <StatCard label="Score actual"     :value="data.estudiante.ultimo_score?.toFixed(2) ?? '—'" icon="🎯" tone="peach" />
      </section>

      <section v-if="tieneSerie" class="card p-6 fade-in-up">
        <h2 class="section-title">📊 Evolución del nivel de riesgo</h2>
        <div class="h-64 mt-3"><canvas ref="chartCanvas"></canvas></div>
      </section>

      <section class="card overflow-hidden fade-in-up">
        <h2 class="section-title p-6 pb-4 !mb-0">📝 Sesiones</h2>

        <p v-if="data.sesiones.length === 0" class="text-ink-500 text-center py-10">
          Este estudiante aún no ha realizado evaluaciones.
        </p>

        <ul v-else class="divide-y divide-ink-100 border-t border-ink-100">
          <li v-for="s in data.sesiones" :key="s.session_id">
            <button @click="toggleSesion(s.session_id)" class="w-full text-left px-6 py-4 flex items-center justify-between gap-4 hover:bg-brand-50/50 transition">
              <div class="flex items-center gap-3 flex-wrap">
                <RiskBadge :nivel="s.nivel_riesgo" />
                <span class="text-sm text-ink-700">{{ fechaLarga(s.fecha_inicio) }}</span>
                <span class="chip" :class="s.estado === 'completada' ? 'chip-mint' : 'chip-peach'">{{ s.estado }}</span>
              </div>
              <span class="text-brand-600 text-xs font-semibold whitespace-nowrap">
                {{ sesionAbierta === s.session_id ? '▲ Ocultar' : '▼ Ver detalle' }}
              </span>
            </button>

            <div v-if="sesionAbierta === s.session_id" class="px-6 pb-6 bg-cream-50 border-t border-ink-100 fade-in-up">
              <div v-if="s.explicacion" class="card-pastel p-4 mt-4">
                <p class="text-xs font-bold text-brand-700 uppercase tracking-wider mb-1">Explicación clínica</p>
                <p class="text-sm text-ink-800 whitespace-pre-wrap">{{ s.explicacion }}</p>
              </div>

              <div class="mt-4">
                <p class="text-xs font-bold text-ink-500 uppercase tracking-wider mb-3">Conversación ({{ s.conversacion.length }} preguntas)</p>
                <ol class="space-y-3">
                  <li v-for="c in s.conversacion" :key="c.numero" class="card p-4">
                    <p class="text-xs text-ink-400 mb-1 font-semibold uppercase tracking-wider">Pregunta {{ c.numero }}</p>
                    <p class="text-sm font-medium text-ink-900 mb-2">{{ c.pregunta }}</p>
                    <p class="text-sm text-ink-700 italic border-l-4 border-brand-400 pl-3 py-1 bg-brand-50/60 rounded">{{ c.respuesta }}</p>
                  </li>
                </ol>
              </div>
            </div>
          </li>
        </ul>
      </section>
    </div>

    <!-- Modal cita -->
    <Teleport to="body">
      <div v-if="modalCita.abierto" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm fade-in-up" @click.self="cerrarModal">
        <div class="card-hero w-full max-w-md p-6">
          <h2 class="text-xl font-bold text-ink-900 mb-1">Agendar cita</h2>
          <p class="text-sm text-ink-500 mb-5">
            Con <strong>{{ data?.estudiante.nombre }} {{ data?.estudiante.apellido }}</strong>
          </p>

          <div v-if="modalCita.exito" class="text-center py-4">
            <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-mint-100 text-mint-600 text-2xl mb-3">✓</div>
            <p class="font-bold text-mint-600">Cita agendada</p>
          </div>

          <div v-else class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div><label class="label">Fecha</label><input v-model="modalCita.fecha" type="date" class="input" /></div>
              <div><label class="label">Hora</label><input v-model="modalCita.hora" type="time" class="input" /></div>
            </div>
            <div>
              <label class="label">Modalidad</label>
              <select v-model="modalCita.modalidad" class="input">
                <option value="presencial">Presencial</option>
                <option value="virtual">Virtual</option>
              </select>
            </div>
            <div>
              <label class="label">Notas <span class="text-ink-400 font-normal">(opcional)</span></label>
              <textarea v-model="modalCita.notas" rows="3" class="input resize-none"></textarea>
            </div>

            <p v-if="modalCita.error" class="field-error">{{ modalCita.error }}</p>

            <div class="flex gap-2 pt-2">
              <button @click="cerrarModal" :disabled="modalCita.guardando" class="btn-ghost flex-1">Cancelar</button>
              <button @click="guardarCita" :disabled="modalCita.guardando" class="btn-primary flex-1">
                {{ modalCita.guardando ? 'Guardando…' : 'Agendar' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
