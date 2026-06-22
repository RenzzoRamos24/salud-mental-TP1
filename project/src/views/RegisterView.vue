<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import AuthShell from "../components/AuthShell.vue";
import { useOAuth } from "../composables/useOAuth";

const router = useRouter();

const nombre = ref("");
const apellido = ref("");
const email = ref("");
const password = ref("");
const password2 = ref("");
const role = ref("estudiante");
const error = ref("");
const cargando = ref(false);
const oauthCargando = ref(null);

const { loginGoogle, loginMicrosoft } = useOAuth();

function destinoTras(user) {
  if (!user.consentimiento_aceptado) return "/consent";
  if (user.role === "psicologo") return "/psicologo";
  if (user.role === "admin") return "/admin";
  return "/menu";
}

async function registrarConGoogle() {
  error.value = "";
  oauthCargando.value = "google";
  try {
    const data = await loginGoogle();
    authStore.setSession(data.access_token, data.user);
    router.push(destinoTras(data.user));
  } catch (e) {
    error.value =
      e.response?.data?.detail || e.message || "No pudimos entrar con Google.";
  } finally {
    oauthCargando.value = null;
  }
}

async function registrarConMicrosoft() {
  error.value = "";
  oauthCargando.value = "microsoft";
  try {
    const data = await loginMicrosoft();
    authStore.setSession(data.access_token, data.user);
    router.push(destinoTras(data.user));
  } catch (e) {
    error.value =
      e.response?.data?.detail ||
      e.message ||
      "No pudimos entrar con Outlook.";
  } finally {
    oauthCargando.value = null;
  }
}

async function registrar() {
  error.value = "";

  if (
    !nombre.value.trim() ||
    !apellido.value.trim() ||
    !email.value.trim() ||
    !password.value
  ) {
    error.value = "Completa todos los campos";
    return;
  }
  if (password.value.length < 8) {
    error.value = "La contraseña debe tener al menos 8 caracteres";
    return;
  }
  if (password.value !== password2.value) {
    error.value = "Las contraseñas no coinciden";
    return;
  }

  cargando.value = true;
  try {
    const data = await api.register({
      email: email.value.trim().toLowerCase(),
      password: password.value,
      nombre: nombre.value.trim(),
      apellido: apellido.value.trim(),
      role: role.value,
    });
    authStore.setSession(data.access_token, data.user);
    router.push("/consent");
  } catch (e) {
    const detail = e.response?.data?.detail;
    if (Array.isArray(detail)) {
      error.value = detail[0]?.msg || "Error de validación";
    } else {
      error.value = detail || "Error al registrarse";
    }
  } finally {
    cargando.value = false;
  }
}
</script>

<template>
  <AuthShell
    title="Crea tu cuenta."
    subtitle="Cuéntanos quién eres para empezar."
  >
    <!-- ─── OAuth ─── -->
    <div class="space-y-2.5">
      <button
        type="button"
        @click="registrarConGoogle"
        :disabled="cargando || oauthCargando !== null"
        class="oauth-btn"
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
        <span>{{
          oauthCargando === "google"
            ? "Conectando…"
            : "Continuar con Google"
        }}</span>
      </button>
      <button
        type="button"
        @click="registrarConMicrosoft"
        :disabled="cargando || oauthCargando !== null"
        class="oauth-btn"
      >
        <svg width="18" height="18" viewBox="0 0 23 23" aria-hidden="true">
          <rect x="1" y="1" width="10" height="10" fill="#F35325" />
          <rect x="12" y="1" width="10" height="10" fill="#81BC06" />
          <rect x="1" y="12" width="10" height="10" fill="#05A6F0" />
          <rect x="12" y="12" width="10" height="10" fill="#FFBA08" />
        </svg>
        <span>{{
          oauthCargando === "microsoft"
            ? "Conectando…"
            : "Continuar con Outlook"
        }}</span>
      </button>
    </div>

    <div class="my-5 flex items-center gap-3 text-[12px] text-ink-400">
      <div class="flex-1 h-px" style="background: #dde4d6"></div>
      <span>o regístrate con tu correo</span>
      <div class="flex-1 h-px" style="background: #dde4d6"></div>
    </div>

    <form @submit.prevent="registrar" class="space-y-4">
      <!-- Selector de rol -->
      <div>
        <label class="label">¿Quién eres?</label>
        <div class="grid grid-cols-2 gap-3">
          <label
            :class="[
              'cursor-pointer flex flex-col items-center gap-1 p-4 rounded-xl border-2 transition',
              role === 'estudiante'
                ? 'border-green-400 bg-green-50 shadow-soft'
                : 'border-ink-200 bg-white hover:border-green-200',
            ]"
          >
            <input
              v-model="role"
              type="radio"
              value="estudiante"
              class="sr-only"
              :disabled="cargando"
            />
            <span class="text-sm font-semibold text-ink-900">Estudiante</span>
          </label>
          <label
            :class="[
              'cursor-pointer flex flex-col items-center gap-1 p-4 rounded-xl border-2 transition',
              role === 'psicologo'
                ? 'border-green-400 bg-green-50 shadow-soft'
                : 'border-ink-200 bg-white hover:border-green-200',
            ]"
          >
            <input
              v-model="role"
              type="radio"
              value="psicologo"
              class="sr-only"
              :disabled="cargando"
            />
            <span class="text-sm font-semibold text-ink-900">Psicólogo/a</span>
          </label>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label">Nombre</label>
          <input
            v-model="nombre"
            type="text"
            :disabled="cargando"
            class="input"
          />
        </div>
        <div>
          <label class="label">Apellido</label>
          <input
            v-model="apellido"
            type="text"
            :disabled="cargando"
            class="input"
          />
        </div>
      </div>

      <div>
        <label class="label">Correo institucional</label>
        <input
          v-model="email"
          type="email"
          :disabled="cargando"
          placeholder="tucorreo@upc.edu.pe"
          class="input"
        />
      </div>

      <div>
        <label class="label">Contraseña</label>
        <input
          v-model="password"
          type="password"
          :disabled="cargando"
          minlength="8"
          placeholder="••••••••"
          class="input"
        />
        <p class="field-hint">Mínimo 8 caracteres</p>
      </div>

      <div>
        <label class="label">Confirmar contraseña</label>
        <input
          v-model="password2"
          type="password"
          :disabled="cargando"
          placeholder="••••••••"
          class="input"
        />
      </div>

      <p v-if="error" class="field-error">{{ error }}</p>

      <button
        type="submit"
        :disabled="cargando || oauthCargando !== null"
        class="btn-primary w-full mt-2"
      >
        {{ cargando ? "Creando…" : "Crear cuenta" }}
      </button>
    </form>

    <template #footer>
      <p class="text-sm text-ink-500">
        ¿Ya tienes cuenta?
        <router-link
          to="/login"
          class="text-green-700 hover:text-green-800 font-semibold"
          >Inicia sesión</router-link
        >
      </p>
    </template>
  </AuthShell>
</template>

<style scoped>
.oauth-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 11px 16px;
  background: #fff;
  color: #27352b;
  border-radius: 12px;
  font-family: "Hanken Grotesk", system-ui, sans-serif;
  font-size: 14px;
  font-weight: 600;
  box-shadow: inset 0 0 0 1px #dde4d6;
  transition: 0.13s;
  cursor: pointer;
}
.oauth-btn:hover:not(:disabled) {
  box-shadow: inset 0 0 0 1.5px #4c6b53;
  transform: translateY(-1px);
}
.oauth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
