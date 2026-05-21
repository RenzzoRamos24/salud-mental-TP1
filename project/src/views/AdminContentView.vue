<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const items = ref([])
const cargando = ref(true)
const error = ref('')
const modalAbierto = ref(false)
const editando = ref(null)
const guardando = ref(false)
const form = ref(emptyForm())

function emptyForm() {
  return { titulo: '', descripcion: '', tipo: 'articulo', categoria: '',
           url: '', contenido: '', autor: 'Sami', icono: '', activo: true }
}

async function cargar() {
  cargando.value = true
  try { items.value = await api.adminListarTodosContenidos() }
  catch (e) { error.value = e.response?.data?.detail || e.message }
  finally { cargando.value = false }
}

onMounted(cargar)

function abrirNuevo() { editando.value = null; form.value = emptyForm(); modalAbierto.value = true; error.value = '' }
function abrirEditar(c) { editando.value = c; form.value = { ...c }; modalAbierto.value = true; error.value = '' }

async function guardar() {
  if (!form.value.titulo?.trim() || !form.value.descripcion?.trim()) {
    error.value = 'Título y descripción son obligatorios.'; return
  }
  guardando.value = true; error.value = ''
  try {
    if (editando.value) await api.adminActualizarContenido(editando.value.id, form.value)
    else await api.adminCrearContenido(form.value)
    modalAbierto.value = false
    await cargar()
  } catch (e) { error.value = e.response?.data?.detail || e.message }
  finally { guardando.value = false }
}

async function eliminar(c) {
  if (!confirm(`¿Eliminar "${c.titulo}"?`)) return
  try { await api.adminEliminarContenido(c.id); await cargar() }
  catch (e) { alert(e.response?.data?.detail || e.message) }
}

const tipoIcon = { articulo: '📰', video: '🎬', infografia: '🖼️', audio: '🎧' }
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">← Volver al menú</button>

    <PageHeader
      title="Contenidos psicoeducativos"
      subtitle="Gestiona artículos, videos e infografías visibles para los estudiantes."
      icon="📚"
      tone="mint"
    >
      <template #actions>
        <button @click="abrirNuevo" class="btn-primary btn-sm mt-3">+ Nuevo contenido</button>
      </template>
    </PageHeader>

    <p v-if="cargando" class="text-center text-ink-500 py-12">Cargando…</p>
    <div v-else-if="!items.length" class="card p-10 text-center">
      <span class="text-4xl block mb-2">📚</span>
      <p class="text-ink-500">Sin contenidos todavía. Crea el primero.</p>
    </div>

    <div v-else class="card overflow-hidden fade-in-up">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-cream-50 text-ink-500 text-left text-xs uppercase tracking-wider">
            <tr>
              <th class="px-5 py-3">Contenido</th>
              <th class="px-5 py-3">Tipo</th>
              <th class="px-5 py-3">Categoría</th>
              <th class="px-5 py-3">Estado</th>
              <th class="px-5 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-ink-100">
            <tr v-for="c in items" :key="c.id" class="hover:bg-brand-50/40 transition">
              <td class="px-5 py-3">
                <p class="font-semibold text-ink-900">{{ c.titulo }}</p>
                <p class="text-xs text-ink-500 line-clamp-1">{{ c.descripcion }}</p>
              </td>
              <td class="px-5 py-3">
                <span class="chip-brand"><span>{{ tipoIcon[c.tipo] || '📄' }}</span>{{ c.tipo }}</span>
              </td>
              <td class="px-5 py-3 capitalize">
                <span v-if="c.categoria" class="dsm5-tag">{{ c.categoria }}</span>
                <span v-else class="text-ink-400">—</span>
              </td>
              <td class="px-5 py-3">
                <span v-if="c.activo" class="text-mint-600 text-xs font-semibold inline-flex items-center gap-1">
                  <span class="w-2 h-2 bg-mint-500 rounded-full"></span> Activo
                </span>
                <span v-else class="text-ink-400 text-xs font-semibold inline-flex items-center gap-1">
                  <span class="w-2 h-2 bg-ink-300 rounded-full"></span> Oculto
                </span>
              </td>
              <td class="px-5 py-3 text-right whitespace-nowrap">
                <button @click="abrirEditar(c)" class="btn-ghost btn-sm">Editar</button>
                <button @click="eliminar(c)" class="btn-ghost btn-sm !text-risk-critico">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal crear/editar -->
    <Teleport to="body">
      <div v-if="modalAbierto" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm fade-in-up" @click.self="modalAbierto = false">
        <div class="card-hero w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
          <h2 class="text-xl font-bold text-ink-900">{{ editando ? 'Editar contenido' : 'Nuevo contenido' }}</h2>
          <p class="text-sm text-ink-500 mb-5">Los estudiantes lo verán en /recursos.</p>

          <div class="grid sm:grid-cols-2 gap-3">
            <div class="sm:col-span-2">
              <label class="label">Título</label>
              <input v-model="form.titulo" class="input" />
            </div>
            <div class="sm:col-span-2">
              <label class="label">Descripción</label>
              <textarea v-model="form.descripcion" rows="3" class="input resize-none"></textarea>
            </div>
            <div>
              <label class="label">Tipo</label>
              <select v-model="form.tipo" class="input">
                <option value="articulo">📰 Artículo</option>
                <option value="video">🎬 Video</option>
                <option value="infografia">🖼️ Infografía</option>
                <option value="audio">🎧 Audio</option>
              </select>
            </div>
            <div>
              <label class="label">Categoría</label>
              <select v-model="form.categoria" class="input">
                <option value="">—</option>
                <option value="ansiedad">Ansiedad</option>
                <option value="depresion">Depresión</option>
                <option value="estres">Estrés escolar</option>
                <option value="sueño">Sueño</option>
                <option value="autocuidado">Autocuidado</option>
                <option value="crisis">Crisis</option>
              </select>
            </div>
            <div class="sm:col-span-2">
              <label class="label">URL externa <span class="text-ink-400 font-normal">(opcional)</span></label>
              <input v-model="form.url" type="url" placeholder="https://…" class="input" />
            </div>
            <div class="sm:col-span-2">
              <label class="flex items-center gap-2 cursor-pointer p-3 rounded-2xl bg-brand-50 border border-brand-100">
                <input v-model="form.activo" type="checkbox" class="w-4 h-4 accent-brand-500" />
                <span class="text-sm text-ink-800 font-medium">Visible para estudiantes</span>
              </label>
            </div>
          </div>

          <p v-if="error" class="field-error mt-3">{{ error }}</p>

          <div class="flex gap-2 mt-5">
            <button @click="modalAbierto = false" class="btn-ghost flex-1">Cancelar</button>
            <button @click="guardar" :disabled="guardando" class="btn-primary flex-1">
              {{ guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Crear contenido' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
