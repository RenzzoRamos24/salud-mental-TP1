<script setup>
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";
import PageHeader from "../components/PageHeader.vue";

const router = useRouter();
const rol = computed(() => authStore.rol.value);
const esEstudiante = computed(() => rol.value === "estudiante");

const contenidos = ref([]);
const cargandoContenidos = ref(true);
const categoriaActiva = ref("todas");

onMounted(async () => {
  try {
    contenidos.value = await api.listarContenidos();
  } catch (_) {
    contenidos.value = [];
  } finally {
    cargandoContenidos.value = false;
  }
});

const categorias = computed(() => {
  const set = new Set(contenidos.value.map((c) => c.categoria).filter(Boolean));
  return ["todas", ...set];
});

const filtrados = computed(() =>
  categoriaActiva.value === "todas"
    ? contenidos.value
    : contenidos.value.filter((c) => c.categoria === categoriaActiva.value),
);

// ─── Recursos urgentes (estudiante) ──────────────────────────────────
const urgent = [
  {
    name: "Línea 113 — MINSA",
    desc: "Atención telefónica gratuita en salud mental.",
    phone: "113 · opción 5",
    href: "tel:113",
    hours: "24 horas, todos los días",
  },
  {
    name: "Línea de la vida",
    desc: "Contención en crisis, cualquier día a cualquier hora.",
    phone: "717-003-700",
    href: "tel:7170037000",
    hours: "24 horas, todos los días",
  },
  {
    name: "Emergencias",
    desc: "Si vos o alguien más está en peligro inmediato.",
    phone: "106",
    href: "tel:106",
    hours: "24 horas",
  },
];

// ─── Para leer con calma — fallback si no hay contenidos en el backend
const tips = [
  {
    title: "Cómo releer tu diario sin juzgarte",
    desc: "Releer entradas viejas puede ser incómodo. Algunas ideas para hacerlo con un poco más de amabilidad.",
    read: "4 min",
  },
  {
    title: "Dormir mal una semana no es 'no saber dormir'",
    desc: "Qué dice la evidencia sobre el sueño en época de exámenes, y qué probar primero.",
    read: "6 min",
  },
  {
    title: "Tres líneas también cuentan",
    desc: "Por qué las entradas cortas sostienen el hábito mejor que las largas.",
    read: "3 min",
  },
  {
    title: "Cuándo conviene pedir una cita",
    desc: "Señales de que hablar con alguien del equipo de bienestar puede ayudarte más que seguir solo.",
    read: "5 min",
  },
];

const lecturas = computed(() => {
  if (contenidos.value.length === 0) return tips;
  return contenidos.value.map((c) => ({
    title: c.titulo,
    desc: c.descripcion,
    read: c.tiempo_lectura ? `${c.tiempo_lectura} min` : "—",
    href: c.url || null,
  }));
});

// ─── Vista psicólogo / admin ─────────────────────────────────────────
const escalas = [
  { nombre: "PHQ-9", descripcion: "Patient Health Questionnaire — síntomas depresivos.", rango: "0–27" },
  { nombre: "GAD-7", descripcion: "Generalized Anxiety Disorder — síntomas ansiosos.", rango: "0–21" },
];

const protocolos = [
  {
    titulo: "Riesgo crítico detectado",
    pasos: [
      "Contactar al estudiante en las primeras 24 horas.",
      "Elaborar plan de seguridad junto al estudiante.",
      "Comunicar a Bienestar Estudiantil y, si corresponde, a la familia.",
      "Registrar la intervención y dar seguimiento en 48–72 horas.",
    ],
  },
  {
    titulo: "Riesgo alto",
    pasos: [
      "Agendar cita en la semana.",
      "Confirmar diagnóstico con escalas validadas (PHQ-9, GAD-7).",
      "Plan de intervención breve y reevaluación a las dos semanas.",
    ],
  },
  {
    titulo: "Riesgo medio o bajo",
    pasos: [
      "Monitoreo cada dos a cuatro semanas vía sistema.",
      "Reforzar hábitos protectores y psicoeducación.",
      "Reabrir caso si el nivel sube en evaluaciones siguientes.",
    ],
  },
];

const lineasDerivacion = [
  { titulo: "Línea 113 — MINSA", numero: "113 · opción 5", horario: "24/7", desc: "Atención telefónica gratuita en salud mental." },
  { titulo: "SALUDLINE", numero: "106", horario: "24/7", desc: "Emergencia médica y de salud mental." },
  { titulo: "Teléfono de la Esperanza", numero: "717-003-700", horario: "24/7", desc: "Apoyo emocional confidencial." },
];
</script>

<template>
  <!-- ════════════════════════════════════════════════════════════════ -->
  <!-- ESTUDIANTE — Sami                                              -->
  <!-- ════════════════════════════════════════════════════════════════ -->
  <div v-if="esEstudiante" class="page" data-screen-label="Recursos">
    <div class="page-inner" style="max-width: 820px">
      <h1>Recursos</h1>
      <p class="sub">
        Para cuando escribir no alcanza. Pedir ayuda también es cuidarse.
      </p>

      <div style="font-size: 13.5px; font-weight: 700; margin: 0 0 10px">
        Si necesitás ayuda ahora
      </div>
      <div
        style="
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 14px;
          margin-bottom: 30px;
        "
      >
        <a
          v-for="u in urgent"
          :key="u.name"
          :href="u.href"
          class="card"
          style="
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            text-decoration: none;
            color: inherit;
          "
        >
          <div style="color: var(--accent)">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"
              />
            </svg>
          </div>
          <div style="font-size: 14px; font-weight: 700; margin-top: 4px">
            {{ u.name }}
          </div>
          <p
            style="
              margin: 0;
              font-size: 12.5px;
              color: var(--ink-2);
              line-height: 1.5;
              flex: 1;
            "
          >
            {{ u.desc }}
          </p>
          <div
            style="
              font-size: 19px;
              font-weight: 700;
              letter-spacing: -0.01em;
              margin-top: 6px;
            "
          >
            {{ u.phone }}
          </div>
          <div style="font-size: 11.5px; color: var(--ink-3)">{{ u.hours }}</div>
        </a>
      </div>

      <div style="font-size: 13.5px; font-weight: 700; margin: 0 0 10px">
        Para leer con calma
      </div>
      <div class="card rowlist">
        <a
          v-for="t in lecturas"
          :key="t.title"
          :href="t.href || '#'"
          :target="t.href ? '_blank' : '_self'"
          rel="noopener"
          style="
            display: flex;
            gap: 14px;
            align-items: flex-start;
            padding: 15px 20px;
            border: 0;
            background: none;
            text-align: left;
            width: 100%;
            text-decoration: none;
            color: inherit;
          "
        >
          <span style="color: var(--ink-3); margin-top: 1px">
            <svg
              width="17"
              height="17"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.7"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6" />
            </svg>
          </span>
          <span style="min-width: 0; flex: 1">
            <span style="display: block; font-size: 13.5px; font-weight: 600">
              {{ t.title }}
            </span>
            <span
              style="
                display: block;
                font-size: 12.5px;
                color: var(--ink-2);
                margin-top: 2px;
                line-height: 1.5;
              "
            >
              {{ t.desc }}
            </span>
          </span>
          <span
            style="
              font-size: 11.5px;
              color: var(--ink-3);
              flex: none;
              margin-top: 2px;
            "
          >
            {{ t.read }}
          </span>
        </a>
      </div>
    </div>
  </div>

  <!-- ════════════════════════════════════════════════════════════════ -->
  <!-- PSICÓLOGO / ADMIN — vista original                              -->
  <!-- ════════════════════════════════════════════════════════════════ -->
  <div v-else class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">
      Volver al menú
    </button>

    <PageHeader
      title="Recursos"
      accent="clínicos"
      subtitle="Escalas validadas, protocolos institucionales y líneas de derivación."
    />

    <section class="mb-10">
      <h2 class="section-title">Escalas de referencia</h2>
      <p class="section-subtitle mb-4">
        Estas son las escalas validadas que tomamos como guía.
      </p>
      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="e in escalas" :key="e.nombre" class="card p-5">
          <div class="flex items-center justify-between mb-2">
            <p class="font-semibold text-ink-900">{{ e.nombre }}</p>
            <span class="dsm5-tag">{{ e.rango }}</span>
          </div>
          <p class="text-xs text-ink-600 leading-relaxed">{{ e.descripcion }}</p>
        </div>
      </div>
    </section>

    <section class="mb-10">
      <h2 class="section-title">Protocolos por nivel de riesgo</h2>
      <p class="section-subtitle mb-4">
        Pasos sugeridos cuando un estudiante aparece en el panel.
      </p>
      <div class="space-y-3">
        <div v-for="p in protocolos" :key="p.titulo" class="card p-5">
          <p class="font-semibold text-ink-900 mb-3">{{ p.titulo }}</p>
          <ol class="space-y-2 text-sm text-ink-700">
            <li v-for="(paso, i) in p.pasos" :key="i" class="flex gap-3">
              <span
                class="shrink-0 w-5 h-5 rounded-full bg-green-100 text-green-700 text-[11px] font-semibold flex items-center justify-center"
                >{{ i + 1 }}</span
              >
              <span>{{ paso }}</span>
            </li>
          </ol>
        </div>
      </div>
    </section>

    <section class="mb-10">
      <h2 class="section-title">Líneas de derivación</h2>
      <p class="section-subtitle mb-4">
        Para casos que requieren atención fuera del horario del colegio.
      </p>
      <div class="grid sm:grid-cols-3 gap-4">
        <a
          v-for="r in lineasDerivacion"
          :key="r.titulo"
          :href="
            r.numero.startsWith('113')
              ? 'tel:113'
              : r.numero === '106'
                ? 'tel:106'
                : 'tel:' + r.numero.replace(/-/g, '')
          "
          class="card p-5 hover:border-green-500 transition"
        >
          <h3 class="font-semibold text-ink-900 text-sm">{{ r.titulo }}</h3>
          <p class="text-ink-600 text-xs mt-1 leading-relaxed">{{ r.desc }}</p>
          <p class="mt-4 text-2xl font-semibold text-ink-900 tracking-tight">
            {{ r.numero }}
          </p>
          <p class="text-xs text-ink-500 mt-0.5">Atención {{ r.horario }}</p>
        </a>
      </div>
    </section>

    <section v-if="contenidos.length > 0 || cargandoContenidos">
      <div class="flex justify-between items-end mb-4 flex-wrap gap-2">
        <div>
          <h2 class="section-title !mb-1">Biblioteca</h2>
          <p class="section-subtitle">
            Contenidos también visibles para los estudiantes.
          </p>
        </div>
        <div v-if="categorias.length > 2" class="flex flex-wrap gap-1.5">
          <button
            v-for="cat in categorias"
            :key="cat"
            @click="categoriaActiva = cat"
            :class="
              categoriaActiva === cat
                ? 'chip-brand !bg-green-700 !text-white !border-green-700'
                : 'chip-ink hover:bg-ink-200'
            "
            class="capitalize"
          >
            {{ cat }}
          </button>
        </div>
      </div>
      <p v-if="cargandoContenidos" class="text-sm text-ink-500">Cargando…</p>
      <div v-else class="grid sm:grid-cols-2 gap-4">
        <a
          v-for="c in filtrados"
          :key="c.id"
          :href="c.url || '#'"
          :target="c.url ? '_blank' : '_self'"
          rel="noopener"
          class="card p-5 hover:border-green-500 transition"
        >
          <p class="font-semibold text-ink-900">{{ c.titulo }}</p>
          <p class="text-xs text-ink-500 mt-1.5 leading-relaxed">
            {{ c.descripcion }}
          </p>
          <p v-if="c.categoria" class="dsm5-tag mt-3">{{ c.categoria }}</p>
        </a>
      </div>
    </section>
  </div>
</template>
