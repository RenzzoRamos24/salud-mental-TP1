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
    feedback.value = data.value?.frases_feedback || {};
    if (data.value?.frases_resumen) resumen.value = data.value.frases_resumen;
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

// ── Feedback sobre las clasificaciones de BETO ──────────────────────────
// `feedback` es { numero_de_frase: { veredicto, comentario } }.
const feedback = ref({});
const resumen = ref({
  aceptados: 0, rechazados: 0, revisadas: 0,
  sin_revisar: 0, total: 0, tasa_acierto: null,
});
const metricas = ref(null);
const guardando = ref(null);      // número de frase en curso, para deshabilitar
const errorFeedback = ref({});

function veredictoDe(numero) {
  return feedback.value?.[numero]?.veredicto || null;
}

/**
 * Vota sobre una frase. Volver a pulsar el mismo botón quita el veredicto,
 * así la psicóloga puede corregirse sin quedar atrapada en una elección.
 */
async function votar(numero, veredicto) {
  if (guardando.value !== null) return;
  guardando.value = numero;
  errorFeedback.value = { ...errorFeedback.value, [numero]: "" };

  const actual = veredictoDe(numero);
  const previo = { ...feedback.value };
  const quitar = actual === veredicto;

  // Actualización optimista: la UI responde al instante.
  const optimista = { ...feedback.value };
  if (quitar) delete optimista[numero];
  else optimista[numero] = { ...(optimista[numero] || {}), veredicto };
  feedback.value = optimista;

  try {
    const r = quitar
      ? await api.quitarFeedbackFrase(aplicacionId.value, numero)
      : await api.feedbackFrase(aplicacionId.value, numero, veredicto);
    if (r?.resumen) resumen.value = r.resumen;
    await cargarMetricas();
  } catch (e) {
    feedback.value = previo;   // revierte si el servidor rechazó
    errorFeedback.value = {
      ...errorFeedback.value,
      [numero]: e?.response?.data?.detail || "No se pudo guardar el veredicto.",
    };
  } finally {
    guardando.value = null;
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
      <header class="mb-6">
        <p class="eyebrow mb-2">Resultado del cuestionario</p>
        <h1 class="hero-serif text-[28px]">
          Aplicación <span class="hero-mint">#{{ data.id }}</span>
        </h1>
        <p class="text-sm text-ink-500 mt-2">
          Estudiante: {{ data.estudiante_id }} — Completado el
          {{ fmtFecha(data.completada_at) }}
        </p>
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

      <!-- Capa 5: SVM segunda opinión sobre DASS-21 -->
      <div
        v-if="resultado?.svm_segunda_opinion"
        class="card p-5 mb-6"
        :class="resultado.svm_segunda_opinion.discrepancia_con_reglas ? 'border-amber-300 bg-amber-50' : 'border-green-200 bg-green-50/60'"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-wide text-ink-500 font-semibold">
              Segunda opinión · SVM sobre DASS-21
            </p>
            <p class="text-lg font-semibold mt-1">
              {{ resultado.svm_segunda_opinion.clase === 'en_riesgo' ? 'En riesgo' : 'Sin riesgo' }}
              <span class="text-sm font-normal text-ink-500 ml-2">
                · confianza {{ resultado.svm_segunda_opinion.confianza }}
              </span>
            </p>
            <p class="text-xs text-ink-500 mt-2">
              Probabilidad estimada: {{ (resultado.svm_segunda_opinion.probabilidad * 100).toFixed(1) }} %
              · Dataset: {{ resultado.svm_segunda_opinion.dataset }}
            </p>
          </div>
          <span
            v-if="resultado.svm_segunda_opinion.discrepancia_con_reglas"
            class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-amber-100 text-amber-800 text-xs font-semibold border border-amber-300"
          >
            ⚠ Discrepa con las reglas — revisar
          </span>
          <span
            v-else
            class="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-800 text-xs font-semibold border border-green-300"
          >
            ✓ Coincide con las reglas
          </span>
        </div>

        <!-- Detalle DASS-21 · qué respondió el alumno, agrupado por subescala.
             Esto le permite a la psicóloga validar la opinión del SVM: si
             levanta bandera, ver dónde específicamente están los puntajes
             altos. -->
        <div v-if="dass21Detalle" class="mt-5 pt-5 border-t border-current border-opacity-20">
          <p class="text-xs uppercase tracking-wide text-ink-500 font-semibold mb-3">
            Qué respondió el alumno · 21 ítems agrupados por subescala
          </p>

          <!-- Subtotales por subescala con severidad clínica -->
          <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="p-3 rounded-lg bg-white/70 border border-gray-200">
              <p class="text-[10px] uppercase tracking-wide text-ink-500 font-semibold">Depresión</p>
              <p class="text-xl font-bold mt-1">{{ dass21Detalle.subtotales.depresion }}</p>
              <span :class="'inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold mt-1 ' + colorSev(sevDep(dass21Detalle.subtotales.depresion))">
                {{ sevDep(dass21Detalle.subtotales.depresion) }}
              </span>
            </div>
            <div class="p-3 rounded-lg bg-white/70 border border-gray-200">
              <p class="text-[10px] uppercase tracking-wide text-ink-500 font-semibold">Ansiedad</p>
              <p class="text-xl font-bold mt-1">{{ dass21Detalle.subtotales.ansiedad }}</p>
              <span :class="'inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold mt-1 ' + colorSev(sevAns(dass21Detalle.subtotales.ansiedad))">
                {{ sevAns(dass21Detalle.subtotales.ansiedad) }}
              </span>
            </div>
            <div class="p-3 rounded-lg bg-white/70 border border-gray-200">
              <p class="text-[10px] uppercase tracking-wide text-ink-500 font-semibold">Estrés</p>
              <p class="text-xl font-bold mt-1">{{ dass21Detalle.subtotales.estres }}</p>
              <span :class="'inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold mt-1 ' + colorSev(sevEst(dass21Detalle.subtotales.estres))">
                {{ sevEst(dass21Detalle.subtotales.estres) }}
              </span>
            </div>
          </div>

          <!-- Los 21 ítems, uno por fila -->
          <div class="space-y-1.5">
            <div
              v-for="grupo in [{ key: 'D', label: 'Depresión' }, { key: 'A', label: 'Ansiedad' }, { key: 'S', label: 'Estrés' }]"
              :key="grupo.key"
            >
              <p class="text-[10px] uppercase tracking-wide text-ink-500 font-semibold mt-3 mb-1">{{ grupo.label }}</p>
              <div
                v-for="it in dass21Items[grupo.key]"
                :key="it.numero"
                class="flex items-start gap-3 text-sm py-1 border-b border-gray-200 border-opacity-30 last:border-0"
              >
                <span class="w-6 text-right text-ink-500 font-mono text-xs pt-0.5">{{ it.numero }}.</span>
                <span class="flex-1 text-ink-700">{{ it.texto }}</span>
                <span
                  :class="'inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold whitespace-nowrap ' + colorValor(it.valor)"
                >
                  {{ it.valor !== null ? it.valor : '—' }} · {{ it.etiqueta || 'sin dato' }}
                </span>
              </div>
            </div>
          </div>

          <p class="text-[11px] text-ink-500 mt-4 italic">
            Subtotales multiplicados × 2 para equipararlos a la escala DASS-42 (Lovibond &amp; Lovibond, 1995).
            Cortes clínicos aplicados según normas validadas para adolescentes.
          </p>
        </div>
      </div>

      <!-- Bloques por instrumento / custom -->
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
        <div class="flex flex-wrap items-end justify-between gap-3 mb-3">
          <div>
            <h2 class="text-lg font-semibold">Frases incompletas</h2>
            <p class="text-xs text-ink-400 mt-0.5">
              Marca si la categoría que asignó el modelo es correcta. Tu
              veredicto alimenta la métrica de precisión del clasificador.
            </p>
          </div>

          <!-- Conteo de esta aplicación -->
          <div class="flex items-center gap-2 text-xs">
            <span
              class="px-2.5 py-1 rounded-full bg-green-50 text-green-700 border border-green-200"
              title="Clasificaciones que diste por correctas"
            >
              {{ resumen.aceptados }} aceptadas
            </span>
            <span
              class="px-2.5 py-1 rounded-full bg-coral-50 text-risk-critico border border-coral-200"
              title="Clasificaciones que descartaste por incorrectas"
            >
              {{ resumen.rechazados }} descartadas
            </span>
            <span
              v-if="resumen.sin_revisar > 0"
              class="px-2.5 py-1 rounded-full bg-cream-100 text-ink-400 border border-cream-200"
            >
              {{ resumen.sin_revisar }} sin revisar
            </span>
            <span
              v-if="resumen.tasa_acierto !== null"
              class="px-2.5 py-1 rounded-full bg-mint-50 text-green-700 border border-mint-200 font-semibold"
              title="Aceptadas sobre el total de revisadas"
            >
              {{ Math.round(resumen.tasa_acierto * 100) }}% de acierto
            </span>
          </div>
        </div>

        <div class="grid gap-3">
          <div
            v-for="f in resultado.frases"
            :key="`${f.area}-${f.numero}`"
            class="card p-4 transition-opacity"
            :class="{
              'border-red-300': f.crisis && veredictoDe(f.numero) !== 'rechazado',
              'opacity-60': veredictoDe(f.numero) === 'rechazado',
            }"
          >
            <p class="text-xs text-ink-400 mb-1">{{ f.area }} — #{{ f.numero }}</p>
            <p class="text-sm italic text-ink-500 mb-2">{{ f.pregunta }}</p>
            <p class="font-medium">"{{ f.respuesta }}"</p>

            <div class="flex flex-wrap items-center gap-1 mt-3">
              <span
                v-for="d in f.detectadas"
                :key="d"
                class="chip-mint text-xs"
                :class="{ 'line-through opacity-60': veredictoDe(f.numero) === 'rechazado' }"
              >
                {{ d }}
              </span>
              <span
                v-if="f.crisis"
                class="text-xs px-2 py-0.5 rounded-full border"
                :class="veredictoDe(f.numero) === 'rechazado'
                  ? 'bg-cream-100 text-ink-400 border-cream-200 line-through'
                  : 'bg-red-50 text-red-700 border-red-200'"
              >
                ideación detectada
              </span>
              <span
                v-if="!(f.detectadas || []).length && !f.crisis"
                class="text-xs text-ink-300 italic"
              >
                sin categoría asignada
              </span>

              <!-- Botones de veredicto -->
              <div class="flex items-center gap-1 ml-auto">
                <span
                  v-if="veredictoDe(f.numero)"
                  class="text-[11px] mr-1"
                  :class="veredictoDe(f.numero) === 'aceptado'
                    ? 'text-green-600' : 'text-risk-critico'"
                >
                  {{ veredictoDe(f.numero) === 'aceptado' ? 'Marcada correcta' : 'Descartada' }}
                </span>

                <button
                  type="button"
                  class="text-xs px-2.5 py-1 rounded-full border transition-colors disabled:opacity-40"
                  :class="veredictoDe(f.numero) === 'aceptado'
                    ? 'bg-green-600 text-white border-green-600'
                    : 'bg-white text-ink-400 border-cream-200 hover:border-green-300 hover:text-green-600'"
                  :disabled="guardando === f.numero"
                  :title="veredictoDe(f.numero) === 'aceptado'
                    ? 'Quitar el veredicto' : 'La clasificación es correcta'"
                  @click="votar(f.numero, 'aceptado')"
                >
                  Correcta
                </button>

                <button
                  type="button"
                  class="text-xs px-2.5 py-1 rounded-full border transition-colors disabled:opacity-40"
                  :class="veredictoDe(f.numero) === 'rechazado'
                    ? 'bg-coral-500 text-white border-coral-500'
                    : 'bg-white text-ink-400 border-cream-200 hover:border-coral-300 hover:text-risk-critico'"
                  :disabled="guardando === f.numero"
                  :title="veredictoDe(f.numero) === 'rechazado'
                    ? 'Quitar el veredicto' : 'Descartar: la clasificación es incorrecta'"
                  @click="votar(f.numero, 'rechazado')"
                >
                  Descartar
                </button>
              </div>
            </div>

            <p v-if="errorFeedback[f.numero]" class="text-xs text-risk-critico mt-2">
              {{ errorFeedback[f.numero] }}
            </p>
          </div>
        </div>

        <!-- Acumulado global del clasificador -->
        <div v-if="metricas && metricas.revisadas > 0" class="card p-4 mt-4">
          <h3 class="text-sm font-semibold mb-1">Precisión acumulada del clasificador</h3>
          <p class="text-xs text-ink-400 mb-3">
            Sobre todas las frases que revisaste, no solo las de este cuestionario.
          </p>
          <div class="flex flex-wrap items-center gap-4">
            <div>
              <p class="text-2xl font-semibold text-green-700">
                {{ metricas.tasa_acierto !== null
                    ? Math.round(metricas.tasa_acierto * 100) + '%' : '—' }}
              </p>
              <p class="text-xs text-ink-400">de acierto</p>
            </div>
            <div class="text-sm">
              <p class="text-green-700">{{ metricas.aceptados }} aceptadas</p>
              <p class="text-risk-critico">{{ metricas.rechazados }} descartadas</p>
              <p class="text-ink-400 text-xs mt-0.5">
                {{ metricas.revisadas }} frases revisadas en total
              </p>
            </div>
            <div v-if="(metricas.por_categoria || []).length" class="text-xs ml-auto">
              <p class="text-ink-400 mb-1">Por categoría del modelo</p>
              <div class="flex flex-wrap gap-1.5">
                <span
                  v-for="c in metricas.por_categoria"
                  :key="c.categoria"
                  class="px-2 py-0.5 rounded-full bg-cream-100 border border-cream-200"
                  :title="`${c.aceptados} aceptadas · ${c.rechazados} descartadas`"
                >
                  {{ c.categoria }}:
                  {{ c.tasa_acierto !== null ? Math.round(c.tasa_acierto * 100) + '%' : '—' }}
                </span>
              </div>
            </div>
          </div>
          <p
            v-if="metricas.crisis && metricas.crisis.revisadas > 0"
            class="text-xs text-ink-400 mt-3 pt-3 border-t border-cream-200"
          >
            En frases marcadas como ideación:
            <strong class="text-ink-500">{{ metricas.crisis.aceptados }}</strong> confirmadas ·
            <strong class="text-ink-500">{{ metricas.crisis.rechazados }}</strong> descartadas
            <span v-if="metricas.crisis.tasa_acierto !== null">
              ({{ Math.round(metricas.crisis.tasa_acierto * 100) }}% de acierto)
            </span>
          </p>
        </div>
      </template>
    </template>
  </div>
</template>
