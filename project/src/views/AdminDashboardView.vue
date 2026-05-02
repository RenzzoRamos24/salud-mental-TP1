<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'

const usuarios = ref([])
const stats = ref(null)
const cargando = ref(true)
const error = ref('')
const filtroRol = ref('todos')
const filtroTexto = ref('')

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    const [u, s] = await Promise.all([
      api.listarUsuarios(),
      api.statsUsuarios(),
    ])
    usuarios.value = u
    stats.value = s
  } catch (e) {
    error.value = e.response?.data?.detail || e.message
  } finally {
    cargando.value = false
  }
}

onMounted(cargar)

const filtrados = computed(() => {
  const q = filtroTexto.value.trim().toLowerCase()
  return usuarios.value.filter(u => {
    if (filtroRol.value !== 'todos' && u.role !== filtroRol.value) return false
    if (q && !`${u.nombre} ${u.apellido} ${u.email}`.toLowerCase().includes(q)) return false
    return true
  })
})

const colorRol = {
  estudiante: 'bg-blue-100 text-blue-800 border-blue-300',
  psicologo:  'bg-emerald-100 text-emerald-800 border-emerald-300',
  admin:      'bg-purple-100 text-purple-800 border-purple-300',
}

function fechaCorta(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PE', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}
</script>

<template>
  <div class="min-h-[calc(100vh-3rem)] bg-slate-50 py-8 px-4">
    <div class="max-w-6xl mx-auto">
      <header class="mb-6 fade-in-up">
        <p class="text-sm text-slate-500">Panel de administración</p>
        <h1 class="text-3xl font-bold text-slate-900">Usuarios del sistema</h1>
        <p class="text-slate-600 mt-1">
          Visibilidad de todas las cuentas registradas (estudiantes, psicólogos y admins).
        </p>
      </header>

      <!-- Stats -->
      <div v-if="stats" class="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6 fade-in-up">
        <div class="bg-white border border-slate-200 rounded-xl p-4">
          <p class="text-xs text-slate-500 uppercase">Total</p>
          <p class="text-2xl font-bold text-slate-900">{{ stats.total }}</p>
        </div>
        <div class="bg-blue-50 border border-blue-200 rounded-xl p-4">
          <p class="text-xs text-blue-700 uppercase">Estudiantes</p>
          <p class="text-2xl font-bold text-blue-900">{{ stats.estudiantes }}</p>
        </div>
        <div class="bg-emerald-50 border border-emerald-200 rounded-xl p-4">
          <p class="text-xs text-emerald-700 uppercase">Psicólogos</p>
          <p class="text-2xl font-bold text-emerald-900">{{ stats.psicologos }}</p>
        </div>
        <div class="bg-purple-50 border border-purple-200 rounded-xl p-4">
          <p class="text-xs text-purple-700 uppercase">Admins</p>
          <p class="text-2xl font-bold text-purple-900">{{ stats.admins }}</p>
        </div>
        <div class="bg-slate-100 border border-slate-200 rounded-xl p-4">
          <p class="text-xs text-slate-600 uppercase">Inactivos</p>
          <p class="text-2xl font-bold text-slate-700">{{ stats.inactivos }}</p>
        </div>
      </div>

      <!-- Filtros -->
      <div class="flex flex-wrap items-center gap-3 mb-4 fade-in-up">
        <div class="flex gap-1 bg-white rounded-lg p-1 border border-slate-200">
          <button v-for="op in ['todos','estudiante','psicologo','admin']" :key="op"
            @click="filtroRol = op"
            :class="['px-3 py-1 text-sm rounded-md transition capitalize',
              filtroRol === op
                ? 'bg-brand-600 text-white'
                : 'text-slate-600 hover:bg-slate-100']">
            {{ op === 'todos' ? 'Todos' : op + 's' }}
          </button>
        </div>
        <input v-model="filtroTexto" type="text" placeholder="Buscar nombre o correo…"
          class="flex-1 min-w-[200px] px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
      </div>

      <p v-if="cargando" class="text-center text-slate-500 py-12">Cargando usuarios…</p>
      <p v-else-if="error" class="text-red-600">{{ error }}</p>
      <p v-else-if="filtrados.length === 0" class="text-center text-slate-500 py-12">
        No hay usuarios que coincidan con los filtros.
      </p>

      <div v-else class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden fade-in-up">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-slate-600 text-left text-xs uppercase tracking-wide">
            <tr>
              <th class="px-4 py-3">Usuario</th>
              <th class="px-4 py-3">Correo</th>
              <th class="px-4 py-3">Rol</th>
              <th class="px-4 py-3">Estado</th>
              <th class="px-4 py-3">Registrado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="u in filtrados" :key="u.id" class="hover:bg-slate-50 transition">
              <td class="px-4 py-3">
                <p class="font-semibold text-slate-900">{{ u.nombre }} {{ u.apellido }}</p>
              </td>
              <td class="px-4 py-3 text-slate-600 font-mono text-xs">{{ u.email }}</td>
              <td class="px-4 py-3">
                <span :class="['inline-block px-2 py-1 rounded-full text-xs font-bold border capitalize',
                  colorRol[u.role] || 'bg-slate-100 text-slate-700 border-slate-300']">
                  {{ u.role }}
                </span>
              </td>
              <td class="px-4 py-3">
                <span v-if="u.activo" class="text-emerald-700 text-xs font-semibold">● Activo</span>
                <span v-else class="text-slate-400 text-xs font-semibold">● Inactivo</span>
              </td>
              <td class="px-4 py-3 text-slate-600">{{ fechaCorta(u.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
