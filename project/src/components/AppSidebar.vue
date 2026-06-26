<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { authStore } from "../store/auth";
import { api } from "../api";

const router = useRouter();
const route = useRoute();

const rol = computed(() => authStore.rol.value);
const esPsicologo = computed(() => rol.value === "psicologo");
const user = computed(() => authStore.state.user);

const nombreCompleto = computed(() => {
  const u = user.value;
  if (!u) return "—";
  return `${u.nombre || ""} ${u.apellido || ""}`.trim();
});

const iniciales = computed(() => {
  const u = user.value;
  if (!u) return "··";
  return (
    (u.nombre || "·").charAt(0) + (u.apellido || "").charAt(0)
  ).toUpperCase();
});

const rolLabel = computed(() => {
  if (rol.value === "psicologo") return "Psicóloga";
  if (rol.value === "admin") return "Administradora";
  return "Profesional";
});

const alertasCrit = ref(0);
const sosAbiertos = ref(0);

async function refrescarBadges() {
  if (!esPsicologo.value) return;
  try {
    const stats = await api.dashboardStats();
    alertasCrit.value = (stats?.estudiantes_en_alerta || []).filter(
      (a) =>
        (a.riesgo_global || "").toUpperCase().startsWith("C") ||
        a.crisis_activada,
    ).length;
  } catch (_) {
    alertasCrit.value = 0;
  }
  try {
    const sos = await api.listarSOSAbiertos();
    sosAbiertos.value = Array.isArray(sos) ? sos.length : 0;
  } catch (_) {
    sosAbiertos.value = 0;
  }
}

onMounted(refrescarBadges);
watch(() => route.path, refrescarBadges);

const items = computed(() => [
  { to: "/psicologo", label: "Panel clínico", icon: iconHome() },
  { to: "/psicologo/estudiantes", label: "Estudiantes", icon: iconStudents() },
  {
    to: "/psicologo/alertas",
    label: "Alertas",
    icon: iconBell(),
    badge: alertasCrit.value || null,
  },
  {
    to: "/psicologo/sos",
    label: "SOS",
    icon: iconHelp(),
    badge: sosAbiertos.value || null,
  },
  { to: "/psicologo/citas", label: "Citas", icon: iconCalendar() },
  { to: "/psicologo/banco", label: "Banco", icon: iconBook() },
  { to: "/psicologo/plantillas", label: "Plantillas", icon: iconLayers() },
  { to: "/psicologo/asignar", label: "Asignar", icon: iconSend() },
  { to: "/recursos", label: "Recursos", icon: iconLifebuoy() },
  { to: "/perfil", label: "Mi cuenta", icon: iconUser() },
]);

function esActivo(to) {
  const p = route.path;
  if (to === "/psicologo") return p === "/psicologo";
  if (to === "/recursos") return p.startsWith("/recursos");
  if (to === "/perfil") return p.startsWith("/perfil");
  return p.startsWith(to);
}

async function logout() {
  await api.logout();
  authStore.clear();
  router.push({ name: "login" });
}

function iconHome() {
  return `<path d="M3 21h18M5 21V9l7-5 7 5v12M10 21v-6h4v6"/>`;
}
function iconStudents() {
  return `<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>`;
}
function iconBell() {
  return `<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>`;
}
function iconHelp() {
  return `<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>`;
}
function iconCalendar() {
  return `<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/>`;
}
function iconBook() {
  return `<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>`;
}
function iconLayers() {
  return `<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>`;
}
function iconSend() {
  return `<line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>`;
}
function iconLifebuoy() {
  return `<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><line x1="4.93" y1="4.93" x2="9.17" y2="9.17"/><line x1="14.83" y1="14.83" x2="19.07" y2="19.07"/><line x1="14.83" y1="9.17" x2="19.07" y2="4.93"/><line x1="4.93" y1="19.07" x2="9.17" y2="14.83"/>`;
}
function iconUser() {
  return `<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>`;
}
function iconMenu() {
  return `<path d="M3 6h18M3 12h18M3 18h18"/>`;
}
function iconPhone() {
  return `<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M11 18h2"/>`;
}
</script>

<template>
  <aside class="apollo-sidebar">
    <!-- logo row -->
    <div class="apollo-logo">
      <div class="apollo-logo__brand">
        <div class="apollo-logo__mark">
          <img src="/sentir-isotipo.svg" alt="Sami" class="apollo-logo__img" />
        </div>
        <span class="apollo-logo__name">Sami</span>
      </div>
      <button class="apollo-logo__menu" type="button">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          v-html="iconMenu()"
        />
      </button>
    </div>

    <!-- profile -->
    <div class="apollo-profile">
      <div class="apollo-profile__avatar">{{ iniciales }}</div>
      <div class="apollo-profile__name">{{ nombreCompleto }}</div>
      <div class="apollo-profile__role">{{ rolLabel }}</div>
    </div>

    <!-- nav -->
    <nav class="apollo-nav">
      <a
        v-for="it in items"
        :key="it.to"
        href="#"
        class="apollo-nav__item"
        :class="{ 'is-active': esActivo(it.to) }"
        @click.prevent="router.push(it.to)"
      >
        <span class="apollo-nav__icon-wrap">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.7"
            stroke-linecap="round"
            stroke-linejoin="round"
            v-html="it.icon"
          />
        </span>
        {{ it.label }}
        <span v-if="it.badge" class="apollo-nav__badge">{{ it.badge }}</span>
      </a>
    </nav>

    <!-- support card -->
    <div class="apollo-support">
      <div class="apollo-support__card">
        <div class="apollo-support__icon">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#fff"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            v-html="iconPhone()"
          />
        </div>
        <div>
          <div class="apollo-support__number">113 — opción 5</div>
          <div class="apollo-support__label">Línea de ayuda · MINSA 24/7</div>
        </div>
      </div>
      <button class="apollo-support__logout" type="button" @click="logout">
        Cerrar sesión
      </button>
    </div>
  </aside>
</template>

<style scoped>
.apollo-sidebar {
  width: 264px;
  flex: 0 0 264px;
  background: #ffffff;
  border-right: 1px solid #eef1f2;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  font-family: "Figtree", system-ui, sans-serif;
  z-index: 30;
}

.apollo-logo {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid #f1f4f4;
  flex: none;
}
.apollo-logo__brand {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}
.apollo-logo__mark {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.apollo-logo__img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.apollo-logo__name {
  font-size: 22px;
  font-weight: 800;
  color: #243239;
  letter-spacing: -0.5px;
}
.apollo-logo__menu {
  margin-left: auto;
  width: 30px;
  height: 30px;
  border: none;
  background: #f3f6f6;
  border-radius: 8px;
  color: #6b7b80;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.apollo-profile {
  padding: 22px 18px 18px;
  text-align: center;
  border-bottom: 1px solid #f1f4f4;
  flex: none;
}
.apollo-profile__avatar {
  width: 62px;
  height: 62px;
  border-radius: 50%;
  margin: 0 auto;
  border: 3px solid #eaf5f2;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  font-weight: 700;
  font-size: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.apollo-profile__name {
  margin-top: 10px;
  font-weight: 700;
  font-size: 15px;
  color: #243239;
}
.apollo-profile__role {
  margin-top: 2px;
  font-size: 12px;
  color: #9aa7ab;
}

.apollo-nav {
  flex: 1;
  overflow-y: auto;
  padding: 14px 12px;
}
.apollo-nav::-webkit-scrollbar {
  width: 6px;
}
.apollo-nav::-webkit-scrollbar-thumb {
  background: #cfd8d6;
  border-radius: 6px;
}

.apollo-nav__item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  margin-bottom: 4px;
  text-decoration: none;
  color: #5a6a70;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  position: relative;
}
.apollo-nav__item:hover {
  background: #f4f7f7;
}
.apollo-nav__icon-wrap {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7c8b90;
  flex: none;
}
.apollo-nav__item.is-active {
  background: #e3f3ef;
  color: #0e8d7e;
  font-weight: 700;
}
.apollo-nav__item.is-active .apollo-nav__icon-wrap {
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #ffffff;
  box-shadow: 0 4px 9px rgba(20, 150, 135, 0.4);
}
.apollo-nav__badge {
  margin-left: auto;
  min-width: 20px;
  height: 18px;
  padding: 0 6px;
  border-radius: 99px;
  background: #ef4444;
  color: #ffffff;
  font-size: 10.5px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.apollo-support {
  padding: 14px 14px 16px;
  flex: none;
}
.apollo-support__card {
  background: linear-gradient(135deg, #1aa896, #0c8475);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 8px 18px rgba(15, 130, 115, 0.3);
}
.apollo-support__icon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 40px;
}
.apollo-support__number {
  color: #ffffff;
  font-weight: 800;
  font-size: 17px;
  line-height: 1.2;
}
.apollo-support__label {
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
  margin-top: 2px;
}
.apollo-support__logout {
  width: 100%;
  margin-top: 10px;
  padding: 8px;
  background: transparent;
  border: 0;
  font-size: 12px;
  color: #667085;
  cursor: pointer;
  border-radius: 8px;
  font-family: inherit;
  transition: color 0.15s;
}
.apollo-support__logout:hover {
  color: #0a0a0a;
}

/* ── RESPONSIVE ── */
@media (max-width: 1100px) {
  .apollo-sidebar { width: 78px; flex: 0 0 78px; }
  .apollo-logo__name,
  .apollo-profile__name,
  .apollo-profile__role,
  .apollo-nav__label,
  .apollo-support__txt { display: none; }
  .apollo-nav__link { justify-content: center; padding: 10px 8px; }
  .apollo-logo { justify-content: center; padding: 0 12px; }
  .apollo-logo__menu { display: none; }
  .apollo-profile { padding: 18px 8px; }
  .apollo-profile__avatar { width: 46px; height: 46px; font-size: 17px; }
  .apollo-support { padding: 12px; justify-content: center; }
}
@media (max-width: 760px) {
  .apollo-sidebar { display: none; }
}
</style>
