<script setup>
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import AuthShell from "../components/AuthShell.vue";
import { useOAuth } from "../composables/useOAuth";

const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");
const error = ref("");
const cargando = ref(false);
const oauthCargando = ref(null); // "google" | "microsoft" | null

const { config: oauthConfig, loginGoogle, loginMicrosoft } = useOAuth();

function destinoTras(user) {
  if (!user.consentimiento_aceptado) return "/consent";
  if (user.role === "psicologo") return "/psicologo";
  if (user.role === "admin") return "/admin";
  return "/menu";
}

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
    router.push(route.query.redirect || destinoTras(data.user));
  } catch (e) {
    error.value = e.response?.data?.detail || "Error iniciando sesión";
  } finally {
    cargando.value = false;
  }
}

async function loginConGoogle() {
  error.value = "";
  oauthCargando.value = "google";
  try {
    const data = await loginGoogle();
    authStore.setSession(data.access_token, data.user);
    router.push(route.query.redirect || destinoTras(data.user));
  } catch (e) {
    error.value =
      e.response?.data?.detail || e.message || "No pudimos entrar con Google.";
  } finally {
    oauthCargando.value = null;
  }
}

async function loginConMicrosoft() {
  error.value = "";
  oauthCargando.value = "microsoft";
  try {
    const data = await loginMicrosoft();
    authStore.setSession(data.access_token, data.user);
    router.push(route.query.redirect || destinoTras(data.user));
  } catch (e) {
    error.value =
      e.response?.data?.detail || e.message || "No pudimos entrar con Outlook.";
  } finally {
    oauthCargando.value = null;
  }
}
</script>

<template>
  <AuthShell title="Hola de nuevo." subtitle="Entra para escribir.">
    <!-- ─── OAuth ─── -->
    <div class="oauth-stack">
      <button
        type="button"
        class="oauth-btn"
        :disabled="cargando || oauthCargando !== null"
        @click="loginConGoogle"
      >
        <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
          <path
            fill="#FFC107"
            d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"
          />
          <path
            fill="#FF3D00"
            d="M6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 16.318 4 9.656 8.337 6.306 14.691z"
          />
          <path
            fill="#4CAF50"
            d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238C29.211 35.091 26.715 36 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"
          />
          <path
            fill="#1976D2"
            d="M43.611 20.083H42V20H24v8h11.303c-.792 2.237-2.231 4.166-4.087 5.571.001-.001.002-.001.003-.002l6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"
          />
        </svg>
        <span>
          {{
            oauthCargando === "google" ? "Conectando…" : "Continuar con Google"
          }}
        </span>
      </button>

      <button
        type="button"
        class="oauth-btn"
        :disabled="cargando || oauthCargando !== null"
        @click="loginConMicrosoft"
      >
        <svg width="18" height="18" viewBox="0 0 23 23" aria-hidden="true">
          <rect x="1" y="1" width="10" height="10" fill="#F35325" />
          <rect x="12" y="1" width="10" height="10" fill="#81BC06" />
          <rect x="1" y="12" width="10" height="10" fill="#05A6F0" />
          <rect x="12" y="12" width="10" height="10" fill="#FFBA08" />
        </svg>
        <span>
          {{
            oauthCargando === "microsoft"
              ? "Conectando…"
              : "Continuar con Outlook"
          }}
        </span>
      </button>
    </div>

    <div class="auth-divider">
      <span class="line"></span>
      <span class="lbl">o con tu correo</span>
      <span class="line"></span>
    </div>

    <!-- ─── Formulario clásico ─── -->
    <form class="auth-form" @submit.prevent="entrar">
      <div class="auth-field">
        <label>Correo</label>
        <input
          v-model="email"
          type="email"
          placeholder="tucorreo@colegio.edu.pe"
          :disabled="cargando || oauthCargando !== null"
          autofocus
        />
      </div>
      <div class="auth-field">
        <label>Contraseña</label>
        <input
          v-model="password"
          type="password"
          placeholder="••••••••"
          :disabled="cargando || oauthCargando !== null"
        />
      </div>

      <p v-if="error" class="auth-err">{{ error }}</p>

      <button
        type="submit"
        class="auth-submit"
        :disabled="cargando || oauthCargando !== null"
      >
        {{ cargando ? "Entrando…" : "Entrar" }}
      </button>

      <p class="auth-link-row">
        <router-link to="/forgot-password">¿Olvidaste tu contraseña?</router-link>
      </p>
    </form>

    <template #footer>
      <p>
        ¿No tienes cuenta?
        <router-link to="/register">Regístrate</router-link>
      </p>
    </template>
  </AuthShell>
</template>

<style scoped>
.oauth-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.oauth-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 11px 16px;
  background: #fff;
  color: #1d1d1f;
  border: 1px solid #e4e4e8;
  border-radius: 9px;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 500;
  cursor: pointer;
  transition: 0.13s;
}
.oauth-btn:hover:not(:disabled) {
  border-color: #8e8e95;
  background: #fafafb;
}
.oauth-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.auth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
  font-size: 12px;
  color: #8e8e95;
}
.auth-divider .line {
  flex: 1;
  height: 1px;
  background: #ececef;
}

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
.auth-field input::placeholder {
  color: #b0b0b8;
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

.auth-link-row {
  text-align: center;
  margin: 4px 0 0;
  font-size: 13px;
}
.auth-link-row a {
  color: #56565c;
  text-decoration: none;
}
.auth-link-row a:hover {
  color: #0d9488;
}
</style>
