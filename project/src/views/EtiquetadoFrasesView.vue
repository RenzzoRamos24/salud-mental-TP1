<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { api } from "../api";

// Una frase por pantalla y dos preguntas. Nada más, porque son 100 frases y
// cada campo extra se multiplica por 100.
//
// Son estas dos y no otras porque tienen que hablar el mismo idioma que el
// modelo: BETO emite una categoría dominante (las 4 opciones de abajo) y una
// bandera de crisis. Sin esas dos respuestas no hay nada que comparar; con
// más de esas dos, se paga tiempo que no compra métrica.

const frase = ref(null);
const progreso = ref(null);
const cargando = ref(true);
const guardando = ref(false);
const error = ref("");
const terminado = ref(false);
const esPrueba = ref(false);

const categoria = ref(null);
const ideacion = ref(null);
const confianza = ref("alta");
const comentario = ref("");
const detallesAbiertos = ref(false);

// Cuánto tardó en esta frase. Detecta etiquetado apresurado y, al revés,
// documenta que el trabajo fue serio.
let t0 = Date.now();

const urgenteAbierto = ref(false);
const motivoUrgente = ref("");
const avisoUrgente = ref("");

const CATEGORIAS = [
  {
    v: "depresion",
    label: "Depresión",
    tecla: "1",
    pista: "Tristeza profunda, desesperanza, vacío, inutilidad",
    clase: "bg-indigo-50 border-indigo-300 text-indigo-800",
  },
  {
    v: "ansiedad",
    label: "Ansiedad",
    tecla: "2",
    pista: "Preocupación, nerviosismo, tensión, miedo",
    clase: "bg-amber-50 border-amber-300 text-amber-800",
  },
  {
    v: "adaptativo",
    label: "Afrontamiento sano",
    tecla: "3",
    pista: "Metas, resiliencia, esfuerzo, autoconocimiento",
    clase: "bg-green-50 border-green-300 text-green-800",
  },
  {
    v: "neutral",
    label: "Nada preocupante",
    tecla: "4",
    pista: "Cotidiano, hobbies, cansancio normal",
    clase: "bg-gray-50 border-gray-300 text-gray-700",
  },
];

const puedeGuardar = computed(
  () => !!categoria.value && ideacion.value !== null && !guardando.value,
);

function limpiar() {
  categoria.value = null;
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
  try {
    try {
      esPrueba.value = !!(await api.etiquetadoProgreso()).es_cuenta_prueba;
    } catch {
      /* si falla, se sigue sin el aviso */
    }
    const f = await api.etiquetadoSiguienteFrase();
    if (f === null) {
      terminado.value = true;
      frase.value = null;
    } else {
      frase.value = f;
      progreso.value = f.progreso;
    }
    limpiar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar la frase.";
  } finally {
    cargando.value = false;
  }
}

async function guardar() {
  if (!puedeGuardar.value) return;
  guardando.value = true;
  error.value = "";
  try {
    await api.etiquetadoGuardarFrase({
      ref: frase.value.ref,
      ideacion_presente: ideacion.value,
      categoria: categoria.value,
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
      Number(frase.value.ref.split(":")[0]),
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

// ── Teclado ──────────────────────────────────────────────────────────
// 1-4 categoría, S/N ideación, Enter guarda. Con mouse son ~45 s por frase;
// con teclado, ~15.
function onKey(e) {
  if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
  const k = e.key.toLowerCase();
  if (["1", "2", "3", "4"].includes(k)) {
    categoria.value = CATEGORIAS.find((c) => c.tecla === k).v;
  } else if (k === "s") ideacion.value = true;
  else if (k === "n") ideacion.value = false;
  else if (k === "enter") guardar();
  else return;
  e.preventDefault();
}

onMounted(() => {
  cargar();
  window.addEventListener("keydown", onKey);
});
onUnmounted(() => window.removeEventListener("keydown", onKey));

const pct = computed(() => {
  if (!progreso.value?.total) return 0;
  return Math.round((progreso.value.hechas / progreso.value.total) * 100);
});
</script>

<template>
  <div class="page-shell">
    <header class="mb-5">
      <p class="eyebrow mb-2">Etiquetado ciego</p>
      <h1 class="hero-serif text-[26px]">
        Frases <span class="hero-mint">incompletas</span>
      </h1>
    </header>

      <div v-if="esPrueba" class="banner-warn mb-4 text-sm">
        <strong>Cuenta de prueba.</strong> Podés recorrer todo el flujo y tus
        etiquetas se guardan, pero quedan fuera de las métricas — no son
        juicio clínico. Para la validación real hay que usar un código
        <code>SAMI-PSI-NN</code>.
      </div>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>

    <div v-else-if="terminado" class="card p-8 text-center">
      <p class="text-lg font-semibold text-green-900 mb-2">
        No queda ninguna frase por etiquetar.
      </p>
      <p class="text-sm text-ink-500">
        Gracias. Los resultados están en
        <router-link to="/etiquetado/metricas" class="underline">
          Resultados del etiquetado</router-link>.
      </p>
    </div>

    <template v-else-if="frase">
      <div class="mb-4">
        <div class="flex items-center justify-between text-xs text-ink-500 mb-1">
          <span>{{ progreso.fase }}</span>
          <span>{{ progreso.hechas }} de {{ progreso.total }}</span>
        </div>
        <div class="h-1.5 bg-cream-200 rounded-full overflow-hidden">
          <div class="h-full bg-green-600 transition-all" :style="{ width: pct + '%' }" />
        </div>
        <p v-if="frase.fase === 'corpus'" class="text-[11px] text-ink-400 mt-1">
          Esta frase ya no cuenta para las métricas — suma al conjunto de
          reentrenamiento.
        </p>
      </div>

      <div v-if="error" class="banner-danger mb-4">{{ error }}</div>
      <div v-if="avisoUrgente" class="banner-success mb-4">{{ avisoUrgente }}</div>

      <!-- La frase -->
      <div class="card p-6 mb-4">
        <p class="label-kicker mb-3">{{ frase.codigo }}</p>
        <p class="text-[19px] leading-relaxed text-ink-700">
          <span class="text-ink-500">{{ frase.estimulo }}</span>
          <span class="font-semibold text-green-900"> {{ frase.respuesta }}</span>
        </p>
      </div>

      <!-- Pregunta 1 -->
      <div class="card p-5 mb-3">
        <p class="text-sm font-semibold text-green-900 mb-3">
          1. ¿Qué expresa esta frase?
        </p>
        <div class="grid sm:grid-cols-2 gap-2">
          <button
            v-for="c in CATEGORIAS"
            :key="c.v"
            class="text-left px-3 py-2.5 rounded-lg border transition"
            :class="
              categoria === c.v
                ? c.clase + ' font-semibold ring-2 ring-offset-1 ring-green-400'
                : 'bg-white border-cream-300 hover:bg-cream-50'
            "
            @click="categoria = c.v"
          >
            <span class="text-sm">
              {{ c.label }}
              <span class="opacity-40 text-[10px] font-normal">({{ c.tecla }})</span>
            </span>
            <span class="block text-[11px] text-ink-500 mt-0.5">{{ c.pista }}</span>
          </button>
        </div>
      </div>

      <!-- Pregunta 2 -->
      <div class="card p-5 mb-3">
        <p class="text-sm font-semibold text-green-900 mb-1">
          2. ¿Expresa ideación suicida?
        </p>
        <p class="text-xs text-ink-500 mb-3">
          Deseo de morir, de no existir o de desaparecer; pensamientos sobre la
          propia muerte; intención, plan o método con fin suicida.
          <strong>Tristeza severa sin referencia a morir es No.</strong>
        </p>
        <div class="flex gap-2">
          <button
            class="btn-sm flex-1"
            :class="ideacion === true ? 'btn-coral' : 'btn-ghost'"
            @click="ideacion = true"
          >
            Sí <span class="opacity-50 text-[10px]">(S)</span>
          </button>
          <button
            class="btn-sm flex-1"
            :class="ideacion === false ? 'btn-primary' : 'btn-ghost'"
            @click="ideacion = false"
          >
            No <span class="opacity-50 text-[10px]">(N)</span>
          </button>
        </div>
      </div>

      <!-- Guardar -->
      <div class="flex items-center justify-between gap-3 mb-3">
        <button
          class="btn-ghost btn-sm"
          @click="detallesAbiertos = !detallesAbiertos"
        >
          {{ detallesAbiertos ? "Ocultar" : "Agregar" }} confianza o comentario
        </button>
        <button class="btn-primary" :disabled="!puedeGuardar" @click="guardar">
          {{ guardando ? "Guardando…" : "Guardar y siguiente" }}
          <span class="opacity-50 text-[10px]">(Enter)</span>
        </button>
      </div>

      <!-- Opcional -->
      <div v-if="detallesAbiertos" class="card p-5 grid md:grid-cols-2 gap-4 mb-3">
        <div>
          <label class="text-xs text-ink-500">Confianza en tu juicio</label>
          <select v-model="confianza" class="input">
            <option value="alta">Alta</option>
            <option value="media">Media</option>
            <option value="baja">Baja</option>
          </select>
          <p class="text-[11px] text-ink-400 mt-1">
            Si dudás, marcá tu mejor juicio con confianza baja. Preferimos eso a
            una frase sin etiquetar.
          </p>
        </div>
        <div>
          <label class="text-xs text-ink-500">Comentario</label>
          <textarea
            v-model="comentario"
            class="input"
            rows="2"
            placeholder="Por qué, si el caso es dudoso…"
          />
        </div>
      </div>

      <div class="text-center">
        <button
          class="btn-ghost btn-sm text-red-700"
          @click="urgenteAbierto = !urgenteAbierto"
        >
          Esta frase requiere atención ahora
        </button>
      </div>

      <div v-if="urgenteAbierto" class="banner-warn grid gap-2 mt-3">
        <p class="text-sm">
          Esto deja una nota en el expediente del alumno para la psicóloga a
          cargo. No interrumpe el etiquetado y no te muestra nada del modelo.
        </p>
        <textarea
          v-model="motivoUrgente"
          class="input"
          rows="2"
          placeholder="Qué viste que requiere atención ahora."
        />
        <div class="flex gap-2">
          <button
            class="btn-coral btn-sm"
            :disabled="!motivoUrgente.trim()"
            @click="enviarUrgente"
          >
            Avisar
          </button>
          <button class="btn-ghost btn-sm" @click="urgenteAbierto = false">
            Cancelar
          </button>
        </div>
      </div>

      <p class="text-[11px] text-ink-400 mt-5 text-center">
        No vas a ver lo que predijo el sistema, y es deliberado: si etiquetaras
        viendo su respuesta, la comparación posterior no valdría como validación
        independiente.
      </p>
    </template>
  </div>
</template>
