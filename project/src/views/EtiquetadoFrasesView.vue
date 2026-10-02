<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue";
import { api } from "../api";

// Una frase por pantalla, sin nada de lo que dijo el modelo. La ceguedad la
// garantiza el backend (el payload no trae scores); acá no hay nada que
// ocultar, y es a propósito.

const frase = ref(null);
const progreso = ref(null);
const cargando = ref(true);
const guardando = ref(false);
const error = ref("");
const terminado = ref(false);

// El formulario
const ideacion = ref(null); // true | false
const sufrimiento = ref(false);
const categoria = ref(null);
const confianza = ref("alta");
const comentario = ref("");

// Cuánto tardó en esta frase — detecta etiquetado apresurado y, al revés,
// documenta que el trabajo fue serio.
let t0 = Date.now();

const urgenteAbierto = ref(false);
const motivoUrgente = ref("");
const avisoUrgente = ref("");

const CATEGORIAS = [
  { v: "depresion", label: "Depresión", tecla: "1" },
  { v: "ansiedad", label: "Ansiedad", tecla: "2" },
  { v: "adaptativo", label: "Adaptativo", tecla: "3" },
  { v: "neutral", label: "Neutral", tecla: "4" },
];

const puedeGuardar = computed(() => ideacion.value !== null && !guardando.value);

function limpiar() {
  ideacion.value = null;
  sufrimiento.value = false;
  categoria.value = null;
  confianza.value = "alta";
  comentario.value = "";
  urgenteAbierto.value = false;
  motivoUrgente.value = "";
  t0 = Date.now();
}

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
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
      sufrimiento_grave: sufrimiento.value,
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

// ── Atajos de teclado ────────────────────────────────────────────────
// Etiquetar 100 frases con el mouse es tortura; con el teclado son ~20 s
// por frase. S/N marcan ideación, 1-4 la categoría, Enter guarda.
function onKey(e) {
  if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
  const k = e.key.toLowerCase();
  if (k === "s") ideacion.value = true;
  else if (k === "n") ideacion.value = false;
  else if (k === "g") sufrimiento.value = !sufrimiento.value;
  else if (["1", "2", "3", "4"].includes(k)) {
    categoria.value = CATEGORIAS.find((c) => c.tecla === k).v;
  } else if (k === "enter") guardar();
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
      <!-- Progreso -->
      <div class="mb-4">
        <div class="flex items-center justify-between text-xs text-ink-500 mb-1">
          <span>{{ progreso.fase }}</span>
          <span>{{ progreso.hechas }} de {{ progreso.total }}</span>
        </div>
        <div class="h-1.5 bg-cream-200 rounded-full overflow-hidden">
          <div
            class="h-full bg-green-600 transition-all"
            :style="{ width: pct + '%' }"
          />
        </div>
        <p
          v-if="frase.fase === 'corpus'"
          class="text-[11px] text-ink-400 mt-1"
        >
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

      <!-- Formulario -->
      <div class="card p-6 grid gap-5">
        <div>
          <p class="text-sm font-semibold text-green-900 mb-1">
            ¿Expresa ideación suicida?
          </p>
          <p class="text-xs text-ink-500 mb-2">
            Deseo de morir, de no existir o de desaparecer; pensamientos sobre
            la propia muerte; intención, plan o método con fin suicida.
            Tristeza severa sin referencia a morir es <strong>No</strong>.
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

        <div>
          <label class="flex items-start gap-2 cursor-pointer">
            <input v-model="sufrimiento" type="checkbox" class="mt-1" />
            <span>
              <span class="text-sm font-semibold text-green-900">
                Sufrimiento clínico grave
                <span class="opacity-50 text-[10px] font-normal">(G)</span>
              </span>
              <span class="block text-xs text-ink-500">
                Desesperanza total sobre el futuro, o sentimientos profundos e
                incapacitantes de inutilidad, fracaso o vacío — aunque no haya
                referencia a morir.
              </span>
            </span>
          </label>
        </div>

        <div>
          <p class="text-sm font-semibold text-green-900 mb-2">
            Categoría dominante
            <span class="text-xs font-normal text-ink-400">(opcional)</span>
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="c in CATEGORIAS"
              :key="c.v"
              class="btn-sm"
              :class="categoria === c.v ? 'btn-mint' : 'btn-ghost'"
              @click="categoria = categoria === c.v ? null : c.v"
            >
              {{ c.label }}
              <span class="opacity-50 text-[10px]">({{ c.tecla }})</span>
            </button>
          </div>
        </div>

        <div class="grid md:grid-cols-2 gap-4">
          <div>
            <label class="text-xs text-ink-500">Confianza en tu juicio</label>
            <select v-model="confianza" class="input">
              <option value="alta">Alta</option>
              <option value="media">Media</option>
              <option value="baja">Baja</option>
            </select>
            <p class="text-[11px] text-ink-400 mt-1">
              Si dudás, marcá tu mejor juicio con confianza baja. Preferimos eso
              a una frase sin etiquetar.
            </p>
          </div>
          <div>
            <label class="text-xs text-ink-500">Comentario (opcional)</label>
            <textarea
              v-model="comentario"
              class="input"
              rows="2"
              placeholder="Por qué, si el caso es dudoso…"
            />
          </div>
        </div>

        <div class="flex items-center justify-between gap-3 pt-1">
          <button
            class="btn-ghost btn-sm text-red-700"
            @click="urgenteAbierto = !urgenteAbierto"
          >
            Esta frase es urgente
          </button>
          <button
            class="btn-primary"
            :disabled="!puedeGuardar"
            @click="guardar"
          >
            {{ guardando ? "Guardando…" : "Guardar y siguiente" }}
            <span class="opacity-50 text-[10px]">(Enter)</span>
          </button>
        </div>

        <div v-if="urgenteAbierto" class="banner-warn grid gap-2">
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
      </div>

      <p class="text-[11px] text-ink-400 mt-4 text-center">
        No vas a ver lo que predijo el sistema, y es deliberado: si etiquetaras
        viendo su respuesta, la comparación posterior no valdría como
        validación independiente.
      </p>
    </template>
  </div>
</template>
