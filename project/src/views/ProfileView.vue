<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { authStore } from '../store/auth'

const router = useRouter()

// ─────────── Datos personales ───────────
const perfil = reactive({
  nombre: authStore.state.user?.nombre || '',
  apellido: authStore.state.user?.apellido || '',
})
const guardandoPerfil = ref(false)
const mensajePerfil = ref('')
const errorPerfil = ref('')

async function guardarPerfil() {
  errorPerfil.value = ''
  mensajePerfil.value = ''
  if (!perfil.nombre.trim() || !perfil.apellido.trim()) {
    errorPerfil.value = 'Completa nombre y apellido'
    return
  }
  guardandoPerfil.value = true
  try {
    const u = await api.actualizarPerfil(perfil.nombre.trim(), perfil.apellido.trim())
    authStore.setUser(u)
    mensajePerfil.value = 'Datos actualizados correctamente'
  } catch (e) {
    errorPerfil.value = e.response?.data?.detail || 'Error al guardar'
  } finally {
    guardandoPerfil.value = false
  }
}

// ─────────── Cambiar contraseña ───────────
const pwd = reactive({ actual: '', nueva: '', confirmar: '' })
const cambiandoPwd = ref(false)
const mensajePwd = ref('')
const errorPwd = ref('')

async function cambiarPassword() {
  errorPwd.value = ''
  mensajePwd.value = ''
  if (!pwd.actual || !pwd.nueva) {
    errorPwd.value = 'Completa ambos campos'
    return
  }
  if (pwd.nueva.length < 8) {
    errorPwd.value = 'La nueva contraseña debe tener al menos 8 caracteres'
    return
  }
  if (pwd.nueva !== pwd.confirmar) {
    errorPwd.value = 'Las contraseñas no coinciden'
    return
  }
  cambiandoPwd.value = true
  try {
    const r = await api.cambiarPassword(pwd.actual, pwd.nueva)
    mensajePwd.value = r.mensaje
    pwd.actual = pwd.nueva = pwd.confirmar = ''
  } catch (e) {
    errorPwd.value = e.response?.data?.detail || 'Error al cambiar contraseña'
  } finally {
    cambiandoPwd.value = false
  }
}

// ─────────── Eliminar cuenta ───────────
const eliminar = reactive({
  abierto: false,
  password: '',
  confirmacion: '',
})
const eliminando = ref(false)
const errorEliminar = ref('')

async function eliminarCuenta() {
  errorEliminar.value = ''
  if (eliminar.confirmacion !== 'ELIMINAR') {
    errorEliminar.value = 'Escribe ELIMINAR en mayúsculas para confirmar'
    return
  }
  if (!eliminar.password) {
    errorEliminar.value = 'Ingresa tu contraseña'
    return
  }
  eliminando.value = true
  try {
    await api.eliminarCuenta(eliminar.password, eliminar.confirmacion)
    authStore.clear()
    alert('Tu cuenta ha sido eliminada. Serás redirigido al login.')
    router.push('/login')
  } catch (e) {
    errorEliminar.value = e.response?.data?.detail || 'Error al eliminar cuenta'
  } finally {
    eliminando.value = false
  }
}
</script>

<template>
  <div class="min-h-[calc(100vh-3rem)] bg-slate-50 py-8 px-4">
    <div class="max-w-2xl mx-auto space-y-6">
      <header class="fade-in-up">
        <h1 class="text-3xl font-bold text-slate-900">Mi perfil</h1>
        <p class="text-slate-600 mt-1">
          Gestiona tus datos personales, tu contraseña y tu cuenta.
        </p>
      </header>

      <!-- ─────────── DATOS PERSONALES (HU-04) ─────────── -->
      <section class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 fade-in-up">
        <h2 class="text-xl font-bold text-slate-900 mb-4">Datos personales</h2>

        <form @submit.prevent="guardarPerfil" class="space-y-4">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Nombre</label>
              <input v-model="perfil.nombre" type="text" :disabled="guardandoPerfil"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Apellido</label>
              <input v-model="perfil.apellido" type="text" :disabled="guardandoPerfil"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Correo institucional</label>
            <input :value="authStore.state.user?.email" disabled
              class="w-full px-3 py-2 border border-slate-200 rounded-lg bg-slate-50 text-slate-500" />
            <p class="text-xs text-slate-500 mt-1">El correo institucional no puede modificarse.</p>
          </div>

          <p v-if="errorPerfil" class="text-red-600 text-sm">{{ errorPerfil }}</p>
          <p v-if="mensajePerfil" class="text-emerald-700 text-sm bg-emerald-50 border border-emerald-200 p-2 rounded">
            ✅ {{ mensajePerfil }}
          </p>

          <button type="submit" :disabled="guardandoPerfil"
            class="bg-brand-600 hover:bg-brand-700 disabled:bg-slate-400 text-white font-semibold py-2 px-5 rounded-lg shadow-sm transition">
            {{ guardandoPerfil ? 'Guardando…' : 'Guardar cambios' }}
          </button>
        </form>
      </section>

      <!-- ─────────── CAMBIAR CONTRASEÑA ─────────── -->
      <section class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 fade-in-up">
        <h2 class="text-xl font-bold text-slate-900 mb-4">Cambiar contraseña</h2>

        <form @submit.prevent="cambiarPassword" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Contraseña actual</label>
            <input v-model="pwd.actual" type="password" :disabled="cambiandoPwd"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
          <div class="grid sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Nueva contraseña</label>
              <input v-model="pwd.nueva" type="password" :disabled="cambiandoPwd" minlength="8"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Confirmar</label>
              <input v-model="pwd.confirmar" type="password" :disabled="cambiandoPwd"
                class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
          </div>

          <p v-if="errorPwd" class="text-red-600 text-sm">{{ errorPwd }}</p>
          <p v-if="mensajePwd" class="text-emerald-700 text-sm bg-emerald-50 border border-emerald-200 p-2 rounded">
            ✅ {{ mensajePwd }}
          </p>

          <button type="submit" :disabled="cambiandoPwd"
            class="bg-brand-600 hover:bg-brand-700 disabled:bg-slate-400 text-white font-semibold py-2 px-5 rounded-lg shadow-sm transition">
            {{ cambiandoPwd ? 'Guardando…' : 'Cambiar contraseña' }}
          </button>
        </form>
      </section>

      <!-- ─────────── ELIMINAR CUENTA (HU-05) ─────────── -->
      <section class="bg-white rounded-2xl shadow-sm border-2 border-red-200 p-6 fade-in-up">
        <h2 class="text-xl font-bold text-red-800 mb-2">Eliminar mi cuenta</h2>
        <p class="text-sm text-slate-700 mb-4">
          Esta acción es <strong>permanente e irreversible</strong>. Se eliminarán tu cuenta,
          tus evaluaciones, respuestas y resultados de análisis emocional.
        </p>

        <button v-if="!eliminar.abierto"
          @click="eliminar.abierto = true"
          class="bg-white text-red-700 border border-red-400 hover:bg-red-50 font-semibold py-2 px-5 rounded-lg transition">
          Quiero eliminar mi cuenta
        </button>

        <div v-else class="bg-red-50 border border-red-200 rounded-lg p-4 space-y-3">
          <p class="text-sm text-red-900">
            Para confirmar, escribe <strong>ELIMINAR</strong> y tu contraseña actual.
          </p>
          <div>
            <label class="block text-sm font-medium text-red-900 mb-1">
              Escribe ELIMINAR
            </label>
            <input v-model="eliminar.confirmacion" type="text" placeholder="ELIMINAR"
              class="w-full px-3 py-2 border border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none font-mono" />
          </div>
          <div>
            <label class="block text-sm font-medium text-red-900 mb-1">Contraseña</label>
            <input v-model="eliminar.password" type="password"
              class="w-full px-3 py-2 border border-red-300 rounded-lg focus:ring-2 focus:ring-red-500 outline-none" />
          </div>

          <p v-if="errorEliminar" class="text-red-700 text-sm font-medium">{{ errorEliminar }}</p>

          <div class="flex gap-2 pt-2">
            <button @click="eliminar.abierto = false; eliminar.password = ''; eliminar.confirmacion = ''"
              :disabled="eliminando"
              class="px-4 py-2 bg-white border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50">
              Cancelar
            </button>
            <button @click="eliminarCuenta" :disabled="eliminando"
              class="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-400 text-white font-semibold rounded-lg shadow-sm">
              {{ eliminando ? 'Eliminando…' : 'Eliminar cuenta permanentemente' }}
            </button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
