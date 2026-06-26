<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const contenidos = ref([]);
const cargando = ref(true);
const error = ref("");

async function cargar() {
  cargando.value = true;
  try {
    contenidos.value = await api.adminListarTodosContenidos();
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
      <p class="eyebrow mb-2">Contenidos</p>
      <h1 class="hero-serif text-[28px]">
        Material <span class="hero-mint">psicoeducativo</span>
      </h1>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <div v-else>
      <div v-if="contenidos.length === 0" class="card p-6 text-ink-500">
        No hay contenidos cargados.
      </div>
      <div v-else class="grid gap-3">
        <div
          v-for="c in contenidos"
          :key="c.id"
          class="card p-4"
        >
          <p class="text-xs text-ink-400">{{ c.categoria }}</p>
          <p class="font-semibold text-green-900">{{ c.titulo }}</p>
          <p v-if="c.descripcion" class="text-sm text-ink-500 mt-1">
            {{ c.descripcion }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
