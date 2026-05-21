<script setup>
import { ref, onMounted, computed } from "vue";
import { api } from "../api";
import PageHeader from "../components/PageHeader.vue";
import StatCard from "../components/StatCard.vue";

const usuarios = ref([]);
const stats = ref(null);
const cargando = ref(true);
const error = ref("");
const filtroRol = ref("todos");
const filtroTexto = ref("");

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
    const [u, s] = await Promise.all([
      api.listarUsuarios(),
      api.statsUsuarios(),
    ]);
    usuarios.value = u;
    stats.value = s;
  } catch (e) {
    error.value = e.response?.data?.detail || e.message;
  } finally {
    cargando.value = false;
  }
}
onMounted(cargar);

const filtrados = computed(() => {
  const q = filtroTexto.value.trim().toLowerCase();
  return usuarios.value.filter((u) => {
    if (filtroRol.value !== "todos" && u.role !== filtroRol.value) return false;
    if (q && !`${u.nombre} ${u.apellido} ${u.email}`.toLowerCase().includes(q))
      return false;
    return true;
  });
});

const rolChip = {
  estudiante: "chip-brand",
  psicologo: "chip-mint",
  admin: "chip-peach",
};

function fechaCorta(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
</script>

<template>
  <div class="page-shell-wide">
    <PageHeader
      title="Usuarios"
      accent="del sistema"
      subtitle="Estudiantes, psicólogos y administradores."
      tone="brand"
    />

    <!-- Stats -->
    <section v-if="stats" class="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-6">
      <StatCard label="Total" :value="stats.total" tone="brand" />
      <StatCard label="Estudiantes" :value="stats.estudiantes" tone="sky2" />
      <StatCard label="Psicólogos" :value="stats.psicologos" tone="mint" />
      <StatCard label="Admins" :value="stats.admins" tone="peach" />
      <StatCard label="Inactivos" :value="stats.inactivos" tone="brand" />
    </section>

    <!-- Filtros -->
    <div class="flex flex-wrap items-center gap-3 mb-4 fade-in-up">
      <div
        class="flex gap-1 bg-white rounded-xl p-1 border border-ink-100 shadow-soft"
      >
        <button
          v-for="op in ['todos', 'estudiante', 'psicologo', 'admin']"
          :key="op"
          @click="filtroRol = op"
          :class="[
            'px-3 py-1.5 text-sm rounded-xl transition capitalize',
            filtroRol === op
              ? 'bg-green-600 text-white shadow-soft'
              : 'text-ink-600 hover:bg-green-50',
          ]"
        >
          {{ op === "todos" ? "Todos" : op + "s" }}
        </button>
      </div>
      <input
        v-model="filtroTexto"
        type="text"
        placeholder="Buscar nombre o correo"
        class="input flex-1 min-w-[220px]"
      />
    </div>

    <p v-if="cargando" class="text-center text-ink-500 py-12">
      Cargando usuarios…
    </p>
    <p v-else-if="error" class="banner-danger">{{ error }}</p>
    <p
      v-else-if="filtrados.length === 0"
      class="text-center text-ink-500 py-12"
    >
      No encontramos a nadie con esos filtros.
    </p>

    <div v-else class="card overflow-hidden fade-in-up">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead
            class="bg-white text-ink-500 text-left text-xs uppercase tracking-wider"
          >
            <tr>
              <th class="px-5 py-3">Usuario</th>
              <th class="px-5 py-3">Correo</th>
              <th class="px-5 py-3">Rol</th>
              <th class="px-5 py-3">Estado</th>
              <th class="px-5 py-3">Registrado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-ink-100">
            <tr
              v-for="u in filtrados"
              :key="u.id"
              class="hover:bg-green-50/50 transition"
            >
              <td class="px-5 py-3">
                <div class="flex items-center gap-3">
                  <div class="avatar-sm">
                    {{ (u.nombre[0] + (u.apellido[0] || "")).toUpperCase() }}
                  </div>
                  <p class="font-semibold text-ink-900">
                    {{ u.nombre }} {{ u.apellido }}
                  </p>
                </div>
              </td>
              <td class="px-5 py-3 text-ink-600 font-mono text-xs">
                {{ u.email }}
              </td>
              <td class="px-5 py-3">
                <span
                  :class="rolChip[u.role] || 'chip-ink'"
                  class="capitalize"
                  >{{ u.role }}</span
                >
              </td>
              <td class="px-5 py-3">
                <span
                  v-if="u.activo"
                  class="text-green-600 text-xs font-semibold inline-flex items-center gap-1"
                >
                  Activo
                </span>
                <span
                  v-else
                  class="text-ink-400 text-xs font-semibold inline-flex items-center gap-1"
                >
                  Inactivo
                </span>
              </td>
              <td class="px-5 py-3 text-ink-600">
                {{ fechaCorta(u.created_at) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
