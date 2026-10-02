<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import AuthShell from "../components/AuthShell.vue";

const router = useRouter();
const route = useRoute();

const codigo = ref("");
const error = ref("");
const cargando = ref(false);

async function entrar() {
  error.value = "";
  if (!codigo.value.trim()) {
    error.value = "Escribe tu código";
    return;
  }
  cargando.value = true;
  try {
    const data = await api.loginCodigo(codigo.value.trim());
    authStore.setSession(data.access_token, data.user);

    if (route.query.redirect) {
      router.push(route.query.redirect);
      return;
    }
    if (!data.user.consentimiento_aceptado) {
      router.push("/consent");
      return;
    }

    // Un código de psicólogo (SAMI-PSI-NN) no responde cuestionarios: entra
    // directo a la bandeja con las últimas evaluaciones del sistema.
    if (data.user.role === "psicologo" || data.user.role === "admin") {
      router.push({ name: "psicologo-evaluaciones" });
      return;
    }

    // Va directo al cuestionario pendiente, sin pasar por el menú.
    let destino = "/menu";
    try {
      const cuestionarios = await api.misCuestionarios();
      const pendiente = cuestionarios.find(
        (c) => c.estado === "pendiente" || c.estado === "en_progreso",
      );
      if (pendiente) destino = { name: "responder", params: { id: pendiente.id } };
    } catch {
      // si falla la consulta, entra igual al menú
    }
    router.push(destino);
  } catch (e) {
    error.value = e.response?.data?.detail || "Código inválido";
  } finally {
    cargando.value = false;
  }
}
</script>

<template>
  <AuthShell
    title="Ingresa con tu código."
    subtitle="Escribe el código que te dio tu profesor o psicóloga."
  >
    <form class="auth-form" @submit.prevent="entrar">
      <div class="auth-field">
        <label>Código</label>
        <input
          v-model="codigo"
          type="text"
          placeholder="SAMI-4TO-07"
          :disabled="cargando"
          autofocus
          autocapitalize="characters"
          class="codigo-input"
        />
      </div>

      <p v-if="error" class="auth-err">{{ error }}</p>

      <button type="submit" class="auth-submit" :disabled="cargando">
        {{ cargando ? "Entrando…" : "Entrar" }}
      </button>
    </form>

    <template #footer>
      <p>
        ¿Tienes cuenta con correo?
        <router-link to="/login">Entra por aquí</router-link>
      </p>
    </template>
  </AuthShell>
</template>

<style scoped>
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.auth-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.auth-field label {
  font-size: 12.5px;
  font-weight: 600;
  color: #56565c;
}
.auth-field input {
  border: 1px solid #e4e4e8;
  border-radius: 8px;
  padding: 10px 12px;
  font-family: inherit;
  font-size: 14px;
  color: #1d1d1f;
  background: #fff;
  outline: none;
  transition:
    border-color 0.12s,
    box-shadow 0.12s;
}
.codigo-input {
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
  text-align: center;
  font-size: 18px !important;
}
.auth-field input::placeholder {
  color: #b0b0b8;
  text-transform: none;
  font-weight: 400;
}
.auth-field input:focus {
  border-color: #0d9488;
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.18);
}
.auth-field input:disabled {
  background: #f5f5f6;
  color: #8e8e95;
}

.auth-err {
  margin: 0;
  font-size: 12.5px;
  color: #c0392b;
}

.auth-submit {
  margin-top: 4px;
  background: #0d9488;
  color: #fff;
  border: 0;
  border-radius: 9px;
  padding: 11px 16px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: filter 0.12s;
}
.auth-submit:hover:not(:disabled) {
  filter: brightness(0.94);
}
.auth-submit:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
</style>
