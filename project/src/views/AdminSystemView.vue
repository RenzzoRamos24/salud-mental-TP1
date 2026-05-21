<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const tab = ref('encuesta')

const encuesta = ref(null)
const encuestaGuardando = ref(false)
const encuestaMensaje = ref('')

async function cargarEncuesta() { encuesta.value = await api.adminGetEncuesta() }
async function guardarEncuesta() {
  encuestaGuardando.value = true; encuestaMensaje.value = ''
  try {
    await api.adminUpdateEncuesta(encuesta.value.preguntas, encuesta.value.frecuencia_dias)
    encuestaMensaje.value = '✅ Configuración guardada.'
  } catch (e) { encuestaMensaje.value = '⚠️ Error: ' + (e.response?.data?.detail || e.message) }
  finally { encuestaGuardando.value = false }
}

const logs = ref([])
async function cargarLogs() {
  const res = await api.adminGetAuditLogs({ limit: 50, offset: 0 })
  logs.value = res.logs
}

const backups = ref([])
const backupCreando = ref(false)
const backupMensaje = ref('')
async function cargarBackups() { backups.value = await api.adminListarBackups() }
async function crearBackup() {
  backupCreando.value = true; backupMensaje.value = ''
  try {
    const res = await api.adminCrearBackup()
    backupMensaje.value = `✅ Respaldo creado: ${res.archivo}`
    await cargarBackups()
  } catch (e) { backupMensaje.value = '⚠️ Error: ' + (e.response?.data?.detail || e.message) }
  finally { backupCreando.value = false }
}

const modeloInfo = ref(null)
const umbrales = ref(null)
const bertMensaje = ref('')

const CONDICION_LABELS = {
  depresion: 'Depresión', ansiedad: 'Ansiedad', tdah: 'TDAH',
  estres_academico: 'Estrés escolar', soledad: 'Soledad',
  riesgo_suicida: 'Riesgo suicida', estabilidad: 'Estabilidad emocional',
}
const CONDICION_ICON = {
  depresion: '🌧️', ansiedad: '🌪️', tdah: '⚡',
  estres_academico: '📚', soledad: '🫂',
  riesgo_suicida: '🚨', estabilidad: '🌿',
}

async function cargarBert() {
  const [info, u] = await Promise.all([api.adminGetModeloInfo(), api.adminGetUmbrales()])
  modeloInfo.value = info; umbrales.value = u
}
async function guardarUmbrales() {
  bertMensaje.value = ''
  try {
    await api.adminUpdateUmbrales(umbrales.value)
    bertMensaje.value = '✅ Umbrales actualizados.'
  } catch (e) { bertMensaje.value = '⚠️ Error: ' + (e.response?.data?.detail || e.message) }
}
async function recargarModelo() {
  bertMensaje.value = ''
  try {
    const res = await api.adminRecargarModelo()
    bertMensaje.value = `✅ ${res.mensaje}`
    modeloInfo.value = await api.adminGetModeloInfo()
  } catch (e) { bertMensaje.value = '⚠️ Error: ' + (e.response?.data?.detail || e.message) }
}

function statusChip(code) {
  if (code >= 200 && code < 300) return 'chip-mint'
  if (code >= 300 && code < 400) return 'chip-brand'
  if (code >= 400 && code < 500) return 'chip-peach'
  return 'chip bg-red-100 text-risk-critico'
}

onMounted(async () => {
  await Promise.all([cargarEncuesta(), cargarLogs(), cargarBackups(), cargarBert()])
})

const TABS = [
  ['encuesta',  'Encuesta',     '📋'],
  ['auditoria', 'Auditoría',    '🛡️'],
  ['backups',   'Respaldos',    '💾'],
  ['bert',      'Modelo BERT',  '🧠'],
]
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">← Volver al menú</button>

    <PageHeader
      title="Configuración del sistema"
      subtitle="Encuestas, auditoría, respaldos y calibración del modelo BERT."
      icon="⚙️"
      tone="sky2"
    />

    <!-- Tabs -->
    <nav class="flex gap-1 bg-white rounded-2xl border border-ink-100 p-1 shadow-soft mb-6 overflow-x-auto fade-in-up">
      <button
        v-for="[key, label, icon] in TABS"
        :key="key"
        @click="tab = key"
        :class="[
          'px-4 py-2 rounded-xl text-sm font-semibold transition whitespace-nowrap inline-flex items-center gap-2',
          tab === key ? 'bg-brand-500 text-white shadow-soft' : 'text-ink-600 hover:bg-brand-50',
        ]"
      >
        <span>{{ icon }}</span>{{ label }}
      </button>
    </nav>

    <!-- Encuesta -->
    <section v-if="tab === 'encuesta'" class="card p-6 fade-in-up">
      <h2 class="section-title">📋 Configuración de la encuesta clínica</h2>
      <div v-if="encuesta" class="mt-4 space-y-5">
        <div>
          <label class="label">Frecuencia recomendada (días)</label>
          <input v-model.number="encuesta.frecuencia_dias" type="number" min="1" max="90" class="input w-40" />
          <p class="field-hint">Periodo sugerido para que el estudiante repita la evaluación.</p>
        </div>

        <div>
          <h3 class="text-sm font-semibold text-ink-700 mb-2 flex items-center gap-2">
            <span class="dsm5-tag">PHQ-9 · GAD-7</span>
            Preguntas activas ({{ encuesta.preguntas?.length || 0 }})
          </h3>
          <ol class="space-y-2 text-sm text-ink-700 mt-2">
            <li v-for="(p, i) in encuesta.preguntas" :key="i" class="card-pastel p-3 flex gap-2">
              <span class="font-bold text-brand-700 shrink-0">{{ i + 1 }}.</span>
              <span>{{ typeof p === 'string' ? p : p.pregunta }}</span>
            </li>
          </ol>
          <p class="field-hint mt-2">Las preguntas son fijas (alineadas a PHQ-9/GAD-7). Solo se actualiza la frecuencia.</p>
        </div>

        <button @click="guardarEncuesta" :disabled="encuestaGuardando" class="btn-primary">
          {{ encuestaGuardando ? 'Guardando…' : 'Guardar cambios' }}
        </button>
        <p v-if="encuestaMensaje" class="text-sm text-ink-600 mt-3">{{ encuestaMensaje }}</p>
      </div>
    </section>

    <!-- Auditoría -->
    <section v-if="tab === 'auditoria'" class="card p-6 fade-in-up">
      <h2 class="section-title">🛡️ Auditoría de accesos</h2>
      <p class="section-subtitle mb-4">Últimas 50 llamadas a la API.</p>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-cream-50 text-xs uppercase tracking-wider text-ink-500 text-left">
            <tr>
              <th class="px-4 py-3">Hora</th>
              <th class="px-4 py-3">Usuario</th>
              <th class="px-4 py-3">Método</th>
              <th class="px-4 py-3">Endpoint</th>
              <th class="px-4 py-3">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-ink-100">
            <tr v-for="l in logs" :key="l.id" class="hover:bg-brand-50/40 transition">
              <td class="px-4 py-3 text-xs font-mono text-ink-500 whitespace-nowrap">{{ new Date(l.timestamp).toLocaleString('es-PE') }}</td>
              <td class="px-4 py-3 text-sm">{{ l.email || '—' }} <span v-if="l.role" class="text-xs text-ink-400">· {{ l.role }}</span></td>
              <td class="px-4 py-3 text-xs font-mono font-semibold text-brand-700">{{ l.method }}</td>
              <td class="px-4 py-3 text-xs font-mono truncate max-w-[280px] text-ink-700">{{ l.endpoint }}</td>
              <td class="px-4 py-3"><span :class="statusChip(l.status_code)">{{ l.status_code }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Backups -->
    <section v-if="tab === 'backups'" class="card p-6 fade-in-up">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 class="section-title">💾 Respaldos de la base de datos</h2>
          <p class="section-subtitle">Copias de seguridad locales de mental_health.db</p>
        </div>
        <button @click="crearBackup" :disabled="backupCreando" class="btn-primary">
          {{ backupCreando ? 'Creando…' : '+ Crear respaldo ahora' }}
        </button>
      </div>

      <p v-if="backupMensaje" class="text-sm text-ink-600 mt-3">{{ backupMensaje }}</p>

      <ul class="mt-5 divide-y divide-ink-100 border-t border-ink-100">
        <li v-for="b in backups" :key="b.archivo" class="py-3 flex justify-between items-center text-sm">
          <div class="flex items-center gap-3 min-w-0">
            <span class="text-2xl">💾</span>
            <span class="font-mono text-ink-700 truncate">{{ b.archivo }}</span>
          </div>
          <span class="chip-ink">{{ (b.tamanio_bytes / 1024).toFixed(1) }} KB</span>
        </li>
        <li v-if="backups.length === 0" class="py-6 text-center text-ink-400 text-sm">No hay respaldos aún.</li>
      </ul>
    </section>

    <!-- Modelo BERT -->
    <section v-if="tab === 'bert'" class="space-y-6 fade-in-up">
      <div class="card p-6">
        <h2 class="section-title">🧠 Modelo BERT</h2>
        <div v-if="modeloInfo" class="mt-3 space-y-2 text-sm">
          <div class="flex items-start gap-3 flex-wrap">
            <span class="dsm5-tag">{{ modeloInfo.cargado ? 'Cargado' : 'No cargado' }}</span>
            <p class="text-ink-700">
              <strong>Modelo:</strong> <span class="font-mono text-xs">{{ modeloInfo.modelo }}</span>
            </p>
          </div>
          <button @click="recargarModelo" class="btn-secondary mt-3">↻ Recargar modelo</button>
        </div>
      </div>

      <div class="card p-6">
        <h2 class="section-title">🎛️ Umbrales de detección</h2>
        <p class="section-subtitle mb-4">Probabilidad mínima para considerar una condición como detectada.</p>

        <div v-if="umbrales" class="space-y-3">
          <div
            v-for="(cfg, clave) in umbrales"
            :key="clave"
            class="card-pastel p-4 flex items-center gap-4 flex-wrap"
          >
            <span class="text-2xl">{{ CONDICION_ICON[clave] || '•' }}</span>
            <label class="flex-1 text-sm font-semibold text-ink-900">{{ CONDICION_LABELS[clave] || clave }}</label>
            <input
              v-model.number="cfg.umbral"
              type="range" min="0" max="1" step="0.05"
              class="flex-1 max-w-xs accent-brand-500"
            />
            <input v-model.number="cfg.umbral" type="number" step="0.05" min="0" max="1" class="input w-24" />
            <span class="dsm5-tag w-16 justify-center">{{ Math.round(cfg.umbral * 100) }}%</span>
          </div>
        </div>

        <button @click="guardarUmbrales" class="btn-primary mt-4">Guardar umbrales</button>
        <p v-if="bertMensaje" class="text-sm text-ink-600 mt-3">{{ bertMensaje }}</p>
      </div>
    </section>
  </div>
</template>
