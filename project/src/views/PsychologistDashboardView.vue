<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()

const estudiantes = ref([])
const cargando = ref(true)
const error = ref('')
const filtro = ref('')

onMounted(async () => {
  try {
    estudiantes.value = await api.listarEstudiantes()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    cargando.value = false
  }
})

const filtrados = computed(() => {
  const q = filtro.value.trim().toLowerCase()
  if (!q) return estudiantes.value
  return estudiantes.value.filter(e =>
    e.nombre.toLowerCase().includes(q) ||
    e.apellido.toLowerCase().includes(q) ||
    e.email.toLowerCase().includes(q)
  )
})

const colorRiesgo = {
  'CRÍTICO': 'bg-red-100 text-red-800 border-red-300',
  'ALTO':    'bg-orange-100 text-orange-800 border-orange-300',
  'MEDIO':   'bg-amber-100 text-amber-800 border-amber-300',
  'BAJO':    'bg-emerald-100 text-emerald-800 border-emerald-300',
}

function fechaCorta(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PE', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

function abrirHistorial(student_id) {
  router.push(`/psicologo/estudiante/${student_id}`)
}
</script>

<template>
  <div class="min-h-[calc(100vh-3rem)] bg-slate-50 py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <header class="flex items-end justify-between mb-6 fade-in-up">
        <div>
          <p class="text-sm text-slate-500">Panel del psicólogo</p>
          <h1 class="text-3xl font-bold text-slate-900">Estudiantes</h1>
          <p class="text-slate-600 mt-1">
            Acceso al historial emocional de los estudiantes registrados (HU-20).
          </p>
        </div>
        <input v-model="filtro" type="text" placeholder="Buscar por nombre o correo…"
          class="w-72 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
      </header>

      <div v-if="cargando" class="text-center text-slate-500 py-12">Cargando estudiantes…</div>
      <p v-else-if="error" class="text-red-600">{{ error }}</p>
      <p v-else-if="filtrados.length === 0" class="text-center text-slate-500 py-12">
        No se encontraron estudiantes.
      </p>

      <div v-else class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden fade-in-up">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-600 text-left text-xs uppercase tracking-wide">
            <tr>
              <th class="px-4 py-3">Estudiante</th>
              <th class="px-4 py-3">Correo</th>
              <th class="px-4 py-3 text-center">Sesiones</th>
              <th class="px-4 py-3">Último riesgo</th>
              <th class="px-4 py-3">Última evaluación</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="e in filtrados" :key="e.id" class="hover:bg-slate-50 transition">
              <td class="px-4 py-3">
                <p class="font-semibold text-slate-900">{{ e.nombre }} {{ e.apellido }}</p>
              </td>
              <td class="px-4 py-3 text-slate-600 font-mono text-xs">{{ e.email }}</td>
              <td class="px-4 py-3 text-center">
                <span class="text-slate-900 font-semibold">{{ e.sesiones_completadas }}</span>
                <span class="text-slate-400 text-xs"> / {{ e.total_sesiones }}</span>
              </td>
              <td class="px-4 py-3">
                <span v-if="e.ultimo_riesgo"
                  :class="['inline-block px-2 py-1 rounded-full text-xs font-bold border',
                    colorRiesgo[e.ultimo_riesgo] || 'bg-slate-100 text-slate-700 border-slate-300']">
                  {{ e.ultimo_riesgo }}
                </span>
                <span v-else class="text-slate-400 text-xs">—</span>
              </td>
              <td class="px-4 py-3 text-slate-600">{{ fechaCorta(e.ultima_evaluacion) }}</td>
              <td class="px-4 py-3 text-right">
                <button @click="abrirHistorial(e.id)"
                  class="text-brand-600 hover:text-brand-800 font-semibold text-sm">
                  Ver historial →
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
