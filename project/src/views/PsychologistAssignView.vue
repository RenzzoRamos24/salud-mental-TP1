<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

// Mismo tope que el backend (plantilla_service.MAX_PREGUNTAS). El backend
// rechaza igual; esto es solo para avisar antes.
const MAX_PREGUNTAS = 26;

const route = useRoute();
const router = useRouter();
const estudiantes = ref([]);
const plantillas = ref([]);
const seleccionPlantilla = ref(null);
const seleccionEstudiante = ref(null);
const seleccionGrado = ref(null);
const modo = ref("salon"); // "salon" | "alumno"
const cargando = ref(true);
const enviando = ref(false);
const mensaje = ref("");
const error = ref("");

async function cargar() {
  cargando.value = true;
  try {
    const [est, pls] = await Promise.all([
      api.listarEstudiantes(),
      api.listarPlantillas(),
    ]);
    estudiantes.value = est;
    plantillas.value = pls;
    if (route.query.plantilla) {
      seleccionPlantilla.value = Number(route.query.plantilla);
    }
    if (route.query.estudiante) {
      // Si viene desde la ficha de un alumno, abrir en modo individual.
      seleccionEstudiante.value = route.query.estudiante;
      modo.value = "alumno";
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const plantillaElegida = computed(
  () => plantillas.value.find((p) => p.id === seleccionPlantilla.value) || null,
);
const excedeMaximo = computed(
  () => (plantillaElegida.value?.n_preguntas || 0) > MAX_PREGUNTAS,
);

// Salones disponibles: los grados de los alumnos a cargo, con su cantidad.
const salones = computed(() => {
  const conteo = {};
  for (const e of estudiantes.value) {
    if (e.grado) conteo[e.grado] = (conteo[e.grado] || 0) + 1;
  }
  return Object.entries(conteo)
    .map(([grado, n]) => ({ grado, n }))
    .sort((a, b) => a.grado.localeCompare(b.grado));
});

const puedeEnviar = computed(() => {
  if (!seleccionPlantilla.value || excedeMaximo.value) return false;
  return modo.value === "salon" ? !!seleccionGrado.value : !!seleccionEstudiante.value;
});

async function asignar() {
  if (!puedeEnviar.value) return;
  error.value = "";
  mensaje.value = "";
  enviando.value = true;
  try {
    if (modo.value === "salon") {
      const r = await api.asignarCuestionarioGrado(
        seleccionPlantilla.value,
        seleccionGrado.value,
      );
      mensaje.value =
        `"${r.plantilla}" asignado a ${r.asignados} alumno(s) de ${r.grado}.` +
        (r.omitidos_ya_tenian
          ? ` ${r.omitidos_ya_tenian} ya lo tenían pendiente y no se duplicó.`
          : "") +
        " Lo verán en su panel para responderlo en la sesión.";
    } else {
      const res = await api.asignarCuestionario(
        seleccionPlantilla.value,
        seleccionEstudiante.value,
      );
      mensaje.value = `Cuestionario asignado (#${res.id}). El alumno lo verá en su panel.`;
      seleccionEstudiante.value = null;
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo asignar.";
  } finally {
    enviando.value = false;
  }
}
</script>

<template>
  <div class="page-shell">
    <header class="mb-6">
      <p class="eyebrow mb-2">Aplicar cuestionario</p>
      <h1 class="hero-serif text-[28px]">
        Asignar <span class="hero-mint">cuestionario</span>
      </h1>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>

    <template v-else>
      <div v-if="error" class="banner-danger mb-4">{{ error }}</div>
      <div v-if="mensaje" class="banner-success mb-4">{{ mensaje }}</div>

      <div class="card p-6 mb-4">
        <label class="label">Plantilla</label>
        <select v-model="seleccionPlantilla" class="input">
          <option :value="null" disabled>— Elige una plantilla —</option>
          <option v-for="p in plantillas" :key="p.id" :value="p.id">
            {{ p.nombre }} — {{ p.n_preguntas ?? "?" }} preguntas
            {{ (p.n_preguntas || 0) > MAX_PREGUNTAS ? "(supera el máximo)" : "" }}
          </option>
        </select>
        <p v-if="plantillas.length === 0" class="text-sm text-ink-500 mt-2">
          Todavía no tienes plantillas.
          <router-link to="/psicologo/plantillas" class="text-green-700 underline">
            Crear una
          </router-link>.
        </p>
        <div v-if="excedeMaximo" class="banner-danger mt-3">
          Esta plantilla tiene {{ plantillaElegida.n_preguntas }} preguntas y el
          máximo permitido es {{ MAX_PREGUNTAS }}. No se puede asignar: edítala en
          Plantillas hasta dejarla en {{ MAX_PREGUNTAS }} o menos.
        </div>
      </div>

      <div class="card p-6 mb-4">
        <div class="flex gap-2 mb-4">
          <button
            class="px-3 py-1.5 rounded-lg text-sm border transition"
            :class="modo === 'salon'
              ? 'bg-green-700 text-white border-green-700'
              : 'bg-white text-ink-600 border-cream-200 hover:border-green-400'"
            @click="modo = 'salon'"
          >
            Por salón
          </button>
          <button
            class="px-3 py-1.5 rounded-lg text-sm border transition"
            :class="modo === 'alumno'
              ? 'bg-green-700 text-white border-green-700'
              : 'bg-white text-ink-600 border-cream-200 hover:border-green-400'"
            @click="modo = 'alumno'"
          >
            Por alumno
          </button>
        </div>

        <template v-if="modo === 'salon'">
          <label class="label">Salón</label>
          <select v-model="seleccionGrado" class="input">
            <option :value="null" disabled>— Elige un salón —</option>
            <option v-for="s in salones" :key="s.grado" :value="s.grado">
              {{ s.grado }} ({{ s.n }} alumnos)
            </option>
          </select>
          <p v-if="salones.length === 0" class="text-sm text-ink-500 mt-2">
            No tienes alumnos con salón registrado a tu cargo.
          </p>
          <p v-else class="text-xs text-ink-400 mt-2">
            Se asigna a todos los alumnos del salón a la vez, para responderlo en
            una misma sesión. Si alguno ya lo tiene pendiente, no se duplica.
          </p>
        </template>

        <template v-else>
          <label class="label">Estudiante</label>
          <select v-model="seleccionEstudiante" class="input">
            <option :value="null" disabled>— Elige un estudiante —</option>
            <option v-for="e in estudiantes" :key="e.id" :value="e.id">
              {{ e.nombre }} {{ e.apellido }} ({{ e.email }})
            </option>
          </select>
        </template>
      </div>

      <div class="flex justify-between">
        <button class="btn-ghost" @click="router.push('/psicologo/plantillas')">
          ← Plantillas
        </button>
        <button
          class="btn-mint"
          :disabled="!puedeEnviar || enviando"
          @click="asignar"
        >
          {{
            enviando
              ? "Asignando…"
              : modo === "salon"
                ? "Asignar a todo el salón"
                : "Asignar cuestionario"
          }}
        </button>
      </div>
    </template>
  </div>
</template>
