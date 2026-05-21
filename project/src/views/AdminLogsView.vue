<script setup>
import { onMounted, onBeforeUnmount, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import PageHeader from "../components/PageHeader.vue";

const router = useRouter();
const logs = ref([]);
const total = ref(0);
const filtroRol = ref(null);
const filtroEndpoint = ref("");
const tiempoReal = ref(true);
const cargando = ref(false);
const error = ref("");
const ultimaActualizacion = ref(null);
let timer = null;

async function cargar() {
  cargando.value = true;
  try {
    const r = await api.adminGetAuditLogs({
      limit: 100,
      offset: 0,
      role: filtroRol.value || undefined,
      endpoint: filtroEndpoint.value || undefined,
    });
    logs.value = r.logs;
    total.value = r.total;
    ultimaActualizacion.value = new Date();
  } catch (e) {
    error.value = e.response?.data?.detail || e.message;
  } finally {
    cargando.value = false;
  }
}

onMounted(() => {
  cargar();
  timer = setInterval(() => {
    if (tiempoReal.value) cargar();
  }, 5000);
});
onBeforeUnmount(() => clearInterval(timer));

function statusChip(code) {
  if (code >= 500) return "chip bg-red-100 text-risk-critico";
  if (code >= 400) return "chip-peach";
  if (code >= 300) return "chip-brand";
  return "chip-mint";
}
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">
      Volver al menú
    </button>

    <PageHeader
      title="Auditoría"
      subtitle="Cada llamada a la API queda registrada (Ley 29733)."
      tone="sky2"
    >
      <template #actions>
        <div class="flex items-center gap-3 mt-3">
          <span
            class="text-sm"
            :class="tiempoReal ? 'text-green-600' : 'text-ink-400'"
          >
            {{ tiempoReal ? "En vivo · cada 5s" : "Pausado" }}
          </span>
        </div>
      </template>
      <template #aside>
        <div class="flex gap-2">
          <button
            @click="tiempoReal = !tiempoReal"
            class="btn-secondary btn-sm"
          >
            {{ tiempoReal ? "Pausar" : "Reanudar" }}
          </button>
          <button @click="cargar" class="btn-secondary btn-sm">
            Refrescar
          </button>
        </div>
      </template>
    </PageHeader>

    <!-- Filtros -->
    <div class="flex flex-wrap gap-3 items-center mb-4 fade-in-up">
      <div
        class="flex gap-1 bg-white border border-ink-100 rounded-xl p-1 shadow-soft"
      >
        <button
          v-for="op in ['todos', 'estudiante', 'psicologo', 'admin']"
          :key="op"
          @click="
            filtroRol = op === 'todos' ? null : op;
            cargar();
          "
          :class="[
            'px-3 py-1.5 text-xs rounded-xl transition capitalize',
            filtroRol === op || (filtroRol === null && op === 'todos')
              ? 'bg-green-600 text-white shadow-soft'
              : 'text-ink-600 hover:bg-green-50',
          ]"
        >
          {{ op }}
        </button>
      </div>
      <input
        v-model="filtroEndpoint"
        @keyup.enter="cargar"
        type="text"
        placeholder="Filtrar por endpoint"
        class="input flex-1 min-w-[200px]"
      />
    </div>

    <p v-if="error" class="banner-danger">{{ error }}</p>

    <!-- Tabla -->
    <div class="card overflow-hidden fade-in-up">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead
            class="bg-white text-xs uppercase tracking-wider text-ink-500 text-left"
          >
            <tr>
              <th class="px-4 py-3">Hora</th>
              <th class="px-4 py-3">Usuario</th>
              <th class="px-4 py-3">Rol</th>
              <th class="px-4 py-3">Método</th>
              <th class="px-4 py-3">Endpoint</th>
              <th class="px-4 py-3">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-ink-100">
            <tr v-if="!logs.length">
              <td colspan="6" class="text-center text-ink-400 py-10">
                Sin registros.
              </td>
            </tr>
            <tr
              v-for="l in logs"
              :key="l.id"
              class="hover:bg-green-50/40 transition"
            >
              <td
                class="px-4 py-2.5 text-xs font-mono text-ink-500 whitespace-nowrap"
              >
                {{ new Date(l.timestamp).toLocaleTimeString("es-PE") }}
              </td>
              <td class="px-4 py-2.5 text-sm text-ink-800">
                {{ l.email || "—" }}
              </td>
              <td class="px-4 py-2.5">
                <span v-if="l.role" class="dsm5-tag capitalize">{{
                  l.role
                }}</span>
                <span v-else class="text-ink-400 text-xs">—</span>
              </td>
              <td
                class="px-4 py-2.5 text-xs font-mono font-semibold text-green-700"
              >
                {{ l.method }}
              </td>
              <td
                class="px-4 py-2.5 text-xs font-mono text-ink-700 truncate max-w-[320px]"
              >
                {{ l.endpoint }}
              </td>
              <td class="px-4 py-2.5">
                <span :class="statusChip(l.status_code)">{{
                  l.status_code
                }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <p class="text-xs text-ink-400 text-right mt-3">
      {{ logs.length }} de {{ total }} registros
      <span v-if="ultimaActualizacion"
        >· Última: {{ ultimaActualizacion.toLocaleTimeString("es-PE") }}</span
      >
    </p>
  </div>
</template>
