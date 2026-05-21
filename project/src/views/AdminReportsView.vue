<script setup>
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import PageHeader from "../components/PageHeader.vue";
import StatCard from "../components/StatCard.vue";

const router = useRouter();
const hoy = new Date();
const year = ref(hoy.getFullYear());
const month = ref(hoy.getMonth() + 1);
const reporte = ref(null);
const cargando = ref(false);
const error = ref("");

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
    reporte.value = await api.reporteMensualAdmin(year.value, month.value);
  } catch (e) {
    error.value = e.response?.data?.detail || e.message;
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const meses = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];
const totalEvals = computed(() => reporte.value?.evaluaciones_analizadas || 0);
const distPct = (n) =>
  totalEvals.value ? Math.round((100 * n) / totalEvals.value) : 0;

const colorSev = {
  CRÍTICO: "bg-risk-critico",
  ALTO: "bg-ink-600",
  MEDIO: "bg-amber-500",
  BAJO: "bg-green-700",
};
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">
      Volver al menú
    </button>

    <PageHeader
      title="Reportes"
      accent="del mes"
      subtitle="Cómo va el uso del sistema, mes a mes."
      tone="brand"
    >
      <template #actions>
        <div class="flex gap-2 items-end mt-3 flex-wrap">
          <div>
            <label class="label">Mes</label>
            <select v-model="month" @change="cargar" class="input w-40">
              <option v-for="(m, i) in meses" :key="i" :value="i + 1">
                {{ m }}
              </option>
            </select>
          </div>
          <div>
            <label class="label">Año</label>
            <input
              v-model.number="year"
              @change="cargar"
              type="number"
              class="input w-24 text-center"
            />
          </div>
          <button @click="() => window.print()" class="btn-secondary no-print">
            Imprimir
          </button>
        </div>
      </template>
    </PageHeader>

    <p v-if="cargando" class="text-center text-ink-500 py-12">
      Cargando reporte…
    </p>
    <p v-else-if="error" class="banner-danger">{{ error }}</p>

    <div v-else-if="reporte" class="space-y-6 fade-in-up">
      <p class="text-sm text-ink-500">Período</p>
      <h2 class="text-2xl font-bold text-ink-900 -mt-4">
        {{ meses[month - 1] }} {{ year }}
      </h2>

      <!-- Stats -->
      <section class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="Sesiones iniciadas"
          :value="reporte.sesiones_iniciadas"
          tone="brand"
        />
        <StatCard
          label="Completadas"
          :value="reporte.sesiones_completadas"
          tone="mint"
        />
        <StatCard
          label="Evaluaciones analizadas"
          :value="reporte.evaluaciones_analizadas"
          tone="sky2"
        />
        <StatCard
          label="Casos en crisis"
          :value="reporte.crisis_detectadas"
          tone="risk-critico"
        />
      </section>

      <!-- Distribución -->
      <section class="card p-6">
        <h2 class="section-title">Niveles de riesgo</h2>
        <p class="section-subtitle mb-4">
          Sobre {{ totalEvals }} evaluaciones del mes.
        </p>
        <div class="space-y-4">
          <div v-for="(n, sev) in reporte.distribucion_riesgo" :key="sev">
            <div class="flex justify-between text-sm mb-1.5">
              <span
                class="font-semibold text-ink-800 inline-flex items-center gap-2"
              >
                {{ sev }}
              </span>
              <span class="text-ink-500"
                >{{ n }} · <strong>{{ distPct(n) }}%</strong></span
              >
            </div>
            <div class="h-2.5 bg-ink-100 rounded-full overflow-hidden">
              <div
                class="h-full transition-all duration-700"
                :class="colorSev[sev]"
                :style="{ width: distPct(n) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </section>

      <!-- PHQ-9 / GAD-7 -->
      <section class="grid sm:grid-cols-2 gap-4">
        <div class="card-pastel p-6">
          <p class="text-xs uppercase tracking-wider text-green-700 font-bold">
            PHQ-9 promedio
          </p>
          <p class="text-3xl font-bold text-ink-900 mt-2">
            {{ reporte.promedio_phq9 }}
            <span class="text-lg text-ink-400 font-medium">/ 27</span>
          </p>
          <p class="text-xs text-ink-600 mt-1">Síntomas de depresión</p>
        </div>
        <div class="card-peach p-6">
          <p class="text-xs uppercase tracking-wider text-ink-700 font-bold">
            GAD-7 promedio
          </p>
          <p class="text-3xl font-bold text-ink-900 mt-2">
            {{ reporte.promedio_gad7 }}
            <span class="text-lg text-ink-400 font-medium">/ 21</span>
          </p>
          <p class="text-xs text-ink-600 mt-1">Síntomas de ansiedad</p>
        </div>
      </section>
    </div>
  </div>
</template>
