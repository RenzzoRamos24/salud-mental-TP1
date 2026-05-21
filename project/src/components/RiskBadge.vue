<script setup>
const props = defineProps({
  nivel: { type: String, default: null }, // BAJO | MEDIO | ALTO | CRÍTICO | null
  score: { type: Number, default: null },
});

const classMap = {
  BAJO: "risk-bajo",
  MEDIO: "risk-medio",
  ALTO: "risk-alto",
  CRÍTICO: "risk-critico",
  CRITICO: "risk-critico",
};
const iconMap = {
  BAJO: "",
  MEDIO: "",
  ALTO: "",
  CRÍTICO: "",
  CRITICO: "",
};
</script>

<template>
  <span v-if="nivel" :class="classMap[nivel] || 'risk-sin'">
    <span>{{ iconMap[nivel] || "•" }}</span>
    <span>{{ nivel }}</span>
    <span v-if="score != null" class="opacity-70"
      >· {{ (score * 100).toFixed(0) }}%</span
    >
  </span>
  <span v-else class="risk-sin">
    <span>—</span>
    <span>Sin evaluación</span>
  </span>
</template>
