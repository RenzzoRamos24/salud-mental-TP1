<script setup>
import { computed } from "vue";

// Gráfico de línea escalable: funciona igual para C1–C3 que para C1–C20.
// Los puntos se colorean por severidad; solo se etiquetan el primero,
// el último y los ciclos con crisis. No hay columnas que se amontonan.
const props = defineProps({
  cycles:    { type: Array,  required: true },
  metricKey: { type: String, required: true },
  max:       { type: Number, required: true },
  bands:     { type: Array,  default: () => [] },
});

const W = 280, H = 110;
const PL = 10, PR = 10, PT = 22, PB = 20;
const IW = W - PL - PR;
const IH = H - PT - PB;

function dotColor(val) {
  if (val <= 9)  return "#2BB673";
  if (val <= 14) return "#E8B04B";
  return "#E25555";
}

const n = computed(() => Math.max(props.cycles.length, 1));

function xOf(i) {
  if (props.cycles.length <= 1) return PL + IW / 2;
  return PL + (IW * i) / (props.cycles.length - 1);
}
function yOf(v) {
  return PT + IH - (IH * Math.min(v, props.max)) / props.max;
}

const pts = computed(() =>
  props.cycles.map((c, i) => ({
    x: xOf(i),
    y: yOf(c[props.metricKey] || 0),
    v: c[props.metricKey] || 0,
    n: c.n,
    crisis: c.crisis,
    color: dotColor(c[props.metricKey] || 0),
  })),
);

const linePath = computed(() =>
  pts.value.length < 2
    ? ""
    : pts.value.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" "),
);

// Etiqueta solo si: primer punto, último punto, o crisis
function showLabel(i) {
  return i === 0 || i === pts.value.length - 1 || pts.value[i].crisis;
}

// Etiqueta del eje X: solo mostrar cada cuántos ciclos según cantidad total
function showXLabel(i) {
  const total = props.cycles.length;
  if (total <= 6) return true;
  if (total <= 12) return i % 2 === 0;
  if (total <= 20) return i % 5 === 0 || i === total - 1;
  return i % 10 === 0 || i === total - 1;
}
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" style="width:100%;height:auto;display:block;overflow:visible">
    <!-- baseline -->
    <line :x1="PL" :x2="W-PR" :y1="PT+IH" :y2="PT+IH" stroke="#EEF3F2" stroke-width="1"/>
    <!-- max reference -->
    <line :x1="PL" :x2="W-PR" :y1="PT" :y2="PT" stroke="#EEF3F2" stroke-width="1" stroke-dasharray="3,3"/>
    <text :x="PL" :y="PT-4" font-size="8" fill="#9DB2AE">{{ max }}</text>
    <text :x="PL" :y="PT+IH+10" font-size="8" fill="#9DB2AE">0</text>

    <!-- area fill bajo la línea -->
    <path
      v-if="linePath"
      :d="`${linePath} L${pts[pts.length-1].x.toFixed(1)} ${PT+IH} L${pts[0].x.toFixed(1)} ${PT+IH} Z`"
      fill="url(#areaGrad)" opacity="0.18"
    />
    <defs>
      <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#0D9488"/>
        <stop offset="100%" stop-color="#0D9488" stop-opacity="0"/>
      </linearGradient>
    </defs>

    <!-- línea de tendencia -->
    <path v-if="linePath" :d="linePath" fill="none" stroke="#0D9488"
          stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>

    <!-- puntos -->
    <g v-for="(p, i) in pts" :key="p.n">
      <circle :cx="p.x" :cy="p.y" r="5" fill="#fff" :stroke="p.color" stroke-width="2.5"/>
      <!-- punto crisis: icono -->
      <circle v-if="p.crisis" :cx="p.x" :cy="p.y" r="7" fill="none" stroke="#ef4444"
              stroke-width="1.5" stroke-dasharray="2,2"/>

      <!-- score label: solo 1º, último y crisis -->
      <text v-if="showLabel(i)"
            :x="p.x" :y="p.y - 9"
            text-anchor="middle" font-size="11" font-weight="800" :fill="p.color">
        {{ p.v }}
      </text>

      <!-- etiqueta C{n} en eje X -->
      <text v-if="showXLabel(i)"
            :x="p.x" :y="H - 3"
            text-anchor="middle" font-size="8.5" fill="#9DB2AE">
        C{{ p.n }}
      </text>
    </g>

    <text v-if="!cycles.length" x="140" y="60" text-anchor="middle" font-size="11" fill="#9DB2AE">
      Sin ciclos
    </text>
  </svg>
</template>
