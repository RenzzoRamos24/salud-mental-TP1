<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const email = ref('')
const mensaje = ref('')
const error = ref('')
const cargando = ref(false)

async function enviar() {
  error.value = ''
  mensaje.value = ''
  if (!email.value.trim()) {
    error.value = 'Ingresa tu correo'
    return
  }
  cargando.value = true
  try {
    const data = await api.forgotPassword(email.value.trim())
    mensaje.value = data.mensaje
    setTimeout(() => {
      router.push({ name: 'reset', query: { email: email.value.trim() } })
    }, 1500)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error enviando solicitud'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-brand-50 via-white to-indigo-50">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 fade-in-up">
      <h1 class="text-2xl font-bold text-slate-900 mb-2">Recuperar contraseña</h1>
      <p class="text-slate-600 text-sm mb-6">
        Te enviaremos un código de 6 dígitos.
        <span class="text-amber-600">(En modo dev se imprime en la consola del backend.)</span>
      </p>

      <form @submit.prevent="enviar" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Correo institucional</label>
          <input v-model="email" type="email" :disabled="cargando"
            class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
        </div>

        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>
        <p v-if="mensaje" class="text-emerald-700 text-sm bg-emerald-50 border border-emerald-200 p-3 rounded-lg">
          {{ mensaje }}
        </p>

        <button
          type="submit"
          :disabled="cargando"
          class="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-slate-400 text-white font-semibold py-3 rounded-lg shadow-md transition"
        >
          {{ cargando ? 'Enviando…' : 'Enviar código' }}
        </button>
      </form>

      <p class="text-center text-sm text-slate-600 mt-4">
        <router-link to="/login" class="text-brand-600 hover:underline">Volver al login</router-link>
      </p>
    </div>
  </div>
</template>
