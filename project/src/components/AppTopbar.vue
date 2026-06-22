<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { authStore } from "../store/auth";
import { useRouter, useRoute } from "vue-router";
import { api } from "../api";
import { buildAlerts } from "../composables/samiPsicoHelpers";

const router = useRouter();
const route = useRoute();

const enConsent = computed(() => route.name === "consent");
const rol = computed(() => authStore.rol.value);
const esEstudiante = computed(() => rol.value === "estudiante");
const esPsicologo = computed(() => rol.value === "psicologo");

const inicial = computed(() => {
  const u = authStore.state.user;
  if (!u) return "·";
  return (u.nombre || "·").charAt(0).toUpperCase();
});

const iniciales = computed(() => {
  const u = authStore.state.user;
  if (!u) return "··";
  const n = (u.nombre || "·").charAt(0);
  const a = (u.apellido || "").charAt(0);
  return (n + a).toUpperCase();
});

const primerNombre = computed(() => {
  const n = (authStore.state.user?.nombre || "").trim();
  return n.split(" ")[0] || "";
});

const rolLabel = computed(() => {
  const r = rol.value;
  if (r === "estudiante") return "estudiante";
  if (r === "psicologo") return "psicóloga";
  if (r === "admin") return "admin";
  return r || "";
});

const seccion = computed(() => {
  const path = route?.path || "";
  if (path.startsWith("/diario")) return "Diario";
  if (path.startsWith("/chat")) return "Chat";
  if (path.startsWith("/historial")) return "Historial";
  if (path.startsWith("/perfil")) return "Cuenta";
  if (path.startsWith("/recursos")) return "Recursos";
  if (path.startsWith("/psicologo")) return "Panel";
  if (path.startsWith("/admin")) return "Panel";
  if (path.startsWith("/resultados")) return "Resultados";
  return "";
});

// ─── Nav para estudiante ──────────────────────────────────────────────
const navSami = [
  { id: "inicio", label: "Inicio", to: "/menu" },
  { id: "diario", label: "Diario", to: "/diario" },
  { id: "historial", label: "Mi historial", to: "/mi-historial" },
  { id: "recursos", label: "Recursos", to: "/recursos" },
];

const navActivoEst = computed(() => {
  const p = route?.path || "";
  if (p.startsWith("/menu")) return "inicio";
  if (p.startsWith("/diario")) return "diario";
  if (p.startsWith("/mi-historial")) return "historial";
  if (p.startsWith("/recursos")) return "recursos";
  return "";
});

// ─── Nav para psicólogo ──────────────────────────────────────────────
const navClinico = [
  { id: "panel", label: "Panel", to: "/psicologo" },
  { id: "estudiantes", label: "Estudiantes", to: "/psicologo/estudiantes" },
  { id: "alertas", label: "Alertas", to: "/psicologo/alertas" },
];

const navActivoPsi = computed(() => {
  const p = route?.path || "";
  if (p.startsWith("/psicologo/estudiantes")) return "estudiantes";
  if (p.startsWith("/psicologo/alertas")) return "alertas";
  if (p.startsWith("/psicologo/estudiante/")) return ""; // ficha = sin tab activa
  if (p.startsWith("/psicologo")) return "panel";
  return "";
});

const alertasCrit = ref(0);

async function refrescarAlertas() {
  if (!esPsicologo.value) return;
  try {
    const data = await api.resumenEstudiantes();
    const list = buildAlerts(data || []);
    alertasCrit.value = list.filter((a) => a.tipo === "crit").length;
  } catch (_) {
    alertasCrit.value = 0;
  }
}

onMounted(refrescarAlertas);
watch(esPsicologo, refrescarAlertas);

async function logout() {
  await api.logout();
  authStore.clear();
  router.push({ name: "login" });
}

function irAMenu() {
  router.push("/menu");
}
</script>

<template>
  <!-- ════════════ Estudiante (Sami) ════════════ -->
  <header
    v-if="authStore.isAuthenticated.value && !enConsent && esEstudiante"
    class="topbar"
  >
    <button class="wordmark" type="button" @click="router.push('/menu')">
      <img src="/sentir-isotipo.svg" class="topbar-logo" alt="SENTIR" />
      <span>Sami</span>
    </button>
    <nav class="topnav">
      <button
        v-for="n in navSami"
        :key="n.id"
        type="button"
        :class="navActivoEst === n.id ? 'on' : ''"
        @click="router.push(n.to)"
      >
        {{ n.label }}
      </button>
    </nav>
    <span class="spacer"></span>
    <button
      class="userchip"
      :class="route.path.startsWith('/perfil') ? 'on' : ''"
      type="button"
      title="Perfil"
      @click="router.push('/perfil')"
    >
      <span class="avatar">{{ iniciales }}</span>
      <span>{{ primerNombre || "—" }}</span>
    </button>
    <button class="signout" type="button" @click="logout">Cerrar sesión</button>
  </header>

  <!-- ════════════ Psicóloga (Sami · Clínico) ════════════ -->
  <header
    v-else-if="authStore.isAuthenticated.value && !enConsent && esPsicologo"
    class="topbar"
  >
    <button class="wordmark" type="button" @click="router.push('/psicologo')">
      <img src="/sentir-isotipo.svg" class="topbar-logo" alt="SENTIR" />
      <span>Sami <span class="sub">· Clínico</span></span>
    </button>
    <nav class="topnav">
      <button
        v-for="n in navClinico"
        :key="n.id"
        type="button"
        :class="navActivoPsi === n.id ? 'on' : ''"
        @click="router.push(n.to)"
      >
        {{ n.label
        }}<span v-if="n.id === 'alertas' && alertasCrit > 0" class="nav-badge">
          {{ alertasCrit }}
        </span>
      </button>
    </nav>
    <span class="spacer"></span>
    <button
      class="userchip"
      type="button"
      title="Perfil"
      @click="router.push('/perfil')"
    >
      <span class="avatar" style="background: var(--accent)">{{ iniciales }}</span>
      <span>{{ primerNombre || "—" }}</span>
    </button>
    <button class="signout" type="button" @click="logout">Cerrar sesión</button>
  </header>

  <!-- ════════════ Admin / otros ════════════ -->
  <header
    v-else-if="authStore.isAuthenticated.value && !enConsent"
    class="topbar-pastel"
  >
    <div
      class="max-w-6xl mx-auto px-6 sm:px-10 h-[68px] flex items-center justify-between gap-6"
    >
      <button
        @click="irAMenu"
        class="sami-wordmark hover:opacity-80 transition flex items-center gap-2.5"
        type="button"
      >
        <img src="/sentir-isotipo.svg" class="topbar-logo" alt="SENTIR" />
        Sami
        <span v-if="seccion" class="accent">{{ seccion }}</span>
      </button>

      <div class="flex items-center gap-5">
        <router-link to="/perfil" class="user-pill hover:bg-green-50 transition">
          <span class="avatar-sm">{{ inicial }}</span>
          <span class="whitespace-nowrap"
            >{{ primerNombre || "—" }}
            <span class="font-medium text-ink-400"
              >· {{ rolLabel }}</span
            ></span
          >
        </router-link>
        <button
          @click="logout"
          class="text-[13px] font-medium text-ink-400 hover:text-ink-700 transition"
          type="button"
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  </header>
</template>
