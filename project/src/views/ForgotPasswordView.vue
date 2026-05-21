<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import AuthShell from "../components/AuthShell.vue";

const router = useRouter();
const email = ref("");
const mensaje = ref("");
const error = ref("");
const cargando = ref(false);

async function enviar() {
  error.value = "";
  mensaje.value = "";
  if (!email.value.trim()) {
    error.value = "Ingresa tu correo";
    return;
  }
  cargando.value = true;
  try {
    const data = await api.forgotPassword(email.value.trim());
    mensaje.value = data.mensaje;
    setTimeout(() => {
      router.push({ name: "reset", query: { email: email.value.trim() } });
    }, 1500);
  } catch (e) {
    error.value = e.response?.data?.detail || "Error enviando solicitud";
  } finally {
    cargando.value = false;
  }
}
</script>

<template>
  <AuthShell
    title="¿Olvidaste tu contraseña?"
    subtitle="Te mandamos un código de seis dígitos para que la cambies."
  >
    <form @submit.prevent="enviar" class="space-y-4">
      <div>
        <label class="label">Correo institucional</label>
        <input
          v-model="email"
          type="email"
          :disabled="cargando"
          placeholder="tucorreo@upc.edu.pe"
          class="input-lg"
          autofocus
        />
      </div>

      <p v-if="error" class="field-error">{{ error }}</p>
      <p v-if="mensaje" class="banner-success">{{ mensaje }}</p>

      <button
        type="submit"
        :disabled="cargando"
        class="btn-primary w-full py-3 text-base"
      >
        {{ cargando ? "Enviando…" : "Enviar código" }}
      </button>
    </form>

    <template #footer>
      <router-link
        to="/login"
        class="text-sm text-green-600 hover:text-green-700 font-semibold"
      >
        Volver al inicio de sesión
      </router-link>
    </template>
  </AuthShell>
</template>
