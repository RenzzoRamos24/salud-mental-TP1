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
  <div class="min-h-screen bg-slate-50 py-8 px-4">
    <div class="max-w-3xl mx-auto bg-white rounded-2xl shadow-md p-8 fade-in-up">
      <h1 class="text-2xl font-bold text-slate-900 mb-2">Consentimiento informado</h1>
      <p class="text-slate-500 text-sm mb-6">Versión {{ VERSION }}</p>

      <div class="prose prose-sm max-w-none text-slate-700 space-y-4 leading-relaxed">
        <p>
          Bienvenido/a al sistema de evaluación de bienestar emocional para estudiantes,
          desarrollado como prototipo de tesis con tecnología de Procesamiento de Lenguaje Natural (BERT).
          Antes de comenzar, lee y acepta los siguientes puntos:
        </p>

        <div class="bg-slate-50 border border-slate-200 rounded-lg p-4">
          <h3 class="font-semibold text-slate-800 mb-2">1. Naturaleza informativa</h3>
          <p class="text-sm">
            Este sistema realiza un <strong>cribado preliminar</strong> mediante análisis automático
            de tus respuestas. <strong>No constituye un diagnóstico clínico</strong> ni reemplaza la
            evaluación de un profesional de salud mental.
          </p>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-lg p-4">
          <h3 class="font-semibold text-slate-800 mb-2">2. Uso de tus datos</h3>
          <ul class="list-disc list-inside text-sm space-y-1">
            <li>Tus respuestas se almacenan de forma confidencial en nuestra base de datos.</li>
            <li>Los resultados pueden ser revisados por un psicólogo/a asignado/a.</li>
            <li>No se comparten con terceros fuera del marco académico de la tesis.</li>
            <li>Puedes solicitar la eliminación de tus datos en cualquier momento.</li>
          </ul>
        </div>

        <div class="bg-slate-50 border border-slate-200 rounded-lg p-4">
          <h3 class="font-semibold text-slate-800 mb-2">3. Voluntariedad</h3>
          <p class="text-sm">
            Tu participación es completamente voluntaria. Puedes interrumpir la evaluación
            en cualquier momento sin consecuencias.
          </p>
        </div>

        <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <h3 class="font-semibold text-amber-900 mb-2">⚠️ 4. Si estás en crisis</h3>
          <p class="text-sm text-amber-900">
            Si en este momento sientes pensamientos de hacerte daño, comunícate de inmediato
            con la <strong>Línea 113 (MINSA), opción 5</strong> — atención 24/7 en salud mental,
            o acude a la emergencia más cercana.
          </p>
        </div>
      </div>

      <div class="mt-6 border-t border-slate-200 pt-6">
        <label class="flex items-start gap-3 cursor-pointer">
          <input
            v-model="aceptado"
            type="checkbox"
            class="mt-1 w-5 h-5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
            :disabled="cargando"
          />
          <span class="text-slate-800">
            <strong>He leído y acepto</strong> los términos del consentimiento informado y
            autorizo el tratamiento de mis datos según lo descrito.
          </span>
        </label>

        <p v-if="error" class="text-red-600 text-sm mt-3">{{ error }}</p>

        <button
          @click="aceptar"
          :disabled="cargando || !aceptado"
          class="mt-4 w-full bg-brand-600 hover:bg-brand-700 disabled:bg-slate-300 text-white font-semibold py-3 rounded-lg shadow-md transition"
        >
          {{ cargando ? 'Guardando…' : 'Aceptar y continuar' }}
        </button>
      </div>
    </div>
  </div>
</template>
