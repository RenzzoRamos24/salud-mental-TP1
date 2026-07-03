<script setup>
import { ref, onMounted, computed } from "vue";
import { api } from "../api";

const data = ref({ total: 0, logs: [] });
const usuarios = ref([]);
const cargando = ref(true);
const error = ref("");
const filtroRol = ref("");
const filtroEndpoint = ref("");

async function cargar() {
  cargando.value = true;
  try {
    const [logs, todos] = await Promise.all([
      api.adminGetAuditLogs({
        role: filtroRol.value || undefined,
        endpoint: filtroEndpoint.value || undefined,
        limit: 200,
      }),
      api.listarUsuarios().catch(() => []),
    ]);
    data.value = logs;
    usuarios.value = todos || [];
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const psicologos = computed(() =>
  usuarios.value.filter((u) => u.role === "psicologo"),
);
const estudiantes = computed(() =>
  usuarios.value.filter((u) => u.role === "estudiante"),
);

const usuariosUnicos = computed(() => {
  const set = new Set();
  for (const l of data.value.logs || []) {
    if (l.user_id) set.add(l.user_id);
  }
  return set.size;
});

const peticionesCriticas = computed(
  () =>
    (data.value.logs || []).filter(
      (l) => (l.endpoint || "").includes("/sos") || (l.status_code || 0) >= 500,
    ).length,
);

function fmt(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE");
}

function colorMetodo(m) {
  return (
    {
      GET: "bg-sky-50 text-sky-700",
      POST: "bg-green-50 text-green-700",
      PUT: "bg-amber-50 text-amber-700",
      PATCH: "bg-purple-50 text-purple-700",
      DELETE: "bg-red-50 text-red-700",
    }[m] || "bg-gray-50 text-gray-700"
  );
}

function colorStatus(s) {
  if (s >= 500) return "text-red-700 font-semibold";
  if (s >= 400) return "text-amber-700 font-semibold";
  if (s >= 300) return "text-sky-700";
  return "text-green-700";
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Auditoría</p>
      <h1 class="hero-serif text-[28px]">
        Auditoría y <span class="hero-mint">logs</span>
      </h1>
      <p class="text-ink-500 mt-2 text-sm">
        Trazabilidad completa de las acciones realizadas en el sistema —
        cumplimiento de la Ley 29733 de Protección de Datos Personales.
      </p>
    </header>

    <!-- KPIs -->
    <div class="grid sm:grid-cols-4 gap-3 mb-6">
      <div class="card p-4">
        <p class="text-xs text-ink-400">Total de peticiones</p>
        <p class="text-2xl font-semibold text-green-900">
          {{ data.total || 0 }}
        </p>
        <p class="text-xs text-ink-500 mt-1">desde el inicio del sistema</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-ink-400">Usuarios únicos (últimos 200)</p>
        <p class="text-2xl font-semibold text-green-900">
          {{ usuariosUnicos }}
        </p>
        <p class="text-xs text-ink-500 mt-1">con actividad reciente</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-ink-400">Acciones críticas</p>
        <p class="text-2xl font-semibold text-red-700">
          {{ peticionesCriticas }}
        </p>
        <p class="text-xs text-ink-500 mt-1">eventos SOS / errores 5xx</p>
      </div>
      <div class="card p-4">
        <p class="text-xs text-ink-400">Total usuarios registrados</p>
        <p class="text-2xl font-semibold text-green-900">
          {{ usuarios.length }}
        </p>
        <p class="text-xs text-ink-500 mt-1">
          {{ estudiantes.length }} estudiantes · {{ psicologos.length }} psicólogas
        </p>
      </div>
    </div>

    <!-- Listas de usuarios -->
    <div class="grid sm:grid-cols-2 gap-3 mb-6">
      <div class="card p-4">
        <h2 class="text-base font-semibold mb-3 text-green-900">
          Psicólogas activas ({{ psicologos.length }})
        </h2>
        <div class="space-y-2">
          <div
            v-for="p in psicologos"
            :key="p.id"
            class="flex justify-between items-center py-1 text-sm border-b border-cream-100"
          >
            <span>{{ p.nombre }} {{ p.apellido }}</span>
            <span class="text-xs text-ink-400">{{ p.email }}</span>
          </div>
          <p v-if="!psicologos.length" class="text-xs text-ink-400">
            Sin psicólogas registradas todavía.
          </p>
        </div>
      </div>

      <div class="card p-4">
        <h2 class="text-base font-semibold mb-3 text-green-900">
          Estudiantes registrados ({{ estudiantes.length }})
        </h2>
        <div class="space-y-2">
          <div
            v-for="e in estudiantes.slice(0, 6)"
            :key="e.id"
            class="flex justify-between items-center py-1 text-sm border-b border-cream-100"
          >
            <span>{{ e.nombre }} {{ e.apellido }}</span>
            <span class="text-xs text-ink-400">
              {{ e.estado_caso || "activo" }}
            </span>
          </div>
          <p v-if="estudiantes.length > 6" class="text-xs text-ink-400 mt-2">
            … y {{ estudiantes.length - 6 }} más
          </p>
          <p v-if="!estudiantes.length" class="text-xs text-ink-400">
            Sin estudiantes registrados todavía.
          </p>
        </div>
      </div>
    </div>

    <!-- Filtros -->
    <div class="card p-4 mb-4 flex gap-2 flex-wrap items-center">
      <p class="text-sm text-ink-500 font-medium">Filtrar logs:</p>
      <input
        v-model="filtroRol"
        class="input flex-1"
        placeholder="rol (estudiante / psicologo / admin)"
      />
      <input
        v-model="filtroEndpoint"
        class="input flex-1"
        placeholder="endpoint (ej. /api/v1/auth)"
      />
      <button class="btn-mint btn-sm" @click="cargar">Aplicar filtros</button>
    </div>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">
      Cargando…
    </div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <div v-else class="card p-2 overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-cream-200 text-left text-xs text-ink-400">
            <th class="p-2">Fecha</th>
            <th class="p-2">Rol</th>
            <th class="p-2">Usuario</th>
            <th class="p-2">Método</th>
            <th class="p-2">Endpoint</th>
            <th class="p-2">Status</th>
            <th class="p-2">IP</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="l in data.logs"
            :key="l.id"
            class="border-b border-cream-100 hover:bg-cream-50"
          >
            <td class="p-2 text-xs">{{ fmt(l.timestamp) }}</td>
            <td class="p-2 text-xs">{{ l.role || "—" }}</td>
            <td class="p-2 text-xs">{{ l.email || "—" }}</td>
            <td class="p-2 text-xs">
              <span
                class="px-2 py-0.5 rounded font-mono text-[10px]"
                :class="colorMetodo(l.method)"
              >
                {{ l.method }}
              </span>
            </td>
            <td class="p-2 text-xs font-mono">{{ l.endpoint }}</td>
            <td class="p-2 text-xs tabular" :class="colorStatus(l.status_code)">
              {{ l.status_code }}
            </td>
            <td class="p-2 text-xs text-ink-400 font-mono">{{ l.ip || "—" }}</td>
          </tr>
        </tbody>
      </table>
      <p class="text-xs text-ink-400 mt-2 px-2 pb-2">
        Mostrando {{ data.logs.length }} de {{ data.total }} registros totales
      </p>
    </div>
  </div>
</template>
