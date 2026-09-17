<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import AppSidebar from "./AppSidebar.vue";
import { uiStore } from "../store/ui";
import { api } from "../api";

const route = useRoute();
const router = useRouter();

// ─── Buscador de la topbar ────────────────────────────────────────────
// Índice en memoria: estudiantes + plantillas. Se carga una sola vez, al
// primer foco del input, para no pedir datos que quizá no se usen.
const consulta = ref("");
const indice = ref([]);
const indiceCargado = ref(false);
const mostrarResultados = ref(false);

async function cargarIndice() {
  mostrarResultados.value = true;
  if (indiceCargado.value) return;
  indiceCargado.value = true;
  try {
    const [estudiantes, plantillas] = await Promise.all([
      api.listarEstudiantes(),
      api.listarPlantillas(),
    ]);
    indice.value = [
      ...(estudiantes || []).map((e) => ({
        tipo: "estudiante",
        etiqueta: "Estudiante",
        id: e.id,
        nombre: [e.nombre, e.apellido].filter(Boolean).join(" ") || e.email,
        ruta: `/psicologo/estudiante/${e.id}`,
      })),
      ...(plantillas || []).map((p) => ({
        tipo: "plantilla",
        etiqueta: "Cuestionario",
        id: p.id,
        nombre: p.nombre,
        ruta: "/psicologo/plantillas",
      })),
    ];
  } catch {
    // Si falla, el buscador queda vacío en vez de romper la barra.
    indice.value = [];
    indiceCargado.value = false;
  }
}

const normalizar = (s) =>
  (s || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");

const resultados = computed(() => {
  const q = normalizar(consulta.value.trim());
  if (!q) return [];
  return indice.value
    .filter((r) => normalizar(r.nombre).includes(q))
    .slice(0, 8);
});

function abrir(r) {
  if (!r) return;
  consulta.value = "";
  mostrarResultados.value = false;
  router.push(r.ruta);
}

// `mousedown.prevent` en los resultados ya evita el blur, pero si el foco se
// pierde de otra forma (tab, clic fuera) cerramos el panel.
function cerrarConRetraso() {
  setTimeout(() => {
    mostrarResultados.value = false;
  }, 120);
}

// ─── Badge de alertas ─────────────────────────────────────────────────
const alertasActivas = ref(0);

async function refrescarAlertas() {
  try {
    const stats = await api.dashboardStats();
    alertasActivas.value = (stats?.estudiantes_en_alerta || []).length;
  } catch {
    alertasActivas.value = 0;
  }
}

onMounted(refrescarAlertas);
// Al navegar, el índice puede haber quedado viejo (alumno nuevo, plantilla
// nueva). Se invalida para que el próximo foco lo vuelva a pedir.
watch(
  () => route.path,
  () => {
    refrescarAlertas();
    indiceCargado.value = false;
  },
);

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
        <button
          class="apollo-topbar__menu"
          type="button"
          title="Menú"
          aria-label="Abrir menú de navegación"
          @click="uiStore.abrirMenu()"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
          >
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>

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
            v-model="consulta"
            placeholder="Buscar estudiante o cuestionario…"
            class="apollo-search__input"
            type="search"
            autocomplete="off"
            aria-label="Buscar estudiante o cuestionario"
            @focus="cargarIndice"
            @keydown.esc="consulta = ''"
            @keydown.enter="abrir(resultados[0])"
            @blur="cerrarConRetraso"
          />

          <ul v-if="consulta.trim() && mostrarResultados" class="apollo-search__pop">
            <li v-if="!resultados.length" class="apollo-search__empty">
              Sin coincidencias para “{{ consulta.trim() }}”.
            </li>
            <li v-for="r in resultados" :key="r.tipo + r.id">
              <button
                type="button"
                class="apollo-search__hit"
                @mousedown.prevent="abrir(r)"
              >
                <span class="apollo-search__hit-nombre">{{ r.nombre }}</span>
                <span class="apollo-search__hit-tipo">{{ r.etiqueta }}</span>
              </button>
            </li>
          </ul>
        </div>

        <div class="apollo-topbar__actions">
          <button
            class="apollo-topbar__btn"
            type="button"
            title="Alertas activas"
            @click="router.push('/psicologo/alertas')"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.7 21a2 2 0 0 1-3.4 0" />
            </svg>
            <span
              v-if="alertasActivas"
              class="apollo-topbar__dot apollo-topbar__dot--red"
            ></span>
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
.apollo-topbar__dot--red {
  background: #ef4444;
}

/* ── Resultados del buscador ── */
.apollo-search__pop {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  margin: 0;
  padding: 6px;
  list-style: none;
  background: #fff;
  border: 1px solid #e7ecec;
  border-radius: 12px;
  box-shadow: 0 12px 28px rgba(31, 61, 71, 0.12);
  max-height: 320px;
  overflow-y: auto;
  z-index: 30;
}
.apollo-search__empty {
  padding: 10px 12px;
  font-size: 13px;
  color: #7d8b91;
}
.apollo-search__hit {
  width: 100%;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 12px;
  border: none;
  background: none;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
}
.apollo-search__hit:hover {
  background: #f2f7f6;
}
.apollo-search__hit-nombre {
  font-size: 14px;
  color: #29383f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.apollo-search__hit-tipo {
  flex: 0 0 auto;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #8b989e;
}

.apollo-content {
  flex: 1;
  overflow-y: auto;
  background: linear-gradient(180deg, #e9f4f1 0%, #f5f7f8 220px);
  padding: 22px 26px 40px;
}

/* Solo visible en móvil: en escritorio el sidebar ya está en pantalla. */
.apollo-topbar__menu {
  display: none;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  border: none;
  background: #f4f7f7;
  border-radius: 10px;
  color: #5a6a70;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* ── RESPONSIVE ── */
@media (max-width: 1100px) {
  .apollo-search { width: 220px; }
}
@media (max-width: 760px) {
  .apollo-topbar { padding: 0 14px; gap: 10px; }
  .apollo-topbar__menu { display: flex; }
  .apollo-search { flex: 1; width: auto; max-width: none; }
  .apollo-search__input { font-size: 13px; }
  .apollo-content { padding: 16px 14px 32px; }
}
</style>
