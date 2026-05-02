<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '../api'
import { authStore } from '../store/auth'

const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const error = ref('')
const cargando = ref(false)

async function entrar() {
  error.value = ''
  if (!email.value.trim() || !password.value) {
    error.value = 'Completa todos los campos'
    return
  }
  cargando.value = true
  try {
    const data = await api.login(email.value.trim(), password.value)
    authStore.setSession(data.access_token, data.user)
    const destino = data.user.consentimiento_aceptado ? '/menu' : '/consent'
    router.push(route.query.redirect || destino)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Error iniciando sesión'
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-brand-50 via-white to-indigo-50">
    <div class="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 fade-in-up">
      <div class="text-center mb-6">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-brand-100 mb-4">
          <span class="text-3xl">🧠</span>
        </div>
        <h1 class="text-2xl font-bold text-slate-900">Iniciar sesión</h1>
        <p class="text-slate-600 text-sm mt-1">Sistema de Salud Mental</p>
      </div>

      <form @submit.prevent="entrar" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Correo institucional</label>
          <input
            v-model="email"
            type="email"
            placeholder="tucorreo@institucion.edu"
            class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            :disabled="cargando"
            autofocus
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Contraseña</label>
          <input
            v-model="password"
            type="password"
            class="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            :disabled="cargando"
          />
        </div>

        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>

        <button
          type="submit"
          :disabled="cargando"
          class="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-slate-400 text-white font-semibold py-3 rounded-lg shadow-md transition"
        >
          {{ cargando ? 'Ingresando…' : 'Ingresar' }}
        </button>
      </form>

      <div class="mt-6 flex items-center justify-between text-sm">
        <router-link to="/forgot-password" class="text-brand-600 hover:underline">
          ¿Olvidaste tu contraseña?
        </router-link>
        <router-link to="/register" class="text-brand-600 hover:underline">
          Crear cuenta
        </router-link>
      </div>
    </div>
  </div>
</template>
