<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { authStore } from "../store/auth";
import { api } from "../api";
import SOSButton from "../components/SOSButton.vue";

const router = useRouter();
const user = computed(() => authStore.state.user);
const rol = computed(() => authStore.rol.value);

const totalSesiones = ref(0);

onMounted(async () => {
  if (rol.value !== "estudiante") return;
  try {
    const h = await api.miHistorial();
    totalSesiones.value = h?.total_sesiones || 0;
  } catch (_) {
    /* no-op */
  }
});

const opcionesEstudiante = [
  {
    titulo: "Empezar una conversación",
    desc: "Cuéntale a Sami cómo te has sentido estos días.",
    destino: "/chat",
  },
  {
    titulo: "Mi historial",
    desc: "Mira cómo te ha ido en las últimas semanas.",
    destino: "/mi-historial",
  },
  {
    titulo: "Lecturas y consejos",
    desc: "Cosas útiles para entenderte un poco mejor.",
    destino: "/recursos",
  },
  {
    titulo: "Encuesta",
    desc: "Cuéntanos qué te pareció hablar con Sami.",
    destino: "/encuesta",
  },
  {
    titulo: "Mi perfil",
    desc: "Tus datos y tu privacidad.",
    destino: "/perfil",
  },
];

const opcionesPsicologo = [
  {
    titulo: "Panel de estudiantes",
    desc: "Cómo está cada uno, alertas y citas pendientes.",
    destino: "/psicologo",
  },
  {
    titulo: "Recursos",
    desc: "Material clínico y líneas de apoyo.",
    destino: "/recursos",
  },
  {
    titulo: "Mi perfil",
    desc: "Tus datos y contraseña.",
    destino: "/perfil",
  },
];

const opcionesAdmin = [
  {
    titulo: "Usuarios",
    desc: "Estudiantes, psicólogos y otros administradores.",
    destino: "/admin",
  },
  {
    titulo: "Configuración",
    desc: "Preguntas, umbrales del modelo y respaldos.",
    destino: "/admin/sistema",
  },
  {
    titulo: "Contenidos",
    desc: "Lo que los estudiantes ven en la sección de lecturas.",
    destino: "/admin/contenidos",
  },
  {
    titulo: "Mensajes de Sami",
    desc: "Plantillas que usa la conversación.",
    destino: "/admin/mensajes-chatbot",
  },
  {
    titulo: "Reportes",
    desc: "Cómo va el sistema en general.",
    destino: "/admin/reportes",
  },
  {
    titulo: "Auditoría",
    desc: "Registro de accesos al sistema.",
    destino: "/admin/logs",
  },
];

const opciones = computed(() => {
  if (rol.value === "admin") return opcionesAdmin;
  if (rol.value === "psicologo") return opcionesPsicologo;
  return opcionesEstudiante;
});

const esEstudiante = computed(() => rol.value === "estudiante");

const tituloHero = computed(() => {
  if (rol.value === "admin")
    return ["Bienvenido al", "panel de administración"];
  if (rol.value === "psicologo") return ["Bienvenido a", "tu panel clínico"];
  return ["Bienvenido a", "tu espacio de bienestar"];
});
</script>

<template>
  <div class="max-w-5xl mx-auto px-6 py-10">
    <section class="mb-10">
      <p class="text-sm text-green-700 mb-2">Hola, {{ user?.nombre }}.</p>
      <h1 class="hero-serif text-3xl sm:text-4xl">
        {{ tituloHero[0] }} <span class="hero-mint">{{ tituloHero[1] }}</span>
      </h1>
    </section>

    <div class="grid sm:grid-cols-2 gap-4">
      <button
        v-for="(op, i) in opciones"
        :key="i"
        @click="router.push(op.destino)"
        class="group menu-card text-left"
      >
        <span class="menu-card-arrow">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </span>
        <p class="text-xs text-ink-400 mb-3 font-medium tracking-wider">
          {{ String(i + 1).padStart(2, "0") }}
        </p>
        <h3 class="font-semibold text-ink-900 text-lg leading-snug">
          {{ op.titulo }}
        </h3>
        <p class="text-sm text-ink-600 mt-1.5 leading-relaxed">{{ op.desc }}</p>
      </button>
    </div>

    <div
      v-if="esEstudiante"
      class="mt-8 rounded-xl bg-white border border-ink-200 p-6"
    >
      <p class="font-semibold text-ink-900">
        Si estás pasando por un mal momento
      </p>
      <p class="text-sm text-ink-700 mt-1 leading-relaxed">
        Puedes llamar gratis a la <strong>Línea 113, opción 5</strong> a
        cualquier hora, hablar con la psicóloga del colegio o con tu tutor de
        aula. No tienes que pasarlo solo.
      </p>
    </div>

    <SOSButton v-if="esEstudiante" />
  </div>
</template>
