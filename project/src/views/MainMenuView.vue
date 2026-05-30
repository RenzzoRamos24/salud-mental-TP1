<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { authStore } from "../store/auth";
import { api } from "../api";
import SOSButton from "../components/SOSButton.vue";

const router = useRouter();
const user = computed(() => authStore.state.user);
const rol = computed(() => authStore.rol.value);

// ─── Estado del diario para el menú del estudiante ─────────────────────
const totalEntradasDiario = ref(0);
const ultimaEntradaFecha = ref(null); // ISO timestamp o null

onMounted(async () => {
  if (rol.value !== "estudiante") return;
  try {
    const entradas = await api.listarMisEntradasDiario();
    totalEntradasDiario.value = entradas?.length || 0;
    if (entradas && entradas.length > 0) {
      // El backend devuelve ordenadas por timestamp desc
      ultimaEntradaFecha.value = entradas[0].timestamp || entradas[0].fecha;
    }
  } catch (_) {
    /* no-op */
  }
});

// Mensaje cálido según cuánto hace de la última entrada
const mensajeDiario = computed(() => {
  if (rol.value !== "estudiante") return null;
  if (!ultimaEntradaFecha.value) {
    return "Tu espacio personal. Escribe cómo te sientes cuando quieras.";
  }
  const ultima = new Date(ultimaEntradaFecha.value);
  const hoy = new Date();
  // Días calendario, no horas
  const ms = new Date(hoy.toDateString()) - new Date(ultima.toDateString());
  const dias = Math.round(ms / 86400000);
  if (dias <= 0) return "Ya escribiste hoy. Puedes añadir algo más si quieres.";
  if (dias === 1) return "Tu última entrada fue ayer. ¿Cómo va el día?";
  if (dias < 7) return `Hace ${dias} días que no escribes.`;
  return "Hace tiempo que no pasas por aquí. Tómate unos minutos si quieres.";
});

// ─── Opciones secundarias del estudiante (debajo de la card destacada) ──
// Las pestañas del diario (Escribir / Mi diario / Apoyo) ya están en la
// tabbar interna del diario — no las duplicamos acá.
const opcionesSecundariasEstudiante = computed(() => [
  {
    titulo: "Mi perfil",
    desc: "Tus datos y tu privacidad.",
    destino: "/perfil",
  },
]);

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

// Para psicólogo y admin seguimos usando el grid uniforme. Para el estudiante
// la "card destacada" del diario se renderiza aparte arriba.
const opciones = computed(() => {
  if (rol.value === "admin") return opcionesAdmin;
  if (rol.value === "psicologo") return opcionesPsicologo;
  return opcionesSecundariasEstudiante.value;
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

    <!-- ══════════════════════════════════════════════════════════════ -->
    <!-- CARD DESTACADA DEL ESTUDIANTE: Mi diario                       -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <button
      v-if="esEstudiante"
      @click="router.push('/diario')"
      class="group block w-full text-left bg-white border border-ink-100 rounded-xl shadow-card hover:border-green-500 hover:shadow-pastel hover:-translate-y-0.5 transition p-7 mb-4"
    >
      <div class="flex items-start justify-between gap-6 flex-wrap">
        <div class="flex-1 min-w-0">
          <p
            class="text-[11px] uppercase tracking-wider text-green-700 font-semibold mb-2"
          >
            Tu diario
          </p>
          <h2 class="hero-serif text-2xl sm:text-3xl mb-2">
            Escribe cómo te <span class="hero-mint">sientes hoy</span>
          </h2>
          <p class="text-ink-600 leading-relaxed max-w-xl">
            {{ mensajeDiario }}
          </p>
        </div>
        <div class="shrink-0 self-end">
          <span class="btn-primary">
            Ir a mi diario
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </span>
        </div>
      </div>
    </button>

    <!-- ══════════════════════════════════════════════════════════════ -->
    <!-- GRID de opciones secundarias (estudiante) o principal (otros) -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <div
      class="grid gap-4"
      :class="esEstudiante ? 'sm:grid-cols-1 max-w-md' : 'sm:grid-cols-2'"
    >
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
