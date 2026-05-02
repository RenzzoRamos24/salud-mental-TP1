<script setup>
import { computed, onMounted, ref } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const props = defineProps({
  resultado: { type: Object, required: true },
  // { session_id, usuario, fecha_analisis, respuestas_analizadas,
  //   resultado: { nivel_riesgo, condiciones_detectadas, scores_completos, explicacion, modelo } }
})
const emit = defineEmits(['reset'])

const canvas = ref(null)
let chartInstance = null

// Mapeo de claves a etiquetas legibles
const ETIQUETAS = {
  depresion: 'Depresión',
  ansiedad: 'Ansiedad',
  tdah: 'TDAH',
  estres_academico: 'Estrés académico',
  soledad: 'Soledad',
  riesgo_suicida: 'Riesgo suicida',
  estabilidad: 'Estabilidad',
}

// Colores por condición
const COLORES = {
  depresion: '#6366f1',
  ansiedad: '#f59e0b',
  tdah: '#14b8a6',
  estres_academico: '#ec4899',
  soledad: '#8b5cf6',
  riesgo_suicida: '#dc2626',
  estabilidad: '#10b981',
}

const r = computed(() => props.resultado.resultado)
const scores = computed(() => r.value.scores_completos || {})
const detectadas = computed(() => r.value.condiciones_detectadas || {})
const numDetectadas = computed(() => Object.keys(detectadas.value).length)

const nivelConfig = computed(() => {
  const map = {
    CRÍTICO: { color: 'bg-red-600',    text: 'text-red-900',    border: 'border-red-600',    bg: 'bg-red-50',    emoji: '🔴' },
    ALTO:    { color: 'bg-orange-500', text: 'text-orange-900', border: 'border-orange-500', bg: 'bg-orange-50', emoji: '🟠' },
    MEDIO:   { color: 'bg-amber-500',  text: 'text-amber-900',  border: 'border-amber-500',  bg: 'bg-amber-50',  emoji: '🟡' },
    BAJO:    { color: 'bg-emerald-500',text: 'text-emerald-900',border: 'border-emerald-500',bg: 'bg-emerald-50',emoji: '🟢' },
  }
  return map[r.value.nivel_riesgo] || map.MEDIO
})

const fechaFormateada = computed(() => {
  try {
    return new Date(props.resultado.fecha_analisis).toLocaleString('es-PE', {
      dateStyle: 'long', timeStyle: 'short',
    })
  } catch { return props.resultado.fecha_analisis }
})

// Conclusión breve para psicólogo (generada en cliente a partir del resultado)
const conclusionPsicologo = computed(() => {
  const nivel = r.value.nivel_riesgo
  const conds = Object.entries(detectadas.value)
    .sort((a, b) => b[1].confianza - a[1].confianza)
    .map(([, v]) => `${v.etiqueta} (${v.confianza}%)`)

  let resumen = `Paciente: ${props.resultado.usuario}. `
  resumen += `Nivel de riesgo global: ${nivel}. `

  if (conds.length === 0) {
    resumen += 'No se detectaron condiciones clínicamente significativas; estabilidad emocional predominante. '
    resumen += 'Recomendación: seguimiento de mantenimiento, refuerzo de hábitos protectores.'
  } else {
    resumen += `Condiciones detectadas (${conds.length}): ${conds.join(', ')}. `
    if (nivel === 'CRÍTICO') {
      resumen += 'ATENCIÓN URGENTE: riesgo suicida activo requiere evaluación inmediata y plan de seguridad.'
    } else if (nivel === 'ALTO') {
      resumen += 'Se sugiere evaluación clínica estructurada (ej. PHQ-9, GAD-7) y plan de intervención.'
    } else if (nivel === 'MEDIO') {
      resumen += 'Monitoreo recomendado; considerar psicoterapia breve y reevaluación en 2–4 semanas.'
    }
  }
  return resumen
})

function construirGrafico() {
  if (!canvas.value) return

  const claves = Object.keys(scores.value)
  const data = claves.map(k => scores.value[k])
  const labels = claves.map(k => ETIQUETAS[k] || k)
  const backgroundColor = claves.map(k => COLORES[k] || '#64748b')
  const umbrales = {
    depresion: 55, ansiedad: 55, tdah: 50,
    estres_academico: 55, soledad: 55, riesgo_suicida: 40, estabilidad: 60,
  }

  chartInstance = new Chart(canvas.value, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Confianza (%)',
        data,
        backgroundColor,
        borderRadius: 6,
        borderWidth: 0,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: (ctx) => {
              const k = claves[ctx.dataIndex]
              const umbral = umbrales[k] || 55
              const det = data[ctx.dataIndex] >= umbral ? '✅ Supera umbral' : '⚪ Bajo umbral'
              return `Umbral: ${umbral}%  ·  ${det}`
            },
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true, max: 100,
          ticks: { callback: v => v + '%' },
          grid: { color: '#e2e8f0' },
        },
        y: { grid: { display: false } },
      },
    },
  })
}

onMounted(() => construirGrafico())

function imprimir() { window.print() }
</script>

<template>
  <div class="min-h-screen bg-slate-50 py-8 px-4">
    <div class="max-w-5xl mx-auto space-y-6">

      <!-- ═══════════════ HEADER ═══════════════ -->
      <header class="bg-white rounded-2xl shadow-md p-6 fade-in-up">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-sm text-slate-500">Informe clínico preliminar</p>
            <h1 class="text-3xl font-bold text-slate-900 mt-1">Perfil Emocional</h1>
            <p class="text-slate-600 mt-1">
              <span class="font-medium">{{ resultado.usuario }}</span>
              &middot; {{ fechaFormateada }}
            </p>
          </div>
          <div class="flex gap-2 no-print">
            <button
              @click="imprimir"
              class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition"
            >
              🖨️ Imprimir / PDF
            </button>
            <button
              @click="emit('reset')"
              class="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg text-sm font-medium transition"
            >
              Nueva evaluación
            </button>
          </div>
        </div>
      </header>

      <!-- ═══════════════ PERFIL + NIVEL DE RIESGO ═══════════════ -->
      <section class="grid md:grid-cols-3 gap-4 fade-in-up">
        <div :class="['md:col-span-2 rounded-2xl border-l-4 p-6 shadow-md', nivelConfig.bg, nivelConfig.border]">
          <p class="text-sm font-medium text-slate-600 uppercase tracking-wide">Nivel de riesgo global</p>
          <div class="flex items-center gap-3 mt-2">
            <span class="text-4xl">{{ nivelConfig.emoji }}</span>
            <span :class="['text-4xl font-bold', nivelConfig.text]">
              {{ r.nivel_riesgo }}
            </span>
          </div>
          <p class="text-slate-700 mt-3 text-sm">
            Análisis basado en <strong>{{ resultado.respuestas_analizadas }}</strong> respuestas
            procesadas con el modelo <strong>BERT</strong> en español.
          </p>
        </div>

        <div class="rounded-2xl bg-white p-6 shadow-md">
          <p class="text-sm font-medium text-slate-600 uppercase tracking-wide">Resumen</p>
          <div class="mt-3 space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Condiciones detectadas</span>
              <span class="font-bold text-slate-900">{{ numDetectadas }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Respuestas analizadas</span>
              <span class="font-bold text-slate-900">{{ resultado.respuestas_analizadas }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-600">Sesión</span>
              <span class="font-mono text-xs text-slate-500 truncate max-w-[120px]" :title="resultado.session_id">
                {{ resultado.session_id.slice(0, 8) }}…
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══════════════ GRÁFICO ═══════════════ -->
      <section class="bg-white rounded-2xl shadow-md p-6 fade-in-up">
        <h2 class="text-xl font-bold text-slate-900 mb-1">📊 Perfil de Condiciones</h2>
        <p class="text-sm text-slate-600 mb-4">
          Probabilidad detectada por el modelo BERT para cada condición clínica evaluada.
        </p>
        <div class="h-80">
          <canvas ref="canvas"></canvas>
        </div>
      </section>

      <!-- ═══════════════ CONDICIONES DETECTADAS ═══════════════ -->
      <section v-if="numDetectadas > 0" class="bg-white rounded-2xl shadow-md p-6 fade-in-up">
        <h2 class="text-xl font-bold text-slate-900 mb-4">🩺 Condiciones Detectadas</h2>
        <div class="grid sm:grid-cols-2 gap-3">
          <div
            v-for="(cond, clave) in detectadas"
            :key="clave"
            class="border border-slate-200 rounded-xl p-4 hover:shadow-md transition"
          >
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-slate-900">{{ cond.etiqueta }}</h3>
              <span
                class="text-xs font-bold px-2 py-1 rounded-full text-white"
                :style="{ backgroundColor: COLORES[clave] || '#64748b' }"
              >
                {{ cond.confianza }}%
              </span>
            </div>
            <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                class="h-full transition-all duration-700"
                :style="{ width: cond.confianza + '%', backgroundColor: COLORES[clave] || '#64748b' }"
              ></div>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══════════════ INDICACIONES / EXPLICACIÓN ═══════════════ -->
      <section class="bg-white rounded-2xl shadow-md p-6 fade-in-up">
        <h2 class="text-xl font-bold text-slate-900 mb-4">💡 Indicaciones e Interpretación</h2>
        <pre class="whitespace-pre-wrap text-sm text-slate-800 font-sans leading-relaxed bg-slate-50 p-4 rounded-lg border border-slate-200">{{ r.explicacion }}</pre>
      </section>

      <!-- ═══════════════ MÉTODOS (para validación del psicólogo) ═══════════════ -->
      <section class="bg-white rounded-2xl shadow-md p-6 fade-in-up">
        <h2 class="text-xl font-bold text-slate-900 mb-4">🔬 Métodos</h2>
        <div class="grid md:grid-cols-2 gap-4 text-sm">
          <div class="space-y-2">
            <div>
              <p class="font-semibold text-slate-700">Modelo</p>
              <p class="text-slate-600 font-mono text-xs break-all">{{ r.modelo }}</p>
            </div>
            <div>
              <p class="font-semibold text-slate-700">Técnica</p>
              <p class="text-slate-600">Zero-shot multi-label classification (BERT + XNLI)</p>
            </div>
            <div>
              <p class="font-semibold text-slate-700">Idioma de análisis</p>
              <p class="text-slate-600">Español (sin traducción intermedia)</p>
            </div>
            <div>
              <p class="font-semibold text-slate-700">Optimización de precisión</p>
              <p class="text-slate-600">
                Hypothesis templating + keyword boost clínico + umbrales calibrados por condición
              </p>
            </div>
          </div>
          <div class="space-y-2">
            <div>
              <p class="font-semibold text-slate-700">Escalas de referencia</p>
              <ul class="text-slate-600 list-disc list-inside text-xs space-y-0.5">
                <li>PHQ-9 (Patient Health Questionnaire — depresión)</li>
                <li>GAD-7 (Generalized Anxiety Disorder)</li>
                <li>ASRS-v1.1 (Adult ADHD Self-Report Scale)</li>
                <li>UCLA-3 Loneliness Scale</li>
                <li>C-SSRS (Columbia Suicide Severity Rating)</li>
              </ul>
            </div>
            <div>
              <p class="font-semibold text-slate-700">Umbrales de detección</p>
              <p class="text-slate-600 text-xs">
                Depresión/Ansiedad/Estrés/Soledad: 55% &middot;
                TDAH: 50% &middot;
                <span class="text-red-600 font-semibold">Riesgo suicida: 40%</span> (alta sensibilidad)
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══════════════ CONCLUSIÓN PARA PSICÓLOGO ═══════════════ -->
      <section class="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-2xl shadow-md p-6 fade-in-up">
        <h2 class="text-xl font-bold text-indigo-900 mb-3">
          👨‍⚕️ Conclusión para Revisión Profesional
        </h2>
        <p class="text-slate-800 leading-relaxed">{{ conclusionPsicologo }}</p>

        <div class="mt-4 p-4 bg-white rounded-lg border border-indigo-100 text-xs text-slate-600">
          <strong class="text-slate-800">Para el psicólogo/a evaluador/a:</strong>
          Este informe es un <em>cribado</em> preliminar generado por IA. Se sugiere contrastar los
          hallazgos con entrevista clínica directa y aplicación de escalas validadas. La herramienta
          no sustituye el juicio clínico profesional.
        </div>
      </section>

      <!-- Disclaimer final -->
      <footer class="text-center text-xs text-slate-500 pb-6">
        Sistema desarrollado como prototipo de tesis &middot;
        Procesamiento de Lenguaje Natural para Salud Mental Juvenil
      </footer>
    </div>
  </div>
</template>
