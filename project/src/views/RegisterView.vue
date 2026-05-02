<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { authStore } from '../store/auth'

const router = useRouter()

const nombre = ref('')
const apellido = ref('')
const email = ref('')
const password = ref('')
const password2 = ref('')
const role = ref('estudiante')
const error = ref('')
const cargando = ref(false)

async function registrar() {
  error.value = ''

  if (!nombre.value.trim() || !apellido.value.trim() || !email.value.trim() || !password.value) {
    error.value = 'Completa todos los campos'
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
    const data = await api.register({
      email: email.value.trim().toLowerCase(),
      password: password.value,
      nombre: nombre.value.trim(),
      apellido: apellido.value.trim(),
      role: role.value,
    })
    authStore.setSession(data.access_token, data.user)
    router.push('/consent')
  } catch (e) {
    const detail = e.response?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail[0]?.msg || 'Error de validación'
    } else {
      error.value = detail || 'Error al registrarse'
    }
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
        <h1 class="text-2xl font-bold text-slate-900">Crear cuenta</h1>
        <p class="text-slate-600 text-sm mt-1">
          Usa tu correo institucional
        </p>
      </div>

      <form @submit.prevent="registrar" class="space-y-3">
        <!-- Selector de rol -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">¿Cómo te registras?</label>
          <div class="grid grid-cols-2 gap-2">
            <label
              :class="[
                'cursor-pointer flex flex-col items-center gap-1 p-3 rounded-lg border-2 transition',
                role === 'estudiante'
                  ? 'border-brand-500 bg-brand-50'
                  : 'border-slate-200 bg-white hover:border-slate-300',
              ]"
            >
              <input v-model="role" type="radio" value="estudiante" class="sr-only" :disabled="cargando" />
              <span class="text-2xl">🎓</span>
              <span class="text-sm font-semibold text-slate-800">Estudiante</span>
            </label>
            <label
              :class="[
                'cursor-pointer flex flex-col items-center gap-1 p-3 rounded-lg border-2 transition',
                role === 'psicologo'
                  ? 'border-brand-500 bg-brand-50'
                  : 'border-slate-200 bg-white hover:border-slate-300',
              ]"
            >
              <input v-model="role" type="radio" value="psicologo" class="sr-only" :disabled="cargando" />
              <span class="text-2xl">🧑‍⚕️</span>
              <span class="text-sm font-semibold text-slate-800">Psicólogo/a</span>
            </label>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
            <input v-model="nombre" type="text" :disabled="cargando"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Apellido</label>
            <input v-model="apellido" type="text" :disabled="cargando"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Correo institucional</label>
          <input v-model="email" type="email" :disabled="cargando"
            placeholder="tucorreo@institucion.edu"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Contraseña</label>
          <input v-model="password" type="password" :disabled="cargando" minlength="8"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
          <p class="text-xs text-slate-500 mt-1">Mínimo 8 caracteres</p>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Confirmar contraseña</label>
          <input v-model="password2" type="password" :disabled="cargando"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
        </div>

        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>

        <button
          type="submit"
          :disabled="cargando"
          class="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-slate-400 text-white font-semibold py-3 rounded-lg shadow-md transition"
        >
          {{ cargando ? 'Creando cuenta…' : 'Registrarme' }}
        </button>
      </form>

      <p class="text-center text-sm text-slate-600 mt-4">
        ¿Ya tienes cuenta?
        <router-link to="/login" class="text-brand-600 hover:underline">Inicia sesión</router-link>
      </p>
    </div>
  </div>
</template>
