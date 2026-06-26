<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const stats = ref(null);
const cargando = ref(true);
const error = ref("");

const ahora = new Date();
const anio = ref(ahora.getFullYear());
const mes = ref(ahora.getMonth() + 1);
const exportando = ref(false);

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

async function exportarMensual() {
  if (exportando.value) return;
  exportando.value = true;
  try {
    const blob = await api.descargarReporteMensual(anio.value, mes.value);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reporte_${anio.value}_${String(mes.value).padStart(2, "0")}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo generar el reporte.");
  } finally {
    exportando.value = false;
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

      <div class="card p-5 mb-6">
        <h2 class="text-lg font-semibold mb-3">Reporte mensual para autoridades (HU-18)</h2>
        <p class="text-sm text-ink-500 mb-3">
          Descarga un PDF agregado y anonimizado con totales del mes elegido.
        </p>
        <div class="flex flex-wrap items-center gap-3">
          <label class="text-sm text-ink-600">Año
            <input v-model.number="anio" type="number" min="2024" max="2099"
              class="border rounded-md px-2 py-1 w-24 ml-1" />
          </label>
          <label class="text-sm text-ink-600">Mes
            <input v-model.number="mes" type="number" min="1" max="12"
              class="border rounded-md px-2 py-1 w-16 ml-1" />
          </label>
          <button class="btn-mint" :disabled="exportando" @click="exportarMensual">
            {{ exportando ? "Generando…" : "Descargar PDF" }}
          </button>
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
