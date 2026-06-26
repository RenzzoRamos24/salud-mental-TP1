<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { authStore } from "../store/auth";

const router = useRouter();
const user = computed(() => authStore.state.user);
const rol = computed(() => authStore.rol.value);

const primerNombre = computed(() => {
  const n = (user.value?.nombre || "").trim();
  return n.split(" ")[0] || "";
});

const opcionesEstudiante = [
  {
    titulo: "Mis cuestionarios",
    desc: "Responde los cuestionarios que te asignó tu psicóloga.",
    destino: "/mis-cuestionarios",
  },
  {
    titulo: "Recursos",
    desc: "Material psicoeducativo y líneas de apoyo.",
    destino: "/recursos",
  },
  {
    titulo: "Mi cuenta",
    desc: "Datos personales y contraseña.",
    destino: "/perfil",
  },
];

const opcionesPsicologo = [
  {
    titulo: "Estudiantes",
    desc: "Panel clínico, alertas y resultados por alumno.",
    destino: "/psicologo",
  },
  {
    titulo: "SOS",
    desc: "Solicitudes de apoyo enviadas por los alumnos.",
    destino: "/psicologo/sos",
  },
  {
    titulo: "Citas",
    desc: "Agenda con tus alumnos.",
    destino: "/psicologo/citas",
  },
  {
    titulo: "Banco de instrumentos",
    desc: "Escalas validadas, frases incompletas y tus bloques personalizados.",
    destino: "/psicologo/banco",
  },
  {
    titulo: "Mis plantillas",
    desc: "Cuestionarios armados con bloques del banco.",
    destino: "/psicologo/plantillas",
  },
  {
    titulo: "Asignar cuestionario",
    desc: "Aplicar una plantilla a un alumno.",
    destino: "/psicologo/asignar",
  },
  {
    titulo: "Recursos",
    desc: "Escalas, protocolos y líneas de derivación.",
    destino: "/recursos",
  },
  {
    titulo: "Mi cuenta",
    desc: "Datos y contraseña.",
    destino: "/perfil",
  },
];

const opcionesAdmin = [
  {
    titulo: "Usuarios",
    desc: "Estudiantes, psicólogas y administradores.",
    destino: "/admin",
  },
  {
    titulo: "Configuración",
    desc: "Modelo NLP y respaldos.",
    destino: "/admin/sistema",
  },
  {
    titulo: "Contenidos",
    desc: "Material psicoeducativo del banco.",
    destino: "/admin/contenidos",
  },
  {
    titulo: "Reportes",
    desc: "Métricas de uso y cuestionarios.",
    destino: "/admin/reportes",
  },
  {
    titulo: "Auditoría",
    desc: "Registro de accesos.",
    destino: "/admin/logs",
  },
];

const opciones = computed(() => {
  if (rol.value === "admin") return opcionesAdmin;
  if (rol.value === "psicologo") return opcionesPsicologo;
  return opcionesEstudiante;
});

const tituloHero = computed(() => {
  if (rol.value === "admin") return ["Panel de", "administración"];
  if (rol.value === "psicologo") return ["Tu panel", "clínico"];
  return ["Tu espacio", "en Sami"];
});
</script>

<template>
  <div class="page-shell-wide">
    <section class="mb-8">
      <p class="eyebrow mb-2">Hola, {{ primerNombre || "tú" }}</p>
      <h1 class="hero-serif text-[32px] sm:text-[37px]">
        {{ tituloHero[0] }} <span class="hero-mint">{{ tituloHero[1] }}</span>
      </h1>
    </section>

    <div class="grid gap-4 sm:grid-cols-2">
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
        <p class="label-kicker mb-3 tabular">
          {{ String(i + 1).padStart(2, "0") }}
        </p>
        <h3 class="gb text-[19px] font-semibold text-green-900 leading-snug">
          {{ op.titulo }}
        </h3>
        <p class="text-[14px] text-ink-500 mt-1.5 leading-relaxed">
          {{ op.desc }}
        </p>
      </button>
    </div>
  </div>
</template>
