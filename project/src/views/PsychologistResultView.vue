<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

const route = useRoute();
const router = useRouter();
const aplicacionId = computed(() => Number(route.params.id));

const cargando = ref(true);
const error = ref("");
const data = ref(null);

async function cargar() {
  cargando.value = true;
  try {
    data.value = await api.obtenerResultado(aplicacionId.value);
    veredicto.value = data.value?.feedback?.veredicto || null;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(async () => {
  await cargar();
  await cargarMetricas();
});

async function marcarRevisado() {
  try {
    await api.marcarRevisado(aplicacionId.value);
    await cargar();
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo marcar.");
  }
}

const resultado = computed(() => data.value?.resultado || null);
const dass21Detalle = computed(() => data.value?.dass21_detalle || null);
const instrumentos = computed(() => data.value?.instrumentos_detalle || []);
const estudiante = computed(() => data.value?.estudiante || null);

// Nombre a mostrar: código del alumno (SAMI-…) si existe, si no el nombre.
const tituloAlumno = computed(() => {
  const e = estudiante.value;
  if (!e) return "Estudiante";
  if (e.codigo_acceso) return e.codigo_acceso;
  return [e.nombre, e.apellido].filter(Boolean).join(" ") || "Estudiante";
});

// ── Exportar reporte individual / agendar cita ─────────────────────────
// Los endpoints trabajan sobre el estudiante, no sobre la aplicación.
const exportando = ref(false);
async function exportarReporte(formato = "pdf") {
  if (exportando.value || !estudiante.value?.id) return;
  exportando.value = true;
  try {
    const blob =
      formato === "pdf"
        ? await api.descargarReporteIndividual(estudiante.value.id)
        : await api.descargarReporteIndividualWord(estudiante.value.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reporte_${tituloAlumno.value.toLowerCase()}.${formato === "pdf" ? "pdf" : "docx"}`;
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
const exportarPDF = () => exportarReporte("pdf");
const exportarWord = () => exportarReporte("docx");

function agendarCita() {
  if (!estudiante.value?.id) return;
  router.push({ name: "psicologo-citas", query: { estudiante: estudiante.value.id } });
}

// ── Veredicto de la psicóloga sobre el análisis del modelo ─────────────
const veredicto = ref(null);          // 'aceptado' | 'rechazado' | null
const metricas = ref(null);
const guardando = ref(false);
const errorFeedback = ref("");

/**
 * Vota sobre el análisis de este cuestionario. Volver a pulsar el mismo
 * botón quita el veredicto, así la psicóloga puede corregirse sin quedar
 * atrapada en una elección.
 */
async function votar(nuevo) {
  if (guardando.value) return;
  guardando.value = true;
  errorFeedback.value = "";

  const previo = veredicto.value;
  const quitar = previo === nuevo;
  veredicto.value = quitar ? null : nuevo;   // actualización optimista

  try {
    const r = quitar
      ? await api.quitarFeedbackResultado(aplicacionId.value)
      : await api.feedbackResultado(aplicacionId.value, nuevo);
    if (r?.metricas) metricas.value = r.metricas;
  } catch (e) {
    veredicto.value = previo;   // revierte si el servidor rechazó
    errorFeedback.value =
      e?.response?.data?.detail || "No se pudo guardar el veredicto.";
  } finally {
    guardando.value = false;
  }
}

async function cargarMetricas() {
  try {
    metricas.value = await api.metricasClasificador();
  } catch {
    // Las métricas son informativas: si fallan, la pantalla sigue usable.
    metricas.value = null;
  }
}

const dass21Items = computed(() => {
  const d = dass21Detalle.value;
  if (!d) return { D: [], A: [], S: [] };
  const grupos = { D: [], A: [], S: [] };
  for (const it of d.items) grupos[it.subescala]?.push(it);
  return grupos;
});

function sevDep(s) {
  if (s <= 9) return "normal";
  if (s <= 13) return "leve";
  if (s <= 20) return "moderada";
  if (s <= 27) return "severa";
  return "ext. severa";
}
function sevAns(s) {
  if (s <= 7) return "normal";
  if (s <= 9) return "leve";
  if (s <= 14) return "moderada";
  if (s <= 19) return "severa";
  return "ext. severa";
}
function sevEst(s) {
  if (s <= 14) return "normal";
  if (s <= 18) return "leve";
  if (s <= 25) return "moderado";
  if (s <= 33) return "severo";
  return "ext. severo";
}
function colorSev(sev) {
  if (sev.startsWith("normal")) return "text-green-700 bg-green-100";
  if (sev.startsWith("leve")) return "text-yellow-700 bg-yellow-100";
  if (sev.startsWith("moderad")) return "text-orange-700 bg-orange-100";
  return "text-red-700 bg-red-100";
}
function colorValor(v) {
  if (v === 0) return "bg-green-100 text-green-800";
  if (v === 1) return "bg-yellow-100 text-yellow-800";
  if (v === 2) return "bg-orange-100 text-orange-800";
  if (v === 3) return "bg-red-100 text-red-800";
  return "bg-gray-100 text-gray-500";
}

function colorRiesgo(r) {
  const map = {
    CRITICO: "bg-red-50 text-red-700 border-red-200",
    ALTO: "bg-orange-50 text-orange-700 border-orange-200",
    MEDIO: "bg-amber-50 text-amber-700 border-amber-200",
    BAJO: "bg-sky-50 text-sky-700 border-sky-200",
    SIN_RIESGO: "bg-green-50 text-green-700 border-green-200",
  };
  return map[r] || "bg-gray-50 text-gray-700 border-gray-200";
}

function colorBloque(b) {
  if (b.bandera_crisis || b.severidad_alerta) {
    return "bg-amber-50 border-amber-200";
  }
  return "bg-green-50 border-green-200";
}

function fmtFecha(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE");
}
</script>

<template>
  <div class="page-shell-wide">
    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <header class="mb-6 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <p class="eyebrow mb-2">Resultado del cuestionario</p>
          <h1 class="hero-serif text-[28px]">
            <span class="hero-mint">{{ tituloAlumno }}</span>
          </h1>
          <p class="text-sm text-ink-500 mt-2">
            <span v-if="estudiante?.nombre">
              {{ estudiante.nombre }} {{ estudiante.apellido }} ·
            </span>
            <span v-if="estudiante?.grado">{{ estudiante.grado }} · </span>
            Aplicación #{{ data.id }} (CASO-{{ String(data.id).padStart(3, "0") }})
            · Completado el {{ fmtFecha(data.completada_at) }}
          </p>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <button class="btn-ghost" @click="agendarCita">+ Cita</button>
          <button class="btn-ghost" :disabled="exportando" @click="exportarPDF">
            {{ exportando ? "Generando…" : "Exportar PDF" }}
          </button>
          <button class="btn-ghost" :disabled="exportando" @click="exportarWord">
            Exportar Word
          </button>
        </div>
      </header>

      <div
        v-if="resultado?.crisis_activada"
        class="banner-danger mb-4"
      >
        PROTOCOLO DE CRISIS ACTIVADO. Revisa de inmediato las respuestas
        marcadas y deriva según protocolo.
      </div>

      <div class="grid sm:grid-cols-2 gap-4 mb-6">
        <div class="card p-6 text-center">
          <p class="text-xs text-ink-400 mb-2">Riesgo global</p>
          <span
            class="inline-block px-4 py-2 rounded-full border text-lg font-semibold"
            :class="colorRiesgo(resultado?.riesgo_global)"
          >
            {{ resultado?.riesgo_global || "—" }}
          </span>
          <p class="text-xs text-ink-500 mt-3">
            {{ resultado?.n_senales || 0 }} señales en zona de alerta sobre
            {{ resultado?.n_bloques || 0 }} bloques.
          </p>
        </div>

        <div class="card p-6">
          <p class="text-xs text-ink-400 mb-2">Estado</p>
          <p class="font-semibold capitalize">{{ data.estado }}</p>
          <button
            v-if="data.estado === 'completado'"
            class="btn-mint mt-3 btn-sm"
            @click="marcarRevisado"
          >
            Marcar como revisado
          </button>
        </div>
      </div>

      <!-- Veredicto de la psicóloga sobre el análisis del modelo -->
      <div class="card p-5 mb-6">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-[16rem] flex-1">
            <h2 class="text-base font-semibold">¿El análisis es correcto?</h2>
            <p class="text-xs text-ink-400 mt-1">
              Tu veredicto sobre este cuestionario alimenta la métrica de
              precisión del clasificador. Marcar el análisis como incorrecto
              no borra nada del resultado clínico: solo lo deja registrado
              como fallo del modelo.
            </p>

            <div class="flex flex-wrap items-center gap-3 mt-4">
              <!-- Aceptar: verde sólido. Al elegirlo queda con anillo y check. -->
              <button
                type="button"
                class="text-sm font-semibold px-5 py-2.5 rounded-full border-2 shadow-soft
                       transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                :class="veredicto === 'rechazado'
                  ? 'bg-white text-green-700 border-green-300 hover:bg-green-50'
                  : 'bg-green-600 text-white border-green-600 hover:bg-green-700 hover:border-green-700'"
                :style="veredicto === 'aceptado'
                  ? 'box-shadow: 0 0 0 3px #C5E1DC' : ''"
                :disabled="guardando"
                :title="veredicto === 'aceptado'
                  ? 'Quitar el veredicto' : 'El análisis del modelo es correcto'"
                @click="votar('aceptado')"
              >
                <span v-if="veredicto === 'aceptado'" class="mr-1">✓</span>
                Análisis correcto
              </button>

              <!-- Descartar: rojo sólido, el mismo tono del riesgo crítico. -->
              <button
                type="button"
                class="text-sm font-semibold px-5 py-2.5 rounded-full border-2 shadow-soft
                       transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                :class="veredicto === 'aceptado'
                  ? 'bg-white text-coral-600 border-coral-300 hover:bg-coral-50'
                  : 'bg-coral-600 text-white border-coral-600 hover:bg-red-700 hover:border-red-700'"
                :style="veredicto === 'rechazado'
                  ? 'box-shadow: 0 0 0 3px #FECACA' : ''"
                :disabled="guardando"
                :title="veredicto === 'rechazado'
                  ? 'Quitar el veredicto' : 'El análisis del modelo es incorrecto'"
                @click="votar('rechazado')"
              >
                <span v-if="veredicto === 'rechazado'" class="mr-1">✕</span>
                Análisis incorrecto
              </button>

              <span v-if="guardando" class="text-xs text-ink-400">Guardando…</span>
              <span
                v-else-if="veredicto"
                class="text-xs"
                :class="veredicto === 'aceptado' ? 'text-green-700' : 'text-coral-600'"
              >
                {{ veredicto === 'aceptado'
                    ? 'Marcado como correcto. Podés cambiarlo, o pulsar de nuevo para deshacer.'
                    : 'Marcado como incorrecto. Podés cambiarlo, o pulsar de nuevo para deshacer.' }}
              </span>
            </div>

            <p v-if="errorFeedback" class="text-xs text-risk-critico mt-2">
              {{ errorFeedback }}
            </p>
          </div>

          <!-- Conteo acumulado -->
          <div
            v-if="metricas"
            class="border-l border-cream-200 pl-5 min-w-[13rem]"
          >
            <p class="text-xs text-ink-400 mb-2">Precisión acumulada</p>
            <p class="text-3xl font-semibold text-green-700 leading-none">
              {{ metricas.tasa_acierto !== null
                  ? Math.round(metricas.tasa_acierto * 100) + '%' : '—' }}
            </p>
            <div class="text-sm mt-3 space-y-0.5">
              <p class="text-green-700">
                <strong>{{ metricas.aceptados }}</strong> aceptados
              </p>
              <p class="text-risk-critico">
                <strong>{{ metricas.rechazados }}</strong> descartados
              </p>
              <p v-if="metricas.sin_revisar > 0" class="text-ink-400 text-xs pt-1">
                {{ metricas.sin_revisar }} sin revisar
                de {{ metricas.total_evaluados }}
              </p>
            </div>
          </div>
        </div>

        <!-- Desgloses -->
        <div
          v-if="metricas && metricas.revisados > 0"
          class="mt-4 pt-4 border-t border-cream-200 flex flex-wrap gap-x-6 gap-y-2 text-xs"
        >
          <div v-if="(metricas.por_riesgo || []).length">
            <span class="text-ink-400">Por nivel de riesgo:</span>
            <span
              v-for="r in metricas.por_riesgo"
              :key="r.riesgo"
              class="ml-1.5 px-2 py-0.5 rounded-full bg-cream-100 border border-cream-200"
              :title="`${r.aceptados} aceptados · ${r.rechazados} descartados`"
            >
              {{ r.riesgo }}:
              {{ r.tasa_acierto !== null ? Math.round(r.tasa_acierto * 100) + '%' : '—' }}
            </span>
          </div>
          <div v-if="metricas.crisis && metricas.crisis.revisados > 0" class="text-ink-400">
            En casos con bandera de crisis:
            <strong class="text-ink-500">{{ metricas.crisis.aceptados }}</strong> confirmados ·
            <strong class="text-ink-500">{{ metricas.crisis.rechazados }}</strong> descartados
            <span v-if="metricas.crisis.tasa_acierto !== null">
              ({{ Math.round(metricas.crisis.tasa_acierto * 100) }}%)
            </span>
          </div>
        </div>
      </div>

      <!-- Respuestas ítem por ítem de cada instrumento (PHQ-A, GAD-7, …).
           Deja ver el valor exacto de cada ítem y resalta los ítems con
           bandera de crisis, para poder explicar por qué saltó una alerta. -->
      <section v-if="instrumentos.length" class="mb-6">
        <h2 class="text-lg font-semibold mb-3">Respuestas por ítem</h2>
        <div class="grid gap-4">
          <div
            v-for="instr in instrumentos"
            :key="instr.codigo"
            class="card p-5"
          >
            <div class="flex items-baseline justify-between mb-3">
              <h3 class="font-semibold">
                {{ instr.codigo }}
                <span class="font-normal text-ink-500">— {{ instr.nombre }}</span>
              </h3>
              <span class="text-xs text-ink-400">
                escala {{ instr.likert_min }}–{{ instr.likert_max }}
              </span>
            </div>
            <div class="grid gap-1.5">
              <div
                v-for="it in instr.items"
                :key="it.numero"
                class="flex items-start gap-3 px-3 py-2 rounded-lg text-sm"
                :class="it.es_crisis
                  ? 'bg-red-50 border border-red-200'
                  : 'bg-gray-50/70'"
              >
                <span class="font-mono text-xs text-ink-400 mt-0.5 w-6 shrink-0">
                  {{ it.numero }}
                </span>
                <span class="flex-1">
                  {{ it.texto }}
                  <span
                    v-if="it.es_crisis"
                    class="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 text-[10px] font-semibold border border-red-200"
                  >
                    ítem de crisis
                  </span>
                </span>
                <span
                  class="font-bold tabular-nums shrink-0"
                  :class="it.es_crisis && it.valor >= 1 ? 'text-red-700' : 'text-ink-700'"
                >
                  {{ it.valor }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <h2 class="text-lg font-semibold mb-3">Termómetros por bloque</h2>
      <div class="grid sm:grid-cols-2 gap-3 mb-6">
        <div
          v-for="b in resultado?.bloques || []"
          :key="b.codigo"
          class="rounded-xl border p-4"
          :class="colorBloque(b)"
        >
          <div class="flex items-start justify-between mb-2">
            <div>
              <p class="text-xs text-ink-400">{{ b.dominio }}</p>
              <p class="font-semibold text-green-900">
                {{ b.codigo }}
                <span v-if="b.nombre !== b.codigo" class="font-normal text-ink-500">
                  — {{ b.nombre }}
                </span>
              </p>
            </div>
            <span class="tabular text-sm">
              {{ b.puntaje }} / {{ b.rango_max }}
            </span>
          </div>
          <p class="text-sm font-medium capitalize">{{ b.severidad }}</p>
          <p v-if="b.bandera_crisis" class="text-xs text-red-700 mt-2">
            Bandera de crisis encendida.
          </p>
        </div>
      </div>

      <!-- Frases incompletas -->
      <template v-if="(resultado?.frases || []).length > 0">
        <h2 class="text-lg font-semibold mb-3">Frases incompletas</h2>
        <div class="grid gap-3">
          <div
            v-for="f in resultado.frases"
            :key="`${f.area}-${f.numero}`"
            class="card p-4"
            :class="{ 'border-red-300': f.crisis }"
          >
            <p class="text-xs text-ink-400 mb-1">{{ f.area }} — #{{ f.numero }}</p>
            <p class="text-sm italic text-ink-500 mb-2">{{ f.pregunta }}</p>
            <p class="font-medium">"{{ f.respuesta }}"</p>
            <div class="flex flex-wrap gap-1 mt-3">
              <span
                v-for="d in f.detectadas"
                :key="d"
                class="chip-mint text-xs"
              >
                {{ d }}
              </span>
              <span
                v-if="f.crisis"
                class="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200"
              >
                ideación detectada
              </span>
            </div>
          </div>
        </div>
      </template>

    </template>
  </div>
</template>
