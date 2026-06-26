<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();
const instrumentos = ref([]);
const bloquesCustom = ref([]);
const areasFrases = ref([]);
const cargando = ref(true);
const error = ref("");
const seleccionado = ref(null);
const detalleInstrumento = ref(null);

async function cargar() {
  cargando.value = true;
  try {
    const [ins, bc, af] = await Promise.all([
      api.listarInstrumentos(),
      api.listarBloquesCustom(),
      api.listarAreasFrases(),
    ]);
    instrumentos.value = ins;
    bloquesCustom.value = bc;
    areasFrases.value = af;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar el banco.";
  } finally {
    cargando.value = false;
  }
}

async function verInstrumento(codigo) {
  seleccionado.value = codigo;
  try {
    detalleInstrumento.value = await api.obtenerInstrumento(codigo);
  } catch (e) {
    detalleInstrumento.value = null;
  }
}

async function borrarCustom(id) {
  if (!confirm("¿Eliminar este bloque personalizado?")) return;
  try {
    await api.borrarBloqueCustom(id);
    bloquesCustom.value = bloquesCustom.value.filter((b) => b.id !== id);
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo eliminar.");
  }
}

onMounted(cargar);
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6 flex items-start justify-between gap-4">
      <div>
        <p class="eyebrow mb-2">Catálogo de instrumentos</p>
        <h1 class="hero-serif text-[28px] sm:text-[34px]">
          Banco <span class="hero-mint">clínico</span>
        </h1>
        <p class="text-ink-500 mt-2">
          Instrumentos validados, tus bloques personalizados y áreas de frases incompletas.
        </p>
      </div>
      <div class="flex gap-2">
        <button class="btn-mint" @click="router.push('/psicologo/bloque-custom')">
          + Nuevo bloque personalizado
        </button>
      </div>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <!-- Instrumentos validados -->
      <h2 class="text-lg font-semibold mb-3">Escalas validadas (no editables)</h2>
      <div class="grid sm:grid-cols-2 gap-3 mb-8">
        <div
          v-for="i in instrumentos"
          :key="i.id"
          class="card p-4 cursor-pointer hover:border-green-400"
          :class="{ 'border-green-500 ring-2 ring-green-100': seleccionado === i.codigo }"
          @click="verInstrumento(i.codigo)"
        >
          <div class="flex items-start justify-between">
            <div>
              <p class="text-xs text-ink-400">{{ i.dominio }}</p>
              <p class="font-semibold text-green-900">{{ i.codigo }}</p>
              <p class="text-[13px] text-ink-500 mt-1">{{ i.nombre }}</p>
            </div>
            <span class="text-xs text-ink-400 tabular">{{ i.n_items }} ítems</span>
          </div>
          <p class="text-xs text-ink-400 mt-3">
            {{ i.autor }} ({{ i.anio }})
          </p>
        </div>
      </div>

      <div v-if="detalleInstrumento" class="card p-6 mb-8">
        <h3 class="text-lg font-semibold text-green-900 mb-1">
          {{ detalleInstrumento.nombre }}
        </h3>
        <p class="text-sm text-ink-500 italic mb-3">{{ detalleInstrumento.instruccion }}</p>
        <ol class="list-decimal pl-5 space-y-1 text-sm">
          <li v-for="it in detalleInstrumento.items" :key="it.numero">
            {{ it.texto }}
            <span
              v-if="it.bandera_crisis"
              class="ml-2 text-xs px-1.5 py-0.5 rounded bg-red-50 text-red-700 border border-red-200"
            >crisis</span>
            <span
              v-if="it.inverso"
              class="ml-1 text-xs px-1.5 py-0.5 rounded bg-gray-50 text-gray-700 border border-gray-200"
            >inverso</span>
          </li>
        </ol>
        <p class="text-xs text-ink-400 mt-4 italic">
          Cita: {{ detalleInstrumento.citacion }}
        </p>
      </div>

      <!-- Áreas de frases -->
      <h2 class="text-lg font-semibold mb-3">Frases incompletas — áreas disponibles</h2>
      <div class="card p-4 mb-8">
        <div class="flex flex-wrap gap-2">
          <span
            v-for="a in areasFrases"
            :key="a.area"
            class="chip-mint"
          >
            {{ a.area }} <span class="text-xs opacity-70">({{ a.n_frases }})</span>
          </span>
        </div>
      </div>

      <!-- Bloques custom -->
      <h2 class="text-lg font-semibold mb-3">Tus bloques personalizados</h2>
      <div v-if="bloquesCustom.length === 0" class="card p-6 text-ink-500">
        Aún no has creado bloques personalizados.
      </div>
      <div v-else class="grid sm:grid-cols-2 gap-3">
        <div v-for="b in bloquesCustom" :key="b.id" class="card p-4">
          <div class="flex items-start justify-between mb-2">
            <div>
              <p class="text-xs text-ink-400">{{ b.dominio || "personalizado" }}</p>
              <p class="font-semibold text-green-900">{{ b.nombre }}</p>
            </div>
            <div class="flex gap-2">
              <button
                class="text-xs text-green-700 hover:underline"
                @click="router.push({ path: '/psicologo/bloque-custom', query: { id: b.id } })"
              >
                Editar
              </button>
              <button
                class="text-xs text-red-600 hover:underline"
                @click="borrarCustom(b.id)"
              >
                Eliminar
              </button>
            </div>
          </div>
          <p class="text-xs text-ink-500">
            {{ b.n_items }} ítems — {{ b.tipo_escala }}
            <span v-if="b.tipo_escala === 'likert'">
              (0–{{ b.likert_max }})
            </span>
          </p>
          <p class="text-xs text-ink-400 mt-1">
            Cortes: ≤{{ b.corte_sin_alerta_max }} sin alerta ·
            ≤{{ b.corte_posible_max }} posible ·
            ≤{{ b.corte_alto_max }} alto
          </p>
        </div>
      </div>
    </template>
  </div>
</template>
