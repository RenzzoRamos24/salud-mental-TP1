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
      <div v-if="stats?.marcados_urgentes" class="banner-danger mb-4">
        <strong>
          {{ stats.marcados_urgentes }}
          {{ stats.marcados_urgentes === 1 ? "alumno marcado" : "alumnos marcados" }}
          como urgente
        </strong>
        por quien está evaluando los cuestionarios. No es un cálculo del
        sistema: una persona leyó el caso y decidió avisar. Van primeros en la
        lista.
      </div>

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
          :class="{
            'border-red-300 bg-red-50/40': a.crisis_activada,
            'border-red-500 bg-red-50 ring-1 ring-red-300': a.marcado_urgente,
          }"
        >
          <div class="min-w-0">
            <p class="font-semibold text-green-900">
              {{ a.nombre }} {{ a.apellido }}
              <span
                v-if="a.marcado_urgente"
                class="ml-2 text-[11px] px-2 py-0.5 rounded-full bg-red-600 text-white align-middle"
              >
                MARCADO URGENTE
              </span>
            </p>
            <p class="text-xs text-ink-500">{{ a.email }}</p>
            <p v-if="a.crisis_activada" class="text-xs text-red-700 mt-1">
              Crisis activada
            </p>
            <p
              v-if="a.marcado_urgente"
              class="text-xs text-red-800 mt-1.5 whitespace-pre-line bg-white/70 rounded p-2 border border-red-200"
            >{{ a.motivo_urgente }}</p>
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
