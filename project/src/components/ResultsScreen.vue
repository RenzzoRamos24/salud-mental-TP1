<script setup>
import { computed, onMounted, ref } from "vue";
import { Chart, registerables } from "chart.js";
import RiskBadge from "./RiskBadge.vue";

Chart.register(...registerables);

const props = defineProps({
  resultado: { type: Object, required: true },
});
const emit = defineEmits(["reset"]);

const canvas = ref(null);
let chartInstance = null;

const ETIQUETAS = {
  depresion: "Depresión",
  ansiedad: "Ansiedad",
  tdah: "TDAH",
  estres_academico: "Estrés académico",
  soledad: "Soledad",
  riesgo_suicida: "Riesgo suicida",
  estabilidad: "Estabilidad",
};

// Paleta pastel coherente con el design system
const COLORES = {
  depresion: "#8B6CF0", // brand
  ansiedad: "#F2A93B", // amber
  tdah: "#3DC57E", // mint
  estres_academico: "#FB9573", // peach
  soledad: "#A78BFA", // lavanda
  riesgo_suicida: "#E0413A", // critico
  estabilidad: "#1FA862", // mint dark
};

// Recomendaciones por condición (Sprint 4)
const RECOMENDACIONES = {
  depresion: {
    titulo: "Manejo de síntomas depresivos",
    pasos: [
      "Programa al menos una actividad placentera al día (caminar, escuchar música, ver a alguien querido).",
      "Mantén horarios regulares de sueño y comida — el cuerpo necesita estructura.",
      "Habla con alguien de confianza sobre cómo te sientes; no es debilidad.",
      "Considera agendar cita con Bienestar Estudiantil UPC esta semana.",
    ],
  },
  ansiedad: {
    titulo: "Reducción de la ansiedad",
    pasos: [
      "Practica respiración 4-7-8: inhala 4s, retén 7s, exhala 8s, 3 ciclos.",
      "Identifica disparadores específicos y anótalos para verlos con un psicólogo.",
      "Limita cafeína y revisa tu uso de redes sociales en momentos de estrés.",
      "Si la ansiedad interfiere con tus estudios o sueño, busca apoyo profesional.",
    ],
  },
  tdah: {
    titulo: "Estrategias para inatención/hiperactividad",
    pasos: [
      "Divide tareas grandes en bloques de 25 min con descansos (técnica Pomodoro).",
      "Usa un único calendario digital con recordatorios para todo.",
      "Reduce estímulos visuales en tu escritorio durante el estudio.",
      "Una evaluación clínica con un profesional puede confirmar el cuadro.",
    ],
  },
  estres_academico: {
    titulo: "Estrés académico",
    pasos: [
      "Prioriza con la regla de 3: elige solo 3 tareas críticas por día.",
      "Negocia plazos con tus docentes antes de que el malestar crezca.",
      "Reserva un día a la semana sin estudios — el descanso también es productividad.",
      "Conversa con tu tutor académico si la carga es estructural.",
    ],
  },
  soledad: {
    titulo: "Red de apoyo",
    pasos: [
      "Identifica 2 personas con las que sí te sientes en confianza y escríbeles esta semana.",
      "Únete a un grupo o actividad UPC (deportes, voluntariado, círculo de estudio).",
      "La soledad es señal, no diagnóstico: pide apoyo a Bienestar Estudiantil.",
      "Considera terapia breve: aprender a vincularse también se trabaja.",
    ],
  },
  riesgo_suicida: {
    titulo: "Atención prioritaria",
    pasos: [
      "Llama AHORA a Línea 113 (MINSA), opción 5 — atención 24/7.",
      "No estés solo/a: contacta a alguien de tu red de apoyo inmediatamente.",
      "Acude a Bienestar Estudiantil UPC o a la emergencia médica más cercana hoy.",
      "Recuerda: lo que sientes es temporal. Hay ayuda profesional disponible.",
    ],
  },
};

const r = computed(() => props.resultado.resultado);
const scores = computed(() => r.value.scores_completos || {});
const detectadas = computed(() => r.value.condiciones_detectadas || {});
const numDetectadas = computed(() => Object.keys(detectadas.value).length);
const nivelRiesgo = computed(() => r.value.nivel_riesgo);

const phq9 = computed(() => props.resultado.phq9 || null);
const gad7 = computed(() => props.resultado.gad7 || null);
const crisisProtocolo = computed(() => !!props.resultado.crisis_protocolo);

function severidadTone(sev) {
  const s = (sev || "").toLowerCase();
  if (s.includes("severa") || s.includes("severo")) return "text-risk-critico";
  if (s.includes("moderada-severa")) return "text-risk-critico";
  if (s.includes("moderada")) return "text-orange-600";
  if (s.includes("leve")) return "text-amber-600";
  return "text-green-700";
}

const fechaFormateada = computed(() => {
  try {
    return new Date(props.resultado.fecha_analisis).toLocaleString("es-PE", {
      dateStyle: "long",
      timeStyle: "short",
    });
  } catch {
    return props.resultado.fecha_analisis;
  }
});

const nivelTone = computed(() => {
  const map = {
    CRÍTICO: {
      bg: " ",
      border: "border-red-200",
      text: "text-risk-critico",
      emoji: "",
    },
    ALTO: {
      bg: " ",
      border: "border-ink-200",
      text: "text-ink-700",
      emoji: "",
    },
    MEDIO: {
      bg: " ",
      border: "border-ink-200",
      text: "text-ink-700",
      emoji: "",
    },
    BAJO: {
      bg: " ",
      border: "border-green-200",
      text: "text-green-600",
      emoji: "",
    },
  };
  return map[nivelRiesgo.value] || map.MEDIO;
});

const conclusionPsicologo = computed(() => {
  const nivel = nivelRiesgo.value;
  const conds = Object.entries(detectadas.value)
    .sort((a, b) => b[1].confianza - a[1].confianza)
    .map(([, v]) => `${v.etiqueta} (${v.confianza}%)`);

  let resumen = `Paciente: ${props.resultado.usuario}. Nivel de riesgo global: ${nivel}. `;
  if (conds.length === 0) {
    resumen +=
      "No se detectaron condiciones clínicamente significativas; estabilidad emocional predominante. ";
    resumen +=
      "Recomendación: seguimiento de mantenimiento, refuerzo de hábitos protectores.";
  } else {
    resumen += `Condiciones detectadas (${conds.length}): ${conds.join(", ")}. `;
    if (nivel === "CRÍTICO")
      resumen +=
        "ATENCIÓN URGENTE: riesgo suicida activo requiere evaluación inmediata y plan de seguridad.";
    else if (nivel === "ALTO")
      resumen +=
        "Se sugiere evaluación clínica estructurada (PHQ-9, GAD-7) y plan de intervención.";
    else if (nivel === "MEDIO")
      resumen +=
        "Monitoreo recomendado; considerar psicoterapia breve y reevaluación en 2–4 semanas.";
  }
  return resumen;
});

function construirGrafico() {
  if (!canvas.value) return;
  const claves = Object.keys(scores.value);
  const data = claves.map((k) => scores.value[k]);
  const labels = claves.map((k) => ETIQUETAS[k] || k);
  const backgroundColor = claves.map((k) => COLORES[k] || "#9A93A4");
  const umbrales = {
    depresion: 55,
    ansiedad: 55,
    tdah: 50,
    estres_academico: 55,
    soledad: 55,
    riesgo_suicida: 40,
    estabilidad: 60,
  };

  chartInstance = new Chart(canvas.value, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Confianza (%)",
          data,
          backgroundColor,
          borderRadius: 8,
          borderWidth: 0,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: (ctx) => {
              const k = claves[ctx.dataIndex];
              const u = umbrales[k] || 55;
              const det =
                data[ctx.dataIndex] >= u ? " Supera umbral" : " Bajo umbral";
              return `Umbral: ${u}% · ${det}`;
            },
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          max: 100,
          ticks: { callback: (v) => v + "%" },
          grid: { color: "#EDEAF0" },
        },
        y: { grid: { display: false } },
      },
    },
  });
}

onMounted(() => construirGrafico());

function imprimir() {
  window.print();
}
</script>

<template>
  <div class="page-shell-wide">
    <div class="space-y-6">
      <!-- ═══ HEADER ═══ -->
      <header class="fade-in-up">
        <div class="flex flex-wrap items-end justify-between gap-4 mb-2">
          <div>
            <p
              class="text-xs uppercase tracking-widest text-green-500 font-bold"
            >
              Informe clínico preliminar
            </p>
            <h1 class="hero-serif text-3xl sm:text-4xl mt-1">
              Perfil <span class="hero-mint">emocional</span>
            </h1>
            <p class="text-ink-500 mt-2">
              <span class="font-semibold text-ink-700">{{
                resultado.usuario
              }}</span>
              <span class="mx-2 text-ink-300">·</span>
              {{ fechaFormateada }}
            </p>
          </div>
          <div class="flex gap-2 no-print">
            <button @click="imprimir" class="btn-secondary">
              Imprimir / PDF
            </button>
            <button @click="emit('reset')" class="btn-mint">
              Nueva evaluación
            </button>
          </div>
        </div>
      </header>

      <!-- ═══ NIVEL DE RIESGO + RESUMEN ═══ -->
      <section class="grid md:grid-cols-3 gap-5 fade-in-up">
        <div
          class="md:col-span-2 rounded-xl border-l-4 p-6 shadow-soft"
          :class="[nivelTone.bg, nivelTone.border]"
        >
          <p class="text-xs uppercase tracking-widest text-ink-500 font-bold">
            Nivel de riesgo global
          </p>
          <div class="flex items-center gap-3 mt-2">
            <span class="text-4xl">{{ nivelTone.emoji }}</span>
            <span class="text-4xl font-bold" :class="nivelTone.text">{{
              nivelRiesgo
            }}</span>
          </div>
          <p class="text-ink-700 mt-3 text-sm leading-relaxed">
            Análisis basado en
            <strong>{{ resultado.respuestas_analizadas }}</strong> respuestas
            procesadas con el modelo <strong>BERT</strong> en español.
          </p>
        </div>

        <div class="card p-6">
          <p class="text-xs uppercase tracking-widest text-ink-500 font-bold">
            Resumen
          </p>
          <div class="mt-3 space-y-3">
            <div class="flex justify-between text-sm items-center">
              <span class="text-ink-500">Condiciones detectadas</span>
              <span class="dsm5-tag">{{ numDetectadas }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-ink-500">Respuestas analizadas</span>
              <span class="font-bold text-ink-900">{{
                resultado.respuestas_analizadas
              }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-ink-500">Sesión</span>
              <span
                class="font-mono text-xs text-ink-400 truncate max-w-[120px]"
                :title="resultado.session_id"
              >
                {{ resultado.session_id.slice(0, 8) }}…
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══ ESCALAS CLÍNICAS (PHQ-9 + GAD-7) ═══ -->
      <section v-if="phq9 || gad7" class="grid md:grid-cols-2 gap-5 fade-in-up">
        <!-- PHQ-9 -->
        <div v-if="phq9" class="card p-6">
          <div class="flex items-start justify-between gap-3 mb-2">
            <div>
              <p class="text-xs uppercase tracking-widest text-ink-500 font-bold">
                PHQ-9 — Depresión
              </p>
              <p class="text-3xl font-bold text-ink-900 mt-1">
                {{ phq9.total }}<span class="text-lg text-ink-400">/{{ phq9.max }}</span>
              </p>
            </div>
            <span
              class="dsm5-tag"
              :class="severidadTone(phq9.severidad)"
            >{{ phq9.severidad }}</span>
          </div>
          <div class="h-2 bg-ink-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-green-600 transition-all duration-700"
              :style="{ width: (phq9.total / phq9.max) * 100 + '%' }"
            ></div>
          </div>
          <p class="text-xs text-ink-600 mt-3 leading-relaxed">
            <strong>Acción sugerida:</strong> {{ phq9.accion }}
          </p>
        </div>

        <!-- GAD-7 -->
        <div v-if="gad7" class="card p-6">
          <div class="flex items-start justify-between gap-3 mb-2">
            <div>
              <p class="text-xs uppercase tracking-widest text-ink-500 font-bold">
                GAD-7 — Ansiedad
              </p>
              <p class="text-3xl font-bold text-ink-900 mt-1">
                {{ gad7.total }}<span class="text-lg text-ink-400">/{{ gad7.max }}</span>
              </p>
            </div>
            <span
              class="dsm5-tag"
              :class="severidadTone(gad7.severidad)"
            >{{ gad7.severidad }}</span>
          </div>
          <div class="h-2 bg-ink-100 rounded-full overflow-hidden">
            <div
              class="h-full bg-green-600 transition-all duration-700"
              :style="{ width: (gad7.total / gad7.max) * 100 + '%' }"
            ></div>
          </div>
          <p class="text-xs text-ink-600 mt-3 leading-relaxed">
            <strong>Acción sugerida:</strong> {{ gad7.accion }}
          </p>
        </div>
      </section>

      <!-- ═══ ALERTA DE CRISIS (PHQ-9 ítem 9) ═══ -->
      <section v-if="crisisProtocolo" class="banner-danger">
        <div>
          <p class="font-semibold">Protocolo de atención prioritaria</p>
          <p class="text-sm mt-1 leading-relaxed">
            En el ítem 9 del PHQ-9 (ideación de daño hacia ti mismo) hubo una
            respuesta que activa el protocolo. Llama a la
            <strong>Línea 113, opción 5</strong> ahora, o ve a la emergencia
            más cercana. Tu psicóloga/o del colegio también verá esta alerta.
          </p>
        </div>
      </section>

      <!-- ═══ GRÁFICO ═══ -->
      <section class="card p-6 fade-in-up">
        <h2 class="section-title">Perfil de condiciones</h2>
        <p class="section-subtitle mb-4">
          Probabilidad detectada por el modelo BERT para cada condición clínica
          evaluada.
        </p>
        <div class="h-80"><canvas ref="canvas"></canvas></div>
      </section>

      <!-- ═══ CONDICIONES DETECTADAS ═══ -->
      <section v-if="numDetectadas > 0" class="card p-6 fade-in-up">
        <h2 class="section-title">Condiciones detectadas</h2>
        <div class="grid sm:grid-cols-2 gap-4 mt-4">
          <div
            v-for="(cond, clave) in detectadas"
            :key="clave"
            class="rounded-xl border border-ink-100 p-4 hover:shadow-soft transition"
          >
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-semibold text-ink-900">{{ cond.etiqueta }}</h3>
              <span class="dsm5-tag">{{ cond.confianza }}%</span>
            </div>
            <div class="h-2 bg-ink-100 rounded-full overflow-hidden">
              <div
                class="h-full transition-all duration-700"
                :style="{
                  width: cond.confianza + '%',
                  backgroundColor: COLORES[clave] || '#9A93A4',
                }"
              ></div>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══ RECOMENDACIONES PERSONALIZADAS ═══ -->
      <section v-if="numDetectadas > 0" class="card p-6 fade-in-up">
        <h2 class="section-title">Recomendaciones personalizadas</h2>
        <p class="section-subtitle mb-4">
          Pasos concretos que puedes empezar a aplicar hoy.
        </p>
        <div class="space-y-4 mt-4">
          <div
            v-for="(cond, clave) in detectadas"
            :key="clave"
            v-show="RECOMENDACIONES[clave]"
            class="rounded-xl border p-5"
            :class="
              clave === 'riesgo_suicida'
                ? 'bg-red-50 border-red-200'
                : 'bg-green-50 border-green-100'
            "
          >
            <div class="flex items-center justify-between mb-3">
              <h3 class="font-bold text-ink-900 flex items-center gap-2">
                <span class="text-2xl">{{ RECOMENDACIONES[clave]?.icon }}</span>
                {{ RECOMENDACIONES[clave]?.titulo }}
              </h3>
              <span class="dsm5-tag">{{ cond.confianza }}%</span>
            </div>
            <ol class="space-y-2 text-sm text-ink-700">
              <li
                v-for="(paso, i) in RECOMENDACIONES[clave]?.pasos || []"
                :key="i"
                class="flex gap-3"
              >
                <span
                  class="shrink-0 w-6 h-6 rounded-full bg-white border border-green-200 text-green-700 font-bold text-xs flex items-center justify-center"
                  >{{ i + 1 }}</span
                >
                <span>{{ paso }}</span>
              </li>
            </ol>
          </div>
        </div>
      </section>

      <!-- Sin condiciones — mantenimiento -->
      <section v-else class="card-mint p-6 fade-in-up">
        <div class="flex items-start gap-4">
          <div>
            <h2 class="text-xl font-bold text-green-600">
              ¡Buen estado emocional!
            </h2>
            <p class="text-ink-700 text-sm mt-2 leading-relaxed">
              No se detectaron condiciones clínicas significativas. Mantén tus
              hábitos protectores: sueño regular, actividad física, contacto con
              tu red de apoyo y momentos de descanso. Te recomendamos hacer esta
              evaluación cada 1–2 semanas.
            </p>
          </div>
        </div>
      </section>

      <!-- ═══ INDICACIONES (explicación BERT) ═══ -->
      <section class="card p-6 fade-in-up">
        <h2 class="section-title">Indicaciones e interpretación</h2>
        <pre
          class="whitespace-pre-wrap text-sm text-ink-700 font-sans leading-relaxed bg-white p-5 rounded-xl border border-ink-100 mt-3"
          >{{ r.explicacion }}</pre
        >
      </section>

      <!-- ═══ MÉTODOS ═══ -->
      <section class="card p-6 fade-in-up">
        <h2 class="section-title">Métodos</h2>
        <div class="grid md:grid-cols-2 gap-5 text-sm mt-4">
          <div class="space-y-3">
            <div>
              <p
                class="text-xs uppercase tracking-wider font-semibold text-ink-400"
              >
                Modelo
              </p>
              <p class="font-mono text-xs text-ink-700 break-all">
                {{ r.modelo }}
              </p>
            </div>
            <div>
              <p
                class="text-xs uppercase tracking-wider font-semibold text-ink-400"
              >
                Técnica
              </p>
              <p class="text-ink-700">
                Zero-shot multi-label classification (BERT + XNLI)
              </p>
            </div>
            <div>
              <p
                class="text-xs uppercase tracking-wider font-semibold text-ink-400"
              >
                Idioma
              </p>
              <p class="text-ink-700">Español (sin traducción intermedia)</p>
            </div>
          </div>
          <div class="space-y-3">
            <div>
              <p
                class="text-xs uppercase tracking-wider font-semibold text-ink-400"
              >
                Escalas de referencia
              </p>
              <div class="flex flex-wrap gap-1.5 mt-1.5">
                <span class="dsm5-tag">PHQ-9</span>
                <span class="dsm5-tag">GAD-7</span>
              </div>
            </div>
            <div>
              <p
                class="text-xs uppercase tracking-wider font-semibold text-ink-400"
              >
                Umbrales de detección
              </p>
              <p class="text-ink-700 text-xs leading-relaxed">
                Depresión / Ansiedad / Estrés / Soledad: <strong>55%</strong> ·
                TDAH: <strong>50%</strong> ·
                <span class="text-risk-critico font-semibold"
                  >Riesgo suicida: 40%</span
                >
                (alta sensibilidad)
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══ CONCLUSIÓN PARA PSICÓLOGO ═══ -->
      <section class="card-hero p-6 fade-in-up">
        <h2 class="section-title text-green-800">
          Conclusión para revisión profesional
        </h2>
        <p class="text-ink-800 leading-relaxed mt-3">
          {{ conclusionPsicologo }}
        </p>
        <div
          class="mt-4 p-4 bg-white rounded-xl border border-green-100 text-xs text-ink-600"
        >
          <strong class="text-ink-800">Para el psicólogo/a evaluador/a:</strong>
          Este informe es un <em>cribado</em> preliminar generado por IA. Se
          sugiere contrastar los hallazgos con entrevista clínica directa y
          aplicación de escalas validadas. La herramienta no sustituye el juicio
          clínico profesional.
        </div>
      </section>

      <footer class="text-center text-xs text-ink-400 pb-2">
        Sistema desarrollado como prototipo de tesis · Procesamiento de Lenguaje
        Natural para Salud Mental Juvenil
      </footer>
    </div>
  </div>
</template>
