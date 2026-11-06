<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();
const estudiantes = ref([]);
const cargando = ref(true);
const error = ref("");
const filtroNombre = ref("");
const filtroRiesgo = ref("");

async function cargar() {
  cargando.value = true;
  try {
    estudiantes.value = await api.listarEstudiantes();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

// Normaliza "CRÍTICO"/"CRITICO" y valores vacíos: un estudiante sin evaluación
// no trae `ultimo_riesgo` y no debe romper el filtro (QA CP089).
const nivel = (r) => (r || "").toUpperCase().replace("Í", "I");

const filtrados = computed(() => {
  const q = filtroNombre.value.trim().toLowerCase();
  const lista = estudiantes.value || [];
  return lista.filter((e) => {
    const coincideTexto =
      !q ||
      [`${e.nombre} ${e.apellido}`.toLowerCase(), (e.email || "").toLowerCase()].some(
        (x) => x.includes(q),
      );
    const coincideRiesgo =
      !filtroRiesgo.value || nivel(e.ultimo_riesgo) === filtroRiesgo.value;
    return coincideTexto && coincideRiesgo;
  });
});

function verEstudiante(e) {
  router.push({ name: "psicologo-estudiante", params: { id: e.id } });
}

function asignar(e) {
  router.push({ name: "asignar-cuestionario", query: { estudiante: e.id } });
}

function colorRiesgo(r) {
  const k = (r || "").toUpperCase();
  if (k.startsWith("C")) return "text-red-700 bg-red-50 border-red-200";
  if (k === "ALTO") return "text-orange-700 bg-orange-50 border-orange-200";
  if (k === "MEDIO") return "text-amber-700 bg-amber-50 border-amber-200";
  if (k === "BAJO") return "text-sky-700 bg-sky-50 border-sky-200";
  return "text-gray-700 bg-gray-50 border-gray-200";
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Listado</p>
      <h1 class="hero-serif text-[28px]">
        Mis <span class="hero-mint">estudiantes</span>
      </h1>
    </header>

    <div class="flex flex-wrap gap-3 mb-4">
      <input
        v-model="filtroNombre"
        class="input flex-1 min-w-[220px]"
        placeholder="Buscar por nombre o email…"
      />
      <select v-model="filtroRiesgo" class="input" style="width: 200px" aria-label="Nivel de riesgo">
        <option value="">Todos los niveles</option>
        <option value="CRITICO">Crítico</option>
        <option value="ALTO">Alto</option>
        <option value="MEDIO">Medio</option>
        <option value="BAJO">Bajo</option>
        <option value="SIN_RIESGO">Sin riesgo</option>
      </select>
    </div>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <div v-else-if="filtrados.length === 0" class="card p-6 text-ink-500">
      Ningún estudiante coincide con el filtro.
    </div>

    <div v-else class="grid gap-3">
      <div
        v-for="e in filtrados"
        :key="e.id"
        class="card p-4 flex items-center justify-between"
      >
        <div class="flex-1">
          <p class="font-semibold text-green-900">
            {{ e.nombre }} {{ e.apellido }}
          </p>
          <p class="text-xs text-ink-500">
            {{ e.email }}
            <span v-if="e.grado"> — {{ e.grado }}</span>
          </p>
          <p class="text-xs text-ink-400 mt-1">
            {{ e.total_cuestionarios }} cuestionarios
          </p>
        </div>
        <div class="flex items-center gap-3">
          <span
            v-if="e.ultimo_riesgo"
            class="text-xs px-2 py-0.5 rounded-full border"
            :class="colorRiesgo(e.ultimo_riesgo)"
          >
            {{ e.ultimo_riesgo }}
          </span>
          <button class="btn-ghost btn-sm" @click="verEstudiante(e)">Ver</button>
          <button class="btn-mint btn-sm" @click="asignar(e)">Asignar</button>
        </div>
      </div>
    </div>
  </div>
</template>
