<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { authStore } from "../store/auth";

const props = defineProps({
  view: { type: String, required: true },
  crumb: { type: String, default: "Panel del Alumno" },
});
const emit = defineEmits(["change-view"]);
const router = useRouter();

const user = computed(() => authStore.state.user);
const fullName = computed(() => {
  const u = user.value;
  if (!u) return "";
  return `${u.nombre || ""} ${u.apellido || ""}`.trim();
});
const initials = computed(() => {
  const u = user.value;
  if (!u) return "?";
  return `${(u.nombre || "?")[0]}${(u.apellido || "")[0] || ""}`.toUpperCase();
});

const nowLabel = computed(() => {
  const d = new Date();
  const semana = Math.ceil(
    ((d - new Date(d.getFullYear(), 0, 1)) / 86400000 + 1) / 7,
  );
  const mes = d.toLocaleString("es-PE", { month: "long" });
  return `Semana ${semana} · ${mes[0].toUpperCase()}${mes.slice(1)} ${d.getFullYear()}`;
});

function goView(v) {
  emit("change-view", v);
}
function goSOS() {
  emit("change-view", "inicio");
  setTimeout(() => {
    document.getElementById("sos-card")?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 80);
}
function logout() {
  authStore.clear();
  router.push("/login");
}

const nav = [
  { key: "inicio", label: "Inicio" },
  { key: "cuestionario", label: "Cuestionario" },
  { key: "reuniones", label: "Reuniones" },
  { key: "recursos", label: "Recursos de apoyo" },
  { key: "sos", label: "SOS · Ayuda", action: goSOS },
  { key: "bienestar", label: "Mi bienestar" },
  { key: "perfil", label: "Mi Perfil" },
];
</script>

<template>
  <div class="alumno-root">
    <!-- SIDEBAR -->
    <aside class="alumno-side">
      <div class="alumno-side__head">
        <div class="alumno-logo">
          <img src="/sentir-isotipo.svg" alt="Sami" />
        </div>
        <span class="alumno-brand">Sami</span>
      </div>

      <div class="alumno-side__profile">
        <div class="alumno-avatar">{{ initials }}</div>
        <div class="alumno-side__name">{{ fullName || "Alumno" }}</div>
        <div class="alumno-side__role">
          Alumno{{ user?.grado ? ` · ${user.grado}` : "" }}
        </div>
      </div>

      <nav class="alumno-side__nav scrolly">
        <a
          v-for="item in nav"
          :key="item.key"
          href="#"
          class="alumno-nav-link"
          :class="{ active: item.key !== 'sos' && view === item.key }"
          @click.prevent="item.action ? item.action() : goView(item.key)"
        >
          <span class="alumno-nav-icon">
            <svg v-if="item.key === 'inicio'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l9-7 9 7M5 10v10h14V10"/></svg>
            <svg v-else-if="item.key === 'cuestionario'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>
            <svg v-else-if="item.key === 'reuniones'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M15 10l5-3v10l-5-3v-4z"/><rect x="3" y="6" width="12" height="12" rx="2"/></svg>
            <svg v-else-if="item.key === 'recursos'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 0 1 2-2h7v18H6a2 2 0 0 0-2 2V5z"/><path d="M20 3h-5v18h5V3z"/></svg>
            <svg v-else-if="item.key === 'sos'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 4.5-3.2 7.8-8 9-4.8-1.2-8-4.5-8-9V7l8-4z"/><path d="M12 9v4M12 16h.01"/></svg>
            <svg v-else-if="item.key === 'bienestar'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20s-7-4.3-7-9.2A4 4 0 0 1 12 8a4 4 0 0 1 7 3.8C19 15.7 12 20 12 20z"/></svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M5 21c0-3.9 3.1-7 7-7s7 3.1 7 7"/></svg>
          </span>
          {{ item.label }}
        </a>
      </nav>

      <div class="alumno-side__cta">
        <button class="alumno-cta" @click="goView('reuniones')">
          <span class="alumno-cta__icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-4.3-7-9.2A4 4 0 0 1 12 8a4 4 0 0 1 7 3.8C19 16.7 12 21 12 21z"/><circle cx="12" cy="11" r="1.6"/></svg>
          </span>
          <div class="alumno-cta__text">
            <div class="alumno-cta__title">Hablar con psicólogo</div>
            <div class="alumno-cta__sub">Apoyo cuando lo necesites</div>
          </div>
        </button>
      </div>
    </aside>

    <!-- MAIN -->
    <div class="alumno-main">
      <header class="alumno-topbar">
        <div class="alumno-search">
          <svg class="alumno-search__icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9aa7ab" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.2-3.2"/></svg>
          <input placeholder="Buscar en Sami…" />
        </div>
        <div class="alumno-topbar__actions">
          <button class="alumno-tb-btn" title="Notificaciones">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9z"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>
            <span class="alumno-tb-dot alumno-tb-dot--y"></span>
          </button>
          <button class="alumno-tb-btn" title="Mensajes" @click="goView('reuniones')">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-12 7.6L3 21l1.9-6A8.4 8.4 0 1 1 21 11.5z"/></svg>
            <span class="alumno-tb-dot alumno-tb-dot--g"></span>
          </button>
          <button class="alumno-avatar-btn" @click="goView('perfil')" :title="fullName || 'Perfil'">
            <span class="alumno-avatar alumno-avatar--sm">{{ initials }}</span>
            <span class="alumno-avatar-status"></span>
          </button>
        </div>
      </header>

      <main class="alumno-content scrolly">
        <div class="alumno-breadcrumb-row">
          <div class="alumno-breadcrumb">
            <span class="alumno-bc-home" @click="goView('inicio')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0e8d7e" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l9-7 9 7M5 10v10h14V10"/></svg>
            </span>
            <span class="alumno-bc-sep">/</span>
            <span class="alumno-bc-current">{{ crumb }}</span>
          </div>
          <div class="alumno-week-chip">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#0e8d7e" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/></svg>
            {{ nowLabel }}
          </div>
        </div>

        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.alumno-root {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  color: #33424a;
  font-family: "Figtree", system-ui, sans-serif;
  background: #f5f7f8;
}
.scrolly::-webkit-scrollbar { width: 8px; height: 8px; }
.scrolly::-webkit-scrollbar-thumb { background: #cfd8d6; border-radius: 8px; }
.scrolly::-webkit-scrollbar-track { background: transparent; }

/* ── SIDEBAR ── */
.alumno-side {
  width: 264px;
  flex: 0 0 264px;
  background: #fff;
  border-right: 1px solid #eef1f2;
  display: flex;
  flex-direction: column;
  position: relative;
}
.alumno-side__head {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  border-bottom: 1px solid #f1f4f4;
}
.alumno-logo {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.alumno-logo img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.alumno-brand {
  font-size: 22px;
  font-weight: 800;
  color: #243239;
  letter-spacing: -0.5px;
}

.alumno-side__profile {
  padding: 22px 18px 18px;
  text-align: center;
  border-bottom: 1px solid #f1f4f4;
}
.alumno-avatar {
  width: 62px;
  height: 62px;
  border-radius: 50%;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  font-weight: 800;
  font-size: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #eaf5f2;
}
.alumno-side__name {
  margin-top: 10px;
  font-weight: 700;
  font-size: 15px;
  color: #243239;
}
.alumno-side__role {
  margin-top: 2px;
  font-size: 12px;
  color: #9aa7ab;
}

.alumno-side__nav {
  flex: 1;
  overflow-y: auto;
  padding: 14px 12px;
}
.alumno-nav-link {
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
  transition: background 0.15s;
}
.alumno-nav-link:hover { background: #f4f7f7; }
.alumno-nav-link.active {
  background: #e3f3ef;
  color: #0e8d7e;
  font-weight: 700;
}
.alumno-nav-icon {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #7c8b90;
  flex: 0 0 30px;
}
.alumno-nav-link.active .alumno-nav-icon {
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  box-shadow: 0 4px 9px rgba(20, 150, 135, 0.4);
}

.alumno-side__cta { padding: 14px 14px 16px; }
.alumno-cta {
  width: 100%;
  background: linear-gradient(135deg, #1aa896, #0c8475);
  border: none;
  border-radius: 14px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 8px 18px rgba(15, 130, 115, 0.3);
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}
.alumno-cta__icon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 40px;
}
.alumno-cta__text { line-height: 1.25; min-width: 0; }
.alumno-cta__title {
  color: #fff;
  font-weight: 800;
  font-size: 15px;
  white-space: nowrap;
}
.alumno-cta__sub {
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
}

/* ── MAIN ── */
.alumno-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.alumno-topbar {
  height: 64px;
  flex: 0 0 64px;
  background: #fff;
  border-bottom: 1px solid #eef1f2;
  display: flex;
  align-items: center;
  padding: 0 26px;
  gap: 18px;
}
.alumno-search {
  position: relative;
  width: 340px;
  max-width: 42vw;
}
.alumno-search__icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
}
.alumno-search input {
  width: 100%;
  height: 42px;
  border: 1px solid #e7ecec;
  background: #f8fafa;
  border-radius: 12px;
  padding: 0 14px 0 40px;
  font-size: 14px;
  font-family: inherit;
  color: #33424a;
  outline: none;
}
.alumno-topbar__actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}
.alumno-tb-btn {
  position: relative;
  width: 38px;
  height: 38px;
  border: none;
  background: #f4f7f7;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #5a6a70;
}
.alumno-tb-dot {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1.5px solid #fff;
}
.alumno-tb-dot--y { background: #f5b301; }
.alumno-tb-dot--g { background: #1fbf75; }
.alumno-avatar-btn {
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}
.alumno-avatar--sm {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  font-size: 14px;
  border: none;
}
.alumno-avatar-status {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #1fbf75;
  border: 2px solid #fff;
}

.alumno-content {
  flex: 1;
  overflow-y: auto;
  background: linear-gradient(180deg, #e9f4f1 0%, #f5f7f8 220px);
  padding: 22px 26px 40px;
}

/* ── RESPONSIVE ── */
@media (max-width: 1100px) {
  .alumno-side { width: 78px; flex: 0 0 78px; }
  .alumno-brand,
  .alumno-side__name,
  .alumno-side__role,
  .alumno-nav-link { font-size: 0; }
  .alumno-nav-link { justify-content: center; padding: 10px 8px; }
  .alumno-nav-icon { margin: 0; }
  .alumno-side__head { justify-content: center; padding: 0 12px; }
  .alumno-side__head .alumno-logo { margin: 0 auto; }
  .alumno-side__profile { padding: 18px 8px; }
  .alumno-side__profile .alumno-avatar { width: 46px; height: 46px; font-size: 17px; }
  .alumno-cta__text { display: none; }
  .alumno-cta { justify-content: center; padding: 12px; }
  .alumno-search { width: 200px; }
}
@media (max-width: 760px) {
  .alumno-side { display: none; }
  .alumno-search { width: 160px; }
  .alumno-search__input { font-size: 13px; }
  .alumno-content { padding: 16px 14px 32px; }
  .alumno-week-chip { display: none; }
}
.alumno-breadcrumb-row {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}
.alumno-breadcrumb {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
}
.alumno-bc-home {
  display: flex;
  cursor: pointer;
}
.alumno-bc-sep { color: #9aa7ab; }
.alumno-bc-current {
  color: #0e8d7e;
  font-weight: 700;
}
.alumno-week-chip {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1px solid #e7ecec;
  border-radius: 12px;
  padding: 9px 14px;
  font-size: 14px;
  color: #33424a;
  font-weight: 500;
  text-transform: capitalize;
}
</style>
