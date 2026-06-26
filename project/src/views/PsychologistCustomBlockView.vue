<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

const route = useRoute();
const router = useRouter();
const guardando = ref(false);
const error = ref("");
const editandoId = computed(() => {
  const id = route.query.id;
  return id ? Number(id) : null;
});

const form = ref({
  nombre: "",
  dominio: "",
  tipo_escala: "likert",
  likert_min: 0,
  likert_max: 3,
  instruccion: "",
  items: [{ numero: 1, texto: "", inverso: 0 }],
  corte_sin_alerta_max: 0,
  corte_posible_max: 0,
  corte_alto_max: 0,
});

onMounted(async () => {
  if (!editandoId.value) return;
  try {
    const b = await api.obtenerBloqueCustom(editandoId.value);
    form.value = {
      nombre: b.nombre,
      dominio: b.dominio || "",
      tipo_escala: b.tipo_escala,
      likert_min: b.likert_min,
      likert_max: b.likert_max,
      instruccion: b.instruccion || "",
      items: b.items.map((it) => ({
        numero: it.numero,
        texto: it.texto,
        inverso: it.inverso || 0,
      })),
      corte_sin_alerta_max: b.corte_sin_alerta_max,
      corte_posible_max: b.corte_posible_max,
      corte_alto_max: b.corte_alto_max,
    };
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar el bloque.";
  }
});

const rangoMax = computed(() => {
  const n = form.value.items.length;
  if (form.value.tipo_escala === "binaria") return n;
  return n * (Number(form.value.likert_max) || 0);
});

watch(rangoMax, async (max) => {
  if (max < 3) return;
  try {
    const s = await api.sugerirCortes(max);
    if (form.value.corte_sin_alerta_max === 0 && form.value.corte_posible_max === 0) {
      form.value.corte_sin_alerta_max = s.corte_sin_alerta_max;
      form.value.corte_posible_max = s.corte_posible_max;
      form.value.corte_alto_max = s.corte_alto_max;
    } else if (form.value.corte_alto_max !== max) {
      form.value.corte_alto_max = max;
    }
  } catch (_) {}
});

function agregarItem() {
  form.value.items.push({
    numero: form.value.items.length + 1,
    texto: "",
    inverso: 0,
  });
}

function quitarItem(i) {
  if (form.value.items.length <= 1) return;
  form.value.items.splice(i, 1);
  form.value.items.forEach((it, idx) => (it.numero = idx + 1));
}

async function usarTercios() {
  try {
    const s = await api.sugerirCortes(rangoMax.value);
    form.value.corte_sin_alerta_max = s.corte_sin_alerta_max;
    form.value.corte_posible_max = s.corte_posible_max;
    form.value.corte_alto_max = s.corte_alto_max;
  } catch (_) {}
}

async function guardar() {
  error.value = "";
  if (!form.value.nombre.trim()) {
    error.value = "Ponle un nombre al bloque.";
    return;
  }
  if (form.value.items.some((it) => !it.texto.trim())) {
    error.value = "Todas las preguntas deben tener texto.";
    return;
  }
  guardando.value = true;
  const payload = {
    nombre: form.value.nombre.trim(),
    dominio: form.value.dominio.trim() || null,
    tipo_escala: form.value.tipo_escala,
    likert_min: Number(form.value.likert_min),
    likert_max: Number(form.value.likert_max),
    instruccion: form.value.instruccion.trim() || null,
    items: form.value.items.map((it) => ({
      numero: it.numero,
      texto: it.texto.trim(),
      inverso: Number(it.inverso || 0),
    })),
    corte_sin_alerta_max: Number(form.value.corte_sin_alerta_max),
    corte_posible_max: Number(form.value.corte_posible_max),
    corte_alto_max: Number(form.value.corte_alto_max),
  };
  try {
    if (editandoId.value) {
      await api.actualizarBloqueCustom(editandoId.value, payload);
    } else {
      await api.crearBloqueCustom(payload);
    }
    router.push("/psicologo/banco");
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo guardar el bloque.";
  } finally {
    guardando.value = false;
  }
}
</script>

<template>
  <div class="page-shell">
    <header class="mb-6">
      <p class="eyebrow mb-2">Banco personalizado</p>
      <h1 class="hero-serif text-[28px]">
        {{ editandoId ? "Editar" : "Nuevo" }}
        <span class="hero-mint">bloque</span>
      </h1>
      <p class="text-ink-500 mt-2">
        Define un bloque con tus propias preguntas, escala y cortes. Quedará
        disponible para incluir en plantillas.
      </p>
    </header>

    <div v-if="error" class="banner-danger mb-4">{{ error }}</div>

    <div class="card p-6 mb-4">
      <h2 class="text-lg font-semibold mb-4">Identificación</h2>
      <div class="grid gap-4">
        <div>
          <label class="label">Nombre del bloque</label>
          <input v-model="form.nombre" class="input" placeholder="Ej. Ansiedad de exámenes" />
        </div>
        <div>
          <label class="label">Dominio (opcional)</label>
          <input v-model="form.dominio" class="input" placeholder="Ej. ansiedad académica" />
        </div>
        <div>
          <label class="label">Instrucción para el alumno (opcional)</label>
          <textarea
            v-model="form.instruccion"
            rows="2"
            class="input-lg"
            placeholder="Ej. Pensando en las últimas dos semanas…"
          ></textarea>
        </div>
      </div>
    </div>

    <div class="card p-6 mb-4">
      <h2 class="text-lg font-semibold mb-4">Escala</h2>
      <div class="grid sm:grid-cols-3 gap-4">
        <div>
          <label class="label">Tipo</label>
          <select v-model="form.tipo_escala" class="input">
            <option value="likert">Likert (0 a N)</option>
            <option value="binaria">Sí / No</option>
          </select>
        </div>
        <div v-if="form.tipo_escala === 'likert'">
          <label class="label">Mínimo</label>
          <input v-model.number="form.likert_min" type="number" min="0" class="input" />
        </div>
        <div v-if="form.tipo_escala === 'likert'">
          <label class="label">Máximo</label>
          <input v-model.number="form.likert_max" type="number" min="1" class="input" />
        </div>
      </div>
    </div>

    <div class="card p-6 mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">Preguntas</h2>
        <button class="btn-ghost btn-sm" @click="agregarItem">+ Agregar pregunta</button>
      </div>
      <div class="grid gap-3">
        <div
          v-for="(it, i) in form.items"
          :key="i"
          class="flex items-start gap-2"
        >
          <span class="pt-3 text-sm text-ink-400 tabular">{{ it.numero }}.</span>
          <textarea
            v-model="it.texto"
            rows="2"
            class="input-lg flex-1"
            placeholder="Ej. Antes de un examen me cuesta dormir"
          ></textarea>
          <label class="text-xs text-ink-500 pt-3 flex items-center gap-1">
            <input
              type="checkbox"
              :checked="it.inverso === 1"
              @change="it.inverso = $event.target.checked ? 1 : 0"
            />
            inverso
          </label>
          <button class="btn-ghost btn-sm pt-3" @click="quitarItem(i)">×</button>
        </div>
      </div>
    </div>

    <div class="card p-6 mb-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">Cortes (rango 0 – {{ rangoMax }})</h2>
        <button class="btn-ghost btn-sm" @click="usarTercios">Usar tercios</button>
      </div>
      <div class="grid sm:grid-cols-3 gap-4">
        <div>
          <label class="label">Sin alerta máx.</label>
          <input
            v-model.number="form.corte_sin_alerta_max"
            type="number"
            min="0"
            :max="rangoMax"
            class="input"
          />
        </div>
        <div>
          <label class="label">Posible problema máx.</label>
          <input
            v-model.number="form.corte_posible_max"
            type="number"
            min="0"
            :max="rangoMax"
            class="input"
          />
        </div>
        <div>
          <label class="label">Alto máx.</label>
          <input
            v-model.number="form.corte_alto_max"
            type="number"
            min="0"
            :max="rangoMax"
            class="input"
          />
        </div>
      </div>
      <p class="text-xs text-ink-500 mt-3">
        Sugerencia: los tres tercios. Podés ajustar libremente; deben ser
        crecientes y el último debe igualar el rango máximo.
      </p>
    </div>

    <div class="flex justify-between">
      <button class="btn-ghost" @click="router.push('/psicologo/banco')">Cancelar</button>
      <button class="btn-mint" :disabled="guardando" @click="guardar">
        {{ guardando ? "Guardando…" : "Guardar bloque" }}
      </button>
    </div>
  </div>
</template>
