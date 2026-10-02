<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import { etiquetaValor } from "../escalas";

// Un alumno: sus respuestas crudas arriba, el formulario de evaluación al
// costado, y el análisis del sistema **debajo, recién después de guardar**.
//
// Ese orden es el punto. Si el análisis estuviera visible de entrada, la
// evaluación mediría cuánto coincide la psicóloga con el modelo que acaba de
// leer, no su criterio propio — y el κ entre las dos evaluadoras no diría
// nada. El backend tampoco lo manda antes: `analisis_sistema` llega en null
// hasta que hay juicio guardado.

const route = useRoute();
const router = useRouter();
const aplicacionId = computed(() => Number(route.params.id));

const caso = ref(null);
const cargando = ref(true);
const guardando = ref(false);
const error = ref("");
const analisis = ref(null);
const recienGuardado = ref(false);

const riesgo = ref(null);
const derivacion = ref(null);
const predominante = ref(null);
const ideacion = ref(null);
const confianza = ref("alta");
const comentario = ref("");

let t0 = Date.now();

const urgenteAbierto = ref(false);
const motivoUrgente = ref("");
const avisoUrgente = ref("");

const RIESGOS = [
  { v: "SIN_RIESGO", label: "Sin riesgo", clase: "bg-gray-50 border-gray-300 text-gray-700" },
  { v: "BAJO", label: "Bajo", clase: "bg-sky-50 border-sky-300 text-sky-800" },
  { v: "MEDIO", label: "Medio", clase: "bg-amber-50 border-amber-300 text-amber-800" },
  { v: "ALTO", label: "Alto", clase: "bg-orange-50 border-orange-300 text-orange-800" },
  { v: "CRITICO", label: "Crítico", clase: "bg-red-50 border-red-300 text-red-800" },
];
const PREDOMINANTES = [
  { v: "depresion", label: "Depresión" },
  { v: "ansiedad", label: "Ansiedad" },
  { v: "estres", label: "Estrés" },
  { v: "ninguno", label: "Ninguno" },
];

const yaEvaluado = computed(() => !!caso.value?.mi_etiqueta);
const puedeGuardar = computed(
  () => !!riesgo.value && derivacion.value !== null && !guardando.value,
);

const bloques = computed(() => {
  if (!caso.value) return [];
  const map = new Map();
  for (const it of caso.value.items) {
    if (!map.has(it.bloque)) map.set(it.bloque, []);
    map.get(it.bloque).push(it);
  }
  return [...map.entries()].map(([nombre, items]) => ({ nombre, items }));
});

async function cargar() {
  cargando.value = true;
  error.value = "";
  recienGuardado.value = false;
  try {
    const c = await api.etiquetadoCaso(aplicacionId.value);
    caso.value = c;
    analisis.value = c.analisis_sistema || null;
    const m = c.mi_etiqueta;
    riesgo.value = m?.riesgo_clinico ?? null;
    derivacion.value = m ? !!m.requiere_derivacion : null;
    predominante.value = m?.predominante ?? null;
    ideacion.value = m?.ideacion_presente ?? null;
    confianza.value = m?.confianza ?? "alta";
    comentario.value = m?.comentario ?? "";
    t0 = Date.now();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar el caso.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);
watch(aplicacionId, cargar);

async function guardar() {
  if (!puedeGuardar.value) return;
  guardando.value = true;
  error.value = "";
  try {
    const r = await api.etiquetadoGuardarCaso({
      aplicacion_id: aplicacionId.value,
      riesgo_clinico: riesgo.value,
      requiere_derivacion: derivacion.value,
      predominante: predominante.value,
      ideacion_presente: ideacion.value,
      confianza: confianza.value,
      comentario: comentario.value.trim() || null,
      segundos: Math.round((Date.now() - t0) / 1000),
    });
    analisis.value = r.analisis_sistema || null;
    recienGuardado.value = true;
    if (caso.value) {
      caso.value.mi_etiqueta = { riesgo_clinico: riesgo.value };
    }
    // Desplazo a la comparación, que es lo que se quiere ver al guardar.
    setTimeout(() => {
      document.getElementById("analisis")?.scrollIntoView({ behavior: "smooth" });
    }, 80);
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo guardar.";
  } finally {
    guardando.value = false;
  }
}

async function enviarUrgente() {
  if (!motivoUrgente.value.trim()) return;
  try {
    await api.etiquetadoMarcarUrgente(aplicacionId.value, motivoUrgente.value.trim());
    avisoUrgente.value =
      "Avisado. Queda una nota en el expediente del alumno para la psicóloga a cargo.";
    urgenteAbierto.value = false;
    motivoUrgente.value = "";
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo avisar.";
  }
}

function colorRiesgo(r) {
  const k = (r || "").toUpperCase();
  if (k.startsWith("C")) return "text-red-700 bg-red-50 border-red-200";
  if (k === "ALTO") return "text-orange-700 bg-orange-50 border-orange-200";
  if (k === "MEDIO") return "text-amber-700 bg-amber-50 border-amber-200";
  if (k === "BAJO") return "text-sky-700 bg-sky-50 border-sky-200";
  return "text-gray-700 bg-gray-50 border-gray-200";
}

// ¿Coincidimos? Binarizado en MEDIO, el mismo corte que usa el sistema para
// considerar que hay señal.
const ORDEN = ["SIN_RIESGO", "BAJO", "MEDIO", "ALTO", "CRITICO"];
const coincidencia = computed(() => {
  if (!analisis.value || !riesgo.value) return null;
  const mio = ORDEN.indexOf(riesgo.value);
  const suyo = ORDEN.indexOf(
    (analisis.value.riesgo_global || "").toUpperCase().replace("Í", "I"),
  );
  if (suyo < 0) return null;
  if (mio === suyo) return { tipo: "exacta", texto: "Coinciden exactamente." };
  const alertaMia = mio >= 2;
  const alertaSuya = suyo >= 2;
  if (alertaMia === alertaSuya) {
    return {
      tipo: "parcial",
      texto: "Distinto nivel, misma decisión: los dos lo ponen "
        + (alertaMia ? "en zona de alerta." : "fuera de zona de alerta."),
    };
  }
  return {
    tipo: "discrepa",
    texto: alertaMia
      ? "Vos lo marcás en alerta y el sistema no. Es el caso más valioso para revisar."
      : "El sistema lo marca en alerta y vos no. Vale la pena mirar por qué.",
  };
});
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-4 flex items-start justify-between gap-4 flex-wrap">
      <div>
        <p class="eyebrow mb-2">Evaluación clínica</p>
        <h1 class="hero-serif text-[26px]">
          {{ caso?.nombre || "Alumno" }}
        </h1>
        <p v-if="caso" class="text-xs text-ink-500 mt-1">
          {{ caso.codigo }}
          <span v-if="caso.codigo_alumno" class="font-mono"> · {{ caso.codigo_alumno }}</span>
          <span v-if="caso.grado"> · {{ caso.grado }}</span>
        </p>
      </div>
      <button class="btn-ghost btn-sm" @click="router.push('/etiquetado')">
        ← Volver a la lista
      </button>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else-if="caso">
      <div v-if="avisoUrgente" class="banner-success mb-4">{{ avisoUrgente }}</div>

      <div class="grid lg:grid-cols-[1fr_340px] gap-4 items-start">
        <!-- Respuestas crudas -->
        <div class="grid gap-3">
          <div v-for="b in bloques" :key="b.nombre" class="card p-4">
            <p class="text-sm font-semibold text-green-900 mb-3">{{ b.nombre }}</p>
            <ol class="grid gap-2">
              <li
                v-for="(it, i) in b.items"
                :key="i"
                class="flex items-start justify-between gap-4 text-sm border-b border-cream-200 last:border-0 pb-2 last:pb-0"
              >
                <span class="text-ink-700">
                  <span class="text-ink-400 mr-1">{{ i + 1 }}.</span>
                  {{ it.pregunta }}
                  <span
                    v-if="it.tipo === 'texto'"
                    class="block font-semibold text-green-900 mt-0.5"
                  >
                    {{ it.respuesta_texto }}
                  </span>
                </span>
                <span
                  v-if="it.tipo !== 'texto'"
                  class="shrink-0 text-xs px-2 py-0.5 rounded border bg-cream-50 border-cream-300 text-ink-700"
                >
                  {{ etiquetaValor(it, it.valor) }}
                </span>
              </li>
            </ol>
          </div>
        </div>

        <!-- Formulario -->
        <div class="card p-5 grid gap-5 lg:sticky lg:top-4">
          <p v-if="yaEvaluado" class="text-xs text-green-700">
            Ya evaluaste este caso. Podés corregir tu juicio y volver a guardar.
          </p>

          <div>
            <p class="text-sm font-semibold text-green-900 mb-2">
              1. Nivel de riesgo clínico
            </p>
            <div class="grid gap-1.5">
              <button
                v-for="r in RIESGOS"
                :key="r.v"
                class="text-xs px-3 py-2 rounded-lg border text-left transition"
                :class="
                  riesgo === r.v
                    ? r.clase + ' font-semibold ring-2 ring-offset-1 ring-green-400'
                    : 'bg-white border-cream-300 text-ink-600 hover:bg-cream-50'
                "
                @click="riesgo = r.v"
              >
                {{ r.label }}
              </button>
            </div>
          </div>

          <div>
            <p class="text-sm font-semibold text-green-900 mb-1">
              2. ¿Requiere atención ahora?
            </p>
            <div class="flex gap-1.5">
              <button
                class="btn-sm flex-1"
                :class="derivacion === true ? 'btn-coral' : 'btn-ghost'"
                @click="derivacion = true"
              >Sí</button>
              <button
                class="btn-sm flex-1"
                :class="derivacion === false ? 'btn-primary' : 'btn-ghost'"
                @click="derivacion = false"
              >No</button>
            </div>
          </div>

          <div>
            <p class="text-xs font-semibold text-green-900 mb-1.5">
              ¿Qué predomina? <span class="font-normal text-ink-400">(opcional)</span>
            </p>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="p in PREDOMINANTES"
                :key="p.v"
                class="btn-sm"
                :class="predominante === p.v ? 'btn-mint' : 'btn-ghost'"
                @click="predominante = predominante === p.v ? null : p.v"
              >{{ p.label }}</button>
            </div>
          </div>

          <div>
            <p class="text-xs font-semibold text-green-900 mb-1.5">
              ¿Hay ideación suicida? <span class="font-normal text-ink-400">(opcional)</span>
            </p>
            <div class="flex gap-1.5">
              <button
                class="btn-sm flex-1"
                :class="ideacion === true ? 'btn-coral' : 'btn-ghost'"
                @click="ideacion = true"
              >Sí</button>
              <button
                class="btn-sm flex-1"
                :class="ideacion === false ? 'btn-primary' : 'btn-ghost'"
                @click="ideacion = false"
              >No</button>
              <button
                class="btn-sm flex-1"
                :class="ideacion === null ? 'btn-mint' : 'btn-ghost'"
                @click="ideacion = null"
              >No evaluable</button>
            </div>
          </div>

          <div>
            <label class="text-xs text-ink-500">Confianza</label>
            <select v-model="confianza" class="input">
              <option value="alta">Alta</option>
              <option value="media">Media</option>
              <option value="baja">Baja</option>
            </select>
          </div>

          <div>
            <label class="text-xs text-ink-500">
              Tu evaluación / observaciones
            </label>
            <textarea
              v-model="comentario"
              class="input"
              rows="4"
              placeholder="Qué pesó en tu decisión. Esto queda guardado con el caso."
            />
          </div>

          <button class="btn-primary" :disabled="!puedeGuardar" @click="guardar">
            {{ guardando ? "Guardando…" : yaEvaluado ? "Actualizar evaluación" : "Guardar evaluación" }}
          </button>
          <p v-if="!analisis" class="text-[11px] text-ink-400 -mt-2">
            Al guardar vas a ver lo que calculó el sistema. No se muestra antes
            para que tu criterio sea independiente.
          </p>

          <button
            class="btn-ghost btn-sm text-red-700"
            @click="urgenteAbierto = !urgenteAbierto"
          >
            Este caso requiere atención ahora
          </button>
          <div v-if="urgenteAbierto" class="banner-warn grid gap-2">
            <p class="text-xs">
              Deja una nota para la psicóloga a cargo. No interrumpe tu trabajo.
            </p>
            <textarea v-model="motivoUrgente" class="input" rows="2" />
            <div class="flex gap-2">
              <button
                class="btn-coral btn-sm"
                :disabled="!motivoUrgente.trim()"
                @click="enviarUrgente"
              >Avisar</button>
              <button class="btn-ghost btn-sm" @click="urgenteAbierto = false">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Análisis del sistema: solo después de guardar ───────────── -->
      <section v-if="analisis" id="analisis" class="mt-6">
        <div v-if="recienGuardado" class="banner-success mb-3 text-sm">
          Evaluación guardada. Esto es lo que había calculado el sistema.
        </div>

        <div
          v-if="coincidencia"
          class="mb-3 text-sm"
          :class="
            coincidencia.tipo === 'exacta'
              ? 'banner-success'
              : coincidencia.tipo === 'parcial'
                ? 'banner-info'
                : 'banner-warn'
          "
        >
          <strong>Tu juicio: {{ riesgo }} · Sistema: {{ analisis.riesgo_global }}.</strong>
          {{ coincidencia.texto }}
        </div>

        <div class="card p-5">
          <div class="flex items-center justify-between flex-wrap gap-3 mb-4">
            <p class="font-semibold text-green-900">Análisis del sistema</p>
            <div class="flex items-center gap-2">
              <span
                class="text-xs px-2 py-0.5 rounded-full border"
                :class="colorRiesgo(analisis.riesgo_global)"
              >
                {{ analisis.riesgo_global }}
              </span>
              <span
                v-if="analisis.crisis_activada"
                class="text-xs px-2 py-0.5 rounded-full border border-red-300 bg-red-50 text-red-800"
              >
                bandera de crisis
              </span>
            </div>
          </div>

          <div class="flex flex-wrap gap-2 mb-4">
            <span
              v-for="b in analisis.bloques"
              :key="b.codigo"
              class="text-xs px-2 py-1 rounded border"
              :class="
                b.bandera_crisis
                  ? 'bg-red-50 border-red-300 text-red-800'
                  : b.severidad_alerta
                    ? 'bg-amber-50 border-amber-300 text-amber-800'
                    : 'bg-green-50 border-green-200 text-green-800'
              "
              :title="b.nombre"
            >
              {{ b.codigo }} {{ b.puntaje }}/{{ b.rango_max }} · {{ b.severidad }}
              <span v-if="b.bandera_crisis"> · ítem crítico</span>
            </span>
          </div>

          <div v-if="analisis.svm" class="banner-info text-xs mb-4">
            <strong>SVM:</strong> {{ analisis.svm.clase }}
            ({{ Math.round((analisis.svm.probabilidad || 0) * 100) }}%,
            confianza {{ analisis.svm.confianza }})
            <span v-if="analisis.svm.discrepancia_con_reglas">
              — discrepa con las reglas
            </span>
          </div>

          <div v-if="analisis.n_frases">
            <p class="text-sm font-semibold text-green-900 mb-2">
              Frases analizadas por BETO
              <span class="font-normal text-xs text-ink-500">
                ({{ analisis.n_frases }}, {{ analisis.n_frases_crisis }} con bandera)
              </span>
            </p>
            <ul class="grid gap-1.5">
              <li
                v-for="(f, i) in analisis.frases"
                :key="i"
                class="text-sm border-b border-cream-200 last:border-0 pb-1.5"
                :class="f.crisis ? 'text-red-800' : 'text-ink-700'"
              >
                <span class="text-ink-500">{{ f.pregunta }}</span>
                <strong> {{ f.respuesta }}</strong>
                <span class="text-xs text-ink-400">
                  — {{ f.dominante }}
                  <span v-if="f.score_depresion !== null">
                    (depresión {{ Math.round(f.score_depresion * 100) }}%)
                  </span>
                  <span v-if="f.crisis" class="text-red-700 font-semibold">
                    · bandera
                  </span>
                </span>
              </li>
            </ul>
          </div>
          <p v-else class="text-xs text-ink-400">
            Este cuestionario no tiene frases analizadas.
          </p>
        </div>

        <div class="mt-4 flex gap-2">
          <button class="btn-mint" @click="router.push('/etiquetado')">
            Volver a la lista y seguir
          </button>
        </div>
      </section>
    </template>
  </div>
</template>
