<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import AuthShell from "../components/AuthShell.vue";

const router = useRouter();

const nombre = ref("");
const apellido = ref("");
const email = ref("");
const password = ref("");
const password2 = ref("");
const role = ref("estudiante");
const error = ref("");
const cargando = ref(false);

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
    title="Crea tu cuenta"
    subtitle="Cuéntanos quién eres para empezar."
  >
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
        :disabled="cargando"
        class="btn-primary w-full py-3 text-base"
      >
        {{ cargando ? "Creando…" : "Crear cuenta" }}
      </button>
    </form>

    <template #footer>
      <p class="text-sm text-ink-500">
        ¿Ya tienes cuenta?
        <router-link
          to="/login"
          class="text-green-600 hover:text-green-700 font-semibold"
          >Inicia sesión</router-link
        >
      </p>
    </template>
  </AuthShell>
</template>
