<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();
const stats = ref(null);
const cargando = ref(true);
const error = ref("");

async function cargar() {
  cargando.value = true;
  try {
    stats.value = await api.dashboardStats();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Cola clínica</p>
      <h1 class="hero-serif text-[28px]">
        Alertas <span class="hero-mint">activas</span>
      </h1>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>
    <div v-else>
      <div
        v-if="(stats?.estudiantes_en_alerta || []).length === 0"
        class="card p-6 text-ink-500"
      >
        No hay alertas activas.
      </div>
      <div v-else class="grid gap-3">
        <div
          v-for="a in stats.estudiantes_en_alerta"
          :key="a.aplicacion_id"
          class="card p-4 flex items-center justify-between"
          :class="{ 'border-red-300 bg-red-50/40': a.crisis_activada }"
        >
          <div>
            <p class="font-semibold text-green-900">
              {{ a.nombre }} {{ a.apellido }}
            </p>
            <p class="text-xs text-ink-500">{{ a.email }}</p>
            <p v-if="a.crisis_activada" class="text-xs text-red-700 mt-1">
              Crisis activada
            </p>
          </div>
          <button
            class="btn-mint btn-sm"
            @click="router.push({ name: 'psicologo-resultado', params: { id: a.aplicacion_id } })"
          >
            Ver resultado
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
