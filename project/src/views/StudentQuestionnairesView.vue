<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();
const cuestionarios = ref([]);
const cargando = ref(true);
const error = ref("");

async function cargar() {
  cargando.value = true;
  try {
    cuestionarios.value = await api.misCuestionarios();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudieron cargar tus cuestionarios.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const pendientes = computed(() =>
  cuestionarios.value.filter((c) => c.estado === "pendiente" || c.estado === "en_progreso"),
);
const completados = computed(() =>
  cuestionarios.value.filter((c) => c.estado === "completado" || c.estado === "revisado"),
);

function abrir(c) {
  router.push({ name: "responder", params: { id: c.id } });
}

function fmtFecha(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function badgeEstado(estado) {
  return {
    pendiente: { label: "Pendiente", clase: "bg-amber-50 text-amber-700 border-amber-200" },
    en_progreso: { label: "En progreso", clase: "bg-sky-50 text-sky-700 border-sky-200" },
    completado: { label: "Completado", clase: "bg-green-50 text-green-700 border-green-200" },
    revisado: { label: "Revisado", clase: "bg-gray-50 text-gray-700 border-gray-200" },
  }[estado] || { label: estado, clase: "bg-gray-50 text-gray-700 border-gray-200" };
}
</script>

<template>
  <div class="page-shell-wide">
    <section class="mb-8">
      <p class="eyebrow mb-2">Tu espacio</p>
      <h1 class="hero-serif text-[32px] sm:text-[37px]">
        Mis <span class="hero-mint">cuestionarios</span>
      </h1>
      <p class="text-ink-500 mt-2">
        Aquí aparecen los cuestionarios que tu psicóloga te asigna.
      </p>
    </section>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">
      Cargando…
    </div>

    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <div v-else>
      <h2 class="text-lg font-semibold mb-3">Por responder</h2>
      <div v-if="pendientes.length === 0" class="card p-6 text-ink-500 mb-8">
        No tienes cuestionarios pendientes.
      </div>
      <div v-else class="grid gap-3 mb-8">
        <button
          v-for="c in pendientes"
          :key="c.id"
          class="menu-card text-left"
          @click="abrir(c)"
        >
          <span class="menu-card-arrow">→</span>
          <div class="flex items-center justify-between mb-2">
            <span
              class="text-xs px-2 py-0.5 rounded-full border"
              :class="badgeEstado(c.estado).clase"
            >
              {{ badgeEstado(c.estado).label }}
            </span>
            <span class="text-xs text-ink-400">
              {{ c.n_preguntas }} preguntas
            </span>
          </div>
          <h3 class="text-[19px] font-semibold text-green-900 leading-snug">
            {{ c.plantilla_nombre }}
          </h3>
          <p class="text-[13px] text-ink-500 mt-2">
            Asignado el {{ fmtFecha(c.asignada_at) }}
          </p>
        </button>
      </div>

      <h2 class="text-lg font-semibold mb-3">Completados</h2>
      <div v-if="completados.length === 0" class="card p-6 text-ink-500">
        Todavía no has completado ningún cuestionario.
      </div>
      <div v-else class="grid gap-3">
        <div
          v-for="c in completados"
          :key="c.id"
          class="card p-4 flex items-center justify-between"
        >
          <div>
            <p class="font-semibold text-green-900">{{ c.plantilla_nombre }}</p>
            <p class="text-xs text-ink-500 mt-1">
              Completado el {{ fmtFecha(c.completada_at) }}
            </p>
          </div>
          <span
            class="text-xs px-2 py-0.5 rounded-full border"
            :class="badgeEstado(c.estado).clase"
          >
            {{ badgeEstado(c.estado).label }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
