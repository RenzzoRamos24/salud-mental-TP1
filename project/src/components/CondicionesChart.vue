<script setup>
import { computed } from "vue";

const props = defineProps({
  cycles: { type: Array, required: true },
});

const CONDS = [
  { key: "depresion",        label: "Depresión"        },
  { key: "ansiedad",         label: "Ansiedad"         },
  { key: "estres_academico", label: "Estrés académico" },
  { key: "soledad",          label: "Soledad"          },
  { key: "tdah",             label: "TDAH"             },
  { key: "riesgo_suicida",   label: "Riesgo suicida"  },
];

function sevColor(avg) {
  if (avg >= 60) return "#E25555";
  if (avg >= 30) return "#E8B04B";
  return "#2BB673";
}

const rows = computed(() =>
  CONDS.map((c) => {
    const vals = props.cycles
      .map((cy) => cy.condiciones_beto?.[c.key] ?? null)
      .filter((v) => v !== null);
    const avg = vals.length
      ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length)
      : 0;
    return { ...c, avg, color: sevColor(avg) };
  }).sort((a, b) => b.avg - a.avg),
);
</script>

<template>
  <div class="cc-wrap">
    <div v-for="r in rows" :key="r.key" class="cc-row">
      <div class="cc-label">{{ r.label }}</div>
      <div class="cc-track">
        <div class="cc-fill" :style="{ width: r.avg + '%', background: r.color }"></div>
      </div>
      <div class="cc-pct" :style="{ color: r.color }">{{ r.avg }}%</div>
    </div>
    <p v-if="!rows.length" style="font-size:12px;color:#9ca3af;text-align:center;padding:16px 0">
      Sin análisis disponible
    </p>
  </div>
</template>

<style scoped>
.cc-wrap { display: flex; flex-direction: column; gap: 10px; }

.cc-row {
  display: grid;
  grid-template-columns: 110px 1fr 38px;
  align-items: center;
  gap: 10px;
}
.cc-label { font-size: 12.5px; font-weight: 500; color: #374151; white-space: nowrap; }
.cc-track {
  height: 12px;
  background: #EEF3F2;
  border-radius: 99px;
  overflow: hidden;
}
.cc-fill {
  height: 100%;
  border-radius: 99px;
  transition: width .5s ease;
}
.cc-pct { font-size: 12px; font-weight: 700; text-align: right; }
</style>
