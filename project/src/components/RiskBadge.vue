<script setup>
defineProps({
  nivel: { type: String, default: null },
  score: { type: Number, default: null },
});

const classMap = {
  BAJO: "risk-bajo",
  MEDIO: "risk-medio",
  ALTO: "risk-alto",
  CRÍTICO: "risk-critico",
  CRITICO: "risk-critico",
};
</script>

<template>
  <span v-if="nivel" :class="classMap[nivel] || 'risk-sin'">
    <span>{{ nivel }}</span>
    <span v-if="score != null" class="opacity-70 tabular"
      >· {{ (score * 100).toFixed(0) }}%</span
    >
  </span>
  <span v-else class="risk-sin">Sin evaluar</span>
</template>
