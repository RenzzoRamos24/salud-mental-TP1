<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { authStore } from '../store/auth'

const router = useRouter()

const VERSION = '1.0'
const aceptado = ref(false)
const cargando = ref(false)
const error = ref('')

async function aceptar() {
  if (!aceptado.value) {
    error.value = 'Debes marcar la casilla para continuar'
    return
  }
  cargando.value = true
  error.value = ''
  try {
    await api.aceptarConsentimiento(VERSION)
    authStore.setUser({
      consentimiento_aceptado: true,
      consentimiento_version: VERSION,
    })
    router.push('/menu')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error registrando consentimiento'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen py-10 px-4">
    <div class="max-w-3xl mx-auto fade-in-up">
      <div class="text-center mb-8">
        <p class="sami-wordmark text-xl">Sami <span class="accent">· Salud Mental Juvenil</span></p>
        <h1 class="hero-serif text-3xl sm:text-4xl mt-4">
          Consentimiento <span class="hero-mint">informado</span>
        </h1>
        <p class="text-ink-500 text-sm mt-3">Versión {{ VERSION }} · Lee antes de comenzar tu evaluación</p>
      </div>

      <div class="bg-white rounded-3xl border border-cream-200 shadow-soft p-6 sm:p-8">
        <div class="space-y-4 text-ink-700 leading-relaxed">
          <p>
            Bienvenido/a al sistema de evaluación de bienestar emocional para estudiantes,
            desarrollado como prototipo de tesis con tecnología de Procesamiento de Lenguaje Natural (BERT).
            Antes de comenzar, lee y acepta los siguientes puntos:
          </p>

          <div class="card-pastel p-5">
            <h3 class="section-title !mb-2">
              <span class="dsm5-tag">1</span>
              Naturaleza informativa
            </h3>
            <p class="text-sm">
              Este sistema realiza un <strong>cribado preliminar</strong> mediante análisis automático
              de tus respuestas. <strong>No constituye un diagnóstico clínico</strong> ni reemplaza la
              evaluación de un profesional de salud mental.
            </p>
          </div>

          <div class="card-pastel p-5">
            <h3 class="section-title !mb-2">
              <span class="dsm5-tag">2</span>
              Uso de tus datos
            </h3>
            <ul class="list-disc list-inside text-sm space-y-1 marker:text-brand-400">
              <li>Tus respuestas se almacenan de forma confidencial en nuestra base de datos.</li>
              <li>Los resultados pueden ser revisados por un psicólogo/a asignado/a.</li>
              <li>No se comparten con terceros fuera del marco académico de la tesis.</li>
              <li>Puedes solicitar la eliminación de tus datos en cualquier momento.</li>
            </ul>
          </div>

          <div class="card-mint p-5">
            <h3 class="section-title !mb-2">
              <span class="dsm5-tag">3</span>
              Voluntariedad
            </h3>
            <p class="text-sm">
              Tu participación es completamente voluntaria. Puedes interrumpir la evaluación
              en cualquier momento sin consecuencias.
            </p>
          </div>

          <div class="banner-danger">
            <span class="text-xl">⚠️</span>
            <div>
              <p class="font-semibold mb-1">Si estás en crisis ahora mismo</p>
              <p class="text-sm">
                Comunícate de inmediato con la <strong>Línea 113 (MINSA), opción 5</strong> —
                atención 24/7 en salud mental, o acude a la emergencia más cercana.
              </p>
            </div>
          </div>
        </div>

        <div class="mt-6 border-t border-ink-100 pt-6">
          <label class="flex items-start gap-3 cursor-pointer p-4 rounded-2xl bg-brand-50 border border-brand-100 hover:border-brand-200 transition">
            <input
              v-model="aceptado"
              type="checkbox"
              class="mt-1 w-5 h-5 rounded border-ink-300 text-brand-500 focus:ring-brand-400"
              :disabled="cargando"
            />
            <span class="text-ink-800 text-sm">
              <strong>He leído y acepto</strong> los términos del consentimiento informado y
              autorizo el tratamiento de mis datos según lo descrito.
            </span>
          </label>

          <p v-if="error" class="field-error mt-3">{{ error }}</p>

          <button
            @click="aceptar"
            :disabled="cargando || !aceptado"
            class="btn-mint w-full mt-4 py-3 text-base"
          >
            {{ cargando ? 'Guardando…' : 'Aceptar y continuar' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
