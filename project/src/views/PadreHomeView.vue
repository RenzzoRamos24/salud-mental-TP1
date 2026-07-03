<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";
import { authStore } from "../store/auth";
import { useRouter } from "vue-router";

const router = useRouter();
const user = authStore.state.user;
const hijos = ref([]);
const cargando = ref(true);
const error = ref("");

async function cargar() {
  cargando.value = true;
  try {
    hijos.value = await api.padreListarHijos();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar la lista de hijos.";
  } finally {
    cargando.value = false;
  }
}
onMounted(cargar);

function abrirHijo(id) {
  router.push({ name: "padre-hijo", params: { id } });
}

async function logout() {
  await api.logout();
  authStore.clear();
  router.push({ name: "login" });
}

function fmtFecha(s) {
  if (!s) return "Sin actividad aún";
  return new Date(s).toLocaleDateString("es-PE", {
    day: "2-digit", month: "short", year: "numeric",
  });
}
</script>

<template>
  <div class="padre-bg">
    <header class="padre-top">
      <div class="padre-top__brand">
        <span class="padre-top__logo">Sami</span>
        <span class="padre-top__pill">Panel para padres</span>
      </div>
      <div class="padre-top__user">
        <span>{{ user?.nombre }} {{ user?.apellido }}</span>
        <button class="padre-top__btn" @click="logout">Cerrar sesión</button>
      </div>
    </header>

    <main class="padre-main">
      <p class="padre-eyebrow">Bienvenido/a</p>
      <h1 class="padre-title">Cómo está tu estudiante</h1>
      <p class="padre-desc">
        Acá puedes ver el seguimiento del bienestar de tus hijos y descargar
        el informe firmado por la psicóloga responsable del colegio.
      </p>

      <div v-if="cargando" class="padre-card padre-card--status">
        Cargando información…
      </div>

      <div v-else-if="error" class="padre-card padre-card--err">{{ error }}</div>

      <div v-else-if="hijos.length === 0" class="padre-card padre-card--empty">
        <h3>Aún no tienes estudiantes vinculados</h3>
        <p>
          La administración del colegio debe vincular tu cuenta con tu hijo/a.
          Si crees que esto es un error, contacta con secretaría.
        </p>
      </div>

      <div v-else class="padre-grid">
        <article
          v-for="h in hijos"
          :key="h.id"
          class="padre-hijo"
          @click="abrirHijo(h.id)"
        >
          <div class="padre-hijo__avatar">
            {{ (h.nombre[0] || "?").toUpperCase() }}
          </div>
          <div class="padre-hijo__info">
            <h3>{{ h.nombre }} {{ h.apellido }}</h3>
            <p class="padre-hijo__meta">
              <span v-if="h.grado">{{ h.grado }}</span>
              <span v-else class="muted">Grado no registrado</span>
              <span>·</span>
              <span class="padre-hijo__estado" :data-estado="h.estado_caso">
                {{ h.estado_caso || "activo" }}
              </span>
            </p>
            <p class="padre-hijo__act">
              {{ h.cuestionarios_completados }} cuestionario(s) completado(s)
              · Última actividad: {{ fmtFecha(h.ultima_actividad) }}
            </p>
            <p v-if="h.psicologo_nombre" class="padre-hijo__psi">
              Psicóloga: <b>{{ h.psicologo_nombre }}</b>
            </p>
          </div>
          <div class="padre-hijo__cta">Ver informe →</div>
        </article>
      </div>
    </main>
  </div>
</template>

<style scoped>
.padre-bg {
  min-height: 100vh;
  background: #f4f5f6;
  font-family: "Work Sans", system-ui, sans-serif;
  color: #1f2937;
}
.padre-top {
  background: #fff;
  border-bottom: 1px solid #eef1f2;
  padding: 16px 36px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.padre-top__brand {
  display: flex;
  align-items: center;
  gap: 14px;
}
.padre-top__logo {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 22px;
  color: #0a0a0a;
}
.padre-top__pill {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #0e8d7e;
  background: #e3f3ef;
  padding: 4px 10px;
  border-radius: 99px;
}
.padre-top__user {
  display: flex;
  gap: 16px;
  align-items: center;
  font-size: 14px;
  color: #475467;
}
.padre-top__btn {
  background: transparent;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  color: #344054;
}
.padre-top__btn:hover {
  border-color: #45988c;
  color: #0e8d7e;
}

.padre-main {
  max-width: 1080px;
  margin: 0 auto;
  padding: 40px 36px 80px;
}
.padre-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #0e8d7e;
  margin-bottom: 8px;
}
.padre-title {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 34px;
  color: #0a0a0a;
  letter-spacing: -0.01em;
  margin-bottom: 10px;
}
.padre-desc {
  color: #475467;
  font-size: 15px;
  line-height: 1.6;
  max-width: 720px;
  margin-bottom: 28px;
}

.padre-card {
  background: #fff;
  border-radius: 18px;
  padding: 28px;
  box-shadow: 0 6px 30px rgba(35, 80, 95, 0.05);
}
.padre-card--status {
  text-align: center;
  color: #667085;
}
.padre-card--err {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}
.padre-card--empty {
  text-align: center;
  padding: 48px 32px;
}
.padre-card--empty h3 {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 22px;
  margin-bottom: 10px;
  color: #0a0a0a;
}
.padre-card--empty p {
  color: #667085;
  line-height: 1.55;
  max-width: 540px;
  margin: 0 auto;
}

.padre-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}
@media (min-width: 720px) {
  .padre-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
.padre-hijo {
  background: #fff;
  border-radius: 16px;
  padding: 22px;
  box-shadow: 0 6px 22px rgba(35, 80, 95, 0.04);
  border: 1px solid #eef1f2;
  display: flex;
  gap: 16px;
  cursor: pointer;
  transition: all 0.15s;
}
.padre-hijo:hover {
  border-color: #c5e1dc;
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(35, 80, 95, 0.08);
}
.padre-hijo__avatar {
  flex: none;
  width: 50px;
  height: 50px;
  border-radius: 14px;
  background: linear-gradient(135deg, #45988c, #0e8d7e);
  color: #fff;
  font-weight: 700;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.padre-hijo__info {
  flex: 1;
  min-width: 0;
}
.padre-hijo__info h3 {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 18px;
  color: #0a0a0a;
  margin-bottom: 4px;
}
.padre-hijo__meta {
  font-size: 12.5px;
  color: #667085;
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.muted {
  color: #98a2b3;
}
.padre-hijo__estado {
  text-transform: capitalize;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
  background: #e3f3ef;
  color: #0e8d7e;
}
.padre-hijo__estado[data-estado="cerrado"] {
  background: #f4f5f6;
  color: #667085;
}
.padre-hijo__act {
  font-size: 13px;
  color: #475467;
  margin-bottom: 6px;
  line-height: 1.45;
}
.padre-hijo__psi {
  font-size: 12.5px;
  color: #667085;
}
.padre-hijo__cta {
  flex: none;
  display: flex;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #0e8d7e;
}
</style>
