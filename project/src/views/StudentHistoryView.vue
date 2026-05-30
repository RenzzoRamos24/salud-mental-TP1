<script setup>
import { ref, onMounted, nextTick, computed, reactive } from "vue";
import { useRoute, useRouter } from "vue-router";
import { Chart, registerables } from "chart.js";
import { api } from "../api";
import PageHeader from "../components/PageHeader.vue";
import StatCard from "../components/StatCard.vue";
import RiskBadge from "../components/RiskBadge.vue";

Chart.register(...registerables);

const route = useRoute();
const router = useRouter();

const cargando = ref(true);
const error = ref("");
const data = ref(null);
const resumen = ref(null);
const reporteCiclo = ref(null);
const entradaAbierta = ref(null);
const chartCanvas = ref(null);
let chartInstance = null;

// ── Mensajes del psicólogo al estudiante ──────────────────────────────
const mensajes = ref([]);
const nuevoMensaje = ref("");
const guardandoMensaje = ref(false);
const errorMensaje = ref("");

async function cargarMensajes() {
  try {
    mensajes.value = await api.listarMensajesEstudiante(route.params.id);
  } catch (_) {
    mensajes.value = [];
  }
}

async function enviarMensaje() {
  const texto = nuevoMensaje.value.trim();
  if (!texto || guardandoMensaje.value) return;
  guardandoMensaje.value = true;
  errorMensaje.value = "";
  try {
    await api.crearMensajeEstudiante(route.params.id, texto);
    nuevoMensaje.value = "";
    await cargarMensajes();
  } catch (e) {
    errorMensaje.value = e.response?.data?.detail || e.message;
  } finally {
    guardandoMensaje.value = false;
  }
}

async function borrarMensaje(id) {
  if (!confirm("¿Borrar este mensaje? El estudiante ya no lo verá.")) return;
  try {
    await api.borrarMensajeEstudiante(route.params.id, id);
    await cargarMensajes();
  } catch (e) {
    alert(e.response?.data?.detail || e.message);
  }
}

const nivelANumero = { BAJO: 1, MEDIO: 2, ALTO: 3, CRÍTICO: 4 };
const numeroANivel = { 1: "BAJO", 2: "MEDIO", 3: "ALTO", 4: "CRÍTICO" };

function fechaCorta(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
function fechaLarga(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
function toggleEntrada(id) {
  entradaAbierta.value = entradaAbierta.value === id ? null : id;
}

const tieneSerie = computed(() => data.value?.serie_temporal?.length > 0);
const entradasDiario = computed(() => data.value?.entradas_diario || []);

// Etiquetas legibles para el chip de mood (mismas del diario del estudiante)
const moodLabel = {
  soleado: "Buen día",
  mixto: "Mezclado",
  nublado: "Apagado",
  lluvioso: "Difícil",
};

function colorPorNivel(nivel) {
  if (nivel === "CRÍTICO") return "#DC2626";
  if (nivel === "ALTO") return "#F97316";
  if (nivel === "MEDIO") return "#F59E0B";
  return "#10B981";
}

function dibujarGrafico() {
  if (!chartCanvas.value || !tieneSerie.value) return;
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
  const serie = data.value.serie_temporal;
  const labels = serie.map((p) => fechaCorta(p.fecha));
  const valores = serie.map((p) => nivelANumero[p.nivel] || 0);
  const colores = serie.map((p) => colorPorNivel(p.nivel));
  // Marcador distinto por fuente: círculo chatbot, triángulo diario.
  const estilosPunto = serie.map((p) =>
    p.fuente === "diario" ? "triangle" : "circle",
  );

  chartInstance = new Chart(chartCanvas.value.getContext("2d"), {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Nivel de riesgo",
          data: valores,
          borderColor: "#10B981",
          backgroundColor: "rgba(16, 185, 129, 0.10)",
          borderWidth: 2.5,
          fill: true,
          tension: 0.35,
          pointBackgroundColor: colores,
          pointBorderColor: "#fff",
          pointBorderWidth: 2,
          pointRadius: 8,
          pointHoverRadius: 10,
          pointStyle: estilosPunto,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const p = serie[ctx.dataIndex];
              const fuente = p.fuente === "diario" ? "Diario" : "Chatbot";
              return `${p.nivel} · ${fuente}${
                p.score != null ? ` (${p.score.toFixed(2)})` : ""
              }`;
            },
          },
        },
      },
      scales: {
        y: {
          min: 0,
          max: 4,
          ticks: { stepSize: 1, callback: (v) => numeroANivel[v] || "" },
          grid: { color: "#EEF0F2" },
        },
        x: { grid: { display: false } },
      },
    },
  });
}

onMounted(async () => {
  try {
    const [hist, res] = await Promise.all([
      api.historialEstudiante(route.params.id),
      api.resumenDiarioEstudiante(route.params.id),
      cargarMensajes(),
    ]);
    data.value = hist;
    resumen.value = res;
    // Reporte clínico del ciclo en curso (PHQ-A por días-con-síntoma,
    // tabla literal Johnson 2002). No bloquea si falla.
    try {
      reporteCiclo.value = await api.reporteCicloEstudiante(route.params.id);
    } catch (_) {
      reporteCiclo.value = null;
    }
    await nextTick();
    dibujarGrafico();
  } catch (e) {
    error.value = e.response?.data?.detail || e.message;
  } finally {
    cargando.value = false;
  }
});

// Etiqueta humana de la confiabilidad
const etiquetaConfiabilidad = computed(() => {
  if (!reporteCiclo.value) return null;
  const c = reporteCiclo.value.confiabilidad;
  if (c === "alta") return { texto: "Confiabilidad alta", tono: "bg-green-100 text-green-800" };
  if (c === "media") return { texto: "Confiabilidad media", tono: "bg-amber-100 text-amber-800" };
  return { texto: "Confiabilidad baja", tono: "bg-red-100 text-red-800" };
});

// Modal cita
const modalCita = reactive({
  abierto: false,
  fecha: "",
  hora: "",
  modalidad: "presencial",
  notas: "",
  es_crisis: false,
  guardando: false,
  error: "",
  exito: false,
});
function abrirModalCita() {
  Object.assign(modalCita, {
    abierto: true,
    fecha: "",
    hora: "",
    modalidad: "presencial",
    notas: "",
    es_crisis: false,
    error: "",
    exito: false,
  });
}
function cerrarModal() {
  modalCita.abierto = false;
}
async function guardarCita() {
  modalCita.error = "";
  if (!modalCita.fecha || !modalCita.hora) {
    modalCita.error = "Fecha y hora son obligatorias";
    return;
  }
  modalCita.guardando = true;
  try {
    await api.crearCita({
      estudiante_id: parseInt(route.params.id),
      fecha: modalCita.fecha,
      hora: modalCita.hora,
      modalidad: modalCita.modalidad,
      notas: modalCita.notas || null,
      es_crisis: modalCita.es_crisis,
    });
    modalCita.exito = true;
    setTimeout(cerrarModal, 1500);
  } catch (e) {
    modalCita.error = e.response?.data?.detail || e.message;
  } finally {
    modalCita.guardando = false;
  }
}
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/psicologo')" class="btn-ghost btn-sm mb-3">
      Volver a estudiantes
    </button>

    <div v-if="cargando" class="text-center text-ink-500 py-16">
      Cargando historial…
    </div>
    <p v-else-if="error" class="banner-danger">{{ error }}</p>

    <div v-else-if="data" class="space-y-6">
      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- BANNER DE ALERTA CRÍTICA                                    -->
      <!-- Por privacidad solo se muestran las frases-señal, nunca el  -->
      <!-- texto completo del diario.                                  -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <div
        v-if="resumen?.alerta_critica"
        class="card border-l-4 border-l-red-600 bg-red-50/60 p-5 fade-in-up"
        role="alert"
      >
        <div class="flex items-start gap-4">
          <div
            class="shrink-0 w-10 h-10 rounded-xl bg-red-600 text-white flex items-center justify-center font-bold text-lg"
          >
            !
          </div>
          <div class="min-w-0 flex-1">
            <p
              class="text-xs font-bold text-red-700 uppercase tracking-wider mb-1"
            >
              Alerta crítica detectada
            </p>
            <p class="text-sm text-ink-900 font-medium mb-2">
              {{ resumen.alerta_critica.motivo }}
            </p>
            <p class="text-xs text-ink-600 mb-3">
              {{ fechaLarga(resumen.alerta_critica.fecha) }} · Nivel
              <strong>{{ resumen.alerta_critica.nivel_riesgo }}</strong>
            </p>

            <div
              v-if="resumen.alerta_critica.frases_detectadas?.length"
              class="bg-white/70 rounded-xl p-3 border border-red-100"
            >
              <p
                class="text-[11px] font-semibold text-red-700 uppercase tracking-wider mb-2"
              >
                Frases que dispararon la señal
              </p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="(f, i) in resumen.alerta_critica.frases_detectadas"
                  :key="i"
                  class="inline-flex items-center gap-1 px-2.5 py-1 bg-red-100 text-red-800 rounded-md text-xs font-medium"
                >
                  "{{ f }}"
                </span>
              </div>
              <p class="text-[11px] text-ink-500 mt-2 italic">
                Por privacidad no se muestra el contenido completo del diario.
              </p>
            </div>
          </div>
        </div>
      </div>

      <PageHeader
        :title="`${data.estudiante.nombre} ${data.estudiante.apellido}`"
        :subtitle="data.estudiante.email"
        tone="brand"
      >
        <template #actions>
          <button @click="abrirModalCita" class="btn-primary btn-sm mt-3">
            + Agendar cita
          </button>
        </template>
        <template #aside>
          <div class="text-right">
            <p
              class="text-xs uppercase tracking-wider text-ink-400 font-semibold"
            >
              Último riesgo
            </p>
            <div class="mt-1.5">
              <RiskBadge
                :nivel="data.estudiante.ultimo_riesgo"
                :score="data.estudiante.ultimo_score"
              />
            </div>
            <p class="text-xs text-ink-500 mt-1.5">
              {{ fechaCorta(data.estudiante.ultima_evaluacion) }}
              <span
                v-if="data.estudiante.fuente_ultima"
                class="ml-1 text-ink-400"
              >
                ·
                {{
                  data.estudiante.fuente_ultima === "diario"
                    ? "Diario"
                    : "Chatbot"
                }}
              </span>
            </p>
          </div>
        </template>
      </PageHeader>

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- ESTADO DE EVALUACIÓN (ventana de 14 días)                   -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <section v-if="resumen" class="card p-6 fade-in-up">
        <div class="flex items-start justify-between gap-4 flex-wrap">
          <div class="min-w-0">
            <p
              class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
            >
              Estado de evaluación
            </p>
            <h2 class="text-xl font-bold text-ink-900 mt-1">
              <span v-if="resumen.estado_evaluacion === 'completo'"
                >Análisis consolidado</span
              >
              <span v-else-if="resumen.estado_evaluacion === 'en_proceso'"
                >En proceso de evaluación</span
              >
              <span v-else>Sin datos todavía</span>
            </h2>
            <p class="text-sm text-ink-600 mt-1 max-w-2xl">
              {{ resumen.mensaje }}
            </p>
          </div>
          <div class="text-right shrink-0">
            <p class="text-3xl font-bold text-green-700">
              {{ resumen.porcentaje_completado }}%
            </p>
            <p class="text-xs text-ink-500">
              {{ resumen.dias_transcurridos }} /
              {{ resumen.dias_objetivo }} días
            </p>
          </div>
        </div>

        <!-- Barra de progreso -->
        <div class="mt-4 h-2 bg-ink-100 rounded-full overflow-hidden">
          <div
            class="h-full transition-all duration-500"
            :class="{
              'bg-green-600': resumen.estado_evaluacion === 'completo',
              'bg-amber-500': resumen.estado_evaluacion === 'en_proceso',
              'bg-ink-300': resumen.estado_evaluacion === 'sin_datos',
            }"
            :style="`width: ${resumen.porcentaje_completado}%`"
          ></div>
        </div>
      </section>

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- MÉTRICAS AGREGADAS (PHQ-9 prom, GAD-7 prom, entradas)       -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <section
        v-if="resumen?.resumen?.entradas_en_ventana"
        class="grid grid-cols-1 sm:grid-cols-4 gap-4 fade-in-up"
      >
        <StatCard
          label="Entradas (14 días)"
          :value="resumen.resumen.entradas_en_ventana"
          tone="brand"
        />
        <StatCard
          label="PHQ-9 promedio"
          :value="
            resumen.resumen.phq9_promedio !== null
              ? `${resumen.resumen.phq9_promedio}/27`
              : '—'
          "
          :subtitle="resumen.resumen.severidad_dominante"
          tone="mint"
        />
        <StatCard
          label="GAD-7 promedio"
          :value="
            resumen.resumen.gad7_promedio !== null
              ? `${resumen.resumen.gad7_promedio}/21`
              : '—'
          "
          tone="mint"
        />
        <StatCard
          label="Nivel dominante"
          :value="resumen.resumen.nivel_dominante || '—'"
          tone="peach"
        />
      </section>

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- REPORTE DEL CICLO ACTUAL (días-con-síntoma → Johnson 2002)  -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <section
        v-if="reporteCiclo && reporteCiclo.dias_escritos != null"
        class="card p-6 fade-in-up"
      >
        <div class="flex flex-wrap items-start justify-between gap-3 mb-1">
          <h2 class="section-title !mb-0">
            Reporte del ciclo
            <span class="text-ink-500 font-normal text-base">
              ({{ reporteCiclo.ciclo_cerrado ? "cerrado" : "en curso" }})
            </span>
          </h2>
          <span
            v-if="etiquetaConfiabilidad"
            class="text-xs font-semibold px-2.5 py-1 rounded-full"
            :class="etiquetaConfiabilidad.tono"
          >
            {{ etiquetaConfiabilidad.texto }}
          </span>
        </div>
        <p class="text-sm text-ink-500 mb-5">
          PHQ-A y GAD-7 calculados contando los <strong>días distintos</strong>
          en que apareció cada síntoma sobre la ventana de 14 días
          (traducción literal de las frases Johnson 2002).
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
          <StatCard
            label="PHQ-A inferido"
            :value="`${reporteCiclo.phqa_total}/27`"
            :subtitle="reporteCiclo.phqa_severidad?.nivel"
            tone="brand"
          />
          <StatCard
            label="GAD-7 inferido"
            :value="`${reporteCiclo.gad7_total}/21`"
            :subtitle="reporteCiclo.gad7_severidad?.nivel"
            tone="mint"
          />
          <StatCard
            label="Cobertura"
            :value="`${reporteCiclo.dias_escritos}/${reporteCiclo.dias_ciclo}`"
            :subtitle="`${reporteCiclo.cobertura_pct}% días escritos`"
            tone="peach"
          />
        </div>

        <div
          v-if="reporteCiclo.confiabilidad === 'baja'"
          class="text-sm text-red-800 bg-red-50 border-l-4 border-l-red-600 rounded-md p-3 mb-4"
        >
          El alumno escribió menos de 5 días en este ciclo. Los puntajes
          son orientativos — no usarlos como base para decisión clínica.
        </div>

        <div v-if="reporteCiclo.items_detalle?.length">
          <h3 class="text-sm font-semibold text-ink-900 mb-2 mt-2">
            Detalle por ítem
          </h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="text-left text-ink-500">
                <tr class="border-b border-ink-100">
                  <th class="py-2 pr-3 font-medium">Ítem</th>
                  <th class="py-2 pr-3 font-medium">Módulo</th>
                  <th class="py-2 pr-3 font-medium">DSM-5</th>
                  <th class="py-2 pr-3 font-medium">Días</th>
                  <th class="py-2 pr-3 font-medium">Puntos</th>
                  <th class="py-2 font-medium">Frase oficial</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="it in reporteCiclo.items_detalle"
                  :key="it.item"
                  class="border-b border-ink-50 last:border-0"
                >
                  <td class="py-2 pr-3 font-mono text-xs text-ink-700">
                    {{ it.item }}
                  </td>
                  <td class="py-2 pr-3">
                    <span
                      class="text-xs px-2 py-0.5 rounded-full"
                      :class="
                        it.modulo === 'PHQ-9'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-sky-100 text-sky-800'
                      "
                    >
                      {{ it.modulo }}
                    </span>
                  </td>
                  <td class="py-2 pr-3 text-ink-600 text-xs">
                    {{ it.criterio_dsm5 || "—" }}
                  </td>
                  <td class="py-2 pr-3 tabular-nums">{{ it.dias_con_sintoma }}</td>
                  <td class="py-2 pr-3 tabular-nums font-semibold">
                    {{ it.puntos }}
                  </td>
                  <td class="py-2 text-ink-700">{{ it.frase_likert }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <p
          v-else
          class="text-sm text-ink-500 italic"
        >
          Todavía no hay ítems activados en este ciclo.
        </p>
      </section>

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- CONDICIONES MÁS RECURRENTES (BERT)                          -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <section
        v-if="resumen?.resumen?.condiciones_top?.length"
        class="card p-6 fade-in-up"
      >
        <h2 class="section-title !mb-3">Señales más recurrentes</h2>
        <p class="text-sm text-ink-500 mb-4">
          Lo que el sistema está detectando con más frecuencia en lo que escribe
          el alumno.
        </p>
        <ul class="space-y-3">
          <li
            v-for="c in resumen.resumen.condiciones_top"
            :key="c.condicion"
            class="flex items-center gap-3"
          >
            <span class="chip-brand min-w-[140px] text-center">{{
              c.etiqueta
            }}</span>
            <div class="flex-1 min-w-0">
              <div class="h-2 bg-ink-100 rounded-full overflow-hidden">
                <div
                  class="h-full bg-green-600"
                  :style="`width: ${Math.min(c.confianza_promedio, 100)}%`"
                ></div>
              </div>
            </div>
            <span class="text-sm text-ink-700 font-medium tabular-nums w-24 text-right">
              {{ c.veces_detectada }}× · {{ c.confianza_promedio }}%
            </span>
          </li>
        </ul>
      </section>

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- MENSAJES AL ESTUDIANTE                                       -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <section class="card p-6 fade-in-up">
        <h2 class="section-title !mb-2">Mensaje al estudiante</h2>
        <p class="text-sm text-ink-500 mb-4">
          Lo verá en su panel de apoyo. Frases cortas, claras. No incluye
          diagnósticos ni notas clínicas privadas.
        </p>

        <div class="space-y-3">
          <textarea
            v-model="nuevoMensaje"
            rows="3"
            maxlength="1000"
            class="input resize-none"
            placeholder="Ej: Buen trabajo escribiendo esta semana. Recordá lo que conversamos sobre dormir antes de las 12."
          ></textarea>
          <div class="flex items-center justify-between gap-3">
            <p class="text-xs text-ink-500">
              {{ nuevoMensaje.length }}/1000
            </p>
            <button
              @click="enviarMensaje"
              :disabled="!nuevoMensaje.trim() || guardandoMensaje"
              class="btn-primary btn-sm"
            >
              {{ guardandoMensaje ? "Enviando…" : "Enviar mensaje" }}
            </button>
          </div>
          <p v-if="errorMensaje" class="field-error">{{ errorMensaje }}</p>
        </div>

        <div v-if="mensajes.length" class="mt-6">
          <p
            class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold mb-2"
          >
            Mensajes enviados ({{ mensajes.length }})
          </p>
          <ul class="divide-y divide-ink-100">
            <li
              v-for="m in mensajes"
              :key="m.id"
              class="py-3 flex items-start justify-between gap-3"
            >
              <div class="min-w-0 flex-1">
                <p
                  class="text-sm text-ink-900 leading-relaxed whitespace-pre-wrap"
                >
                  {{ m.mensaje }}
                </p>
                <p class="text-[11px] text-ink-500 mt-1">
                  {{ fechaLarga(m.created_at) }} ·
                  <span :class="m.leido ? 'text-green-700' : 'text-amber-700'">
                    {{ m.leido ? "Leído" : "Sin leer" }}
                  </span>
                </p>
              </div>
              <button
                @click="borrarMensaje(m.id)"
                class="text-ink-400 hover:text-red-600 text-xs font-semibold shrink-0"
              >
                Borrar
              </button>
            </li>
          </ul>
        </div>
      </section>

      <section v-if="tieneSerie" class="card p-6 fade-in-up">
        <div class="flex items-baseline justify-between gap-3 flex-wrap mb-2">
          <h2 class="section-title !mb-0">Evolución</h2>
          <div class="flex items-center gap-3 text-xs text-ink-500">
            <span class="inline-flex items-center gap-1.5">
              <svg width="10" height="10" viewBox="0 0 10 10">
                <circle cx="5" cy="5" r="4" fill="#10B981" />
              </svg>
              Chatbot
            </span>
            <span class="inline-flex items-center gap-1.5">
              <svg width="11" height="11" viewBox="0 0 11 11">
                <polygon points="5.5,1 10,10 1,10" fill="#10B981" />
              </svg>
              Diario
            </span>
          </div>
        </div>
        <div class="h-64 mt-3"><canvas ref="chartCanvas"></canvas></div>
      </section>

      <!-- ═══════════════════════════════════════════════════════════ -->
      <!-- ENTRADAS DEL DIARIO (con análisis BETO)                     -->
      <!-- ═══════════════════════════════════════════════════════════ -->
      <section class="card overflow-hidden fade-in-up">
        <div class="p-6 pb-4 flex items-baseline justify-between gap-3">
          <h2 class="section-title !mb-0">Entradas del diario</h2>
          <p class="text-xs text-ink-500">
            {{ entradasDiario.length }} en total
          </p>
        </div>

        <p
          v-if="entradasDiario.length === 0"
          class="text-ink-500 text-center py-10 px-6"
        >
          Este estudiante todavía no ha escrito en el diario.
        </p>

        <ul v-else class="divide-y divide-ink-100 border-t border-ink-100">
          <li v-for="e in entradasDiario" :key="`d-${e.id}`">
            <button
              @click="toggleEntrada(e.id)"
              class="w-full text-left px-6 py-4 flex items-center justify-between gap-4 hover:bg-green-50/50 transition"
              :class="{
                'bg-red-50/40': e.analisis?.crisis_protocolo,
              }"
            >
              <div class="flex items-center gap-3 flex-wrap">
                <RiskBadge
                  v-if="e.analisis"
                  :nivel="e.analisis.nivel_riesgo"
                  :score="e.analisis.score"
                />
                <span v-else class="risk-sin">Análisis pendiente</span>
                <span class="text-sm text-ink-700">{{
                  fechaLarga(e.timestamp)
                }}</span>
                <span v-if="e.estado_animo" class="chip-ink capitalize">
                  {{ moodLabel[e.estado_animo] || e.estado_animo }}
                </span>
                <span v-if="e.analisis?.crisis_protocolo" class="risk-critico">
                  Crisis detectada
                </span>
              </div>
              <span
                class="text-green-700 text-xs font-semibold whitespace-nowrap"
              >
                {{ entradaAbierta === e.id ? "▲ Ocultar" : "▼ Ver detalle" }}
              </span>
            </button>

            <div
              v-if="entradaAbierta === e.id"
              class="px-6 pb-6 bg-white border-t border-ink-100 fade-in-up"
            >
              <!-- Prompt mostrado (si hubo) -->
              <p
                v-if="e.prompt_del_dia"
                class="text-xs text-ink-500 mt-4 italic"
              >
                Prompt del día: "{{ e.prompt_del_dia }}"
              </p>

              <!-- Texto del alumno: NO se muestra por privacidad.        -->
              <!-- Solo el análisis clínico, ítems y condiciones detectadas. -->
              <div class="bg-ink-50 rounded-xl p-3 mt-3 flex items-start gap-2">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  class="text-ink-400 mt-0.5 shrink-0"
                  aria-hidden="true"
                >
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <p class="text-xs text-ink-500 italic leading-relaxed">
                  El contenido del diario es personal del estudiante. Solo se
                  muestran las señales clínicas detectadas por el sistema.
                </p>
              </div>

              <!-- Análisis BETO -->
              <div v-if="e.analisis" class="mt-4 space-y-3">
                <!-- Resumen PHQ-9 / GAD-7 -->
                <div class="grid sm:grid-cols-2 gap-3">
                  <div class="card p-4">
                    <p
                      class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
                    >
                      PHQ-9 — Depresión
                    </p>
                    <p class="text-2xl font-semibold text-ink-900 mt-1">
                      {{ e.analisis.phq9_total
                      }}<span class="text-base text-ink-400">/27</span>
                    </p>
                    <p class="text-xs text-ink-600 mt-1">
                      {{ e.analisis.phq9_severidad }}
                    </p>
                  </div>
                  <div class="card p-4">
                    <p
                      class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
                    >
                      GAD-7 — Ansiedad
                    </p>
                    <p class="text-2xl font-semibold text-ink-900 mt-1">
                      {{ e.analisis.gad7_total
                      }}<span class="text-base text-ink-400">/21</span>
                    </p>
                    <p class="text-xs text-ink-600 mt-1">
                      {{ e.analisis.gad7_severidad }}
                    </p>
                  </div>
                </div>

                <!-- Ítems PHQ-9/GAD-7 detectados -->
                <div
                  v-if="e.analisis.items_detectados?.length"
                  class="card p-4"
                >
                  <p
                    class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold mb-3"
                  >
                    Señales clínicas detectadas en el texto
                  </p>
                  <ul class="space-y-2">
                    <li
                      v-for="(it, i) in e.analisis.items_detectados"
                      :key="i"
                      class="flex items-start gap-3 text-sm"
                    >
                      <span class="dsm5-tag shrink-0">
                        {{ it.modulo }} · {{ it.item }}
                      </span>
                      <div class="min-w-0">
                        <p class="text-ink-900 font-medium">
                          {{ it.criterio_dsm5 }}
                          <span class="text-ink-500 font-normal">
                            · score {{ it.score }}/3</span
                          >
                        </p>
                        <p
                          v-if="it.keywords?.length"
                          class="text-xs text-ink-500 mt-0.5"
                        >
                          Disparada por:
                          <span
                            v-for="(kw, k) in it.keywords"
                            :key="k"
                            class="italic"
                            >"{{ kw }}"<span v-if="k < it.keywords.length - 1"
                              >,
                            </span></span
                          >
                        </p>
                      </div>
                    </li>
                  </ul>
                </div>

                <!-- Condiciones BERT -->
                <div
                  v-if="
                    e.analisis.condiciones_detectadas &&
                    Object.keys(e.analisis.condiciones_detectadas).length
                  "
                  class="card p-4"
                >
                  <p
                    class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold mb-3"
                  >
                    Condiciones BERT (sobre el umbral)
                  </p>
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-for="(c, k) in e.analisis.condiciones_detectadas"
                      :key="k"
                      class="chip-brand"
                    >
                      {{ c.etiqueta }} · {{ c.confianza }}%
                    </span>
                  </div>
                </div>
              </div>

              <p v-else class="text-sm text-ink-500 italic mt-4">
                El análisis BETO está pendiente o falló para esta entrada.
              </p>
            </div>
          </li>
        </ul>
      </section>

    </div>

    <!-- Modal cita -->
    <Teleport to="body">
      <div
        v-if="modalCita.abierto"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm fade-in-up"
        @click.self="cerrarModal"
      >
        <div class="card-hero w-full max-w-md p-6">
          <h2 class="text-xl font-bold text-ink-900 mb-1">Agendar cita</h2>
          <p class="text-sm text-ink-500 mb-5">
            Con
            <strong
              >{{ data?.estudiante.nombre }}
              {{ data?.estudiante.apellido }}</strong
            >
          </p>

          <div v-if="modalCita.exito" class="text-center py-4">
            <div
              class="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-green-100 text-green-600 text-2xl mb-3"
            ></div>
            <p class="font-bold text-green-600">Cita agendada</p>
          </div>

          <div v-else class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="label">Fecha</label
                ><input v-model="modalCita.fecha" type="date" class="input" />
              </div>
              <div>
                <label class="label">Hora</label
                ><input v-model="modalCita.hora" type="time" class="input" />
              </div>
            </div>
            <div>
              <label class="label">Modalidad</label>
              <select v-model="modalCita.modalidad" class="input">
                <option value="presencial">Presencial</option>
                <option value="virtual">Virtual</option>
              </select>
            </div>
            <div>
              <label class="label"
                >Notas
                <span class="text-ink-400 font-normal">(opcional)</span></label
              >
              <textarea
                v-model="modalCita.notas"
                rows="3"
                class="input resize-none"
              ></textarea>
            </div>

            <label
              class="flex items-start gap-3 rounded-md border border-ink-100 p-3 cursor-pointer hover:border-red-400"
              :class="modalCita.es_crisis ? 'border-red-500 bg-red-50' : ''"
            >
              <input
                type="checkbox"
                v-model="modalCita.es_crisis"
                class="mt-0.5"
              />
              <span class="text-sm leading-snug">
                <strong class="text-red-800">Atención de crisis</strong>
                <span class="block text-ink-600 mt-0.5">
                  Marca solo si esta cita responde a una situación de riesgo
                  (ideación suicida, bullying severo, violencia familiar).
                  Al completarla, adelanta el cierre del ciclo en curso.
                </span>
              </span>
            </label>

            <p v-if="modalCita.error" class="field-error">
              {{ modalCita.error }}
            </p>

            <div class="flex gap-2 pt-2">
              <button
                @click="cerrarModal"
                :disabled="modalCita.guardando"
                class="btn-ghost flex-1"
              >
                Cancelar
              </button>
              <button
                @click="guardarCita"
                :disabled="modalCita.guardando"
                class="btn-primary flex-1"
              >
                {{ modalCita.guardando ? "Guardando…" : "Agendar" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
