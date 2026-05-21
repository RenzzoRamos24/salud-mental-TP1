<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const mensajes = ref({})
const cargando = ref(true)
const guardando = ref(false)
const guardado = ref(false)
const error = ref('')

const CAMPOS = [
  { clave: 'bot_nombre',        label: 'Nombre del bot',                       rows: 1, hint: 'Ej: Sami' },
  { clave: 'tagline',           label: 'Tagline del header',                   rows: 1, hint: 'Texto secundario visible en el chat.' },
  { clave: 'saludo_inicial',    label: 'Saludo inicial (apertura)',            rows: 5, hint: 'Usa {nombre} para insertar el nombre del estudiante.' },
  { clave: 'cierre_resultados', label: 'Mensaje antes de mostrar resultados',  rows: 2, hint: '' },
  { clave: 'footer_chat',       label: 'Texto del pie del chat',               rows: 1, hint: '' },
]

async function cargar() {
  try { mensajes.value = await api.getChatbotMessages() }
  catch (e) { error.value = e.response?.data?.detail || e.message }
  finally { cargando.value = false }
}

onMounted(cargar)

async function guardar() {
  guardando.value = true; guardado.value = false; error.value = ''
  try {
    mensajes.value = await api.updateChatbotMessages(mensajes.value)
    guardado.value = true
    setTimeout(() => (guardado.value = false), 3000)
  } catch (e) { error.value = e.response?.data?.detail || e.message }
  finally { guardando.value = false }
}
</script>

<template>
  <div class="page-shell">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">← Volver al menú</button>

    <PageHeader
      title="Mensajes del chatbot"
      subtitle="Personaliza el lenguaje conversacional de Sami."
      icon="💬"
      tone="peach"
    />

    <p v-if="cargando" class="text-center text-ink-500 py-8">Cargando…</p>

    <div v-else class="space-y-4 fade-in-up">
      <div v-for="c in CAMPOS" :key="c.clave" class="card p-5">
        <label class="label">{{ c.label }}</label>
        <p v-if="c.hint" class="field-hint mb-2 !mt-0">{{ c.hint }}</p>
        <input v-if="c.rows === 1" v-model="mensajes[c.clave]" class="input" />
        <textarea v-else v-model="mensajes[c.clave]" :rows="c.rows" class="input resize-none"></textarea>
      </div>

      <p v-if="error" class="field-error">{{ error }}</p>
      <p v-if="guardado" class="banner-success">
        <span>✅</span><span>Cambios guardados correctamente.</span>
      </p>

      <button @click="guardar" :disabled="guardando" class="btn-primary w-full py-3 text-base">
        {{ guardando ? 'Guardando…' : 'Guardar mensajes' }}
      </button>
    </div>
  </div>
</template>
