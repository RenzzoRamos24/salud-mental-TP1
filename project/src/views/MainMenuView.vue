<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { authStore } from '../store/auth'

const router = useRouter()
const user = computed(() => authStore.state.user)
const rol = computed(() => authStore.rol.value)

const opcionesEstudiante = [
  {
    titulo: 'Iniciar evaluación',
    descripcion: 'Conversa con el chatbot para evaluar tu bienestar emocional (10 preguntas).',
    icono: '🧠',
    color: 'from-brand-500 to-brand-700',
    accion: () => router.push('/chat'),
  },
  {
    titulo: 'Mi perfil',
    descripcion: 'Actualiza tus datos, cambia tu contraseña o elimina tu cuenta.',
    icono: '👤',
    color: 'from-indigo-500 to-purple-600',
    accion: () => router.push('/perfil'),
  },
]

const opcionesPsicologo = [
  {
    titulo: 'Estudiantes',
    descripcion: 'Revisa el historial emocional de los estudiantes registrados.',
    icono: '👥',
    color: 'from-emerald-500 to-teal-600',
    accion: () => router.push('/psicologo'),
  },
  {
    titulo: 'Mi perfil',
    descripcion: 'Actualiza tus datos personales y contraseña.',
    icono: '👤',
    color: 'from-indigo-500 to-purple-600',
    accion: () => router.push('/perfil'),
  },
]

const opcionesAdmin = [
  {
    titulo: 'Usuarios del sistema',
    descripcion: 'Listado de todos los estudiantes, psicólogos y admins registrados.',
    icono: '🛠️',
    color: 'from-purple-500 to-fuchsia-600',
    accion: () => router.push('/admin'),
  },
  {
    titulo: 'Estudiantes',
    descripcion: 'Acceso al historial emocional de los estudiantes (vista psicólogo).',
    icono: '👥',
    color: 'from-emerald-500 to-teal-600',
    accion: () => router.push('/psicologo'),
  },
  {
    titulo: 'Mi perfil',
    descripcion: 'Actualiza tus datos personales y contraseña.',
    icono: '👤',
    color: 'from-indigo-500 to-purple-600',
    accion: () => router.push('/perfil'),
  },
]

const opciones = computed(() => {
  if (rol.value === 'admin') return opcionesAdmin
  if (rol.value === 'psicologo') return opcionesPsicologo
  return opcionesEstudiante
})

const subtitulo = computed(() => {
  if (rol.value === 'admin') return 'Panel de administración'
  if (rol.value === 'psicologo') return 'Panel del psicólogo'
  return 'Bienvenido a tu espacio de bienestar'
})

const ayuda = computed(() => {
  if (rol.value === 'admin') return 'Administra cuentas y supervisa el uso del sistema.'
  if (rol.value === 'psicologo') return 'Acceso al historial emocional de los estudiantes.'
  return 'Selecciona una opción para continuar.'
})

const esEstudiante = computed(() => rol.value === 'estudiante')
</script>

<template>
  <div class="min-h-[calc(100vh-3rem)] bg-slate-50 py-10 px-4">
    <div class="max-w-4xl mx-auto">
      <header class="mb-8 fade-in-up">
        <p class="text-sm text-slate-500">Hola, {{ user?.nombre }} 👋</p>
        <h1 class="text-3xl font-bold text-slate-900 mt-1">{{ subtitulo }}</h1>
        <p class="text-slate-600 mt-2">{{ ayuda }}</p>
      </header>

      <div class="grid sm:grid-cols-2 gap-5">
        <button
          v-for="(op, i) in opciones"
          :key="i"
          @click="op.accion"
          class="group text-left bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition fade-in-up"
        >
          <div :class="['w-14 h-14 rounded-xl bg-gradient-to-br flex items-center justify-center text-3xl mb-4', op.color]">
            {{ op.icono }}
          </div>
          <h3 class="text-lg font-bold text-slate-900 group-hover:text-brand-700 transition">
            {{ op.titulo }}
          </h3>
          <p class="text-sm text-slate-600 mt-1">{{ op.descripcion }}</p>
        </button>
      </div>

      <div v-if="esEstudiante" class="mt-8 p-5 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-900 fade-in-up">
        <p class="font-semibold mb-1">¿Estás en crisis?</p>
        <p>
          Llama a la <strong>Línea 113 (MINSA), opción 5</strong> — atención 24/7 en salud mental,
          o acude a la emergencia más cercana.
        </p>
      </div>
    </div>
  </div>
</template>
