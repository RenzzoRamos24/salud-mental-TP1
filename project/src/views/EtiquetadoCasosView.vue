<script setup>
import { ref, onMounted, computed } from "vue";
import { api } from "../api";
import { etiquetaValor } from "../escalas";

// Un cuestionario por pantalla, con las respuestas crudas y sin una sola
// suma. Las etiquetas verbales salen del mismo módulo que usa la pantalla del
// alumno, así el psicólogo lee exactamente lo que leyó el chico.

const caso = ref(null);
const cargando = ref(true);
const guardando = ref(false);
const error = ref("");
const terminado = ref(false);
// Arranca APAGADO. El SVM solo opina si la plantilla trae DASS-21 y el
// .joblib está en el servidor; en producción no se cumple ninguna de las dos,
// así que con el filtro encendido la cola saldría vacía y parecería un bug.
const soloConSvm = ref(false);
const svmInstalado = ref(null);

const riesgo = ref(null);
const derivacion = ref(null); // true | false — obligatorio
const predominante = ref(null);
const ideacion = ref(null); // true | false | null (no evaluable)
const confianza = ref("alta");
const comentario = ref("");
const detallesAbiertos = ref(false);

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

// Subescalas del DASS-21. El SVM de hoy es binario y no distingue entre
// ellas, así que esto no se compara contra él: valida el desglose por
// subescala que el panel ya muestra, y queda como objetivo de entrenamiento
// si el SVM pasa a tener tres salidas.
const PREDOMINANTES = [
  { v: "depresion", label: "Depresión" },
  { v: "ansiedad", label: "Ansiedad" },
  { v: "estres", label: "Estrés" },
  { v: "ninguno", label: "Ninguno" },
];

const puedeGuardar = computed(
  () => !!riesgo.value && derivacion.value !== null && !guardando.value,
);

// Agrupo por bloque para que no sea una lista plana de 21 ítems.
const bloques = computed(() => {
  if (!caso.value) return [];
  const map = new Map();
  for (const it of caso.value.items) {
    if (!map.has(it.bloque)) map.set(it.bloque, []);
    map.get(it.bloque).push(it);
  }
  return [...map.entries()].map(([nombre, items]) => ({ nombre, items }));
});

function limpiar() {
  riesgo.value = null;
  derivacion.value = null;
  predominante.value = null;
  ideacion.value = null;
  confianza.value = "alta";
  comentario.value = "";
  detallesAbiertos.value = false;
  urgenteAbierto.value = false;
  motivoUrgente.value = "";
  t0 = Date.now();
}

async function cargar() {
  cargando.value = true;
  error.value = "";
  terminado.value = false;
  try {
    if (svmInstalado.value === null) {
      try {
        svmInstalado.value = (await api.etiquetadoProgreso()).svm_instalado;
      } catch {
        svmInstalado.value = false;
      }
    }
    const c = await api.etiquetadoSiguienteCaso({ soloConSvm: soloConSvm.value });
    if (c === null) {
      terminado.value = true;
      caso.value = null;
    } else {
      caso.value = c;
    }
    limpiar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar el caso.";
  } finally {
    cargando.value = false;
  }
}

async function guardar() {
  if (!puedeGuardar.value) return;
  guardando.value = true;
  error.value = "";
  try {
    await api.etiquetadoGuardarCaso({
      aplicacion_id: caso.value.aplicacion_id,
      riesgo_clinico: riesgo.value,
      requiere_derivacion: derivacion.value,
      predominante: predominante.value,
      ideacion_presente: ideacion.value,
      confianza: confianza.value,
      comentario: comentario.value.trim() || null,
      segundos: Math.round((Date.now() - t0) / 1000),
    });
    avisoUrgente.value = "";
    await cargar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo guardar.";
  } finally {
    guardando.value = false;
  }
}

async function enviarUrgente() {
  if (!motivoUrgente.value.trim()) return;
  try {
    await api.etiquetadoMarcarUrgente(
      caso.value.aplicacion_id,
      motivoUrgente.value.trim(),
    );
    avisoUrgente.value =
      "Avisado. Queda una nota en el expediente del alumno para la psicóloga a cargo.";
    urgenteAbierto.value = false;
    motivoUrgente.value = "";
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo avisar.";
  }
}

onMounted(cargar);

const pct = computed(() => {
  const p = caso.value?.progreso;
  if (!p?.total) return 0;
  return Math.round((p.hechas / p.total) * 100);
});
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-5">
      <p class="eyebrow mb-2">Etiquetado ciego</p>
      <h1 class="hero-serif text-[26px]">
        Casos <span class="hero-mint">completos</span>
      </h1>
      <p class="text-sm text-ink-500 mt-2">
        Las respuestas tal como las marcó el alumno. Sin puntajes, sin
        severidades, sin lo que calculó el sistema.
      </p>
      <p v-if="svmInstalado === false" class="text-xs text-ink-400 mt-1">
        En esta instalación tu juicio valida los cortes de PHQ-A y GAD-7, la
        bandera de crisis y el riesgo compuesto. El SVM no corre acá.
      </p>
    </header>

    <div class="card p-3 mb-4 flex items-center justify-between flex-wrap gap-2">
      <label class="flex items-center gap-2 text-xs text-ink-600">
        <input
          v-model="soloConSvm"
          type="checkbox"
          :disabled="svmInstalado === false"
          @change="cargar"
        />
        Solo casos con DASS-21
        <span v-if="svmInstalado === false" class="text-ink-400">
          — el SVM no está instalado en este servidor, así que no hay ninguno
        </span>
        <span v-else class="text-ink-400">(los únicos donde el SVM opina)</span>
      </label>
      <p v-if="caso" class="text-xs text-ink-500">
        {{ caso.progreso.hechas }} de {{ caso.progreso.total }}
      </p>
    </div>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>

    <div v-else-if="terminado" class="card p-8 text-center">
      <p class="text-lg font-semibold text-green-900 mb-2">
        No queda ningún caso por etiquetar
        <span v-if="soloConSvm">en este subconjunto</span>.
      </p>
      <p v-if="soloConSvm" class="text-sm text-ink-500">
        Destildá el filtro de arriba para seguir con el resto.
      </p>
      <p v-else class="text-sm text-ink-500">
        Los resultados están en
        <router-link to="/etiquetado/metricas" class="underline">
          Resultados del etiquetado</router-link>.
      </p>
    </div>

    <template v-else-if="caso">
      <div class="h-1.5 bg-cream-200 rounded-full overflow-hidden mb-4">
        <div class="h-full bg-green-600 transition-all" :style="{ width: pct + '%' }" />
      </div>

      <div v-if="error" class="banner-danger mb-4">{{ error }}</div>
      <div v-if="avisoUrgente" class="banner-success mb-4">{{ avisoUrgente }}</div>

      <div class="grid lg:grid-cols-[1fr_340px] gap-4 items-start">
        <!-- Respuestas crudas -->
        <div class="grid gap-3">
          <div class="card p-4">
            <p class="label-kicker">{{ caso.codigo }}</p>
            <p class="text-xs text-ink-500 mt-1">
              <span v-if="caso.grado">{{ caso.grado }} — </span>
              {{ caso.items.length }} respuestas
            </p>
          </div>

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

        <!-- Formulario, pegado arriba -->
        <div class="card p-5 grid gap-5 lg:sticky lg:top-4">
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
            <p class="text-xs text-ink-500 mb-2">
              La decisión clínica concreta. Es contra esta respuesta que se mide
              si el sistema sirve para priorizar.
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

          <button class="btn-primary" :disabled="!puedeGuardar" @click="guardar">
            {{ guardando ? "Guardando…" : "Guardar y siguiente" }}
          </button>

          <button
            class="btn-ghost btn-sm"
            @click="detallesAbiertos = !detallesAbiertos"
          >
            {{ detallesAbiertos ? "Ocultar" : "Agregar" }} detalle opcional
          </button>

          <div v-if="detallesAbiertos" class="grid gap-4 pt-1 border-t border-cream-200">
            <div>
              <p class="text-xs font-semibold text-green-900 mb-1.5">
                ¿Qué predomina?
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
              <p class="text-[11px] text-ink-400 mt-1">
                No se compara con el SVM (que es binario). Sirve para validar el
                desglose por subescala.
              </p>
            </div>

            <div>
              <p class="text-xs font-semibold text-green-900 mb-1.5">
                ¿Hay ideación suicida en el caso?
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
                  title="El material no alcanza para opinar"
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
              <label class="text-xs text-ink-500">Comentario</label>
              <textarea
                v-model="comentario"
                class="input"
                rows="3"
                placeholder="Qué pesó en tu decisión. En los casos dudosos es lo que después explica el número."
              />
            </div>
          </div>

          <button
            class="btn-ghost btn-sm text-red-700"
            @click="urgenteAbierto = !urgenteAbierto"
          >
            Este caso requiere atención ahora
          </button>

          <div v-if="urgenteAbierto" class="banner-warn grid gap-2">
            <p class="text-xs">
              Deja una nota para la psicóloga a cargo. No interrumpe el
              etiquetado.
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
    </template>
  </div>
</template>
