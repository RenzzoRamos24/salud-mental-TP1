<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const eventos = ref([]);
const cargando = ref(true);
const error = ref("");
const procesando = ref(null);

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
    eventos.value = await api.listarSOSAbiertos();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudieron cargar los SOS.";
  } finally {
    cargando.value = false;
  }
}

async function atender(ev) {
  if (procesando.value) return;
  if (!confirm(`Marcar como atendido el SOS de ${ev.email}?`)) return;
  procesando.value = ev.id;
  try {
    await api.marcarSOSAtendido(ev.id);
    eventos.value = eventos.value.filter((x) => x.id !== ev.id);
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo marcar atendido.");
  } finally {
    procesando.value = null;
  }
}

function fmtFecha(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

onMounted(cargar);
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6 flex items-start justify-between gap-4">
      <div>
        <p class="eyebrow mb-2">Emergencias</p>
        <h1 class="hero-serif text-[28px] sm:text-[34px]">
          Botón <span class="hero-mint">SOS</span>
        </h1>
        <p class="text-ink-500 mt-2">
          Solicitudes de apoyo enviadas por los alumnos desde el botón SOS.
          Atiéndelas según el protocolo del colegio.
        </p>
      </div>
      <button class="btn-ghost btn-sm" @click="cargar">Refrescar</button>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <div v-if="eventos.length === 0" class="card p-6 text-ink-500">
        No hay SOS abiertos en este momento.
      </div>
      <div v-else class="grid gap-3">
        <div
          v-for="ev in eventos"
          :key="ev.id"
          class="card p-5 border-l-4 border-l-red-500 bg-red-50/40"
        >
          <div class="flex items-start justify-between gap-4 mb-3">
            <div>
              <p class="font-semibold text-green-900">
                {{ ev.nombre || "Alumno/a" }}
                <span v-if="ev.apellido" class="font-normal">{{ ev.apellido }}</span>
              </p>
              <p class="text-xs text-ink-500">{{ ev.email }}</p>
              <p class="text-xs text-ink-400 mt-1">
                Activado {{ fmtFecha(ev.created_at) }}
                <span v-if="ev.origen"> — desde {{ ev.origen }}</span>
              </p>
            </div>
            <button
              class="btn-mint btn-sm"
              :disabled="procesando === ev.id"
              @click="atender(ev)"
            >
              {{ procesando === ev.id ? "Marcando…" : "Marcar atendido" }}
            </button>
          </div>

          <div v-if="ev.mensaje" class="bg-white rounded-lg p-3 border border-cream-200">
            <p class="text-xs text-ink-400 mb-1">Mensaje del alumno:</p>
            <p class="text-sm italic">"{{ ev.mensaje }}"</p>
          </div>
          <p v-else class="text-xs text-ink-400 italic">
            (No dejó mensaje.)
          </p>

          <div class="mt-3 text-xs text-red-700">
            Recuerda: la Línea 113 — opción 5 (MINSA, 24/7) está disponible.
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
