<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();
const plantillas = ref([]);
const instrumentos = ref([]);
const bloquesCustom = ref([]);
const areasFrases = ref([]);
const cargando = ref(true);
const error = ref("");
const modoCrear = ref(false);
const editandoId = ref(null);

const nuevo = ref({
  nombre: "",
  descripcion: "",
  instrumentos_ids: [],
  bloques_custom_ids: [],
  frases_areas: [],
});

async function cargar() {
  cargando.value = true;
  try {
    const [ps, ins, bc, af] = await Promise.all([
      api.listarPlantillas(),
      api.listarInstrumentos(),
      api.listarBloquesCustom(),
      api.listarAreasFrases(),
    ]);
    plantillas.value = ps;
    instrumentos.value = ins;
    bloquesCustom.value = bc;
    areasFrases.value = af;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

function toggle(lista, valor) {
  const i = lista.indexOf(valor);
  if (i >= 0) lista.splice(i, 1);
  else lista.push(valor);
}

const totalPreguntas = computed(() => {
  let n = 0;
  for (const id of nuevo.value.instrumentos_ids) {
    const ins = instrumentos.value.find((x) => x.id === id);
    if (ins) n += ins.n_items;
  }
  for (const id of nuevo.value.bloques_custom_ids) {
    const bc = bloquesCustom.value.find((x) => x.id === id);
    if (bc) n += bc.n_items;
  }
  for (const area of nuevo.value.frases_areas) {
    const a = areasFrases.value.find((x) => x.area === area);
    if (a) n += a.n_frases;
  }
  return n;
});

function abrirCrear() {
  modoCrear.value = true;
  editandoId.value = null;
  nuevo.value = {
    nombre: "",
    descripcion: "",
    instrumentos_ids: [],
    bloques_custom_ids: [],
    frases_areas: [],
  };
}

function abrirEditar(p) {
  modoCrear.value = true;
  editandoId.value = p.id;
  nuevo.value = {
    nombre: p.nombre,
    descripcion: p.descripcion || "",
    instrumentos_ids: p.bloques
      .filter((b) => b.tipo === "instrumento")
      .map((b) => b.instrumento_id),
    bloques_custom_ids: p.bloques
      .filter((b) => b.tipo === "custom")
      .map((b) => b.bloque_custom_id),
    frases_areas: (
      p.bloques.find((b) => b.tipo === "frases")?.frases_areas || []
    ).slice(),
  };
}

async function guardarPlantilla() {
  error.value = "";
  if (!nuevo.value.nombre.trim()) {
    error.value = "Ponle un nombre a la plantilla.";
    return;
  }
  const bloques = [];
  let orden = 0;
  for (const id of nuevo.value.instrumentos_ids) {
    bloques.push({ orden: orden++, tipo: "instrumento", instrumento_id: id });
  }
  for (const id of nuevo.value.bloques_custom_ids) {
    bloques.push({ orden: orden++, tipo: "custom", bloque_custom_id: id });
  }
  if (nuevo.value.frases_areas.length > 0) {
    bloques.push({
      orden: orden++,
      tipo: "frases",
      frases_areas: nuevo.value.frases_areas,
    });
  }
  if (bloques.length === 0) {
    error.value = "Elige al menos un bloque.";
    return;
  }
  const payload = {
    nombre: nuevo.value.nombre.trim(),
    descripcion: nuevo.value.descripcion.trim() || null,
    bloques,
  };
  try {
    if (editandoId.value) {
      await api.actualizarPlantilla(editandoId.value, payload);
    } else {
      await api.crearPlantilla(payload);
    }
    modoCrear.value = false;
    editandoId.value = null;
    await cargar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo guardar.";
  }
}

async function borrar(p) {
  if (!confirm(`¿Eliminar la plantilla "${p.nombre}"?`)) return;
  try {
    await api.borrarPlantilla(p.id);
    plantillas.value = plantillas.value.filter((x) => x.id !== p.id);
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo eliminar.");
  }
}

function asignar(p) {
  router.push({ name: "asignar-cuestionario", query: { plantilla: p.id } });
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6 flex items-start justify-between gap-4">
      <div>
        <p class="eyebrow mb-2">Tus cuestionarios</p>
        <h1 class="hero-serif text-[28px] sm:text-[34px]">
          Mis <span class="hero-mint">plantillas</span>
        </h1>
        <p class="text-ink-500 mt-2">
          Cada plantilla combina los bloques que quieras aplicar al alumno.
        </p>
      </div>
      <button v-if="!modoCrear" class="btn-mint" @click="abrirCrear">
        + Nueva plantilla
      </button>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger mb-4">{{ error }}</div>

    <template v-else>
      <!-- ── Modo crear / editar ── -->
      <div v-if="modoCrear" class="card p-6 mb-6">
        <h2 class="text-lg font-semibold mb-4">
          {{ editandoId ? "Editar plantilla" : "Crear plantilla" }}
        </h2>

        <div class="grid gap-4 mb-6">
          <div>
            <label class="label">Nombre</label>
            <input v-model="nuevo.nombre" class="input" placeholder="Ej. Tamizaje inicial" />
          </div>
          <div>
            <label class="label">Descripción (opcional)</label>
            <textarea v-model="nuevo.descripcion" rows="2" class="input-lg" />
          </div>
        </div>

        <h3 class="text-sm font-semibold text-ink-700 mb-2">
          Escalas validadas
        </h3>
        <div class="grid sm:grid-cols-2 gap-2 mb-6">
          <label
            v-for="i in instrumentos"
            :key="i.id"
            class="flex items-start gap-3 p-3 rounded-lg border border-cream-200 cursor-pointer hover:border-green-400"
            :class="{
              'border-green-500 bg-green-50':
                nuevo.instrumentos_ids.includes(i.id),
            }"
          >
            <input
              type="checkbox"
              :checked="nuevo.instrumentos_ids.includes(i.id)"
              @change="toggle(nuevo.instrumentos_ids, i.id)"
              class="mt-1"
            />
            <span class="flex-1">
              <span class="block font-semibold text-green-900">{{ i.codigo }}</span>
              <span class="block text-xs text-ink-500">{{ i.nombre }}</span>
              <span class="block text-xs text-ink-400 mt-1">
                {{ i.n_items }} ítems — {{ i.dominio }}
              </span>
            </span>
          </label>
        </div>

        <h3 class="text-sm font-semibold text-ink-700 mb-2">
          Bloques personalizados
        </h3>
        <div v-if="bloquesCustom.length === 0" class="text-sm text-ink-400 mb-6">
          No tienes bloques personalizados todavía.
        </div>
        <div v-else class="grid sm:grid-cols-2 gap-2 mb-6">
          <label
            v-for="b in bloquesCustom"
            :key="b.id"
            class="flex items-start gap-3 p-3 rounded-lg border border-cream-200 cursor-pointer hover:border-green-400"
            :class="{
              'border-green-500 bg-green-50':
                nuevo.bloques_custom_ids.includes(b.id),
            }"
          >
            <input
              type="checkbox"
              :checked="nuevo.bloques_custom_ids.includes(b.id)"
              @change="toggle(nuevo.bloques_custom_ids, b.id)"
              class="mt-1"
            />
            <span class="flex-1">
              <span class="block font-semibold text-green-900">{{ b.nombre }}</span>
              <span class="block text-xs text-ink-400">
                {{ b.n_items }} ítems — {{ b.dominio || "personalizado" }}
              </span>
            </span>
          </label>
        </div>

        <h3 class="text-sm font-semibold text-ink-700 mb-2">
          Frases incompletas (elige áreas)
        </h3>
        <div class="flex flex-wrap gap-2 mb-6">
          <button
            v-for="a in areasFrases"
            :key="a.area"
            type="button"
            class="chip-mint cursor-pointer"
            :class="{
              'ring-2 ring-green-500':
                nuevo.frases_areas.includes(a.area),
            }"
            @click="toggle(nuevo.frases_areas, a.area)"
          >
            {{ a.area }} ({{ a.n_frases }})
          </button>
        </div>

        <div class="border-t pt-4 flex items-center justify-between">
          <p class="text-sm text-ink-500">
            Total estimado:
            <strong class="text-green-900">{{ totalPreguntas }} preguntas</strong>
          </p>
          <div class="flex gap-2">
            <button class="btn-ghost" @click="modoCrear = false">Cancelar</button>
            <button class="btn-mint" @click="guardarPlantilla">Guardar</button>
          </div>
        </div>
      </div>

      <!-- ── Lista de plantillas ── -->
      <div v-if="plantillas.length === 0" class="card p-6 text-ink-500">
        Aún no tienes plantillas. Crea una nueva para empezar.
      </div>
      <div v-else class="grid gap-3">
        <div
          v-for="p in plantillas"
          :key="p.id"
          class="card p-4 flex items-center justify-between"
        >
          <div class="flex-1">
            <p class="font-semibold text-green-900">{{ p.nombre }}</p>
            <p v-if="p.descripcion" class="text-sm text-ink-500 mt-1">
              {{ p.descripcion }}
            </p>
            <p class="text-xs text-ink-400 mt-1">
              {{ p.bloques.length }} bloques
            </p>
          </div>
          <div class="flex gap-2">
            <button class="btn-ghost btn-sm" @click="abrirEditar(p)">Editar</button>
            <button class="btn-mint btn-sm" @click="asignar(p)">Asignar</button>
            <button
              class="btn-ghost btn-sm text-red-600"
              @click="borrar(p)"
            >
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
