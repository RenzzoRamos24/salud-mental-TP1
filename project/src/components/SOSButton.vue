<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const abierto = ref(false)
const mensaje = ref('')
const enviando = ref(false)
const enviado = ref(false)
const respuesta = ref(null)

function origenActual() {
  const path = (route?.path || '').toLowerCase()
  if (path.includes('chat')) return 'chat'
  if (path.includes('resultado')) return 'resultados'
  if (path.includes('historial')) return 'historial'
  return 'menu'
}

async function activar() {
  if (enviando.value) return
  enviando.value = true
  try {
    respuesta.value = await api.activarSOS({ origen: origenActual(), mensaje: mensaje.value || null })
    enviado.value = true
  } catch (_) {
    respuesta.value = { mensaje: 'No pudimos registrar tu SOS, pero llama a la Línea 113 ahora.' }
    enviado.value = true
  } finally { enviando.value = false }
}

function cerrar() {
  abierto.value = false
  setTimeout(() => { mensaje.value = ''; enviado.value = false; respuesta.value = null }, 300)
}
</script>

<template>
  <button
    v-if="!abierto"
    @click="abierto = true"
    class="sos-fab"
    title="SOS — Necesito ayuda"
  >
    <span class="inline-flex items-center justify-center w-7 h-7 rounded-md bg-white/20 text-[10px] font-black">SOS</span>
    <span class="text-base font-bold tracking-wide">SOS</span>
  </button>

  <Teleport to="body">
    <div
      v-if="abierto"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm fade-in-up"
      @click.self="cerrar"
    >
      <div class="card-hero w-full max-w-md p-6 sm:p-7">
        <div class="flex items-start gap-3 mb-5">
          <div class="w-12 h-12 rounded-2xl bg-red-100 text-risk-critico flex items-center justify-center text-2xl shrink-0">
            🆘
          </div>
          <div>
            <h2 class="text-xl font-bold text-ink-900">¿Necesitas ayuda ahora?</h2>
            <p class="text-sm text-ink-500 mt-0.5">No estás solo/a. Estos canales están 24/7.</p>
          </div>
        </div>

        <div v-if="!enviado" class="space-y-3">
          <a href="tel:113" class="block rounded-2xl bg-red-50 border border-red-200 hover:bg-red-100 transition p-4">
            <p class="text-[11px] uppercase tracking-wider text-risk-critico font-semibold">Línea Nacional MINSA</p>
            <p class="text-2xl font-bold text-risk-critico mt-0.5">113 · opción 5</p>
          </a>
          <a href="tel:106" class="block rounded-2xl bg-peach-50 border border-peach-200 hover:bg-peach-100 transition p-4">
            <p class="text-[11px] uppercase tracking-wider text-peach-600 font-semibold">Emergencia inmediata</p>
            <p class="text-xl font-bold text-peach-600 mt-0.5">106</p>
          </a>

          <div>
            <label class="label">¿Quieres contarnos algo? <span class="text-ink-400 font-normal">(opcional)</span></label>
            <textarea
              v-model="mensaje"
              rows="3"
              class="input resize-none"
              placeholder="Lo que escribas llegará al psicólogo del colegio."
            ></textarea>
          </div>

          <div class="flex gap-2 pt-2">
            <button @click="cerrar" :disabled="enviando" class="btn-ghost flex-1">Cerrar</button>
            <button @click="activar" :disabled="enviando" class="btn-danger flex-1">
              {{ enviando ? 'Enviando…' : 'Pedir apoyo ahora' }}
            </button>
          </div>
        </div>

        <div v-else class="text-center py-4">
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-mint-100 text-mint-600 text-2xl mb-3">✓</div>
          <p class="text-lg font-bold text-mint-600">Te escuchamos</p>
          <p class="text-sm text-ink-700 mt-2 leading-relaxed">{{ respuesta?.mensaje }}</p>
          <button @click="cerrar" class="btn-primary mt-5">Entendido</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
