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

// ─── Contenido para ESTUDIANTE ───────────────────────────────────────────
const recursosEmergencia = [
  {
    titulo: "Línea 113 — MINSA",
    numero: "113 · opción 5",
    horario: "Todos los días, a cualquier hora",
    desc: "Atienden si necesitas hablar con alguien ahora.",
  },
  {
    titulo: "SALUDLINE — Emergencias",
    numero: "106",
    horario: "Todos los días, a cualquier hora",
    desc: "Para crisis o cuando es urgente.",
  },
  {
    titulo: "Teléfono de la Esperanza",
    numero: "717-003-700",
    horario: "Todos los días, a cualquier hora",
    desc: "Si solo quieres conversar con alguien.",
  },
];

const consejos = [
  {
    titulo: "Dormir bien",
    texto:
      "Ocho horas hacen más por tu ánimo que cualquier app. Trata de acostarte y levantarte a la misma hora.",
  },
  {
    titulo: "Moverte un rato",
    texto:
      "Caminar treinta minutos cambia el día. No tiene que ser gimnasio ni rutina, basta con salir.",
  },
  {
    titulo: "Hablarlo con alguien",
    texto:
      "Cargar las cosas en silencio cansa. Un amigo, un familiar, un profe — sirve más de lo que parece.",
  },
  {
    titulo: "Respirar 4-7-8",
    texto:
      "Inhalas cuatro segundos, sostienes siete, sueltas en ocho. Tres veces y la cabeza baja.",
  },
  {
    titulo: "Partir las tareas",
    texto:
      "Cuando se acumula todo, sirve dividirlo en pedazos chicos y hacer uno a la vez.",
  },
  {
    titulo: "Soltar el celular",
    texto:
      "Antes de dormir, intenta no mirar la pantalla por media hora. Vas a notar la diferencia.",
  },
];

// ─── Contenido para PSICÓLOGO / ADMIN ─────────────────────────────────────
const escalas = [
  {
    nombre: "PHQ-9",
    descripcion: "Patient Health Questionnaire — síntomas depresivos.",
    rango: "0–27",
  },
  {
    nombre: "GAD-7",
    descripcion: "Generalized Anxiety Disorder — síntomas ansiosos.",
    rango: "0–21",
  },
  {
    nombre: "ASRS-v1.1",
    descripcion: "Adult Self-Report Scale — TDAH.",
    rango: "Parte A · 6 ítems",
  },
  {
    nombre: "UCLA-3",
    descripcion: "UCLA Loneliness Scale (versión breve) — soledad.",
    rango: "3–9",
  },
  {
    nombre: "C-SSRS",
    descripcion: "Columbia Suicide Severity Rating — ideación y conducta suicida.",
    rango: "Cribado breve",
  },
];

const protocolos = [
  {
    titulo: "Riesgo crítico detectado",
    pasos: [
      "Contactar al estudiante en las primeras 24 horas.",
      "Aplicar C-SSRS completo y elaborar plan de seguridad.",
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
  {
    titulo: "Línea 113 — MINSA",
    numero: "113 · opción 5",
    horario: "24/7",
    desc: "Atención telefónica gratuita en salud mental.",
  },
  {
    titulo: "SALUDLINE",
    numero: "106",
    horario: "24/7",
    desc: "Emergencia médica y de salud mental.",
  },
  {
    titulo: "Teléfono de la Esperanza",
    numero: "717-003-700",
    horario: "24/7",
    desc: "Apoyo emocional confidencial.",
  },
];
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">
      Volver al menú
    </button>

    <!-- ══════════════════════════════════════════════════════════════ -->
    <!-- ESTUDIANTE                                                     -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <template v-if="esEstudiante">
      <PageHeader
        title="Recursos"
        accent="y apoyo"
        subtitle="Líneas de ayuda, servicios del colegio y cosas que puedes hacer por ti."
      />

      <div class="banner-danger mb-6">
        <div>
          <p class="font-semibold">Si lo necesitas ahora</p>
          <p class="text-sm mt-1">
            Llama a la <strong>Línea 113, opción 5</strong>. Atienden a
            cualquier hora, o ve a la emergencia más cercana.
          </p>
        </div>
      </div>

      <section class="mb-10">
        <h2 class="section-title">Líneas de ayuda</h2>
        <div class="grid sm:grid-cols-3 gap-4 mt-3">
          <a
            v-for="r in recursosEmergencia"
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
            <p class="text-xs text-ink-500 mt-0.5">{{ r.horario }}</p>
          </a>
        </div>
      </section>

      <section class="mb-10">
        <h2 class="section-title">En el colegio</h2>
        <div class="grid sm:grid-cols-2 gap-4 mt-3">
          <div class="card p-5">
            <h3 class="font-semibold text-ink-900">Bienestar Estudiantil</h3>
            <ul class="text-sm text-ink-700 mt-3 space-y-1.5">
              <li>Pabellón D, 2do piso</li>
              <li>(01) 313-3333 anexo 2500</li>
              <li>De lunes a viernes, 8:00 a 18:00</li>
              <li>bienestar@upc.edu.pe</li>
            </ul>
          </div>
          <div class="card p-5">
            <h3 class="font-semibold text-ink-900">Centro Médico</h3>
            <ul class="text-sm text-ink-700 mt-3 space-y-1.5">
              <li>Edificio C, 1er piso</li>
              <li>De lunes a viernes, 7:30 a 19:00</li>
              <li>Si necesitas, te derivan a un psicólogo.</li>
            </ul>
          </div>
        </div>
      </section>

      <section
        v-if="contenidos.length > 0 || cargandoContenidos"
        class="mb-10"
      >
        <div class="flex justify-between items-end mb-4 flex-wrap gap-2">
          <div>
            <h2 class="section-title !mb-1">Para leer</h2>
            <p class="section-subtitle">
              Artículos cortos para entenderte un poco mejor.
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

      <section>
        <h2 class="section-title">Cosas que puedes hacer hoy</h2>
        <p class="section-subtitle mb-4">
          Hábitos pequeños que en el día a día ayudan más de lo que parece.
        </p>
        <div class="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
          <div v-for="c in consejos" :key="c.titulo" class="card p-5">
            <p class="font-semibold text-ink-900 text-sm">{{ c.titulo }}</p>
            <p class="text-xs text-ink-600 mt-1.5 leading-relaxed">
              {{ c.texto }}
            </p>
          </div>
        </div>
      </section>

      <div
        class="mt-10 card p-5 flex items-center justify-between gap-4 flex-wrap"
      >
        <div>
          <p class="font-semibold text-ink-900">¿Quieres ver cómo estás?</p>
          <p class="text-sm text-ink-600 mt-0.5">
            Una conversación corta con Sami. Diez preguntas.
          </p>
        </div>
        <router-link to="/chat" class="btn-mint btn-sm">Empezar</router-link>
      </div>
    </template>

    <!-- ══════════════════════════════════════════════════════════════ -->
    <!-- PSICÓLOGO / ADMIN                                              -->
    <!-- ══════════════════════════════════════════════════════════════ -->
    <template v-else>
      <PageHeader
        title="Recursos"
        accent="clínicos"
        subtitle="Escalas validadas, protocolos institucionales y líneas de derivación."
      />

      <!-- Escalas -->
      <section class="mb-10">
        <h2 class="section-title">Escalas de referencia</h2>
        <p class="section-subtitle mb-4">
          El modelo BERT toma como guía estas escalas validadas.
        </p>
        <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="e in escalas" :key="e.nombre" class="card p-5">
            <div class="flex items-center justify-between mb-2">
              <p class="font-semibold text-ink-900">{{ e.nombre }}</p>
              <span class="dsm5-tag">{{ e.rango }}</span>
            </div>
            <p class="text-xs text-ink-600 leading-relaxed">
              {{ e.descripcion }}
            </p>
          </div>
        </div>
      </section>

      <!-- Protocolos -->
      <section class="mb-10">
        <h2 class="section-title">Protocolos por nivel de riesgo</h2>
        <p class="section-subtitle mb-4">
          Pasos sugeridos cuando un estudiante aparece en el panel.
        </p>
        <div class="space-y-3">
          <div v-for="p in protocolos" :key="p.titulo" class="card p-5">
            <p class="font-semibold text-ink-900 mb-3">{{ p.titulo }}</p>
            <ol class="space-y-2 text-sm text-ink-700">
              <li
                v-for="(paso, i) in p.pasos"
                :key="i"
                class="flex gap-3"
              >
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

      <!-- Líneas de derivación -->
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
            <p class="text-xs text-ink-500 mt-0.5">
              Atención {{ r.horario }}
            </p>
          </a>
        </div>
      </section>

      <!-- Biblioteca compartida -->
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
    </template>
  </div>
</template>
