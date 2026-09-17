<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppTopbar from "./components/AppTopbar.vue";
import AppShellPsico from "./components/AppShellPsico.vue";
import SOSButton from "./components/SOSButton.vue";
import { authStore } from "./store/auth";

const route = useRoute();

const STUDENT_ROUTES = [
  "menu",
  "mis-cuestionarios",
  "responder",
  "recursos",
  "perfil",
  "encuesta",
];

const PSICO_ROUTES = [
  "psicologo",
  "psicologo-estudiantes",
  "psicologo-alertas",
  "psicologo-estudiante",
  "psicologo-banco",
  "psicologo-bloque-custom",
  "psicologo-plantillas",
  "asignar-cuestionario",
  "psicologo-resultado",
  "psicologo-sos",
  "psicologo-citas",
  "psicologo-firma",
  "perfil",
  "recursos",
];

const esEstudianteSami = computed(() => {
  if (!authStore.isAuthenticated.value) return false;
  if (authStore.rol.value !== "estudiante") return false;
  if (!authStore.consentimientoAceptado.value) return false;
  return STUDENT_ROUTES.includes(route.name || "");
});

const esPsicoSami = computed(() => {
  if (!authStore.isAuthenticated.value) return false;
  if (authStore.rol.value !== "psicologo") return false;
  if (!authStore.consentimientoAceptado.value) return false;
  return PSICO_ROUTES.includes(route.name || "");
});

const samiMode = computed(
  () => esEstudianteSami.value || esPsicoSami.value,
);

// El alumno mantiene el shell antiguo (sami-mode). La psicóloga usa AppShellPsico.
const usarShellPsico = computed(() => esPsicoSami.value);

// `/menu` (StudentHomeView) trae su propio shell con sidebar y cabecera. Si
// además pintáramos AppTopbar, el alumno vería dos navegaciones apiladas con
// items distintos. En esa ruta la barra horizontal se omite.
const RUTAS_CON_SHELL_PROPIO = ["menu"];
const ocultarTopbar = computed(() =>
  RUTAS_CON_SHELL_PROPIO.includes((route.name || "").toString()),
);

import { watchEffect, onUnmounted } from "vue";
watchEffect(() => {
  document.body.classList.toggle(
    "sami-mode",
    esEstudianteSami.value && !usarShellPsico.value,
  );
});
onUnmounted(() => {
  document.body.classList.remove("sami-mode");
});

const mostrarSOS = computed(() => {
  if (!authStore.isAuthenticated.value) return false;
  if (!authStore.consentimientoAceptado.value) return false;
  if (authStore.rol.value !== "estudiante") return false;
  const ruta = (route.name || "").toString();
  if (ruta === "login" || ruta === "register") return false;
  return true;
});
</script>

<template>
  <!-- Shell de la psicóloga: sidebar + topbar + main -->
  <AppShellPsico v-if="usarShellPsico">
    <router-view />
  </AppShellPsico>

  <!-- Resto: estudiante / admin / login con topbar horizontal -->
  <div v-else class="min-h-full" :class="{ 'sami-root': samiMode }">
    <AppTopbar v-if="!ocultarTopbar" />
    <router-view />
    <SOSButton v-if="mostrarSOS" />
  </div>
</template>

<style>
.sami-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
body.sami-mode .topbar {
  position: sticky;
  top: 0;
  z-index: 50;
}
</style>
