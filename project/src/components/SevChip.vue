<script setup>
const props = defineProps({ nivel: { type: String, default: 'Mínima' } });
const MAP = {
  'Mínima':          { color: '#2BB673', bg: '#E8F8EF' },
  'Leve':            { color: '#2BB673', bg: '#E8F8EF' },
  'Leve o mínima':   { color: '#2BB673', bg: '#E8F8EF' },
  'Moderada':        { color: '#E8B04B', bg: '#FDF4E1' },
  'Moderada-severa': { color: '#E25555', bg: '#FDEAEA' },
  'Severa':          { color: '#E25555', bg: '#FDEAEA' },
  'Sin datos':       { color: '#9DB2AE', bg: '#F1F5F4' },
  'Crisis':          { color: '#E25555', bg: '#FDEAEA' },
};
function sev() { return MAP[props.nivel] || MAP['Sin datos']; }
</script>

<template>
  <span class="sev-chip" :style="{ background: sev().bg, color: sev().color }">
    <i :style="{ background: sev().color }"></i>{{ nivel }}
  </span>
</template>

<style scoped>
.sev-chip {
  display: inline-flex; align-items: center; gap: 5px;
  font-size: 11.5px; font-weight: 700; font-family: 'Hanken Grotesk', sans-serif;
  padding: 3px 10px 3px 8px; border-radius: 999px;
}
.sev-chip i {
  display: inline-block; width: 7px; height: 7px;
  border-radius: 50%; flex-shrink: 0;
}
</style>
