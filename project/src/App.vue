<script setup>
import { computed } from 'vue'
import { authStore } from './store/auth'
import { useRouter, useRoute } from 'vue-router'
import { api } from './api'

const router = useRouter()
const route = useRoute()

const enMenu = computed(() => route.name === 'menu')
const enConsent = computed(() => route.name === 'consent')

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
  <div>
    <!-- Topbar visible si hay sesión -->
    <header
      v-if="authStore.isAuthenticated.value"
      class="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-20 no-print"
    >
      <div class="max-w-6xl mx-auto px-4 py-2 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="irAMenu"
            :disabled="enMenu || enConsent"
            class="flex items-center gap-3 hover:opacity-80 disabled:cursor-default disabled:hover:opacity-100"
          >
            <span class="text-xl">🧠</span>
            <div class="leading-tight text-left">
              <p class="text-xs text-slate-500">Sistema de Salud Mental</p>
              <p class="text-sm font-semibold text-slate-800">
                {{ authStore.state.user?.nombre }} {{ authStore.state.user?.apellido }}
                <span class="ml-1 text-xs text-slate-400 font-normal">· {{ authStore.rol.value }}</span>
              </p>
            </div>
          </button>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="!enMenu && !enConsent"
            @click="irAMenu"
            class="text-sm text-slate-600 hover:text-brand-700 transition px-3 py-1 rounded-lg hover:bg-slate-100"
          >
            ← Menú
          </button>
          <button
            @click="logout"
            class="text-sm text-slate-600 hover:text-red-600 transition px-3 py-1 rounded-lg hover:bg-slate-100"
          >
            Cerrar sesión
          </button>
        </div>
      </div>
    </header>

    <router-view />
  </div>
</template>
