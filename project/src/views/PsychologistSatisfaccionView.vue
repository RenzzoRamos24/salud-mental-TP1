<script setup>
import { ref, onMounted, computed } from "vue";
import { api } from "../api";

// Cómo vivieron los chicos la aplicación del cuestionario.
//
// Se muestra la distribución y no solo el promedio: un 3.8 puede ser todos en
// 4, o la mitad en 5 y la mitad en 2, y eso cambia por completo qué hacer. Y
// van todos los comentarios, no una muestra — ahí es donde dicen lo que
// ninguna escala captura.

const datos = ref(null);
const cargando = ref(true);
const error = ref("");

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
    datos.value = await api.satisfaccionAlumnos();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}
onMounted(cargar);

const d = computed(() => datos.value);

function pct(x) {
  return x === null || x === undefined ? "—" : (x * 100).toFixed(0) + "%";
}

// Verde si va bien, ámbar si está al límite, rojo si hay que mirarlo.
function colorPromedio(v) {
  if (v === null || v === undefined) return "text-ink-400";
  if (v >= 4) return "text-green-700";
  if (v >= 3) return "text-amber-700";
  return "text-red-700";
}

function anchoBarra(dist, valor) {
  const total = Object.values(dist).reduce((a, b) => a + b, 0);
  if (!total) return 0;
  return Math.round((dist[valor] / total) * 100);
}

const COLOR_VALOR = {
  1: "bg-red-400",
  2: "bg-orange-300",
  3: "bg-amber-300",
  4: "bg-green-300",
  5: "bg-green-500",
};

function fecha(iso) {
  return iso ? new Date(iso).toLocaleDateString("es-PE") : "";
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Experiencia del alumno</p>
      <h1 class="hero-serif text-[28px]">
        Encuesta de <span class="hero-mint">satisfacción</span>
      </h1>
      <p class="text-sm text-ink-500 mt-2">
        Qué les pareció responder el cuestionario. Mide la experiencia de
        ellos, no su estado clínico.
      </p>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <div v-else-if="!d.total" class="card p-8 text-center">
      <p class="font-semibold text-green-900 mb-1">Todavía no hay respuestas.</p>
      <p class="text-sm text-ink-500">
        La encuesta se le ofrece al alumno después de cerrar su cuestionario.
        <span v-if="d.alumnos_con_cuestionario">
          {{ d.alumnos_con_cuestionario }} ya rindieron, así que podrían
          responderla.
        </span>
      </p>
    </div>

    <template v-else>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-5">
        <div class="card p-4">
          <p class="text-xs text-ink-500">Respondieron</p>
          <p class="text-2xl font-semibold text-green-900">{{ d.total }}</p>
          <p class="text-[11px] text-ink-400">
            de {{ d.alumnos_con_cuestionario }} que rindieron
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Tasa de respuesta</p>
          <p class="text-2xl font-semibold text-green-900">
            {{ pct(d.tasa_respuesta) }}
          </p>
          <p class="text-[11px] text-ink-400">
            los promedios describen a quienes contestaron
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Promedio general</p>
          <p class="text-2xl font-semibold" :class="colorPromedio(d.promedio_global)">
            {{ d.promedio_global }}<span class="text-sm text-ink-400">/5</span>
          </p>
        </div>
      </div>

      <div class="grid gap-3 mb-6">
        <div v-for="dim in d.dimensiones" :key="dim.clave" class="card p-5">
          <div class="flex items-start justify-between gap-4 mb-3 flex-wrap">
            <div>
              <p class="font-semibold text-green-900">{{ dim.pregunta }}</p>
              <p v-if="dim.n_bajos" class="text-xs text-red-700 mt-0.5">
                {{ dim.n_bajos }}
                {{ dim.n_bajos === 1 ? "alumno respondió" : "alumnos respondieron" }}
                1 o 2 — son los que vale la pena mirar
              </p>
            </div>
            <p class="text-xl font-semibold" :class="colorPromedio(dim.promedio)">
              {{ dim.promedio }}<span class="text-xs text-ink-400">/5</span>
            </p>
          </div>

          <div class="grid gap-1">
            <div
              v-for="v in [5, 4, 3, 2, 1]"
              :key="v"
              class="flex items-center gap-2 text-xs"
            >
              <span class="w-3 text-ink-500">{{ v }}</span>
              <div class="flex-1 h-4 bg-cream-100 rounded overflow-hidden">
                <div
                  class="h-full transition-all"
                  :class="COLOR_VALOR[v]"
                  :style="{ width: anchoBarra(dim.distribucion, String(v)) + '%' }"
                />
              </div>
              <span class="w-10 text-right text-ink-500">
                {{ dim.distribucion[String(v)] }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <section>
        <h2 class="text-lg font-semibold text-green-900 mb-1">
          Lo que escribieron
        </h2>
        <p class="text-xs text-ink-500 mb-3">
          {{ d.comentarios.length }}
          {{ d.comentarios.length === 1 ? "comentario" : "comentarios" }}
          de {{ d.total }} respuestas. Van todos, sin recortar.
        </p>

        <div v-if="!d.comentarios.length" class="card p-5 text-sm text-ink-500">
          Nadie dejó comentarios.
        </div>

        <div v-else class="grid gap-2">
          <div
            v-for="(c, i) in d.comentarios"
            :key="i"
            class="card p-4"
            :class="c.satisfaccion_general <= 2 ? 'border-red-200 bg-red-50/30' : ''"
          >
            <p class="text-sm text-ink-700 whitespace-pre-line">{{ c.comentario }}</p>
            <p class="text-[11px] text-ink-400 mt-2">
              Satisfacción general: {{ c.satisfaccion_general }}/5
              <span v-if="c.timestamp"> · {{ fecha(c.timestamp) }}</span>
            </p>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
