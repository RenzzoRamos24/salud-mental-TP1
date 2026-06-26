<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import PageHeader from "../components/PageHeader.vue";

const router = useRouter();
const rol = computed(() => authStore.rol.value);
const esEstudiante = computed(() => rol.value === "estudiante");

const perfil = reactive({
  nombre: authStore.state.user?.nombre || "",
  apellido: authStore.state.user?.apellido || "",
});
const guardandoPerfil = ref(false);
const mensajePerfil = ref("");
const errorPerfil = ref("");

const iniciales = computed(() => {
  const n = (perfil.nombre || "?").charAt(0);
  const a = (perfil.apellido || "").charAt(0);
  return (n + a).toUpperCase();
});

// ─── Recordatorio diario (solo cliente, localStorage) ─────────────────
const REM_KEY = "sami-reminder-v1";
const recordatorio = ref(localStorage.getItem(REM_KEY) || "21:00");

const pwd = reactive({ actual: "", nueva: "", confirmar: "" });
const cambiandoPwd = ref(false);
const mensajePwd = ref("");
const errorPwd = ref("");

const eliminar = reactive({ abierto: false, password: "", confirmacion: "" });
const eliminando = ref(false);
const errorEliminar = ref("");

const toast = ref("");
let toastTimer = null;

function showToast(msg) {
  toast.value = msg;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.value = ""), 2400);
}

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
});

async function guardarPerfil() {
  errorPerfil.value = "";
  mensajePerfil.value = "";
  if (!perfil.nombre.trim() || !perfil.apellido.trim()) {
    errorPerfil.value = "Completa nombre y apellido";
    return;
  }
  guardandoPerfil.value = true;
  try {
    const u = await api.actualizarPerfil(
      perfil.nombre.trim(),
      perfil.apellido.trim(),
    );
    authStore.setUser(u);
    localStorage.setItem(REM_KEY, recordatorio.value);
    if (esEstudiante.value) showToast("Cambios guardados");
    else mensajePerfil.value = "Datos actualizados correctamente";
  } catch (e) {
    errorPerfil.value = e.response?.data?.detail || "Error al guardar";
  } finally {
    guardandoPerfil.value = false;
  }
}

async function cambiarPassword() {
  errorPwd.value = "";
  mensajePwd.value = "";
  if (!pwd.actual || !pwd.nueva) {
    errorPwd.value = "Completa ambos campos";
    return;
  }
  if (pwd.nueva.length < 8) {
    errorPwd.value = "La nueva contraseña debe tener al menos 8 caracteres";
    return;
  }
  if (pwd.nueva !== pwd.confirmar) {
    errorPwd.value = "Las contraseñas no coinciden";
    return;
  }
  cambiandoPwd.value = true;
  try {
    const r = await api.cambiarPassword(pwd.actual, pwd.nueva);
    if (esEstudiante.value) showToast("Contraseña actualizada");
    else mensajePwd.value = r.mensaje;
    pwd.actual = pwd.nueva = pwd.confirmar = "";
  } catch (e) {
    errorPwd.value = e.response?.data?.detail || "Error al cambiar contraseña";
  } finally {
    cambiandoPwd.value = false;
  }
}

async function eliminarCuenta() {
  errorEliminar.value = "";
  if (eliminar.confirmacion !== "ELIMINAR") {
    errorEliminar.value = "Escribe ELIMINAR en mayúsculas para confirmar";
    return;
  }
  if (!eliminar.password) {
    errorEliminar.value = "Ingresa tu contraseña";
    return;
  }
  eliminando.value = true;
  try {
    await api.eliminarCuenta(eliminar.password, eliminar.confirmacion);
    authStore.clear();
    alert("Tu cuenta fue borrada. Te llevamos al inicio.");
    router.push("/login");
  } catch (e) {
    errorEliminar.value =
      e.response?.data?.detail || "Error al eliminar cuenta";
  } finally {
    eliminando.value = false;
  }
}

const rolLabel = computed(() => {
  const r = rol.value;
  if (r === "estudiante") return "Estudiante";
  if (r === "psicologo") return "Psicóloga";
  if (r === "admin") return "Administrador";
  return r;
});
</script>

<template>
  <!-- ════════════════════════════════════════════════════════════════ -->
  <!-- ESTUDIANTE — Sami                                              -->
  <!-- ════════════════════════════════════════════════════════════════ -->
  <div v-if="esEstudiante" class="page" data-screen-label="Perfil">
    <div class="page-inner" style="max-width: 560px">
      <h1>Perfil</h1>
      <p class="sub">Tus datos y tu cuenta.</p>

      <!-- Datos -->
      <form
        class="card"
        style="padding: 24px; margin-bottom: 14px"
        @submit.prevent="guardarPerfil"
      >
        <div
          style="font-size: 13.5px; font-weight: 700; margin-bottom: 16px"
        >
          Datos personales
        </div>
        <div class="field">
          <label>Nombre</label>
          <input v-model="perfil.nombre" type="text" :disabled="guardandoPerfil" />
        </div>
        <div class="field">
          <label>Apellido</label>
          <input
            v-model="perfil.apellido"
            type="text"
            :disabled="guardandoPerfil"
          />
        </div>
        <div class="field">
          <label>Email institucional</label>
          <input :value="authStore.state.user?.email" disabled />
        </div>
        <div class="field" style="margin-bottom: 20px">
          <label>Recordatorio diario</label>
          <select v-model="recordatorio">
            <option value="off">Sin recordatorio</option>
            <option value="08:00">08:00 — a la mañana</option>
            <option value="14:00">14:00 — después de almorzar</option>
            <option value="21:00">21:00 — a la noche</option>
          </select>
        </div>
        <p v-if="errorPerfil" style="font-size: 12.5px; color: #d12c2c; margin: -8px 0 12px">
          {{ errorPerfil }}
        </p>
        <button class="btn primary" type="submit" :disabled="guardandoPerfil">
          {{ guardandoPerfil ? "Guardando…" : "Guardar cambios" }}
        </button>
      </form>

      <!-- Contraseña -->
      <form
        class="card"
        style="padding: 24px; margin-bottom: 14px"
        @submit.prevent="cambiarPassword"
      >
        <div
          style="font-size: 13.5px; font-weight: 700; margin-bottom: 16px"
        >
          Contraseña
        </div>
        <div class="field">
          <label>Contraseña actual</label>
          <input
            v-model="pwd.actual"
            type="password"
            placeholder="••••••••"
            :disabled="cambiandoPwd"
          />
        </div>
        <div class="field">
          <label>Contraseña nueva</label>
          <input
            v-model="pwd.nueva"
            type="password"
            placeholder="Mínimo 8 caracteres"
            :disabled="cambiandoPwd"
          />
        </div>
        <div class="field" style="margin-bottom: 20px">
          <label>Repetila</label>
          <input
            v-model="pwd.confirmar"
            type="password"
            placeholder="Una vez más"
            :disabled="cambiandoPwd"
          />
        </div>
        <p v-if="errorPwd" style="font-size: 12.5px; color: #d12c2c; margin: -8px 0 12px">
          {{ errorPwd }}
        </p>
        <button class="btn" type="submit" :disabled="cambiandoPwd">
          {{ cambiandoPwd ? "Guardando…" : "Cambiar contraseña" }}
        </button>
      </form>

      <!-- Borrar cuenta -->
      <div class="card" style="padding: 24px; border-color: #f0d2d2">
        <div style="font-size: 13.5px; font-weight: 700; margin-bottom: 6px">
          Borrar mi cuenta
        </div>
        <p
          style="
            margin: 0 0 16px;
            font-size: 12.5px;
            color: var(--ink-2);
            line-height: 1.55;
          "
        >
          Se borra todo: entradas, ciclos y encuestas. No hay manera de
          recuperarlo, ni siquiera escribiéndonos.
        </p>

        <template v-if="!eliminar.abierto">
          <button class="btn danger" type="button" @click="eliminar.abierto = true">
            Borrar cuenta
          </button>
        </template>
        <template v-else>
          <div class="field">
            <label>Para confirmar, escribe ELIMINAR</label>
            <input
              v-model="eliminar.confirmacion"
              type="text"
              placeholder="ELIMINAR"
              style="text-transform: uppercase"
            />
          </div>
          <div class="field">
            <label>Tu contraseña</label>
            <input v-model="eliminar.password" type="password" />
          </div>
          <p
            v-if="errorEliminar"
            style="font-size: 12.5px; color: #d12c2c; margin: -8px 0 12px"
          >
            {{ errorEliminar }}
          </p>
          <div style="display: flex; gap: 8px">
            <button
              class="btn danger"
              type="button"
              :disabled="eliminando"
              @click="eliminarCuenta"
            >
              {{ eliminando ? "Eliminando…" : "Sí, borrar todo" }}
            </button>
            <button
              class="btn"
              type="button"
              :disabled="eliminando"
              @click="
                eliminar.abierto = false;
                eliminar.password = '';
                eliminar.confirmacion = '';
                errorEliminar = '';
              "
            >
              Mejor no
            </button>
          </div>
        </template>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </Teleport>
  </div>

  <!-- ════════════════════════════════════════════════════════════════ -->
  <!-- PSICÓLOGO / ADMIN — vista original                              -->
  <!-- ════════════════════════════════════════════════════════════════ -->
  <div v-else class="page-shell">
    <PageHeader
      title="Tu"
      accent="cuenta"
      subtitle="Tus datos, contraseña y la opción de borrar tu cuenta."
    >
      <template #aside>
        <div class="flex items-center gap-3">
          <div class="avatar-lg text-lg">{{ iniciales }}</div>
          <div>
            <p class="dsm5-tag">{{ rolLabel }}</p>
          </div>
        </div>
      </template>
    </PageHeader>

    <section class="card p-6 mb-6 fade-in-up">
      <h2 class="section-title">Tus datos</h2>
      <form @submit.prevent="guardarPerfil" class="space-y-4 mt-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label">Nombre</label>
            <input
              v-model="perfil.nombre"
              type="text"
              :disabled="guardandoPerfil"
              class="input"
            />
          </div>
          <div>
            <label class="label">Apellido</label>
            <input
              v-model="perfil.apellido"
              type="text"
              :disabled="guardandoPerfil"
              class="input"
            />
          </div>
        </div>
        <div>
          <label class="label">Correo institucional</label>
          <input
            :value="authStore.state.user?.email"
            disabled
            class="input bg-white text-ink-500"
          />
          <p class="field-hint">El correo no se puede cambiar.</p>
        </div>
        <p v-if="errorPerfil" class="field-error">{{ errorPerfil }}</p>
        <p v-if="mensajePerfil" class="banner-success">{{ mensajePerfil }}</p>
        <button type="submit" :disabled="guardandoPerfil" class="btn-primary">
          {{ guardandoPerfil ? "Guardando…" : "Guardar" }}
        </button>
      </form>
    </section>

    <section class="card p-6 mb-6 fade-in-up">
      <h2 class="section-title">Cambiar tu contraseña</h2>
      <form @submit.prevent="cambiarPassword" class="space-y-4 mt-4">
        <div>
          <label class="label">Contraseña actual</label>
          <input
            v-model="pwd.actual"
            type="password"
            :disabled="cambiandoPwd"
            class="input"
          />
        </div>
        <div class="grid sm:grid-cols-2 gap-3">
          <div>
            <label class="label">Nueva contraseña</label>
            <input
              v-model="pwd.nueva"
              type="password"
              :disabled="cambiandoPwd"
              minlength="8"
              class="input"
            />
          </div>
          <div>
            <label class="label">Confirmar</label>
            <input
              v-model="pwd.confirmar"
              type="password"
              :disabled="cambiandoPwd"
              class="input"
            />
          </div>
        </div>
        <p v-if="errorPwd" class="field-error">{{ errorPwd }}</p>
        <p v-if="mensajePwd" class="banner-success">{{ mensajePwd }}</p>
        <button type="submit" :disabled="cambiandoPwd" class="btn-primary">
          {{ cambiandoPwd ? "Guardando…" : "Cambiar contraseña" }}
        </button>
      </form>
    </section>

    <section class="card p-6 border-coral-200 border-2 fade-in-up">
      <h2 class="section-title text-risk-critico">Borrar tu cuenta</h2>
      <p class="text-sm text-ink-700 mb-4">
        Si la borras, se va todo: tus conversaciones, tus respuestas y tus
        resultados. No se puede recuperar después.
      </p>
      <button
        v-if="!eliminar.abierto"
        @click="eliminar.abierto = true"
        class="btn-secondary !text-risk-critico !border-coral-300 hover:!bg-coral-50"
      >
        Borrar mi cuenta
      </button>
      <div
        v-else
        class="bg-coral-50 border border-coral-200 rounded-xl p-5 space-y-4"
      >
        <p class="text-sm text-risk-critico">
          Para confirmar, escribe <strong>ELIMINAR</strong> y tu contraseña.
        </p>
        <div>
          <label class="label !text-risk-critico">Escribe ELIMINAR</label>
          <input
            v-model="eliminar.confirmacion"
            type="text"
            placeholder="ELIMINAR"
            class="input border-coral-300 font-mono uppercase"
          />
        </div>
        <div>
          <label class="label !text-risk-critico">Contraseña</label>
          <input
            v-model="eliminar.password"
            type="password"
            class="input border-coral-300"
          />
        </div>
        <p v-if="errorEliminar" class="field-error">{{ errorEliminar }}</p>
        <div class="flex gap-2 pt-2">
          <button
            @click="
              eliminar.abierto = false;
              eliminar.password = '';
              eliminar.confirmacion = '';
            "
            :disabled="eliminando"
            class="btn-ghost"
          >
            Cancelar
          </button>
          <button
            @click="eliminarCuenta"
            :disabled="eliminando"
            class="btn-danger"
          >
            {{ eliminando ? "Eliminando…" : "Eliminar cuenta permanentemente" }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
