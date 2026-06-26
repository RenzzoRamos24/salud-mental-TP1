<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "../api";

const stats = ref(null);
const usuarios = ref([]);
const cargando = ref(true);
const error = ref("");
const filtroRol = ref("");
const procesando = ref(null);

async function cargar() {
  cargando.value = true;
  try {
    const [s, u] = await Promise.all([
      api.statsUsuarios(),
      api.listarUsuarios(),
    ]);
    stats.value = s;
    usuarios.value = u;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const psicologas = computed(() =>
  usuarios.value.filter((u) => u.role === "psicologo" && u.activo),
);

const estudiantes = computed(() =>
  usuarios.value.filter((u) => u.role === "estudiante"),
);

const filtrados = computed(() => {
  if (!filtroRol.value) return usuarios.value;
  return usuarios.value.filter((u) => u.role === filtroRol.value);
});

async function asignarPsico(est, psicologo_id) {
  procesando.value = est.id;
  try {
    await api.asignarPsicologo(est.id, psicologo_id || null);
    est.psicologo_id = psicologo_id || null;
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo asignar.");
  } finally {
    procesando.value = null;
  }
}

function nombrePsico(id) {
  if (!id) return "Sin asignar";
  const p = psicologas.value.find((x) => x.id === id);
  return p ? `${p.nombre} ${p.apellido}` : id;
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Administración</p>
      <h1 class="hero-serif text-[28px]">
        Gestión de <span class="hero-mint">usuarios</span>
      </h1>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <div class="grid sm:grid-cols-4 gap-3 mb-6">
        <div class="card p-4">
          <p class="text-xs text-ink-400">Total</p>
          <p class="text-2xl font-semibold">{{ stats?.total || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Estudiantes</p>
          <p class="text-2xl font-semibold">{{ stats?.estudiantes || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Psicólogas</p>
          <p class="text-2xl font-semibold">{{ stats?.psicologos || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Admins</p>
          <p class="text-2xl font-semibold">{{ stats?.admins || 0 }}</p>
        </div>
      </div>

      <!-- ── Asignación estudiante ↔ psicóloga ────────────────────── -->
      <h2 class="text-lg font-semibold mb-3">
        Asignar estudiantes a psicólogas
      </h2>
      <p class="text-xs text-ink-500 mb-3">
        Cada estudiante puede tener una psicóloga responsable. Las alertas y
        SOS llegan a ella primero.
      </p>
      <div v-if="estudiantes.length === 0" class="card p-6 text-ink-500 mb-8">
        No hay estudiantes registrados todavía.
      </div>
      <div v-else class="card p-2 mb-8 overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs text-ink-400 border-b border-cream-200">
              <th class="p-2">Estudiante</th>
              <th class="p-2">Email</th>
              <th class="p-2">Psicóloga asignada</th>
              <th class="p-2"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="e in estudiantes"
              :key="e.id"
              class="border-b border-cream-100"
            >
              <td class="p-2 font-medium">{{ e.nombre }} {{ e.apellido }}</td>
              <td class="p-2 text-xs text-ink-500">{{ e.email }}</td>
              <td class="p-2 text-xs text-ink-500">
                {{ nombrePsico(e.psicologo_id) }}
              </td>
              <td class="p-2">
                <select
                  class="input text-sm"
                  :value="e.psicologo_id || ''"
                  :disabled="procesando === e.id"
                  @change="asignarPsico(e, $event.target.value)"
                >
                  <option value="">Sin asignar</option>
                  <option
                    v-for="p in psicologas"
                    :key="p.id"
                    :value="p.id"
                  >
                    {{ p.nombre }} {{ p.apellido }}
                  </option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── Lista total de usuarios ─────────────────────────────── -->
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-lg font-semibold">Todos los usuarios</h2>
        <select v-model="filtroRol" class="input text-sm" style="width: 200px">
          <option value="">Todos los roles</option>
          <option value="estudiante">Estudiantes</option>
          <option value="psicologo">Psicólogas</option>
          <option value="admin">Administradores</option>
        </select>
      </div>
      <div class="grid gap-2">
        <div
          v-for="u in filtrados"
          :key="u.id"
          class="card p-3 flex items-center justify-between text-sm"
        >
          <div>
            <p class="font-semibold">{{ u.nombre }} {{ u.apellido }}</p>
            <p class="text-xs text-ink-500">{{ u.email }}</p>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span class="chip-mint">{{ u.role }}</span>
            <span
              v-if="u.activo"
              class="px-2 py-0.5 rounded-full bg-green-50 text-green-700 border border-green-200"
            >
              activo
            </span>
            <span
              v-else
              class="px-2 py-0.5 rounded-full bg-gray-50 text-gray-700 border border-gray-200"
            >
              inactivo
            </span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
