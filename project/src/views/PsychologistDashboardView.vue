<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'
import StatCard from '../components/StatCard.vue'
import RiskBadge from '../components/RiskBadge.vue'

const router = useRouter()

const estudiantes = ref([])
const stats = ref(null)
const citas = ref([])
const cargando = ref(true)
const error = ref('')
const filtro = ref('')

// Modal cita
const modalCita = reactive({ abierto: false, estudiante: null, fecha: '', hora: '', modalidad: 'presencial', notas: '', guardando: false, error: '' })

async function cargarTodo() {
  try {
    cargando.value = true
    const [s, st, c] = await Promise.all([
      api.listarEstudiantes(),
      api.dashboardStats().catch(() => null),
      api.listarCitas().catch(() => []),
    ])
    estudiantes.value = s
    stats.value = st
    citas.value = c
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    cargando.value = false
  }
}

onMounted(cargarTodo)

const filtrados = computed(() => {
  const q = filtro.value.trim().toLowerCase()
  if (!q) return estudiantes.value
  return estudiantes.value.filter(e =>
    e.nombre.toLowerCase().includes(q) ||
    e.apellido.toLowerCase().includes(q) ||
    e.email.toLowerCase().includes(q)
  )
})

const alertas = computed(() => stats.value?.estudiantes_en_alerta || [])
const distribucion = computed(() => stats.value?.distribucion_riesgo || {})
const citasProximas = computed(() => (citas.value || []).filter(c => c.estado !== 'cancelada').slice(0, 6))

function fechaCorta(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PE', { year: 'numeric', month: 'short', day: 'numeric' })
}

function abrirHistorial(student_id) { router.push(`/psicologo/estudiante/${student_id}`) }

function abrirModalCita(est) {
  modalCita.abierto = true
  modalCita.estudiante = est
  modalCita.fecha = ''; modalCita.hora = ''; modalCita.modalidad = 'presencial'; modalCita.notas = ''; modalCita.error = ''
}
function cerrarModal() { modalCita.abierto = false }

async function guardarCita() {
  modalCita.error = ''
  if (!modalCita.fecha || !modalCita.hora) { modalCita.error = 'Fecha y hora son obligatorias'; return }
  modalCita.guardando = true
  try {
    await api.crearCita({
      estudiante_id: modalCita.estudiante.id,
      fecha: modalCita.fecha,
      hora: modalCita.hora,
      modalidad: modalCita.modalidad,
      notas: modalCita.notas || null,
    })
    cerrarModal()
    await cargarTodo()
  } catch (e) {
    modalCita.error = e.response?.data?.detail || e.message
  } finally { modalCita.guardando = false }
}

async function actualizarEstadoCita(c, estado) {
  try { await api.actualizarCita(c.id, { estado }); await cargarTodo() } catch (e) { alert(e.response?.data?.detail || e.message) }
}
async function cancelarCita(c) {
  if (!confirm('¿Cancelar esta cita?')) return
  try { await api.cancelarCita(c.id); await cargarTodo() } catch (e) { alert(e.response?.data?.detail || e.message) }
}
</script>

<template>
  <div class="page-shell-wide">
    <PageHeader
      title="Panel del psicólogo"
      subtitle="Monitoreo de bienestar emocional, alertas tempranas y agenda de citas."
      icon="🧑‍⚕️"
      tone="brand"
    />

    <div v-if="cargando" class="text-center text-ink-500 py-12">Cargando panel…</div>
    <p v-else-if="error" class="banner-danger">⚠️ {{ error }}</p>

    <template v-else>
      <!-- Métricas (HU-15) -->
      <section v-if="stats" class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
        <StatCard label="Total"     :value="stats.total_estudiantes"   icon="👥" tone="brand" />
        <StatCard label="CRÍTICO"   :value="distribucion['CRÍTICO'] || 0"   icon="🚨" tone="risk-critico" />
        <StatCard label="ALTO"      :value="distribucion['ALTO']    || 0"   icon="🟠" tone="risk-alto" />
        <StatCard label="MEDIO"     :value="distribucion['MEDIO']   || 0"   icon="🟡" tone="risk-medio" />
        <StatCard label="BAJO / Sin eval" :value="(distribucion['BAJO']||0)+(distribucion['SIN_EVAL']||0)" icon="🌿" tone="risk-bajo" />
      </section>

      <!-- Alertas tempranas (HU-16) -->
      <section v-if="alertas.length > 0" class="card border-red-200 border-l-4 p-6 mb-6 fade-in-up">
        <h2 class="section-title text-risk-critico">🚨 Alertas tempranas — atención prioritaria</h2>
        <p class="section-subtitle mb-4">{{ alertas.length }} estudiante(s) en riesgo CRÍTICO o ALTO</p>
        <div class="space-y-2">
          <div v-for="est in alertas" :key="est.id" class="flex items-center justify-between gap-3 p-3 bg-red-50 border border-red-100 rounded-2xl">
            <div class="flex items-center gap-3 min-w-0">
              <div class="avatar-md bg-red-100 text-risk-critico shrink-0">
                {{ (est.nombre[0] + (est.apellido[0]||'')).toUpperCase() }}
              </div>
              <div class="min-w-0">
                <p class="font-semibold text-ink-900 truncate">{{ est.nombre }} {{ est.apellido }}</p>
                <p class="text-xs text-ink-500 truncate">{{ est.email }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <RiskBadge :nivel="est.ultimo_riesgo" />
              <button @click="abrirModalCita(est)" class="btn-primary btn-sm">+ Cita</button>
              <button @click="abrirHistorial(est.id)" class="btn-secondary btn-sm">Historial →</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Próximas citas (HU-19) -->
      <section v-if="citasProximas.length > 0" class="card p-6 mb-6 fade-in-up">
        <h2 class="section-title">📅 Próximas citas</h2>
        <div class="space-y-2 mt-3">
          <div v-for="c in citasProximas" :key="c.id" class="flex items-center justify-between gap-3 p-3 rounded-2xl border border-ink-100">
            <div class="flex items-center gap-3 min-w-0">
              <div class="avatar-md bg-brand-100">📆</div>
              <div class="min-w-0">
                <p class="font-semibold text-ink-900 truncate">{{ c.estudiante_nombre }} {{ c.estudiante_apellido }}</p>
                <p class="text-xs text-ink-500">
                  {{ c.fecha }} · {{ c.hora }} · <span class="capitalize">{{ c.modalidad }}</span>
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span class="chip" :class="{
                'chip-mint': c.estado === 'confirmada',
                'chip-brand': c.estado === 'pendiente',
                'chip-ink': c.estado === 'completada',
                'chip-peach': c.estado === 'cancelada',
              }">{{ c.estado }}</span>
              <button v-if="c.estado === 'pendiente'" @click="actualizarEstadoCita(c, 'confirmada')" class="btn-mint btn-sm">Confirmar</button>
              <button v-if="c.estado === 'confirmada'" @click="actualizarEstadoCita(c, 'completada')" class="btn-secondary btn-sm">Completada</button>
              <button v-if="c.estado !== 'cancelada' && c.estado !== 'completada'" @click="cancelarCita(c)" class="btn-ghost btn-sm">Cancelar</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Estudiantes -->
      <section class="card overflow-hidden fade-in-up">
        <div class="p-5 flex items-center justify-between gap-3 border-b border-ink-100 flex-wrap">
          <div>
            <h2 class="section-title !mb-0">👥 Todos los estudiantes</h2>
            <p class="section-subtitle">{{ estudiantes.length }} en total</p>
          </div>
          <input v-model="filtro" type="text" placeholder="🔍 Buscar por nombre o correo…" class="input w-72" />
        </div>

        <p v-if="filtrados.length === 0" class="text-center text-ink-500 py-12">No se encontraron estudiantes.</p>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-cream-50 text-ink-500 text-left text-xs uppercase tracking-wider">
              <tr>
                <th class="px-5 py-3">Estudiante</th>
                <th class="px-5 py-3">Correo</th>
                <th class="px-5 py-3 text-center">Sesiones</th>
                <th class="px-5 py-3">Último riesgo</th>
                <th class="px-5 py-3">Última eval.</th>
                <th class="px-5 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-ink-100">
              <tr v-for="e in filtrados" :key="e.id" class="hover:bg-brand-50/50 transition">
                <td class="px-5 py-3">
                  <div class="flex items-center gap-3">
                    <div class="avatar-sm">{{ (e.nombre[0] + (e.apellido[0]||'')).toUpperCase() }}</div>
                    <p class="font-semibold text-ink-900">{{ e.nombre }} {{ e.apellido }}</p>
                  </div>
                </td>
                <td class="px-5 py-3 text-ink-600 font-mono text-xs">{{ e.email }}</td>
                <td class="px-5 py-3 text-center">
                  <span class="text-ink-900 font-semibold">{{ e.sesiones_completadas }}</span>
                  <span class="text-ink-400 text-xs"> / {{ e.total_sesiones }}</span>
                </td>
                <td class="px-5 py-3"><RiskBadge :nivel="e.ultimo_riesgo" /></td>
                <td class="px-5 py-3 text-ink-600">{{ fechaCorta(e.ultima_evaluacion) }}</td>
                <td class="px-5 py-3 text-right whitespace-nowrap">
                  <button @click="abrirModalCita(e)" class="btn-secondary btn-sm mr-2">+ Cita</button>
                  <button @click="abrirHistorial(e.id)" class="btn-primary btn-sm">Historial →</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <!-- Modal cita -->
    <Teleport to="body">
      <div v-if="modalCita.abierto" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm fade-in-up" @click.self="cerrarModal">
        <div class="card-hero w-full max-w-md p-6">
          <h2 class="text-xl font-bold text-ink-900 mb-1">Agendar cita</h2>
          <p class="text-sm text-ink-500 mb-5">
            Estudiante: <strong>{{ modalCita.estudiante?.nombre }} {{ modalCita.estudiante?.apellido }}</strong>
          </p>

          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="label">Fecha</label>
                <input v-model="modalCita.fecha" type="date" class="input" />
              </div>
              <div>
                <label class="label">Hora</label>
                <input v-model="modalCita.hora" type="time" class="input" />
              </div>
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
              <textarea v-model="modalCita.notas" rows="3" class="input resize-none" placeholder="Motivo, acuerdos, link de la sesión virtual…"></textarea>
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
