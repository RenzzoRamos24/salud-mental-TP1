<script setup>
import { computed } from "vue";

const props = defineProps({
  cycles: { type: Array, required: true },
});

const MOODS = [
  { key: "soleado", label: "Bien",     color: "#2BB673", bg: "#E8F8EF" },
  { key: "mixto",   label: "Regular",  color: "#E8B04B", bg: "#FDF4E1" },
  { key: "nublado", label: "Bajo",     color: "#E8B04B", bg: "#FDF4E1" },
  { key: "lluvioso",label: "Muy bajo", color: "#E25555", bg: "#FDEAEA" },
];

const rows = computed(() =>
  props.cycles.map((c) => {
    const emojis = c.emojis || {};
    const total = Object.values(emojis).reduce((a, b) => a + b, 0) || 1;
    return {
      n: c.n,
      encurso: c.encurso,
      total,
      segments: MOODS.map((m) => ({
        ...m,
        count: emojis[m.key] || 0,
        pct: Math.round(((emojis[m.key] || 0) / total) * 100),
      })).filter((m) => m.count > 0),
    };
  }),
);
</script>

<template>
  <div class="mc-wrap">
    <div class="mc-legend">
      <span v-for="m in MOODS" :key="m.key" class="mc-leg-item">
        <i :style="{ background: m.color }"></i>{{ m.label }}
      </span>
    </div>

    <div v-for="r in rows" :key="r.n" class="mc-row">
      <span class="mc-cn">C{{ r.n }}<span v-if="r.encurso" style="color:#9ca3af;font-weight:400"> *</span></span>
      <div class="mc-bar">
        <div
          v-for="seg in r.segments"
          :key="seg.key"
          class="mc-seg"
          :style="{ width: seg.pct + '%', background: seg.color }"
          :title="`${seg.label}: ${seg.count} día${seg.count !== 1 ? 's' : ''}`"
        ></div>
        <div v-if="!r.segments.length" class="mc-seg" style="width:100%;background:#e5e7eb"></div>
      </div>
      <span class="mc-total">{{ r.total === 1 ? '1 d' : r.total + ' d' }}</span>
    </div>

    <p v-if="!rows.length" style="font-size:12px;color:#9ca3af;text-align:center;padding:16px 0">
      Sin datos de ánimo
    </p>
  </div>
</template>

<style scoped>
.mc-wrap { display: flex; flex-direction: column; gap: 10px; }

.mc-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  margin-bottom: 6px;
}
.mc-leg-item {
  display: flex; align-items: center; gap: 5px;
  font-size: 11.5px; color: #6b7280;
}
.mc-leg-item i {
  display: inline-block; width: 10px; height: 10px;
  border-radius: 3px; flex-shrink: 0;
}
.mc-row {
  display: grid;
  grid-template-columns: 28px 1fr 30px;
  align-items: center;
  gap: 10px;
}
.mc-cn { font-size: 11.5px; font-weight: 700; color: #374151; }
.mc-bar {
  height: 16px; border-radius: 99px; overflow: hidden;
  background: #f3f4f6; display: flex;
}
.mc-seg { height: 100%; transition: width .4s ease; }
.mc-total { font-size: 11px; color: #6b7280; text-align: right; }
</style>
