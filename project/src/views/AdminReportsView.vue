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
const totalAnalisis = computed(
  () =>
    (reporte.value?.analisis_diario || 0) +
    (reporte.value?.evaluaciones_analizadas || 0),
);
const distPct = (n) =>
  totalAnalisis.value ? Math.round((100 * n) / totalAnalisis.value) : 0;

const colorSev = {
  CRÍTICO: "bg-risk-critico",
  ALTO: "bg-ink-600",
  MEDIO: "bg-coral-500",
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

      <!-- Stats principales del diario -->
      <section class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          label="Entradas del diario"
          :value="reporte.entradas_diario || 0"
          tone="brand"
        />
        <StatCard
          label="Alumnos activos"
          :value="reporte.alumnos_activos_diario || 0"
          tone="mint"
        />
        <StatCard
          label="Ciclos cerrados"
          :value="reporte.ciclos_cerrados || 0"
          tone="sky2"
        />
        <StatCard
          label="Casos en crisis"
          :value="reporte.crisis_detectadas"
          tone="risk-critico"
        />
      </section>

      <!-- Posibles riesgos según DSM-5 -->
      <section class="card p-6">
        <h2 class="section-title">Posibles riesgos según DSM-5</h2>
        <p class="section-subtitle mb-4">
          Alumnos cuyo patrón observado coincide con criterios mínimos del
          manual. NO son diagnósticos confirmados.
        </p>
        <div class="grid sm:grid-cols-2 gap-4">
          <div
            class="bg-coral-50 border-l-4 border-l-coral-500 rounded-md p-4"
          >
            <p class="text-sm font-semibold text-coral-900 mb-1">
              Posible Episodio Depresivo Mayor
            </p>
            <p class="text-3xl font-semibold text-ink-900 tabular-nums">
              {{ reporte.posibles_riesgos_edm || 0 }}
            </p>
            <p class="text-xs text-ink-600 mt-1">
              ≥5 ítems PHQ-A con anhedonia o ánimo deprimido
            </p>
          </div>
          <div
            class="bg-coral-50 border-l-4 border-l-coral-500 rounded-md p-4"
          >
            <p class="text-sm font-semibold text-coral-900 mb-1">
              Posible Trastorno de Ansiedad Generalizada
            </p>
            <p class="text-3xl font-semibold text-ink-900 tabular-nums">
              {{ reporte.posibles_riesgos_tag || 0 }}
            </p>
            <p class="text-xs text-ink-600 mt-1">
              Ansiedad + descontrol de preocupación + ≥3 ítems GAD-7
            </p>
          </div>
        </div>
      </section>

      <!-- Distribución -->
      <section class="card p-6">
        <h2 class="section-title">Niveles de alerta</h2>
        <p class="section-subtitle mb-4">
          Sobre {{ totalAnalisis }} análisis del mes (entradas del diario y
          sesiones legacy).
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

      <!-- PHQ-A / GAD-7 promedio por entrada -->
      <section class="grid sm:grid-cols-2 gap-4">
        <div class="card p-6 border-l-4 border-l-green-600">
          <p class="text-xs uppercase tracking-wider text-green-700 font-bold">
            PHQ-A promedio por entrada
          </p>
          <p class="text-3xl font-bold text-ink-900 mt-2">
            {{ reporte.promedio_phqa_entrada || 0 }}
            <span class="text-lg text-ink-400 font-medium">/ 27</span>
          </p>
          <p class="text-xs text-ink-600 mt-1">
            Síntomas de depresión inferidos del texto libre
          </p>
        </div>
        <div class="card p-6 border-l-4 border-l-green-600">
          <p class="text-xs uppercase tracking-wider text-green-700 font-bold">
            GAD-7 promedio por entrada
          </p>
          <p class="text-3xl font-bold text-ink-900 mt-2">
            {{ reporte.promedio_gad7_diario_entrada || 0 }}
            <span class="text-lg text-ink-400 font-medium">/ 21</span>
          </p>
          <p class="text-xs text-ink-600 mt-1">
            Síntomas de ansiedad inferidos del texto libre
          </p>
        </div>
      </section>
    </div>
  </div>
</template>
