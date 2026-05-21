<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { authStore } from '../store/auth'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()

const perfil = reactive({
  nombre: authStore.state.user?.nombre || '',
  apellido: authStore.state.user?.apellido || '',
})
const guardandoPerfil = ref(false)
const mensajePerfil = ref('')
const errorPerfil = ref('')

const iniciales = computed(() => {
  const n = (perfil.nombre || '?').charAt(0)
  const a = (perfil.apellido || '').charAt(0)
  return (n + a).toUpperCase()
})

async function guardarPerfil() {
  errorPerfil.value = ''; mensajePerfil.value = ''
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
  } finally { guardandoPerfil.value = false }
}

const pwd = reactive({ actual: '', nueva: '', confirmar: '' })
const cambiandoPwd = ref(false)
const mensajePwd = ref('')
const errorPwd = ref('')

async function cambiarPassword() {
  errorPwd.value = ''; mensajePwd.value = ''
  if (!pwd.actual || !pwd.nueva) { errorPwd.value = 'Completa ambos campos'; return }
  if (pwd.nueva.length < 8) { errorPwd.value = 'La nueva contraseña debe tener al menos 8 caracteres'; return }
  if (pwd.nueva !== pwd.confirmar) { errorPwd.value = 'Las contraseñas no coinciden'; return }
  cambiandoPwd.value = true
  try {
    const r = await api.cambiarPassword(pwd.actual, pwd.nueva)
    mensajePwd.value = r.mensaje
    pwd.actual = pwd.nueva = pwd.confirmar = ''
  } catch (e) {
    errorPwd.value = e.response?.data?.detail || 'Error al cambiar contraseña'
  } finally { cambiandoPwd.value = false }
}

const eliminar = reactive({ abierto: false, password: '', confirmacion: '' })
const eliminando = ref(false)
const errorEliminar = ref('')

async function eliminarCuenta() {
  errorEliminar.value = ''
  if (eliminar.confirmacion !== 'ELIMINAR') {
    errorEliminar.value = 'Escribe ELIMINAR en mayúsculas para confirmar'; return
  }
  if (!eliminar.password) { errorEliminar.value = 'Ingresa tu contraseña'; return }
  eliminando.value = true
  try {
    await api.eliminarCuenta(eliminar.password, eliminar.confirmacion)
    authStore.clear()
    alert('Tu cuenta ha sido eliminada. Serás redirigido al login.')
    router.push('/login')
  } catch (e) {
    errorEliminar.value = e.response?.data?.detail || 'Error al eliminar cuenta'
  } finally { eliminando.value = false }
}

const rolLabel = computed(() => {
  const r = authStore.rol.value
  if (r === 'estudiante') return 'Estudiante'
  if (r === 'psicologo')  return 'Psicólogo/a'
  if (r === 'admin')      return 'Administrador'
  return r
})
</script>

<template>
  <div class="page-shell">
    <PageHeader title="Mi" accent="perfil" subtitle="Gestiona tus datos, contraseña y cuenta." icon="👤" tone="peach">
      <template #aside>
        <div class="flex items-center gap-3">
          <div class="avatar-lg text-lg">{{ iniciales }}</div>
          <div>
            <p class="dsm5-tag">{{ rolLabel }}</p>
          </div>
        </div>
      </template>
    </PageHeader>

    <!-- Datos personales -->
    <section class="card p-6 mb-6 fade-in-up">
      <h2 class="section-title">📝 Datos personales</h2>

      <form @submit.prevent="guardarPerfil" class="space-y-4 mt-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Nombre</label>
            <input v-model="perfil.nombre" type="text" :disabled="guardandoPerfil" class="input" />
          </div>
          <div>
            <label class="label">Apellido</label>
            <input v-model="perfil.apellido" type="text" :disabled="guardandoPerfil" class="input" />
          </div>
        </div>
        <div>
          <label class="label">Correo institucional</label>
          <input :value="authStore.state.user?.email" disabled class="input bg-cream-50 text-ink-500" />
          <p class="field-hint">El correo institucional no puede modificarse.</p>
        </div>

        <p v-if="errorPerfil" class="field-error">{{ errorPerfil }}</p>
        <p v-if="mensajePerfil" class="banner-success">
          <span>✅</span><span>{{ mensajePerfil }}</span>
        </p>

        <button type="submit" :disabled="guardandoPerfil" class="btn-primary">
          {{ guardandoPerfil ? 'Guardando…' : 'Guardar cambios' }}
        </button>
      </form>
    </section>

    <!-- Contraseña -->
    <section class="card p-6 mb-6 fade-in-up">
      <h2 class="section-title">🔑 Cambiar contraseña</h2>

      <form @submit.prevent="cambiarPassword" class="space-y-4 mt-4">
        <div>
          <label class="label">Contraseña actual</label>
          <input v-model="pwd.actual" type="password" :disabled="cambiandoPwd" class="input" />
        </div>
        <div class="grid sm:grid-cols-2 gap-3">
          <div>
            <label class="label">Nueva contraseña</label>
            <input v-model="pwd.nueva" type="password" :disabled="cambiandoPwd" minlength="8" class="input" />
          </div>
          <div>
            <label class="label">Confirmar</label>
            <input v-model="pwd.confirmar" type="password" :disabled="cambiandoPwd" class="input" />
          </div>
        </div>

        <p v-if="errorPwd" class="field-error">{{ errorPwd }}</p>
        <p v-if="mensajePwd" class="banner-success">
          <span>✅</span><span>{{ mensajePwd }}</span>
        </p>

        <button type="submit" :disabled="cambiandoPwd" class="btn-primary">
          {{ cambiandoPwd ? 'Guardando…' : 'Cambiar contraseña' }}
        </button>
      </form>
    </section>

    <!-- Eliminar cuenta -->
    <section class="card p-6 border-red-200 border-2 fade-in-up">
      <h2 class="section-title text-risk-critico">🗑️ Eliminar mi cuenta</h2>
      <p class="text-sm text-ink-700 mb-4">
        Esta acción es <strong>permanente e irreversible</strong>. Se eliminarán tu cuenta,
        tus evaluaciones, respuestas y resultados de análisis emocional.
      </p>

      <button v-if="!eliminar.abierto" @click="eliminar.abierto = true" class="btn-secondary !text-risk-critico !border-red-300 hover:!bg-red-50">
        Quiero eliminar mi cuenta
      </button>

      <div v-else class="bg-red-50 border border-red-200 rounded-2xl p-5 space-y-4">
        <p class="text-sm text-risk-critico">
          Para confirmar, escribe <strong>ELIMINAR</strong> y tu contraseña actual.
        </p>
        <div>
          <label class="label !text-risk-critico">Escribe ELIMINAR</label>
          <input v-model="eliminar.confirmacion" type="text" placeholder="ELIMINAR" class="input border-red-300 font-mono uppercase" />
        </div>
        <div>
          <label class="label !text-risk-critico">Contraseña</label>
          <input v-model="eliminar.password" type="password" class="input border-red-300" />
        </div>

        <p v-if="errorEliminar" class="field-error">{{ errorEliminar }}</p>

        <div class="flex gap-2 pt-2">
          <button
            @click="eliminar.abierto = false; eliminar.password = ''; eliminar.confirmacion = ''"
            :disabled="eliminando"
            class="btn-ghost"
          >Cancelar</button>
          <button @click="eliminarCuenta" :disabled="eliminando" class="btn-danger">
            {{ eliminando ? 'Eliminando…' : 'Eliminar cuenta permanentemente' }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
