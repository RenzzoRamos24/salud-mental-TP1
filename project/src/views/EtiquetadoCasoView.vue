<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import { etiquetaValor } from "../escalas";

// Un alumno: sus respuestas crudas y el formulario de evaluación. Nada más.
//
// En ningún momento se muestra lo que calculó el sistema — ni antes del
// juicio ni después de guardarlo. Un primer diseño lo revelaba al guardar,
// para poder comparar en el momento; el problema es que acá se evalúan 104
// casos seguidos y lo que se ve en el caso 1 queda puesto para el 2. Esa
// contaminación no aparece en ningún número, así que no se podría ni
// detectar. El backend tampoco lo manda: la comparación se mira al final, en
// la pantalla de resultados.

const route = useRoute();
const router = useRouter();
const aplicacionId = computed(() => Number(route.params.id));

const caso = ref(null);
const cargando = ref(true);
const guardando = ref(false);
const error = ref("");
const recienGuardado = ref(false);

const riesgo = ref(null);
const derivacion = ref(null);
const predominante = ref(null);
const ideacion = ref(null);
// El selector se sacó de la pantalla; se sigue mandando "alta" para no
// cambiar el contrato del endpoint ni el esquema de la tabla.
const confianza = ref("alta");
const comentario = ref("");

let t0 = Date.now();

const RIESGOS = [
  { v: "SIN_RIESGO", label: "Sin riesgo", clase: "bg-gray-50 border-gray-300 text-gray-700" },
  { v: "BAJO", label: "Bajo", clase: "bg-sky-50 border-sky-300 text-sky-800" },
  { v: "MEDIO", label: "Medio", clase: "bg-amber-50 border-amber-300 text-amber-800" },
  { v: "ALTO", label: "Alto", clase: "bg-orange-50 border-orange-300 text-orange-800" },
  { v: "CRITICO", label: "Crítico", clase: "bg-red-50 border-red-300 text-red-800" },
];
// Sin "Estrés" a propósito: en esta aplicación corren PHQ-A (depresión) y
// GAD-7 (ansiedad), y nada mide estrés. Ofrecer una opción que ningún
// instrumento respalda produce una etiqueta que después no se puede comparar
// contra nada. (La subescala de estrés es del DASS-21, que no se aplica acá.)
const PREDOMINANTES = [
  { v: "depresion", label: "Depresión" },
  { v: "ansiedad", label: "Ansiedad" },
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
    await api.etiquetadoGuardarCaso({
      aplicacion_id: aplicacionId.value,
      riesgo_clinico: riesgo.value,
      requiere_derivacion: derivacion.value,
      predominante: predominante.value,
      ideacion_presente: ideacion.value,
      confianza: confianza.value,
      comentario: comentario.value.trim() || null,
      segundos: Math.round((Date.now() - t0) / 1000),
    });
    recienGuardado.value = true;
    if (caso.value) {
      caso.value.mi_etiqueta = { riesgo_clinico: riesgo.value };
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo guardar.";
  } finally {
    guardando.value = false;
  }
}

// Busca el próximo alumno sin evaluar y salta directo, para no obligar a
// pasar por la lista en cada caso.
async function siguienteAlumno() {
  try {
    const d = await api.etiquetadoEstudiantes();
    const p = (d.estudiantes || []).find((e) => !e.mi_etiqueta);
    if (p) {
      router.push({ name: "etiquetado-caso", params: { id: p.aplicacion_id } });
      return;
    }
  } catch {
    /* si falla, la lista siempre está */
  }
  router.push("/etiquetado");
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

    <!-- Al guardar: agradecimiento y seguir. Nada del sistema. -->
    <div v-else-if="recienGuardado" class="card p-10 text-center">
      <p class="hero-serif text-[26px] text-green-900 mb-2">
        Gracias por sus <span class="hero-mint">respuestas</span>
      </p>
      <p class="text-sm text-ink-500 mb-6">
        Su evaluación quedó guardada.
      </p>
      <div class="flex flex-wrap gap-2 justify-center">
        <button class="btn-primary" @click="siguienteAlumno">
          Evaluar al siguiente alumno
        </button>
        <button class="btn-ghost" @click="router.push('/etiquetado')">
          Volver a la lista
        </button>
      </div>
    </div>

    <template v-else-if="caso">
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
          <p class="text-[11px] text-ink-400 -mt-2">
            Tu evaluación queda guardada con el caso. No vas a ver lo que
            calculó el sistema: tu criterio tiene que ser independiente del
            suyo, también en los casos que siguen.
          </p>

        </div>
      </div>

    </template>
  </div>
</template>
