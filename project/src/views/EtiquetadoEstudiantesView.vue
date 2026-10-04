<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

// La lista de alumnos a evaluar: se elige uno, se abre su caso y se emite el
// juicio.
//
// A propósito no muestra el riesgo que calculó el modelo. Si la lista dijera
// "CRÍTICO" al lado de cada nombre, se abriría cada caso ya sabiendo la
// respuesta y el juicio dejaría de ser independiente.

const router = useRouter();

const datos = ref(null);
const cargando = ref(true);
const error = ref("");
const esPrueba = ref(false);
const filtro = ref("");
const soloPendientes = ref(false);

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
    const [d, p] = await Promise.all([
      api.etiquetadoEstudiantes(),
      api.etiquetadoProgreso(),
    ]);
    datos.value = d;
    esPrueba.value = !!p.es_cuenta_prueba;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar la lista.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const filas = computed(() => {
  let xs = datos.value?.estudiantes || [];
  const q = filtro.value.trim().toLowerCase();
  if (q) {
    xs = xs.filter((e) =>
      [e.nombre, e.codigo, e.codigo_alumno || "", e.grado || ""].some((x) =>
        x.toLowerCase().includes(q),
      ),
    );
  }
  if (soloPendientes.value) xs = xs.filter((e) => !e.mi_etiqueta);
  return xs;
});

const pct = computed(() => {
  const d = datos.value;
  if (!d?.total) return 0;
  return Math.round((d.etiquetados / d.total) * 100);
});

function abrir(e) {
  router.push({ name: "etiquetado-caso", params: { id: e.aplicacion_id } });
}

function siguientePendiente() {
  const p = (datos.value?.estudiantes || []).find((e) => !e.mi_etiqueta);
  if (p) abrir(p);
}

function fecha(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
  });
}

function colorRiesgo(r) {
  const k = (r || "").toUpperCase();
  if (k.startsWith("C")) return "bg-red-50 border-red-300 text-red-800";
  if (k === "ALTO") return "bg-orange-50 border-orange-300 text-orange-800";
  if (k === "MEDIO") return "bg-amber-50 border-amber-300 text-amber-800";
  if (k === "BAJO") return "bg-sky-50 border-sky-300 text-sky-800";
  return "bg-gray-50 border-gray-300 text-gray-700";
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-5">
      <p class="eyebrow mb-2">Evaluación clínica</p>
      <h1 class="hero-serif text-[28px]">
        Alumnos por <span class="hero-mint">evaluar</span>
      </h1>
      <p class="text-sm text-ink-500 mt-2">
        Abrí cada alumno, leé sus respuestas y dejá tu evaluación clínica.
      </p>
    </header>

    <div
      v-if="datos && datos.total && datos.etiquetados >= datos.total"
      class="banner-success mb-4 text-sm"
    >
      <strong>Terminaste de evaluar.</strong> El panel clínico completo ya está
      disponible en el menú de la izquierda: alumnos con su riesgo, alertas,
      satisfacción y todo lo demás.
    </div>
    <div
      v-else-if="datos && datos.total"
      class="banner-info mb-4 text-sm"
    >
      Te faltan <strong>{{ datos.total - datos.etiquetados }}</strong> de
      {{ datos.total }} alumnos. Al terminarlos se te abre el panel clínico
      completo — hasta entonces queda cerrado para que tu criterio no esté
      influido por lo que calculó el sistema.
    </div>

    <div v-if="esPrueba" class="banner-warn mb-4 text-sm">
      <strong>Cuenta de prueba.</strong> Podés recorrer todo el flujo y tus
      evaluaciones se guardan, pero quedan fuera de las métricas. Para la
      validación real hay que usar un código <code>SAMI-PSI-NN</code>.
    </div>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <div v-else-if="!datos.total" class="card p-8 text-center">
      <p class="font-semibold text-green-900 mb-1">
        No hay alumnos para evaluar.
      </p>
      <p class="text-sm text-ink-500">
        <template v-if="datos.corte_desde">
          El corte vigente solo incluye evaluaciones desde
          <strong>{{ datos.corte_desde }}</strong>. Si la aplicación del
          colegio fue antes de esa fecha, hay que mover el corte desde
          <router-link to="/etiquetado/metricas" class="underline">
            Resultados</router-link>.
        </template>
        <template v-else>
          Todavía no hay cuestionarios cerrados y evaluados.
        </template>
      </p>
    </div>

    <template v-else>
      <!-- Progreso -->
      <div class="card p-4 mb-4">
        <div class="flex items-center justify-between mb-2 flex-wrap gap-2">
          <p class="text-sm text-ink-600">
            <strong class="text-green-900">{{ datos.etiquetados }}</strong>
            de {{ datos.total }} alumnos evaluados
            <span v-if="datos.corte_desde" class="text-ink-400">
              · cohorte desde {{ datos.corte_desde }}
            </span>
          </p>
          <button
            v-if="datos.etiquetados < datos.total"
            class="btn-primary btn-sm"
            @click="siguientePendiente"
          >
            Continuar con el siguiente
          </button>
        </div>
        <div class="h-2 bg-cream-200 rounded-full overflow-hidden">
          <div
            class="h-full bg-green-600 transition-all"
            :style="{ width: pct + '%' }"
          />
        </div>
      </div>

      <!-- Filtros -->
      <div class="flex flex-wrap items-center gap-3 mb-3">
        <input
          v-model="filtro"
          class="input flex-1 min-w-[220px]"
          placeholder="Buscar por nombre, código o grado…"
        />
        <label class="flex items-center gap-2 text-xs text-ink-600">
          <input v-model="soloPendientes" type="checkbox" />
          Solo los que me faltan
        </label>
      </div>

      <p class="text-xs text-ink-400 mb-2">
        {{ filas.length }} de {{ datos.total }}
      </p>

      <div v-if="!filas.length" class="card p-6 text-ink-500">
        Ninguno coincide con el filtro.
      </div>

      <div v-else class="grid gap-2">
        <button
          v-for="e in filas"
          :key="e.aplicacion_id"
          class="card p-4 text-left hover:bg-cream-50 transition flex items-center justify-between gap-4"
          :class="e.mi_etiqueta ? 'border-green-200' : ''"
          @click="abrir(e)"
        >
          <div class="min-w-0">
            <p class="font-semibold text-green-900 truncate">
              {{ e.nombre }}
              <span v-if="e.codigo_alumno" class="font-mono text-xs text-ink-400">
                {{ e.codigo_alumno }}
              </span>
            </p>
            <p class="text-xs text-ink-500">
              {{ e.codigo }}
              <span v-if="e.grado"> · {{ e.grado }}</span>
              · rendido {{ fecha(e.completada_at) }}
            </p>
            <p
              v-if="e.otros_evaluadores"
              class="text-[11px] text-ink-400 mt-0.5"
            >
              Ya lo evaluó {{ e.otros_evaluadores }}
              {{ e.otros_evaluadores === 1 ? "colega" : "colegas" }}
              — no ves su juicio, a propósito
            </p>
          </div>

          <div class="shrink-0 flex items-center gap-2">
            <template v-if="e.mi_etiqueta">
              <span
                class="text-xs px-2 py-0.5 rounded-full border whitespace-nowrap"
                :class="colorRiesgo(e.mi_etiqueta.riesgo_clinico)"
              >
                {{ e.mi_etiqueta.riesgo_clinico }}
              </span>
              <span
                v-if="e.mi_etiqueta.requiere_derivacion"
                class="text-xs px-2 py-0.5 rounded-full border border-red-300 bg-red-50 text-red-800 whitespace-nowrap"
              >
                derivar
              </span>
            </template>
            <span v-else class="text-xs text-amber-700 whitespace-nowrap">
              pendiente
            </span>
          </div>
        </button>
      </div>
    </template>
  </div>
</template>
