<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { authStore } from "../store/auth";
import { api } from "../api";
import {
  buildAlerts,
  riesgoEstudiante,
} from "../composables/samiPsicoHelpers";
import { fmtLong, todayIso } from "../composables/samiHelpers";
import StudentTable from "../components/StudentTable.vue";
import AlertRow from "../components/AlertRow.vue";

const router = useRouter();

const students = ref([]);
const cargando = ref(true);

const primerNombre = computed(() => {
  const u = authStore.state.user;
  if (!u) return "";
  // Prioriza apellido (Dra. Lucía Carrasco → Carrasco) cuando existe.
  return (u.apellido || u.nombre || "").trim().split(" ")[0] || "";
});

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

function diasEntre(a, b) {
  return Math.round(
    (new Date(b + "T00:00:00") - new Date(a + "T00:00:00")) / 86400000,
  );
}

const cerradosSemana = computed(() => {
  const hoy = todayIso();
  return students.value.filter((s) => {
    const last = s.cycles?.[s.cycles.length - 1];
    if (!last || last.encurso) return false;
    return diasEntre(last.end, hoy) <= 7;
  }).length;
});

const enCurso = computed(
  () =>
    students.value.filter(
      (s) => s.cycles?.[s.cycles.length - 1]?.encurso,
    ).length,
);

const tiles = computed(() => [
  { n: students.value.length, l: "Estudiantes a tu cargo" },
  {
    n: criticas.value,
    l: "Alertas que requieren atención",
    alarm: criticas.value > 0,
  },
  { n: cerradosSemana.value, l: "Ciclos cerrados esta semana" },
  { n: enCurso.value, l: "Ciclos en curso" },
]);

const primeros4Alertas = computed(() => alertas.value.slice(0, 4));
// Ordenar por riesgo antes de mostrar los primeros 4 en el dashboard
const primeros4Estudiantes = computed(() =>
  [...students.value]
    .sort((a, b) => riesgoEstudiante(b).rank - riesgoEstudiante(a).rank)
    .slice(0, 4),
);
</script>

<template>
  <div class="page" data-screen-label="Panel clínico">
    <div class="page-inner" style="max-width: 920px">
      <p class="sub" style="margin-bottom: 2px">{{ fmtLong(todayIso()) }}</p>
      <h1>Hola, {{ primerNombre || "tú" }}</h1>
      <p class="sub">
        Esto es lo que pasó con tus estudiantes desde la última vez.
      </p>

      <div v-if="cargando" style="padding: 40px 0; color: var(--ink-3); text-align: center">
        Cargando…
      </div>

      <template v-else>
        <div class="tiles">
          <div
            v-for="(t, i) in tiles"
            :key="i"
            :class="'tile' + (t.alarm ? ' alarm' : '')"
          >
            <div class="n">{{ t.n }}</div>
            <div class="l">{{ t.l }}</div>
          </div>
        </div>

        <div class="panel-card" style="margin-bottom: 22px">
          <div
            class="section-h"
            style="
              padding: 14px 18px 12px;
              border-bottom: 1px solid var(--line-soft);
            "
          >
            <span>Requieren tu atención</span>
            <button class="more" type="button" @click="router.push('/psicologo/alertas')">
              Ver todas las alertas
            </button>
          </div>
          <div class="rowlist">
            <AlertRow v-for="(a, i) in primeros4Alertas" :key="i" :alert="a" />
            <p
              v-if="!primeros4Alertas.length"
              style="padding: 24px; font-size: 13px; color: var(--ink-3); text-align: center"
            >
              Sin alertas. Todos tus estudiantes están bien por ahora.
            </p>
          </div>
        </div>

        <div class="section-h">
          <span>Todos tus estudiantes</span>
          <button
            class="more"
            type="button"
            @click="router.push('/psicologo/estudiantes')"
          >
            Ver lista completa
          </button>
        </div>
        <div class="panel-card">
          <StudentTable :students="primeros4Estudiantes" />
        </div>
      </template>
    </div>
  </div>
</template>
