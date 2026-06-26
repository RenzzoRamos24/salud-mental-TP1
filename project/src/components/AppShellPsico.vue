<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppSidebar from "./AppSidebar.vue";

const route = useRoute();

const breadcrumb = computed(() => {
  const map = {
    psicologo: "Panel clínico",
    "psicologo-estudiantes": "Estudiantes",
    "psicologo-alertas": "Alertas",
    "psicologo-sos": "SOS",
    "psicologo-citas": "Citas",
    "psicologo-banco": "Banco",
    "psicologo-bloque-custom": "Bloque personalizado",
    "psicologo-plantillas": "Plantillas",
    "asignar-cuestionario": "Asignar",
    "psicologo-resultado": "Resultado",
    "psicologo-estudiante": "Ficha del alumno",
    recursos: "Recursos",
    perfil: "Mi cuenta",
  };
  return map[(route.name || "").toString()] || "Panel";
});
</script>

<template>
  <div class="apollo-root">
    <AppSidebar />
    <div class="apollo-main">
      <!-- topbar -->
      <header class="apollo-topbar">
        <div class="apollo-search">
          <svg
            class="apollo-search__icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#9aa7ab"
            stroke-width="2"
            stroke-linecap="round"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.2-3.2" />
          </svg>
          <input
            placeholder="Buscar estudiante o cuestionario…"
            class="apollo-search__input"
          />
        </div>

        <div class="apollo-topbar__actions">
          <button class="apollo-topbar__btn" title="Idioma">
            <span class="apollo-flag">
              <span class="apollo-flag__a"></span>
              <span class="apollo-flag__b"></span>
              <span class="apollo-flag__c"></span>
            </span>
          </button>
          <button class="apollo-topbar__btn" title="Favoritos">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linejoin="round"
            >
              <path
                d="m12 3 2.6 5.6L21 9.5l-4.5 4.3L17.6 21 12 17.8 6.4 21l1.1-7.2L3 9.5l6.4-.9z"
              />
            </svg>
          </button>
          <button class="apollo-topbar__btn" title="Aplicaciones">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
            >
              <rect x="3" y="3" width="7" height="7" rx="1.5" />
              <rect x="14" y="3" width="7" height="7" rx="1.5" />
              <rect x="3" y="14" width="7" height="7" rx="1.5" />
              <rect x="14" y="14" width="7" height="7" rx="1.5" />
            </svg>
            <span class="apollo-topbar__dot apollo-topbar__dot--yellow"></span>
          </button>
          <button class="apollo-topbar__btn" title="Notificaciones">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linejoin="round"
            >
              <rect x="3" y="8" width="18" height="13" rx="2" />
              <path
                d="M3 12h18M12 8v13M12 8c-2 0-4-1-4-3a2 2 0 0 1 4 0m0 3c2 0 4-1 4-3a2 2 0 0 0-4 0"
              />
            </svg>
            <span class="apollo-topbar__dot apollo-topbar__dot--green"></span>
          </button>
          <button class="apollo-topbar__btn" title="Mensajes">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linejoin="round"
            >
              <path d="M21 11.5a8.4 8.4 0 0 1-12 7.6L3 21l1.9-6A8.4 8.4 0 1 1 21 11.5z" />
            </svg>
            <span class="apollo-topbar__dot apollo-topbar__dot--red"></span>
          </button>
        </div>
      </header>

      <main class="apollo-content">
        <slot :breadcrumb="breadcrumb" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.apollo-root {
  display: flex;
  min-height: 100vh;
  background: #f5f7f8;
  color: #33424a;
  font-family: "Figtree", system-ui, sans-serif;
}
.apollo-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.apollo-topbar {
  height: 64px;
  flex: 0 0 64px;
  background: #ffffff;
  border-bottom: 1px solid #eef1f2;
  display: flex;
  align-items: center;
  padding: 0 26px;
  gap: 18px;
  position: sticky;
  top: 0;
  z-index: 20;
}
.apollo-search {
  position: relative;
  width: 340px;
  max-width: 42vw;
}
.apollo-search__icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
}
.apollo-search__input {
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
.apollo-topbar__actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}
.apollo-topbar__btn {
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
.apollo-topbar__dot {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1.5px solid #fff;
}
.apollo-topbar__dot--yellow {
  background: #f5b301;
}
.apollo-topbar__dot--green {
  background: #1fbf75;
}
.apollo-topbar__dot--red {
  background: #ef4444;
}
.apollo-flag {
  display: flex;
  width: 22px;
  height: 16px;
  border-radius: 3px;
  overflow: hidden;
}
.apollo-flag__a {
  flex: 1;
  background: #d91023;
}
.apollo-flag__b {
  flex: 1;
  background: #fff;
}
.apollo-flag__c {
  flex: 1;
  background: #d91023;
}

.apollo-content {
  flex: 1;
  overflow-y: auto;
  background: linear-gradient(180deg, #e9f4f1 0%, #f5f7f8 220px);
  padding: 22px 26px 40px;
}

/* ── RESPONSIVE ── */
@media (max-width: 1100px) {
  .apollo-search { width: 220px; }
}
@media (max-width: 760px) {
  .apollo-search { width: 150px; }
  .apollo-search__input { font-size: 13px; }
  .apollo-content { padding: 16px 14px 32px; }
}
</style>
