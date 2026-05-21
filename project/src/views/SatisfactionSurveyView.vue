<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()
const cargando = ref(true)
const yaRespondio = ref(false)
const enviando = ref(false)
const enviado = ref(false)
const error = ref('')

const respuestas = ref({
  facilidad_uso: 0, utilidad: 0, confianza: 0, recomendaria: 0, nivel_animo_post: 0,
  comentario: '',
})

const preguntas = [
  { clave: 'facilidad_uso',    titulo: '¿Qué tan fácil te fue conversar con Sami?',     icon: '💬' },
  { clave: 'utilidad',         titulo: '¿Qué tan útil te resultó la evaluación?',       icon: '🎯' },
  { clave: 'confianza',        titulo: '¿Cuánta confianza te dio el sistema?',           icon: '🔒' },
  { clave: 'recomendaria',     titulo: '¿Recomendarías Sami a un compañero?',            icon: '👍' },
  { clave: 'nivel_animo_post', titulo: '¿Cómo te sientes después de hablar con Sami?',   icon: '🌈' },
]

onMounted(async () => {
  try { const r = await api.miSatisfaccion(); yaRespondio.value = r.ya_respondio }
  catch (_) {}
  cargando.value = false
})

function setVal(clave, v) { respuestas.value[clave] = v }

async function enviar() {
  error.value = ''
  for (const p of preguntas.slice(0, 4)) {
    if (!respuestas.value[p.clave]) { error.value = 'Por favor responde todas las preguntas.'; return }
  }
  enviando.value = true
  try {
    const payload = { ...respuestas.value }
    if (!payload.nivel_animo_post) payload.nivel_animo_post = null
    if (!payload.comentario?.trim()) payload.comentario = null
    await api.enviarSatisfaccion(payload)
    enviado.value = true
  } catch (e) { error.value = e.response?.data?.detail || e.message }
  finally { enviando.value = false }
}
</script>

<template>
  <div class="page-shell">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">← Volver al menú</button>

    <PageHeader
      title="¿Qué tal te fue con"
      accent="Sami?"
      subtitle="Tu opinión es anónima para los demás estudiantes y nos ayuda a mejorar."
      icon="⭐"
      tone="peach"
    />

    <p v-if="cargando" class="text-center text-ink-500 py-12">Cargando…</p>

    <div v-else-if="enviado" class="card-hero p-8 text-center fade-in-up">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-mint-100 text-mint-600 text-3xl mb-3">✓</div>
      <p class="text-2xl font-bold text-ink-900">¡Gracias por tu feedback!</p>
      <p class="text-sm text-ink-500 mt-2 mb-5">Cada respuesta ayuda a que Sami mejore.</p>
      <button @click="router.push('/menu')" class="btn-mint">Volver al menú</button>
    </div>

    <div v-else-if="yaRespondio" class="card-hero p-8 text-center fade-in-up">
      <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-100 text-brand-700 text-3xl mb-3">✨</div>
      <p class="text-xl font-bold text-ink-900">Ya nos compartiste tu opinión</p>
      <p class="text-sm text-ink-500 mt-2 mb-5">Más adelante te volveremos a preguntar.</p>
      <button @click="router.push('/menu')" class="btn-mint">Volver al menú</button>
    </div>

    <div v-else class="space-y-4 fade-in-up">
      <div v-for="p in preguntas" :key="p.clave" class="card p-5">
        <p class="flex items-center gap-2 text-sm font-semibold text-ink-900 mb-3">
          <span class="text-xl">{{ p.icon }}</span>
          {{ p.titulo }}
        </p>
        <div class="flex gap-2">
          <button
            v-for="n in 5"
            :key="n"
            @click="setVal(p.clave, n)"
            :class="[
              'w-12 h-12 rounded-xl border-2 text-base font-bold transition',
              respuestas[p.clave] >= n
                ? 'bg-mint-400 border-mint-400 text-white shadow-pastel scale-105'
                : 'bg-white border-ink-200 text-ink-400 hover:border-mint-300 hover:text-mint-500',
            ]"
          >{{ n }}</button>
        </div>
        <p class="text-xs text-ink-500 mt-2">
          1 = muy malo · 5 = excelente
          <span v-if="respuestas[p.clave]" class="ml-2 font-semibold text-mint-500">→ {{ respuestas[p.clave] }}/5</span>
        </p>
      </div>

      <div class="card p-5">
        <p class="text-sm font-semibold text-ink-900 mb-2 flex items-center gap-2">
          <span class="text-xl">📝</span> Comentario <span class="text-ink-400 font-normal">(opcional)</span>
        </p>
        <textarea
          v-model="respuestas.comentario"
          rows="4"
          class="input resize-none"
          placeholder="¿Algo que mejorarías? Cuéntanos…"
        ></textarea>
      </div>

      <p v-if="error" class="field-error">{{ error }}</p>

      <button @click="enviar" :disabled="enviando" class="btn-mint w-full py-3 text-base">
        {{ enviando ? 'Enviando…' : 'Enviar feedback' }}
      </button>
    </div>
  </div>
</template>
