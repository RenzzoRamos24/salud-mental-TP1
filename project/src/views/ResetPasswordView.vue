<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const router = useRouter()

const email = ref(route.query.email || '')
const token = ref('')
const password = ref('')
const password2 = ref('')
const error = ref('')
const exito = ref(false)
const cargando = ref(false)

async function resetear() {
  error.value = ''
  if (!email.value.trim() || token.value.length < 6 || !password.value) {
    error.value = 'Completa todos los campos (token de 6 dígitos)'
    return
  }
  if (password.value.length < 8) {
    error.value = 'La contraseña debe tener al menos 8 caracteres'
    return
  }
  if (password.value !== password2.value) {
    error.value = 'Las contraseñas no coinciden'
    return
  }

  cargando.value = true
  try {
    await api.resetPassword(email.value.trim(), token.value.trim(), password.value)
    exito.value = true
    setTimeout(() => router.push('/login'), 2000)
  } catch (e) {
    const detail = e.response?.data?.detail
    error.value = Array.isArray(detail) ? detail[0]?.msg : (detail || 'Error al resetear')
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-brand-50 via-white to-indigo-50">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 fade-in-up">
      <h1 class="text-2xl font-bold text-slate-900 mb-2">Nueva contraseña</h1>
      <p class="text-slate-600 text-sm mb-6">
        Ingresa el código de 6 dígitos que recibiste y tu nueva contraseña.
      </p>

      <form @submit.prevent="resetear" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Correo</label>
          <input v-model="email" type="email" :disabled="cargando || exito"
            class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Código (6 dígitos)</label>
          <input v-model="token" type="text" inputmode="numeric" maxlength="6" :disabled="cargando || exito"
            class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none tracking-widest text-center text-lg font-mono" />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Nueva contraseña</label>
          <input v-model="password" type="password" :disabled="cargando || exito" minlength="8"
            class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Confirmar contraseña</label>
          <input v-model="password2" type="password" :disabled="cargando || exito"
            class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
        </div>

        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>
        <p v-if="exito" class="text-emerald-700 text-sm bg-emerald-50 border border-emerald-200 p-3 rounded-lg">
          ✅ Contraseña actualizada. Redirigiendo al login…
        </p>

        <button
          type="submit"
          :disabled="cargando || exito"
          class="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-slate-400 text-white font-semibold py-3 rounded-lg shadow-md transition"
        >
          {{ cargando ? 'Guardando…' : 'Cambiar contraseña' }}
        </button>
      </form>

      <p class="text-center text-sm text-slate-600 mt-4">
        <router-link to="/login" class="text-brand-600 hover:underline">Volver al login</router-link>
      </p>
    </div>
  </div>
</template>
