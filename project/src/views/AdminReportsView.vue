<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const stats = ref(null);
const cargando = ref(true);
const error = ref("");

async function cargar() {
  cargando.value = true;
  try {
    stats.value = await api.adminStatsCuestionarios();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);
</script>

<template>
  <div class="page-shell">
    <header class="mb-6">
      <p class="eyebrow mb-2">Métricas</p>
      <h1 class="hero-serif text-[28px]">
        Reportes de <span class="hero-mint">cuestionarios</span>
      </h1>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <div class="grid sm:grid-cols-4 gap-3 mb-6">
        <div class="card p-4">
          <p class="text-xs text-ink-400">Plantillas</p>
          <p class="text-2xl font-semibold">{{ stats?.total_plantillas || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Bloques custom</p>
          <p class="text-2xl font-semibold">{{ stats?.total_bloques_custom || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Asignados</p>
          <p class="text-2xl font-semibold">{{ stats?.total_asignados || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Completitud</p>
          <p class="text-2xl font-semibold">{{ stats?.tasa_completitud_pct || 0 }}%</p>
        </div>
      </div>

      <h2 class="text-lg font-semibold mb-3">Distribución de riesgo</h2>
      <div class="grid sm:grid-cols-5 gap-2">
        <div
          v-for="(n, k) in stats?.distribucion_riesgo || {}"
          :key="k"
          class="card p-4 text-center"
        >
          <p class="text-xs text-ink-400">{{ k.replace("_", " ") }}</p>
          <p class="text-xl font-semibold">{{ n }}</p>
        </div>
      </div>
    </template>
  </div>
</template>
