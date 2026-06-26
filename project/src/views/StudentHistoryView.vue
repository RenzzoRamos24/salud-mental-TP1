<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

const route = useRoute();
const router = useRouter();
const id = computed(() => route.params.id);

const data = ref(null);
const notas = ref([]);
const cargando = ref(true);
const error = ref("");

const nuevaNota = ref({ texto: "", etiqueta: "" });
const guardandoNota = ref(false);

async function cargar() {
  cargando.value = true;
  try {
    const [h, n] = await Promise.all([
      api.historialEstudiante(id.value),
      api.listarNotas(id.value).catch(() => []),
    ]);
    data.value = h;
    notas.value = n;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

async function guardarNota() {
  const texto = (nuevaNota.value.texto || "").trim();
  if (!texto) return;
  guardandoNota.value = true;
  try {
    await api.crearNota(id.value, {
      texto,
      etiqueta: nuevaNota.value.etiqueta || null,
    });
    nuevaNota.value = { texto: "", etiqueta: "" };
    notas.value = await api.listarNotas(id.value);
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo guardar la nota.");
  } finally {
    guardandoNota.value = false;
  }
}

async function borrarNota(nota_id) {
  if (!confirm("¿Eliminar esta nota?")) return;
  try {
    await api.borrarNota(id.value, nota_id);
    notas.value = notas.value.filter((n) => n.id !== nota_id);
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo eliminar.");
  }
}

function agendarCita() {
  router.push({ name: "psicologo-citas", query: { estudiante: id.value } });
}

function verResultado(a) {
  router.push({ name: "psicologo-resultado", params: { id: a.id } });
}

function asignar() {
  router.push({ name: "asignar-cuestionario", query: { estudiante: id.value } });
}

function fmt(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE");
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
    <button class="btn-ghost btn-sm mb-4" @click="router.back()">← Volver</button>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <header class="mb-6 flex items-start justify-between gap-4">
        <div>
          <p class="eyebrow mb-2">Ficha</p>
          <h1 class="hero-serif text-[28px]">
            {{ data.estudiante.nombre }}
            <span class="hero-mint">{{ data.estudiante.apellido }}</span>
          </h1>
          <p class="text-sm text-ink-500 mt-2">
            {{ data.estudiante.email }}
            <span v-if="data.estudiante.grado"> — {{ data.estudiante.grado }}</span>
          </p>
        </div>
        <div class="flex gap-2">
          <button class="btn-ghost" @click="agendarCita">+ Cita</button>
          <button class="btn-mint" @click="asignar">+ Asignar cuestionario</button>
        </div>
      </header>

      <h2 class="text-lg font-semibold mb-3">Historial de cuestionarios</h2>

      <div v-if="data.aplicaciones.length === 0" class="card p-6 text-ink-500">
        Este alumno no tiene cuestionarios asignados todavía.
      </div>
      <div v-else class="grid gap-3">
        <div
          v-for="a in data.aplicaciones"
          :key="a.id"
          class="card p-4 flex items-center justify-between"
          :class="{ 'border-red-300 bg-red-50/40': a.crisis_activada }"
        >
          <div>
            <p class="text-xs text-ink-400">Aplicación #{{ a.id }}</p>
            <p class="text-sm">Asignada: {{ fmt(a.asignada_at) }}</p>
            <p v-if="a.completada_at" class="text-xs text-ink-500">
              Completada: {{ fmt(a.completada_at) }}
            </p>
          </div>
          <div class="flex items-center gap-3">
            <span
              v-if="a.riesgo_global"
              class="text-xs px-2 py-0.5 rounded-full border"
              :class="colorRiesgo(a.riesgo_global)"
            >
              {{ a.riesgo_global }}
            </span>
            <span
              class="text-xs px-2 py-0.5 rounded-full bg-gray-50 border border-gray-200 capitalize"
            >
              {{ a.estado }}
            </span>
            <button
              v-if="a.estado === 'completado' || a.estado === 'revisado'"
              class="btn-ghost btn-sm"
              @click="verResultado(a)"
            >
              Ver
            </button>
          </div>
        </div>
      </div>

      <!-- ── Notas clínicas privadas ─────────────────────────────── -->
      <h2 class="text-lg font-semibold mt-10 mb-3">Notas clínicas privadas</h2>
      <p class="text-xs text-ink-500 mb-3">
        Solo tú las ves. El admin tiene acceso únicamente para auditoría.
      </p>

      <div class="card p-4 mb-4">
        <div class="grid sm:grid-cols-[1fr_180px] gap-3 mb-3">
          <textarea
            v-model="nuevaNota.texto"
            rows="3"
            class="input-lg"
            placeholder="Apunta una observación clínica…"
          ></textarea>
          <input
            v-model="nuevaNota.etiqueta"
            class="input"
            placeholder="Etiqueta (opcional)"
            maxlength="50"
          />
        </div>
        <div class="flex justify-end">
          <button
            class="btn-mint btn-sm"
            :disabled="guardandoNota || !nuevaNota.texto.trim()"
            @click="guardarNota"
          >
            {{ guardandoNota ? "Guardando…" : "Guardar nota" }}
          </button>
        </div>
      </div>

      <div v-if="notas.length === 0" class="text-sm text-ink-500">
        Aún no hay notas para este alumno.
      </div>
      <div v-else class="grid gap-2">
        <div
          v-for="n in notas"
          :key="n.id"
          class="card p-3 text-sm"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1">
              <p
                v-if="n.etiqueta"
                class="text-xs text-green-700 mb-1 uppercase tracking-wide"
              >
                {{ n.etiqueta }}
              </p>
              <p class="whitespace-pre-wrap">{{ n.texto }}</p>
              <p class="text-xs text-ink-400 mt-2">
                {{ fmt(n.created_at) }}
              </p>
            </div>
            <button
              class="text-xs text-red-600 hover:underline"
              @click="borrarNota(n.id)"
            >
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
