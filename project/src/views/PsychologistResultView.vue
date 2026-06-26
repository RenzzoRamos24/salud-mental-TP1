<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

const route = useRoute();
const router = useRouter();
const aplicacionId = computed(() => Number(route.params.id));

const cargando = ref(true);
const error = ref("");
const data = ref(null);

async function cargar() {
  cargando.value = true;
  try {
    data.value = await api.obtenerResultado(aplicacionId.value);
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

async function marcarRevisado() {
  try {
    await api.marcarRevisado(aplicacionId.value);
    await cargar();
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo marcar.");
  }
}

const resultado = computed(() => data.value?.resultado || null);

function colorRiesgo(r) {
  const map = {
    CRITICO: "bg-red-50 text-red-700 border-red-200",
    ALTO: "bg-orange-50 text-orange-700 border-orange-200",
    MEDIO: "bg-amber-50 text-amber-700 border-amber-200",
    BAJO: "bg-sky-50 text-sky-700 border-sky-200",
    SIN_RIESGO: "bg-green-50 text-green-700 border-green-200",
  };
  return map[r] || "bg-gray-50 text-gray-700 border-gray-200";
}

function colorBloque(b) {
  if (b.bandera_crisis || b.severidad_alerta) {
    return "bg-amber-50 border-amber-200";
  }
  return "bg-green-50 border-green-200";
}

function fmtFecha(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE");
}
</script>

<template>
  <div class="page-shell-wide">
    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <header class="mb-6">
        <p class="eyebrow mb-2">Resultado del cuestionario</p>
        <h1 class="hero-serif text-[28px]">
          Aplicación <span class="hero-mint">#{{ data.id }}</span>
        </h1>
        <p class="text-sm text-ink-500 mt-2">
          Estudiante: {{ data.estudiante_id }} — Completado el
          {{ fmtFecha(data.completada_at) }}
        </p>
      </header>

      <div
        v-if="resultado?.crisis_activada"
        class="banner-danger mb-4"
      >
        PROTOCOLO DE CRISIS ACTIVADO. Revisa de inmediato las respuestas
        marcadas y deriva según protocolo.
      </div>

      <div class="grid sm:grid-cols-2 gap-4 mb-6">
        <div class="card p-6 text-center">
          <p class="text-xs text-ink-400 mb-2">Riesgo global</p>
          <span
            class="inline-block px-4 py-2 rounded-full border text-lg font-semibold"
            :class="colorRiesgo(resultado?.riesgo_global)"
          >
            {{ resultado?.riesgo_global || "—" }}
          </span>
          <p class="text-xs text-ink-500 mt-3">
            {{ resultado?.n_senales || 0 }} señales en zona de alerta sobre
            {{ resultado?.n_bloques || 0 }} bloques.
          </p>
        </div>

        <div class="card p-6">
          <p class="text-xs text-ink-400 mb-2">Estado</p>
          <p class="font-semibold capitalize">{{ data.estado }}</p>
          <button
            v-if="data.estado === 'completado'"
            class="btn-mint mt-3 btn-sm"
            @click="marcarRevisado"
          >
            Marcar como revisado
          </button>
        </div>
      </div>

      <!-- Bloques por instrumento / custom -->
      <h2 class="text-lg font-semibold mb-3">Termómetros por bloque</h2>
      <div class="grid sm:grid-cols-2 gap-3 mb-6">
        <div
          v-for="b in resultado?.bloques || []"
          :key="b.codigo"
          class="rounded-xl border p-4"
          :class="colorBloque(b)"
        >
          <div class="flex items-start justify-between mb-2">
            <div>
              <p class="text-xs text-ink-400">{{ b.dominio }}</p>
              <p class="font-semibold text-green-900">
                {{ b.codigo }}
                <span v-if="b.nombre !== b.codigo" class="font-normal text-ink-500">
                  — {{ b.nombre }}
                </span>
              </p>
            </div>
            <span class="tabular text-sm">
              {{ b.puntaje }} / {{ b.rango_max }}
            </span>
          </div>
          <p class="text-sm font-medium capitalize">{{ b.severidad }}</p>
          <p v-if="b.bandera_crisis" class="text-xs text-red-700 mt-2">
            Bandera de crisis encendida.
          </p>
        </div>
      </div>

      <!-- Frases incompletas -->
      <template v-if="(resultado?.frases || []).length > 0">
        <h2 class="text-lg font-semibold mb-3">Frases incompletas</h2>
        <div class="grid gap-3">
          <div
            v-for="f in resultado.frases"
            :key="`${f.area}-${f.numero}`"
            class="card p-4"
            :class="{ 'border-red-300': f.crisis }"
          >
            <p class="text-xs text-ink-400 mb-1">{{ f.area }} — #{{ f.numero }}</p>
            <p class="text-sm italic text-ink-500 mb-2">{{ f.pregunta }}</p>
            <p class="font-medium">"{{ f.respuesta }}"</p>
            <div class="flex flex-wrap gap-1 mt-3">
              <span
                v-for="d in f.detectadas"
                :key="d"
                class="chip-mint text-xs"
              >
                {{ d }}
              </span>
              <span
                v-if="f.crisis"
                class="text-xs px-2 py-0.5 rounded-full bg-red-50 text-red-700 border border-red-200"
              >
                ideación detectada
              </span>
            </div>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>
