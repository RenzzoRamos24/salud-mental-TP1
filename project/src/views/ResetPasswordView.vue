<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import AuthShell from '../components/AuthShell.vue'

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
  <AuthShell
    title="Crear nueva contraseña"
    subtitle="Ingresa el código de 6 dígitos que recibiste y elige una nueva contraseña."
  >
    <form @submit.prevent="resetear" class="space-y-4">
      <div>
        <label class="label">Correo</label>
        <input v-model="email" type="email" :disabled="cargando || exito" class="input" />
      </div>

      <div>
        <label class="label">Código (6 dígitos)</label>
        <input
          v-model="token"
          type="text"
          inputmode="numeric"
          maxlength="6"
          :disabled="cargando || exito"
          class="input text-center text-2xl font-mono tracking-[0.5em]"
          placeholder="••••••"
        />
      </div>

      <div>
        <label class="label">Nueva contraseña</label>
        <input v-model="password" type="password" :disabled="cargando || exito" minlength="8" class="input" />
      </div>

      <div>
        <label class="label">Confirmar contraseña</label>
        <input v-model="password2" type="password" :disabled="cargando || exito" class="input" />
      </div>

      <p v-if="error" class="field-error">{{ error }}</p>
      <p v-if="exito" class="banner-success">
        <span>✅</span>
        <span>Contraseña actualizada. Redirigiendo al login…</span>
      </p>

      <button type="submit" :disabled="cargando || exito" class="btn-primary w-full py-3 text-base">
        {{ cargando ? 'Guardando…' : 'Cambiar contraseña' }}
      </button>
    </form>

    <template #footer>
      <router-link to="/login" class="text-sm text-brand-600 hover:text-brand-700 font-semibold">
        ← Volver al inicio de sesión
      </router-link>
    </template>
  </AuthShell>
</template>
