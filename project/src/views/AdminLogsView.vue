<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const data = ref({ total: 0, logs: [] });
const cargando = ref(true);
const error = ref("");
const filtroRol = ref("");
const filtroEndpoint = ref("");

async function cargar() {
  cargando.value = true;
  try {
    data.value = await api.adminGetAuditLogs({
      role: filtroRol.value || undefined,
      endpoint: filtroEndpoint.value || undefined,
      limit: 200,
    });
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

function fmt(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE");
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Auditoría</p>
      <h1 class="hero-serif text-[28px]">
        Logs de <span class="hero-mint">acceso</span>
      </h1>
    </header>

    <div class="card p-4 mb-4 flex gap-2 flex-wrap">
      <input
        v-model="filtroRol"
        class="input flex-1"
        placeholder="Filtrar por rol (estudiante / psicologo / admin)"
      />
      <input
        v-model="filtroEndpoint"
        class="input flex-1"
        placeholder="Filtrar por endpoint"
      />
      <button class="btn-mint btn-sm" @click="cargar">Filtrar</button>
    </div>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
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
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="l in data.logs"
            :key="l.id"
            class="border-b border-cream-100"
          >
            <td class="p-2 text-xs">{{ fmt(l.timestamp) }}</td>
            <td class="p-2 text-xs">{{ l.role || "—" }}</td>
            <td class="p-2 text-xs">{{ l.email || "—" }}</td>
            <td class="p-2 text-xs font-mono">{{ l.method }}</td>
            <td class="p-2 text-xs font-mono">{{ l.endpoint }}</td>
            <td class="p-2 text-xs tabular">{{ l.status_code }}</td>
          </tr>
        </tbody>
      </table>
      <p class="text-xs text-ink-400 mt-2">Total: {{ data.total }}</p>
    </div>
  </div>
</template>
