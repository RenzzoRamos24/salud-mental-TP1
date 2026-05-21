<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import AuthShell from '../components/AuthShell.vue'

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
  <AuthShell
    title="¿Olvidaste tu contraseña?"
    subtitle="No te preocupes. Te enviaremos un código de 6 dígitos para restablecerla."
  >
    <form @submit.prevent="enviar" class="space-y-4">
      <div>
        <label class="label">Correo institucional</label>
        <input v-model="email" type="email" :disabled="cargando" placeholder="tucorreo@upc.edu.pe" class="input-lg" autofocus />
      </div>

      <p v-if="error" class="field-error">{{ error }}</p>
      <p v-if="mensaje" class="banner-success">
        <span>✅</span>
        <span>{{ mensaje }}</span>
      </p>

      <button type="submit" :disabled="cargando" class="btn-primary w-full py-3 text-base">
        {{ cargando ? 'Enviando…' : 'Enviar código' }}
      </button>
    </form>

    <p class="banner-info mt-4 text-xs">
      <span>💡</span>
      <span>En modo desarrollo el código aparece en la consola del backend.</span>
    </p>

    <template #footer>
      <router-link to="/login" class="text-sm text-brand-600 hover:text-brand-700 font-semibold">
        ← Volver al inicio de sesión
      </router-link>
    </template>
  </AuthShell>
</template>
