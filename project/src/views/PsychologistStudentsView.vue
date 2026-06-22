<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import StudentTable from "../components/StudentTable.vue";

const students = ref([]);
const q = ref("");
const cargando = ref(true);

onMounted(async () => {
  try {
    students.value = await api.resumenEstudiantes();
  } catch (_) {
    students.value = [];
  } finally {
    cargando.value = false;
  }
});

const filtrados = computed(() => {
  const term = q.value.trim().toLowerCase();
  if (!term) return students.value;
  return students.value.filter(
    (s) =>
      (s.name || "").toLowerCase().includes(term) ||
      (s.carrera || "").toLowerCase().includes(term),
  );
});
</script>

<template>
  <div class="page" data-screen-label="Estudiantes">
    <div class="page-inner" style="max-width: 920px">
      <h1>Estudiantes</h1>
      <p class="sub">
        {{ students.length }}
        {{ students.length === 1 ? "estudiante a tu cargo" : "estudiantes a tu cargo" }}.
        Ordenados por nivel de riesgo.
      </p>

      <div class="field" style="max-width: 320px; margin-bottom: 18px">
        <input
          v-model="q"
          placeholder="Buscar por nombre o carrera…"
          type="search"
        />
      </div>

      <div v-if="cargando" style="padding: 40px 0; color: var(--ink-3); text-align: center">
        Cargando…
      </div>
      <div v-else class="panel-card">
        <StudentTable :students="filtrados" />
      </div>
    </div>
  </div>
</template>
