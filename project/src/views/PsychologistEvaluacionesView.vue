<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();

const datos = ref(null);
const cargando = ref(true);
const error = ref("");

const soloSinRevisar = ref(false);
const filtroTexto = ref("");
const filtroRiesgo = ref("");
const soloCrisis = ref(false);
const soloDiscrepancia = ref(false);

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
    datos.value = await api.evaluacionesRecientes({
      limite: 200,
      soloSinRevisar: soloSinRevisar.value,
    });
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const filas = computed(() => {
  let xs = datos.value?.evaluaciones || [];
  const q = filtroTexto.value.trim().toLowerCase();
  if (q) {
    xs = xs.filter((f) =>
      [
        `${f.nombre} ${f.apellido}`,
        f.codigo_alumno || "",
        f.plantilla || "",
        f.grado || "",
      ].some((x) => x.toLowerCase().includes(q)),
    );
  }
  if (filtroRiesgo.value) {
    xs = xs.filter(
      (f) => (f.riesgo_global || "").toUpperCase() === filtroRiesgo.value,
    );
  }
  if (soloCrisis.value) xs = xs.filter((f) => f.crisis_activada);
  if (soloDiscrepancia.value) {
    xs = xs.filter((f) => f.svm?.discrepancia_con_reglas);
  }
  return xs;
});

const resumen = computed(() => datos.value?.resumen || null);

function colorRiesgo(r) {
  const k = (r || "").toUpperCase();
  if (k.startsWith("C")) return "text-red-700 bg-red-50 border-red-200";
  if (k === "ALTO") return "text-orange-700 bg-orange-50 border-orange-200";
  if (k === "MEDIO") return "text-amber-700 bg-amber-50 border-amber-200";
  if (k === "BAJO") return "text-sky-700 bg-sky-50 border-sky-200";
  return "text-gray-700 bg-gray-50 border-gray-200";
}

function colorSeveridad(b) {
  if (b.bandera_crisis) return "text-red-700 bg-red-50 border-red-200";
  if (b.severidad_alerta)
    return "text-amber-700 bg-amber-50 border-amber-200";
  return "text-green-800 bg-green-50 border-green-200";
}

function fecha(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function abrir(f) {
  router.push({ name: "psicologo-resultado", params: { id: f.aplicacion_id } });
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Bandeja clínica</p>
      <h1 class="hero-serif text-[28px]">
        Últimas <span class="hero-mint">evaluaciones</span>
      </h1>
      <p class="text-sm text-ink-500 mt-2">
        Cada fila es un cuestionario rendido y ya evaluado por el sistema.
        Puntajes por escala, bandera de crisis, riesgo compuesto, segunda
        opinión del SVM y cuántas frases marcó BETO.
      </p>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <!-- Resumen -->
      <p class="text-[11px] text-ink-400 mb-2">
        Resumen sobre las {{ datos.total }} evaluaciones más recientes.
      </p>
      <div v-if="resumen" class="grid grid-cols-2 md:grid-cols-5 gap-3 mb-5">
        <div class="card p-4">
          <p class="text-xs text-ink-500">Evaluaciones</p>
          <p class="text-2xl font-semibold text-green-900">
            {{ datos.total }}
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Con crisis</p>
          <p class="text-2xl font-semibold text-red-700">
            {{ resumen.con_crisis }}
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Sin revisar</p>
          <p class="text-2xl font-semibold text-amber-700">
            {{ resumen.sin_revisar }}
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Con SVM</p>
          <p class="text-2xl font-semibold text-green-900">
            {{ resumen.con_svm }}
          </p>
          <p class="text-[11px] text-ink-400">
            {{ resumen.svm_discrepante }} discrepan con las reglas
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Con frases (BETO)</p>
          <p class="text-2xl font-semibold text-green-900">
            {{ resumen.con_frases }}
          </p>
          <p class="text-[11px] text-ink-400">
            {{ resumen.juzgadas }} con veredicto tuyo
          </p>
        </div>
      </div>

      <!-- Filtros -->
      <div class="card p-4 mb-4 grid gap-3 md:grid-cols-4 items-end">
        <div class="md:col-span-2">
          <label class="text-xs text-ink-500">Buscar</label>
          <input
            v-model="filtroTexto"
            class="input"
            placeholder="Nombre, código (SAMI-4TO-07), plantilla, grado…"
          />
        </div>
        <div>
          <label class="text-xs text-ink-500">Riesgo</label>
          <select v-model="filtroRiesgo" class="input">
            <option value="">Todos</option>
            <option value="CRITICO">CRÍTICO</option>
            <option value="ALTO">ALTO</option>
            <option value="MEDIO">MEDIO</option>
            <option value="BAJO">BAJO</option>
            <option value="SIN_RIESGO">SIN RIESGO</option>
          </select>
        </div>
        <div class="flex flex-col gap-1 text-xs text-ink-600">
          <label class="flex items-center gap-2">
            <input v-model="soloCrisis" type="checkbox" />
            Solo con bandera de crisis
          </label>
          <label class="flex items-center gap-2">
            <input v-model="soloDiscrepancia" type="checkbox" />
            Solo donde SVM discrepa
          </label>
          <label class="flex items-center gap-2">
            <input
              v-model="soloSinRevisar"
              type="checkbox"
              @change="cargar"
            />
            Solo sin revisar
          </label>
        </div>
      </div>

      <p class="text-xs text-ink-400 mb-2">
        {{ filas.length }} de {{ datos.total }} evaluaciones
      </p>

      <div v-if="filas.length === 0" class="card p-6 text-ink-500">
        No hay evaluaciones que coincidan con el filtro.
      </div>

      <div v-else class="grid gap-3">
        <div
          v-for="f in filas"
          :key="f.aplicacion_id"
          class="card p-4"
          :class="{ 'border-red-300 bg-red-50/30': f.crisis_activada }"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="min-w-0">
              <p class="font-semibold text-green-900">
                <span v-if="f.codigo_alumno" class="font-mono text-sm">
                  {{ f.codigo_alumno }}
                </span>
                <span v-else>{{ f.nombre }} {{ f.apellido }}</span>
              </p>
              <p class="text-xs text-ink-500 truncate">
                {{ f.plantilla }}
                <span v-if="f.grado"> — {{ f.grado }}</span>
              </p>
              <p class="text-[11px] text-ink-400 mt-0.5">
                Rendido {{ fecha(f.completada_at) }}
                <span v-if="f.revisada_at"> · revisado</span>
                <span v-else class="text-amber-700"> · sin revisar</span>
                <span v-if="f.veredicto_psicologo">
                  · análisis {{ f.veredicto_psicologo }}
                </span>
              </p>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span
                class="text-xs px-2 py-0.5 rounded-full border whitespace-nowrap"
                :class="colorRiesgo(f.riesgo_global)"
              >
                {{ f.riesgo_global || "sin riesgo calculado" }}
              </span>
              <button class="btn-mint btn-sm" @click="abrir(f)">Abrir</button>
            </div>
          </div>

          <!-- Bloques -->
          <div v-if="f.bloques.length" class="flex flex-wrap gap-2 mt-3">
            <span
              v-for="b in f.bloques"
              :key="b.codigo"
              class="text-[11px] px-2 py-0.5 rounded border"
              :class="colorSeveridad(b)"
              :title="b.nombre"
            >
              {{ b.codigo }} {{ b.puntaje }}/{{ b.rango_max }} ·
              {{ b.severidad }}
              <span v-if="b.bandera_crisis"> · ítem crítico</span>
            </span>
          </div>

          <!-- SVM + BETO -->
          <div class="flex flex-wrap gap-2 mt-2 text-[11px]">
            <span
              v-if="f.svm"
              class="px-2 py-0.5 rounded border"
              :class="
                f.svm.discrepancia_con_reglas
                  ? 'text-amber-800 bg-amber-50 border-amber-300'
                  : 'text-green-800 bg-green-50 border-green-200'
              "
            >
              SVM: {{ f.svm.clase }} ({{
                Math.round(f.svm.probabilidad * 100)
              }}%, confianza {{ f.svm.confianza }})
              <span v-if="f.svm.discrepancia_con_reglas">
                — discrepa con las reglas
              </span>
            </span>
            <span
              v-if="f.n_frases"
              class="px-2 py-0.5 rounded border"
              :class="
                f.n_frases_crisis
                  ? 'text-red-700 bg-red-50 border-red-200'
                  : 'text-ink-600 bg-gray-50 border-gray-200'
              "
            >
              BETO: {{ f.n_frases }} frases
              <span v-if="f.n_frases_crisis">
                · {{ f.n_frases_crisis }} con ideación
              </span>
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
