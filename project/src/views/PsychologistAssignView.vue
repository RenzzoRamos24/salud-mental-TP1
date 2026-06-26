<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

const route = useRoute();
const router = useRouter();
const estudiantes = ref([]);
const plantillas = ref([]);
const seleccionPlantilla = ref(null);
const seleccionEstudiante = ref(null);
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
      seleccionEstudiante.value = route.query.estudiante;
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const puedeEnviar = computed(
  () => seleccionPlantilla.value && seleccionEstudiante.value,
);

async function asignar() {
  if (!puedeEnviar.value) return;
  error.value = "";
  mensaje.value = "";
  enviando.value = true;
  try {
    const res = await api.asignarCuestionario(
      seleccionPlantilla.value,
      seleccionEstudiante.value,
    );
    mensaje.value = `Cuestionario asignado (#${res.id}). El alumno lo verá en su panel.`;
    seleccionEstudiante.value = null;
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
        Asignar <span class="hero-mint">a un alumno</span>
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
            {{ p.nombre }} ({{ p.bloques.length }} bloques)
          </option>
        </select>
        <p v-if="plantillas.length === 0" class="text-sm text-ink-500 mt-2">
          Todavía no tienes plantillas.
          <router-link to="/psicologo/plantillas" class="text-green-700 underline">
            Crear una
          </router-link>.
        </p>
      </div>

      <div class="card p-6 mb-4">
        <label class="label">Estudiante</label>
        <select v-model="seleccionEstudiante" class="input">
          <option :value="null" disabled>— Elige un estudiante —</option>
          <option v-for="e in estudiantes" :key="e.id" :value="e.id">
            {{ e.nombre }} {{ e.apellido }} ({{ e.email }})
          </option>
        </select>
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
          {{ enviando ? "Asignando…" : "Asignar cuestionario" }}
        </button>
      </div>
    </template>
  </div>
</template>
