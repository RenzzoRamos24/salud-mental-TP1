<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import {
  riesgoEstudiante,
  tendencia,
  avatarColor,
} from "../composables/samiPsicoHelpers";
import SevChip from "./SevChip.vue";

const props = defineProps({
  students: { type: Array, required: true },
});

const router = useRouter();

const ordenados = computed(() =>
  [...props.students].sort(
    (a, b) => riesgoEstudiante(b).rank - riesgoEstudiante(a).rank,
  ),
);

function abrir(id) {
  router.push(`/psicologo/estudiante/${id}`);
}

// Ciclo de referencia: el cerrado con mayor puntaje (mayor confiabilidad clínica)
function refCiclo(s) {
  const cerrados = (s.cycles || []).filter((c) => !c.encurso && c.dias > 0);
  if (!cerrados.length) return s.cycles?.[s.cycles.length - 1] || {};
  return cerrados.reduce((b, c) =>
    (c.phqa || 0) + (c.gad7 || 0) > (b.phqa || 0) + (b.gad7 || 0) ? c : b,
  );
}
</script>

<template>
  <div class="list-head">
    <span></span><span>Estudiante</span><span>PHQ-A</span><span>GAD-7</span
    ><span>Estado</span><span></span>
  </div>
  <div class="rowlist">
    <button
      v-for="s in ordenados"
      :key="s.id"
      class="stu-row"
      type="button"
      @click="abrir(s.id)"
    >
      <span class="avatar" :style="{ background: avatarColor(s.id) }">
        {{ s.initials }}
      </span>
      <span>
        <span class="name">{{ s.name }}</span>
        <span class="meta-sm"
          >{{ s.carrera || "—" }}{{ s.anio ? " · " + s.anio : "" }}</span
        >
      </span>
      <span class="score-cell">
        <span class="big">{{ refCiclo(s).phqa ?? "—" }}</span>
        <span class="cap"> /27</span>
      </span>
      <span class="score-cell">
        <span class="big">{{ refCiclo(s).gad7 ?? "—" }}</span>
        <span class="cap"> /21</span>
      </span>
      <span
        style="display: flex; flex-direction: column; gap: 4px; align-items: flex-start"
      >
        <span v-if="refCiclo(s).crisis" class="crisis-flag">
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M12 9v4M12 17h.01" />
            <path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
          </svg>
          Crisis
        </span>
        <SevChip v-else :nivel="riesgoEstudiante(s).label" />
        <span :class="'trend ' + tendencia(s).dir">
          {{
            tendencia(s).dir === "up"
              ? "↑"
              : tendencia(s).dir === "down"
                ? "↓"
                : "→"
          }}
          {{ tendencia(s).txt }}
        </span>
      </span>
      <span class="chev">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M9 6l6 6-6 6" />
        </svg>
      </span>
    </button>
    <p
      v-if="!ordenados.length"
      style="padding: 24px; font-size: 13px; color: var(--ink-3); text-align: center"
    >
      Sin resultados.
    </p>
  </div>
</template>
