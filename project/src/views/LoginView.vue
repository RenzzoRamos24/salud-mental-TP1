<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import AuthShell from "../components/AuthShell.vue";

const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");
const error = ref("");
const cargando = ref(false);

async function entrar() {
  error.value = "";
  if (!email.value.trim() || !password.value) {
    error.value = "Completa todos los campos";
    return;
  }
  cargando.value = true;
  try {
    const data = await api.login(email.value.trim(), password.value);
    authStore.setSession(data.access_token, data.user);
    const destino = data.user.consentimiento_aceptado ? "/menu" : "/consent";
    router.push(route.query.redirect || destino);
  } catch (e) {
    error.value = e.response?.data?.detail || "Error iniciando sesión";
  } finally {
    cargando.value = false;
  }
}
</script>

<template>
  <AuthShell title="Hola de nuevo" subtitle="Nos alegra verte por aquí">
    <form @submit.prevent="entrar" class="space-y-4">
      <div>
        <label class="label">Correo institucional</label>
        <input
          v-model="email"
          type="email"
          placeholder="estudiante@micolegio.edu.pe"
          class="input"
          :disabled="cargando"
          autofocus
        />
      </div>
      <div>
        <label class="label">Contraseña</label>
        <input
          v-model="password"
          type="password"
          placeholder="••••••••"
          class="input"
          :disabled="cargando"
        />
      </div>

      <p v-if="error" class="field-error">{{ error }}</p>

      <button
        type="submit"
        :disabled="cargando"
        class="btn-primary w-full py-3 text-base mt-2"
      >
        {{ cargando ? "Ingresando…" : "Entrar" }}
      </button>

      <p class="text-center text-sm pt-2">
        <router-link
          to="/forgot-password"
          class="text-ink-600 hover:text-ink-900 transition"
        >
          ¿Olvidaste tu contraseña?
        </router-link>
      </p>
    </form>

    <template #footer>
      <p class="text-sm text-ink-600">
        ¿No tienes cuenta?
        <router-link
          to="/register"
          class="text-green-700 hover:text-green-800 font-semibold"
        >
          Regístrate aquí
        </router-link>
      </p>
    </template>
  </AuthShell>
</template>
