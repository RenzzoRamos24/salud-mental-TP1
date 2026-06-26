<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const modelo = ref(null);
const backups = ref([]);
const cargando = ref(true);
const error = ref("");

async function cargar() {
  cargando.value = true;
  try {
    const [m, b] = await Promise.all([
      api.adminGetModeloInfo(),
      api.adminListarBackups(),
    ]);
    modelo.value = m;
    backups.value = b;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

async function crearBackup() {
  try {
    await api.adminCrearBackup();
    backups.value = await api.adminListarBackups();
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo crear backup.");
  }
}

async function recargarModelo() {
  try {
    await api.adminRecargarModelo();
    modelo.value = await api.adminGetModeloInfo();
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo recargar.");
  }
}

onMounted(cargar);
</script>

<template>
  <div class="page-shell">
    <header class="mb-6">
      <p class="eyebrow mb-2">Sistema</p>
      <h1 class="hero-serif text-[28px]">
        Configuración del <span class="hero-mint">sistema</span>
      </h1>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <div class="card p-6 mb-4">
        <h2 class="text-lg font-semibold mb-3">Modelo NLP (BETO)</h2>
        <p class="text-sm text-ink-500 mb-1">Modelo: {{ modelo?.modelo }}</p>
        <p class="text-sm text-ink-500 mb-1">
          Estado: {{ modelo?.cargado ? "🟢 cargado" : "⚪ no cargado" }}
        </p>
        <p class="text-sm text-ink-500 mb-3">
          Categorías: {{ (modelo?.categorias || []).join(", ") }}
        </p>
        <button class="btn-ghost btn-sm" @click="recargarModelo">
          Recargar modelo
        </button>
      </div>

      <div class="card p-6">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold">Respaldos</h2>
          <button class="btn-mint btn-sm" @click="crearBackup">+ Crear backup</button>
        </div>
        <div v-if="backups.length === 0" class="text-sm text-ink-500">
          No hay respaldos todavía.
        </div>
        <ul v-else class="text-sm space-y-1">
          <li
            v-for="b in backups"
            :key="b.archivo"
            class="flex justify-between border-b border-cream-200 py-1"
          >
            <span class="font-mono text-xs">{{ b.archivo }}</span>
            <span class="text-xs text-ink-400">
              {{ new Date(b.fecha).toLocaleString("es-PE") }}
            </span>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>
