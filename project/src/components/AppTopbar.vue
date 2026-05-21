<script setup>
import { computed } from 'vue'
import { authStore } from '../store/auth'
import { useRouter, useRoute } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const route = useRoute()

const enConsent = computed(() => route.name === 'consent')

const inicial = computed(() => {
  const u = authStore.state.user
  if (!u) return '?'
  return ((u.nombre || '?').charAt(0)).toUpperCase()
})

const rolLabel = computed(() => {
  const r = authStore.rol.value
  if (r === 'estudiante') return 'estudiante'
  if (r === 'psicologo')  return 'psicólogo/a'
  if (r === 'admin')      return 'administrador'
  return r || ''
})

async function logout() {
  await api.logout()
  authStore.clear()
  router.push({ name: 'login' })
}

function irAMenu() {
  router.push('/menu')
}
</script>

<template>
  <header
    v-if="authStore.isAuthenticated.value && !enConsent"
    class="bg-transparent border-b border-cream-200/70 sticky top-0 z-30 no-print"
  >
    <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between gap-6">
      <button @click="irAMenu" class="sami-wordmark hover:opacity-80 transition">
        Sami <span class="accent">· Salud Mental Juvenil</span>
      </button>

      <div class="flex items-center gap-5">
        <router-link to="/perfil" class="user-pill hover:bg-cream-50 transition">
          <span class="avatar-sm bg-peach-100 text-peach-600">{{ inicial }}</span>
          <span class="font-semibold text-ink-800">{{ authStore.state.user?.nombre }}</span>
          <span class="text-ink-400">· {{ rolLabel }}</span>
        </router-link>
        <button
          @click="logout"
          class="text-sm text-ink-600 hover:text-ink-900 transition"
        >Cerrar sesión</button>
      </div>
    </div>
  </header>
</template>
