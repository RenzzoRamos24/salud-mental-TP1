<script setup>
import { computed, watchEffect, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import AppTopbar from "./components/AppTopbar.vue";
import { authStore } from "./store/auth";

const route = useRoute();

const STUDENT_ROUTES = [
  "menu",
  "diario",
  "mi-historial",
  "recursos",
  "perfil",
];
const PSICO_ROUTES = [
  "psicologo",
  "psicologo-estudiantes",
  "psicologo-alertas",
  "psicologo-estudiante",
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

const samiMode = computed(() => esEstudianteSami.value || esPsicoSami.value);

watchEffect(() => {
  document.body.classList.toggle("sami-mode", samiMode.value);
});

onUnmounted(() => {
  document.body.classList.remove("sami-mode");
});
</script>

<template>
  <div class="min-h-full" :class="{ 'sami-root': samiMode }">
    <AppTopbar />
    <router-view />
  </div>
</template>

<style>
.sami-root {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
</style>
