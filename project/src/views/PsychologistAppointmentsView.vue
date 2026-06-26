<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

const route = useRoute();
const router = useRouter();
const estudiantes = ref([]);
const citas = ref([]);
const cargando = ref(true);
const error = ref("");
const modoCrear = ref(false);
const editando = ref(null);

const form = ref({
  estudiante_id: "",
  fecha: "",
  hora: "",
  modalidad: "presencial",
  notas: "",
  es_crisis: false,
});

async function cargar() {
  cargando.value = true;
  try {
    const [est, cs] = await Promise.all([
      api.listarEstudiantes(),
      api.listarCitas(),
    ]);
    estudiantes.value = est;
    citas.value = cs;
    // Si entra con ?estudiante=ID, pre-selecciona
    if (route.query.estudiante) {
      abrirCrear(route.query.estudiante);
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

function abrirCrear(estudiante_id = "") {
  modoCrear.value = true;
  editando.value = null;
  form.value = {
    estudiante_id,
    fecha: "",
    hora: "",
    modalidad: "presencial",
    notas: "",
    es_crisis: false,
  };
}

function abrirEditar(c) {
  modoCrear.value = true;
  editando.value = c.id;
  form.value = {
    estudiante_id: c.estudiante_id,
    fecha: c.fecha,
    hora: c.hora,
    modalidad: c.modalidad,
    notas: c.notas || "",
    es_crisis: !!c.es_crisis,
  };
}

async function guardar() {
  error.value = "";
  if (!form.value.estudiante_id || !form.value.fecha || !form.value.hora) {
    error.value = "Faltan estudiante, fecha u hora.";
    return;
  }
  try {
    if (editando.value) {
      await api.actualizarCita(editando.value, {
        fecha: form.value.fecha,
        hora: form.value.hora,
        modalidad: form.value.modalidad,
        notas: form.value.notas || null,
        es_crisis: form.value.es_crisis,
      });
    } else {
      await api.crearCita(form.value);
    }
    modoCrear.value = false;
    editando.value = null;
    await cargar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo guardar.";
  }
}

async function marcarCompletada(c) {
  if (!confirm(`Marcar la cita del ${c.fecha} ${c.hora} como completada?`)) return;
  try {
    await api.actualizarCita(c.id, { estado: "completada" });
    await cargar();
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo actualizar.");
  }
}

async function cancelar(c) {
  if (!confirm(`Cancelar la cita del ${c.fecha} ${c.hora}?`)) return;
  try {
    await api.cancelarCita(c.id);
    citas.value = citas.value.filter((x) => x.id !== c.id);
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo cancelar.");
  }
}

const proximas = computed(() => {
  const hoy = new Date().toISOString().slice(0, 10);
  return citas.value
    .filter((c) => c.fecha >= hoy && c.estado !== "cancelada")
    .sort((a, b) => (a.fecha + a.hora).localeCompare(b.fecha + b.hora));
});

const historico = computed(() => {
  const hoy = new Date().toISOString().slice(0, 10);
  return citas.value
    .filter((c) => c.fecha < hoy || c.estado === "completada")
    .sort((a, b) => (b.fecha + b.hora).localeCompare(a.fecha + a.hora))
    .slice(0, 20);
});

function badgeEstado(estado) {
  return (
    {
      programada: "bg-sky-50 text-sky-700 border-sky-200",
      completada: "bg-green-50 text-green-700 border-green-200",
      cancelada: "bg-gray-50 text-gray-500 border-gray-200",
    }[estado] || "bg-gray-50 text-gray-700 border-gray-200"
  );
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6 flex items-start justify-between gap-4">
      <div>
        <p class="eyebrow mb-2">Agenda</p>
        <h1 class="hero-serif text-[28px] sm:text-[34px]">
          Citas <span class="hero-mint">con alumnos</span>
        </h1>
      </div>
      <button v-if="!modoCrear" class="btn-mint" @click="abrirCrear()">
        + Nueva cita
      </button>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>

    <template v-else>
      <div v-if="error" class="banner-danger mb-4">{{ error }}</div>

      <div v-if="modoCrear" class="card p-6 mb-6">
        <h2 class="text-lg font-semibold mb-4">
          {{ editando ? "Editar cita" : "Nueva cita" }}
        </h2>
        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <label class="label">Estudiante</label>
            <select v-model="form.estudiante_id" class="input">
              <option value="" disabled>— Elige un estudiante —</option>
              <option v-for="e in estudiantes" :key="e.id" :value="e.id">
                {{ e.nombre }} {{ e.apellido }} ({{ e.email }})
              </option>
            </select>
          </div>
          <div>
            <label class="label">Modalidad</label>
            <select v-model="form.modalidad" class="input">
              <option value="presencial">Presencial</option>
              <option value="virtual">Virtual</option>
              <option value="telefonica">Telefónica</option>
            </select>
          </div>
          <div>
            <label class="label">Fecha</label>
            <input v-model="form.fecha" type="date" class="input" />
          </div>
          <div>
            <label class="label">Hora</label>
            <input v-model="form.hora" type="time" class="input" />
          </div>
          <div class="sm:col-span-2">
            <label class="label">Notas (opcional)</label>
            <textarea v-model="form.notas" rows="2" class="input-lg"></textarea>
          </div>
          <div class="sm:col-span-2">
            <label class="flex items-center gap-2 text-sm">
              <input v-model="form.es_crisis" type="checkbox" />
              <span>Esta cita es atención de crisis (alta prioridad).</span>
            </label>
          </div>
        </div>
        <div class="flex justify-end gap-2 mt-4">
          <button class="btn-ghost" @click="modoCrear = false">Cancelar</button>
          <button class="btn-mint" @click="guardar">
            {{ editando ? "Guardar cambios" : "Crear cita" }}
          </button>
        </div>
      </div>

      <h2 class="text-lg font-semibold mb-3">Próximas</h2>
      <div v-if="proximas.length === 0" class="card p-6 text-ink-500 mb-6">
        No tienes citas programadas.
      </div>
      <div v-else class="grid gap-3 mb-8">
        <div
          v-for="c in proximas"
          :key="c.id"
          class="card p-4 flex items-center justify-between"
          :class="{ 'border-red-300 bg-red-50/40': c.es_crisis }"
        >
          <div>
            <p class="font-semibold text-green-900">
              {{ c.estudiante_nombre }} {{ c.estudiante_apellido }}
              <span v-if="c.es_crisis" class="text-xs text-red-700 ml-2">crisis</span>
            </p>
            <p class="text-sm">
              {{ c.fecha }} — {{ c.hora }} — {{ c.modalidad }}
            </p>
            <p v-if="c.notas" class="text-xs text-ink-500 mt-1 italic">
              {{ c.notas }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <span
              class="text-xs px-2 py-0.5 rounded-full border"
              :class="badgeEstado(c.estado)"
            >
              {{ c.estado }}
            </span>
            <button class="btn-ghost btn-sm" @click="abrirEditar(c)">Editar</button>
            <button class="btn-mint btn-sm" @click="marcarCompletada(c)">
              Completada
            </button>
            <button class="btn-ghost btn-sm text-red-600" @click="cancelar(c)">
              Cancelar
            </button>
          </div>
        </div>
      </div>

      <h2 class="text-lg font-semibold mb-3">Histórico</h2>
      <div v-if="historico.length === 0" class="card p-6 text-ink-500">
        Sin citas pasadas.
      </div>
      <div v-else class="grid gap-2">
        <div
          v-for="c in historico"
          :key="c.id"
          class="card p-3 flex items-center justify-between text-sm"
        >
          <div>
            <p class="font-medium">
              {{ c.estudiante_nombre }} {{ c.estudiante_apellido }}
            </p>
            <p class="text-xs text-ink-500">
              {{ c.fecha }} — {{ c.hora }} — {{ c.modalidad }}
            </p>
          </div>
          <span
            class="text-xs px-2 py-0.5 rounded-full border"
            :class="badgeEstado(c.estado)"
          >
            {{ c.estado }}
          </span>
        </div>
      </div>
    </template>
  </div>
</template>
