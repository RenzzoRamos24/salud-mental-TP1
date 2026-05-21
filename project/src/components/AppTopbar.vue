<script setup>
import { computed } from "vue";
import { authStore } from "../store/auth";
import { useRouter, useRoute } from "vue-router";
import { api } from "../api";

const router = useRouter();
const route = useRoute();

const enConsent = computed(() => route.name === "consent");

const inicial = computed(() => {
  const u = authStore.state.user;
  if (!u) return "·";
  return (u.nombre || "·").charAt(0).toUpperCase();
});

const rolLabel = computed(() => {
  const r = authStore.rol.value;
  if (r === "estudiante") return "estudiante";
  if (r === "psicologo") return "psicólogo/a";
  if (r === "admin") return "administrador";
  return r || "";
});

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
  <header
    v-if="authStore.isAuthenticated.value && !enConsent"
    class="topbar-pastel"
  >
    <div
      class="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-6"
    >
      <button
        @click="irAMenu"
        class="sami-wordmark hover:opacity-70 transition"
      >
        Sami <span class="accent">— Salud Mental Juvenil</span>
      </button>

      <div class="flex items-center gap-4">
        <router-link to="/perfil" class="user-pill hover:bg-ink-100 transition">
          <span class="avatar-sm">{{ inicial }}</span>
          <span class="font-medium text-ink-900">{{
            authStore.state.user?.nombre
          }}</span>
          <span class="text-ink-500">· {{ rolLabel }}</span>
        </router-link>
        <button
          @click="logout"
          class="text-sm text-ink-600 hover:text-ink-900 transition"
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  </header>
</template>
