<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import { buildAlerts } from "../composables/samiPsicoHelpers";
import AlertRow from "../components/AlertRow.vue";

const students = ref([]);
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

const alertas = computed(() => buildAlerts(students.value));
const criticas = computed(
  () => alertas.value.filter((a) => a.tipo === "crit").length,
);
</script>

<template>
  <div class="page" data-screen-label="Alertas">
    <div class="page-inner" style="max-width: 720px">
      <h1>Alertas</h1>
      <p class="sub">
        {{ criticas }} {{ criticas === 1 ? "crítica" : "críticas" }} ·
        {{ alertas.length }} en total. Las más urgentes primero.
      </p>

      <div v-if="cargando" style="padding: 40px 0; color: var(--ink-3); text-align: center">
        Cargando…
      </div>
      <div v-else class="panel-card">
        <div class="rowlist">
          <AlertRow v-for="(a, i) in alertas" :key="i" :alert="a" />
          <p
            v-if="!alertas.length"
            style="padding: 28px; font-size: 13px; color: var(--ink-3); text-align: center"
          >
            Sin alertas activas.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
