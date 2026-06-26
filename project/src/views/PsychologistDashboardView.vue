<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";

const router = useRouter();

const stats = ref(null);
const estudiantes = ref([]);
const cargando = ref(true);
const error = ref("");

async function cargar() {
  cargando.value = true;
  try {
    const [s, e] = await Promise.all([
      api.dashboardStats(),
      api.listarEstudiantes(),
    ]);
    stats.value = s;
    estudiantes.value = e;
  } catch (err) {
    error.value = err?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

// ─── KPIs ─────────────────────────────────────────────────────────────
const totalEstudiantes = computed(() => estudiantes.value.length);
const totalEvaluados = computed(
  () => estudiantes.value.filter((e) => e.total_cuestionarios > 0).length,
);
const totalAsignados = computed(
  () => stats.value?.total_cuestionarios_asignados || 0,
);
const totalCompletados = computed(
  () => stats.value?.total_cuestionarios_completados || 0,
);
const tasaCompletitud = computed(() => {
  if (!totalAsignados.value) return 0;
  return Math.round((totalCompletados.value / totalAsignados.value) * 100);
});

// ─── Rango de fechas (display, no implementado backend aún) ──────────
const rangoFechas = computed(() => {
  const hoy = new Date();
  const hace30 = new Date(hoy.getTime() - 30 * 86400000);
  const fmt = (d) =>
    `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}/${d.getFullYear()}`;
  return `${fmt(hace30)} - ${fmt(hoy)}`;
});

// ─── Distribución por nivel (datos reales del backend) ──────────────
// Antes mostrábamos "5 áreas clínicas" con datos inventados (0,0,0,0). El
// backend no expone conteo por escala (PHQ-A/GAD-7/etc.) en este endpoint;
// solo tenemos `ultimo_riesgo` por estudiante. Hasta que añadamos el detalle
// por escala, esta tarjeta muestra distribución por nivel global, que sí es
// dato verificable del backend.
const nivelesCard = computed(() => {
  const total = estudiantes.value.length || 1;
  const por = (k) =>
    estudiantes.value.filter(
      (e) => (e.ultimo_riesgo || "").toUpperCase().replace("Í", "I") === k,
    ).length;
  const sinEval = estudiantes.value.filter(
    (e) =>
      !e.ultimo_riesgo ||
      (e.ultimo_riesgo || "").toUpperCase() === "SIN_EVALUACION",
  ).length;
  const counts = {
    CRITICO: por("CRITICO"),
    ALTO: por("ALTO"),
    MEDIO: por("MEDIO"),
    BAJO: por("BAJO"),
    SIN_RIESGO: por("SIN_RIESGO"),
  };
  return [
    { codigo: "CRITICO", nombre: "Crítico", color: "#DC2626", count: counts.CRITICO, icon: iconAlertTri() },
    { codigo: "ALTO", nombre: "Alto", color: "#F97316", count: counts.ALTO, icon: iconAlertOctagon() },
    { codigo: "MEDIO", nombre: "Medio", color: "#F59E0B", count: counts.MEDIO, icon: iconActivity() },
    { codigo: "BAJO", nombre: "Bajo", color: "#0EA5E9", count: counts.BAJO, icon: iconPulse() },
    { codigo: "SIN_RIESGO", nombre: "Sin riesgo", color: "#1aa896", count: counts.SIN_RIESGO, icon: iconShield() },
  ];
});

// ─── Indicadores (Depresión / Bienestar / Ansiedad) ──────────────────
const indicadores = computed(() => {
  const total = Math.max(estudiantes.value.length, 1);
  const sinRiesgo = estudiantes.value.filter((e) => {
    const r = (e.ultimo_riesgo || "").toUpperCase();
    return r === "SIN_RIESGO";
  }).length;
  const enAlerta = estudiantes.value.filter((e) => {
    const r = (e.ultimo_riesgo || "").toUpperCase().replace("Í", "I");
    return ["CRITICO", "ALTO", "MEDIO"].includes(r);
  }).length;

  return {
    depresion: Math.round((enAlerta / total) * 100),
    bienestar: Math.round((sinRiesgo / total) * 100),
    ansiedad: Math.round((enAlerta / total) * 100),
  };
});

// ─── Distribución por riesgo (donut) ─────────────────────────────────
const NIVELES = [
  { key: "CRITICO", label: "Crítico", color: "#DC2626" },
  { key: "ALTO", label: "Alto", color: "#F97316" },
  { key: "MEDIO", label: "Medio", color: "#F59E0B" },
  { key: "BAJO", label: "Bajo", color: "#0EA5E9" },
  { key: "SIN_RIESGO", label: "Sin riesgo", color: "#1aa896" },
  { key: "SIN_EVAL", label: "Sin evaluar", color: "#cbd5d8" },
];

const distribucion = computed(() => {
  const conteo = Object.fromEntries(NIVELES.map((n) => [n.key, 0]));
  estudiantes.value.forEach((e) => {
    const r = (e.ultimo_riesgo || "").toUpperCase().replace("Í", "I");
    if (r in conteo) conteo[r]++;
    else conteo.SIN_EVAL++;
  });
  return NIVELES.map((n) => ({ ...n, count: conteo[n.key] }));
});

const totalDist = computed(() =>
  distribucion.value.reduce((s, n) => s + n.count, 0),
);

const arcosDonut = computed(() => {
  const R = 62;
  const STROKE = 22;
  const C = 2 * Math.PI * R;
  let offset = 0;
  return distribucion.value
    .filter((n) => n.count > 0)
    .map((n) => {
      const pct = n.count / Math.max(totalDist.value, 1);
      const len = C * pct;
      const arc = {
        ...n,
        r: R,
        c: C,
        stroke: STROKE,
        dash: `${len} ${C - len}`,
        offset: -offset,
        pct: Math.round(pct * 100),
      };
      offset += len;
      return arc;
    });
});

// ─── Gauge SVG calc ──────────────────────────────────────────────────
function dashArray(pct, r = 22) {
  const c = 2 * Math.PI * r;
  return { c, off: c * (1 - pct / 100) };
}

// ─── Bar chart: evaluaciones completadas por mes (últimos 12) ────────
const barras = computed(() => {
  const hoy = new Date();
  const buckets = new Array(12).fill(0);
  estudiantes.value.forEach((e) => {
    if (!e.ultima_evaluacion) return;
    const d = new Date(e.ultima_evaluacion);
    const diffMonths =
      (hoy.getFullYear() - d.getFullYear()) * 12 +
      (hoy.getMonth() - d.getMonth());
    if (diffMonths >= 0 && diffMonths < 12) {
      buckets[11 - diffMonths] += 1;
    }
  });
  return buckets.map((b, i) => ({ h: b, label: monthLabel(i) }));
});

const sinDatosBarras = computed(() => barras.value.every((b) => b.h === 0));

// Escala adaptativa: 1→5, 5→5, 6→10, 11→15, etc. Y al menos 4 ticks.
const maxBarra = computed(() => {
  const max = Math.max(...barras.value.map((b) => b.h));
  if (max <= 4) return 4;
  return Math.ceil(max / 5) * 5;
});

const ticksY = computed(() => {
  const max = maxBarra.value;
  const step = max <= 4 ? 1 : Math.ceil(max / 4);
  const arr = [];
  for (let v = max; v >= 0; v -= step) arr.push(v);
  if (arr[arr.length - 1] !== 0) arr.push(0);
  return arr;
});

const totalEvalsAnio = computed(() =>
  barras.value.reduce((s, b) => s + b.h, 0),
);
const promedioMensual = computed(() => {
  const mesesActivos = barras.value.filter((b) => b.h > 0).length;
  if (!mesesActivos) return 0;
  return (totalEvalsAnio.value / mesesActivos).toFixed(1);
});

function monthLabel(idx) {
  const hoy = new Date();
  const d = new Date(hoy.getFullYear(), hoy.getMonth() - (11 - idx), 1);
  return d.toLocaleString("es-PE", { month: "short" });
}

// ─── Tabla "Últimas evaluaciones" ────────────────────────────────────
const ultimasEvals = computed(() =>
  estudiantes.value
    .filter((e) => e.ultima_evaluacion)
    .sort((a, b) =>
      (b.ultima_evaluacion || "").localeCompare(a.ultima_evaluacion || ""),
    )
    .slice(0, 5),
);

function iniciales(e) {
  return ((e.nombre || "·").charAt(0) + (e.apellido || "").charAt(0)).toUpperCase();
}

function fmtFecha(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("es-PE", { day: "2-digit", month: "short" });
}

function chipRiesgo(r) {
  const k = (r || "").toUpperCase().replace("Í", "I");
  return (
    {
      CRITICO: { label: "Crítico", bg: "#FEF2F2", fg: "#B91C1C", bd: "#FECACA" },
      ALTO: { label: "Alto", bg: "#FFF7ED", fg: "#C2410C", bd: "#FED7AA" },
      MEDIO: { label: "Medio", bg: "#FFFBEB", fg: "#B45309", bd: "#FDE68A" },
      BAJO: { label: "Bajo", bg: "#F0F9FF", fg: "#0369A1", bd: "#BAE6FD" },
      SIN_RIESGO: { label: "Sin riesgo", bg: "#e3f3ef", fg: "#0e8d7e", bd: "#c5e1dc" },
    }[k] || { label: "Sin evaluar", bg: "#F4F5F6", fg: "#6B7280", bd: "#E5E7EB" }
  );
}

function verAlumno(e) {
  router.push({ name: "psicologo-estudiante", params: { id: e.id } });
}

// ─── Iconos por nivel ─────────────────────────────────────────────────
function iconAlertTri() {
  return `<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>`;
}
function iconAlertOctagon() {
  return `<polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>`;
}
function iconActivity() {
  return `<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>`;
}
function iconPulse() {
  return `<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>`;
}
function iconShield() {
  return `<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/>`;
}
</script>

<template>
  <!-- breadcrumb row -->
  <div class="apollo-breadcrumb">
    <div class="apollo-breadcrumb__path">
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="#0e8d7e"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M3 11l9-7 9 7M5 10v10h14V10" />
      </svg>
      <span class="apollo-breadcrumb__sep">/</span>
      <span class="apollo-breadcrumb__current">Panel clínico</span>
    </div>
    <div class="apollo-datepicker">
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="#0e8d7e"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect x="3" y="4" width="18" height="17" rx="2" />
        <path d="M3 9h18M8 2v4M16 2v4" />
      </svg>
      {{ rangoFechas }}
    </div>
  </div>

  <div v-if="cargando" class="apollo-loading">Cargando datos del colegio…</div>

  <div v-else-if="error" class="apollo-error">{{ error }}</div>

  <template v-else>
    <!-- main grid: left col (KPIs + Specialities) + right col (anatomy) -->
    <div class="apollo-grid">
      <!-- LEFT COLUMN -->
      <div class="apollo-grid__left">
        <!-- KPIs -->
        <div class="apollo-kpis">
          <!-- Estudiantes -->
          <div class="apollo-kpi">
            <div class="apollo-kpi__row">
              <div class="apollo-kpi__icon">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
                </svg>
              </div>
              <div>
                <div class="apollo-kpi__value">{{ totalEstudiantes }}</div>
                <div class="apollo-kpi__label">Estudiantes</div>
              </div>
            </div>
            <div class="apollo-kpi__foot">
              <a class="apollo-kpi__link" @click="router.push('/psicologo/estudiantes')">
                Ver todos
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </a>
              <div class="apollo-kpi__metrics">
                <div class="apollo-kpi__pct">{{ totalEvaluados }}/{{ totalEstudiantes }}</div>
                <div class="apollo-kpi__pill">evaluados</div>
              </div>
            </div>
          </div>

          <!-- Cuestionarios asignados -->
          <div class="apollo-kpi">
            <div class="apollo-kpi__row">
              <div class="apollo-kpi__icon">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <rect x="3" y="4" width="18" height="17" rx="2" />
                  <path d="M3 9h18M8 2v4M16 2v4" />
                </svg>
              </div>
              <div>
                <div class="apollo-kpi__value">{{ totalAsignados }}</div>
                <div class="apollo-kpi__label">Cuestionarios</div>
              </div>
            </div>
            <div class="apollo-kpi__foot">
              <a class="apollo-kpi__link" @click="router.push('/psicologo/asignar')">
                Asignar
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </a>
              <div class="apollo-kpi__metrics">
                <div class="apollo-kpi__pct">{{ totalCompletados }} completados</div>
                <div class="apollo-kpi__pill">este mes</div>
              </div>
            </div>
          </div>

          <!-- En seguimiento (Crítico + Alto + Medio) -->
          <div class="apollo-kpi">
            <div class="apollo-kpi__row">
              <div class="apollo-kpi__icon">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M12 9v4M12 17h0M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                </svg>
              </div>
              <div>
                <div class="apollo-kpi__value">{{ enRiesgo }}</div>
                <div class="apollo-kpi__label">En seguimiento</div>
              </div>
            </div>
            <div class="apollo-kpi__foot">
              <a class="apollo-kpi__link" @click="router.push('/psicologo/alertas')">
                Ver alertas
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </a>
              <div class="apollo-kpi__metrics">
                <div class="apollo-kpi__pct">
                  {{ estudiantes.length > 0 ? Math.round((enRiesgo / estudiantes.length) * 100) : 0 }}%
                </div>
                <div class="apollo-kpi__pill">del total</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Distribución por nivel (datos reales) -->
        <div class="apollo-card">
          <div class="apollo-card__title">Estudiantes por nivel de riesgo</div>
          <div class="apollo-specialities">
            <div
              v-for="esc in nivelesCard"
              :key="esc.codigo"
              class="apollo-speciality"
            >
              <div class="apollo-speciality__icon" :style="{ color: esc.color }">
                <svg
                  width="40"
                  height="40"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.6"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  v-html="esc.icon"
                />
              </div>
              <div class="apollo-speciality__name">{{ esc.nombre }}</div>
              <div class="apollo-speciality__count" :style="{ color: esc.color }">
                {{ esc.count }}
              </div>
              <div class="apollo-speciality__code">
                {{ esc.count === 1 ? "estudiante" : "estudiantes" }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT COLUMN: donut distribución + 3 gauges -->
      <div class="apollo-card apollo-anatomy">
        <div class="apollo-anatomy__title">Distribución del colegio</div>
        <div class="apollo-donut">
          <svg width="200" height="200" viewBox="0 0 200 200">
            <!-- track -->
            <circle
              cx="100"
              cy="100"
              r="62"
              fill="none"
              stroke="#eef1f2"
              stroke-width="22"
            />
            <!-- arcos -->
            <circle
              v-for="arc in arcosDonut"
              :key="arc.key"
              cx="100"
              cy="100"
              :r="arc.r"
              fill="none"
              :stroke="arc.color"
              :stroke-width="arc.stroke"
              :stroke-dasharray="arc.dash"
              :stroke-dashoffset="arc.offset"
              stroke-linecap="butt"
              transform="rotate(-90 100 100)"
            />
            <!-- centro -->
            <text
              x="100"
              y="95"
              text-anchor="middle"
              font-family="Figtree"
              font-size="34"
              font-weight="800"
              fill="#243239"
            >
              {{ totalDist }}
            </text>
            <text
              x="100"
              y="115"
              text-anchor="middle"
              font-family="Figtree"
              font-size="11"
              fill="#8b999e"
              letter-spacing="0.5"
            >
              ESTUDIANTES
            </text>
          </svg>
        </div>

        <div class="apollo-legend">
          <div
            v-for="n in distribucion.filter((x) => x.count > 0 || totalDist === 0).slice(0, 3)"
            :key="n.key"
            class="apollo-legend__item"
          >
            <span
              class="apollo-legend__dot"
              :style="{ background: n.color }"
            ></span>
            <span class="apollo-legend__label">{{ n.label }}</span>
            <span class="apollo-legend__count">{{ n.count }}</span>
          </div>
        </div>

        <div class="apollo-anatomy__divider"></div>

        <div class="apollo-anatomy__subtitle">Indicadores generales</div>
        <div class="apollo-anatomy__gauges">
          <div class="apollo-gauge">
            <div class="apollo-gauge__label">Depresión</div>
            <svg width="64" height="64" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r="22" fill="none" stroke="#eef1f2" stroke-width="7" />
              <circle
                cx="32"
                cy="32"
                r="22"
                fill="none"
                stroke="#0e8d7e"
                stroke-width="7"
                stroke-linecap="round"
                :stroke-dasharray="dashArray(indicadores.depresion).c"
                :stroke-dashoffset="dashArray(indicadores.depresion).off"
                transform="rotate(-90 32 32)"
              />
            </svg>
            <div class="apollo-gauge__value">{{ indicadores.depresion }}%</div>
          </div>
          <div class="apollo-gauge">
            <div class="apollo-gauge__label">Bienestar</div>
            <svg width="64" height="64" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r="22" fill="none" stroke="#eef1f2" stroke-width="7" />
              <circle
                cx="32"
                cy="32"
                r="22"
                fill="none"
                stroke="#ef4444"
                stroke-width="7"
                stroke-linecap="round"
                :stroke-dasharray="dashArray(indicadores.bienestar).c"
                :stroke-dashoffset="dashArray(indicadores.bienestar).off"
                transform="rotate(-90 32 32)"
              />
            </svg>
            <div class="apollo-gauge__value">{{ indicadores.bienestar }}%</div>
          </div>
          <div class="apollo-gauge">
            <div class="apollo-gauge__label">Ansiedad</div>
            <svg width="64" height="64" viewBox="0 0 64 64">
              <circle cx="32" cy="32" r="22" fill="none" stroke="#eef1f2" stroke-width="7" />
              <circle
                cx="32"
                cy="32"
                r="22"
                fill="none"
                stroke="#0e8d7e"
                stroke-width="7"
                stroke-linecap="round"
                :stroke-dasharray="dashArray(indicadores.ansiedad).c"
                :stroke-dashoffset="dashArray(indicadores.ansiedad).off"
                transform="rotate(-90 32 32)"
              />
            </svg>
            <div class="apollo-gauge__value">{{ indicadores.ansiedad }}%</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Evaluaciones completadas por mes -->
    <div class="apollo-card apollo-chart">
      <div class="apollo-chart__head">
        <div>
          <div class="apollo-card__title" style="margin-bottom: 4px">
            Evaluaciones completadas por mes
          </div>
          <p class="apollo-chart__subtitle">
            Cantidad de estudiantes que cerraron su último cuestionario en cada
            mes (últimos 12 meses).
          </p>
        </div>
        <div class="apollo-chart__resumen" v-if="!sinDatosBarras">
          <div class="apollo-chart__res-item">
            <span class="apollo-chart__res-num">{{ totalEvalsAnio }}</span>
            <span class="apollo-chart__res-lbl">total en 12 meses</span>
          </div>
          <div class="apollo-chart__res-item">
            <span class="apollo-chart__res-num">{{ promedioMensual }}</span>
            <span class="apollo-chart__res-lbl">promedio por mes activo</span>
          </div>
        </div>
      </div>

      <div v-if="sinDatosBarras" class="apollo-chart__empty">
        Sin cuestionarios respondidos aún. Las barras aparecerán cuando los
        alumnos completen sus evaluaciones.
      </div>

      <div v-else class="apollo-chart__area">
        <!-- Eje Y con valores -->
        <div class="apollo-chart__yaxis">
          <div
            v-for="t in ticksY"
            :key="t"
            class="apollo-chart__ytick"
          >
            <span class="apollo-chart__ynum">{{ t }}</span>
            <span class="apollo-chart__yline" :class="{ 'is-base': t === 0 }" />
          </div>
        </div>

        <div class="apollo-chart__bars">
          <div
            v-for="(b, i) in barras"
            :key="i"
            class="apollo-chart__col"
            :title="`${b.label} — ${b.h} ${b.h === 1 ? 'evaluación' : 'evaluaciones'}`"
          >
            <span
              v-if="b.h > 0"
              class="apollo-chart__bar-val"
              :style="{ bottom: (b.h / maxBarra) * 100 + '%' }"
            >
              {{ b.h }}
            </span>
            <div
              class="apollo-chart__bar"
              :class="{ 'apollo-chart__bar--dark': i >= barras.length - 3 }"
              :style="{ height: (b.h / maxBarra) * 100 + '%' }"
            />
            <div class="apollo-chart__label">{{ b.label }}</div>
          </div>
        </div>
      </div>

      <div v-if="!sinDatosBarras" class="apollo-chart__leyenda">
        <span class="apollo-chart__leg-sw apollo-chart__leg-sw--light"></span>
        <span>Meses anteriores</span>
        <span class="apollo-chart__leg-sw apollo-chart__leg-sw--dark"></span>
        <span>Últimos 3 meses</span>
      </div>
    </div>

    <!-- Últimas evaluaciones -->
    <div class="apollo-card apollo-table-card">
      <div class="apollo-card__title">Últimas evaluaciones</div>
      <div v-if="ultimasEvals.length === 0" class="apollo-empty">
        Aún no hay evaluaciones completadas. Asigna cuestionarios desde el banco para empezar.
      </div>
      <table v-else class="apollo-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Alumno</th>
            <th>Email</th>
            <th>Fecha</th>
            <th>Nivel</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(e, i) in ultimasEvals" :key="e.id">
            <td class="apollo-table__num">{{ i + 1 }}</td>
            <td>
              <div class="apollo-table__person">
                <span class="apollo-table__avatar">{{ iniciales(e) }}</span>
                <span>{{ e.nombre }} {{ e.apellido }}</span>
              </div>
            </td>
            <td class="apollo-table__muted">{{ e.email }}</td>
            <td class="apollo-table__muted">{{ fmtFecha(e.ultima_evaluacion) }}</td>
            <td>
              <span
                class="apollo-table__chip"
                :style="{
                  background: chipRiesgo(e.ultimo_riesgo).bg,
                  color: chipRiesgo(e.ultimo_riesgo).fg,
                  border: `1px solid ${chipRiesgo(e.ultimo_riesgo).bd}`,
                }"
              >
                {{ chipRiesgo(e.ultimo_riesgo).label }}
              </span>
            </td>
            <td class="apollo-table__action">
              <a class="apollo-link" @click="verAlumno(e)">Ver</a>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>
</template>

<style scoped>
/* Reset font para evitar herencia del Work Sans */
:deep(*),
:scope,
* {
  font-family: "Figtree", system-ui, sans-serif;
}

.apollo-breadcrumb {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}
.apollo-breadcrumb__path {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
}
.apollo-breadcrumb__sep {
  color: #9aa7ab;
}
.apollo-breadcrumb__current {
  color: #0e8d7e;
  font-weight: 700;
}
.apollo-datepicker {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border: 1px solid #e7ecec;
  border-radius: 12px;
  padding: 9px 14px;
  font-size: 14px;
  color: #33424a;
  font-weight: 500;
}

.apollo-loading,
.apollo-error,
.apollo-empty {
  background: #fff;
  border: 1px solid #eef1f2;
  border-radius: 18px;
  padding: 40px;
  text-align: center;
  color: #8b999e;
  font-size: 14px;
}
.apollo-error {
  color: #b91c1c;
  background: #fef2f2;
  border-color: #fecaca;
}

.apollo-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 32px;
  align-items: stretch;
}
.apollo-grid__left {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}
@media (max-width: 1100px) {
  .apollo-grid {
    grid-template-columns: 1fr;
  }
}

/* ── KPI cards ────────────────────────────────────────────── */
.apollo-kpis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.apollo-kpi {
  background: #fff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 6px 20px rgba(35, 80, 95, 0.05);
}
.apollo-kpi__row {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.apollo-kpi__icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 1.5px solid #d3e8e3;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 56px;
  color: #0e8d7e;
}
.apollo-kpi__value {
  font-size: 34px;
  font-weight: 800;
  color: #243239;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.apollo-kpi__label {
  margin-top: 6px;
  font-size: 14px;
  color: #8b999e;
}
.apollo-kpi__foot {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 20px;
}
.apollo-kpi__link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #0e8d7e;
  font-weight: 600;
  font-size: 14px;
  text-decoration: none;
  cursor: pointer;
}
.apollo-kpi__metrics {
  text-align: right;
}
.apollo-kpi__pct {
  color: #1aa896;
  font-weight: 700;
  font-size: 13px;
}
.apollo-kpi__pill {
  margin-top: 5px;
  background: #e3f3ef;
  color: #0e8d7e;
  font-weight: 600;
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 7px;
  display: inline-block;
}

/* ── Card común ───────────────────────────────────────────── */
.apollo-card {
  background: #fff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 6px 20px rgba(35, 80, 95, 0.05);
  overflow: hidden;
  min-width: 0;
}
.apollo-card__title {
  font-size: 18px;
  font-weight: 700;
  color: #243239;
  margin-bottom: 18px;
}

/* ── Specialities ─────────────────────────────────────────── */
.apollo-specialities {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}
.apollo-speciality {
  border: 1px solid #eef1f2;
  border-radius: 14px;
  padding: 20px 12px;
  text-align: center;
}
.apollo-speciality__icon {
  height: 54px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0e8d7e;
}
.apollo-speciality__name {
  margin-top: 10px;
  font-weight: 700;
  font-size: 15px;
  color: #33424a;
}
.apollo-speciality__count {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 800;
  color: #1aa896;
  font-variant-numeric: tabular-nums;
}
.apollo-speciality__code {
  margin-top: 4px;
  font-size: 11px;
  color: #8b999e;
  font-weight: 500;
}

/* ── Right column: donut + gauges ─────────────────────────── */
.apollo-anatomy {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 100%;
}
.apollo-anatomy__title {
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #0e8d7e;
  margin-bottom: 8px;
}
.apollo-anatomy__subtitle {
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #0e8d7e;
  margin-bottom: 14px;
}
.apollo-anatomy__divider {
  height: 1px;
  background: #eef1f2;
  margin: 16px 0;
}
.apollo-donut {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 0;
}
.apollo-legend {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 4px 0;
}
.apollo-legend__item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.apollo-legend__dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  flex: none;
}
.apollo-legend__label {
  flex: 1;
  color: #33424a;
  font-weight: 500;
}
.apollo-legend__count {
  color: #243239;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}
.apollo-anatomy__gauges {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding-top: 4px;
}
.apollo-gauge {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.apollo-gauge__label {
  font-size: 13px;
  color: #8b999e;
  margin-bottom: 4px;
}
.apollo-gauge__value {
  font-size: 12px;
  font-weight: 700;
  color: #33424a;
  font-variant-numeric: tabular-nums;
}

/* ── Bar chart ────────────────────────────────────────────── */
.apollo-chart {
  margin-top: 20px;
  padding: 22px 24px 16px;
}
.apollo-chart__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}
.apollo-chart__subtitle {
  font-size: 12.5px;
  color: #8b999e;
  margin: 0;
  max-width: 60ch;
  line-height: 1.45;
}
.apollo-chart__resumen {
  display: flex;
  gap: 18px;
  flex-shrink: 0;
}
.apollo-chart__res-item {
  display: flex;
  flex-direction: column;
  text-align: right;
  border-left: 1px solid #eef1f2;
  padding-left: 18px;
}
.apollo-chart__res-item:first-child {
  border-left: 0;
  padding-left: 0;
}
.apollo-chart__res-num {
  font-size: 20px;
  font-weight: 800;
  color: #243239;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.apollo-chart__res-lbl {
  font-size: 11px;
  color: #8b999e;
  margin-top: 4px;
}
.apollo-chart__empty {
  background: #f9fafa;
  border: 1px dashed #e7ecec;
  border-radius: 12px;
  padding: 40px 24px;
  text-align: center;
  font-size: 13px;
  color: #8b999e;
}
.apollo-chart__area {
  position: relative;
  height: 230px;
  padding-left: 36px;
}
.apollo-chart__yaxis {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 24px;
  width: 36px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.apollo-chart__ytick {
  position: relative;
  display: flex;
  align-items: center;
}
.apollo-chart__ynum {
  font-size: 10.5px;
  color: #8b999e;
  font-variant-numeric: tabular-nums;
  width: 24px;
  text-align: right;
  padding-right: 4px;
  background: #fff;
  position: relative;
  z-index: 1;
}
.apollo-chart__yline {
  position: absolute;
  left: 28px;
  right: -100vw;
  height: 0;
  border-top: 1px dashed #eef1f2;
}
.apollo-chart__yline.is-base {
  border-top: 1px solid #e7ecec;
}
.apollo-chart__bars {
  position: absolute;
  left: 36px;
  right: 0;
  top: 0;
  bottom: 24px;
  display: flex;
  align-items: flex-end;
  gap: 6px;
  padding: 0 4px;
}
.apollo-chart__col {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  height: 100%;
  position: relative;
}
.apollo-chart__bar {
  width: 60%;
  background: rgba(26, 168, 150, 0.32);
  border-radius: 5px 5px 0 0;
  transition: height 0.3s ease-out;
}
.apollo-chart__bar--dark {
  background: #1aa896;
}
.apollo-chart__bar-val {
  position: absolute;
  font-size: 11px;
  font-weight: 700;
  color: #0e8d7e;
  font-variant-numeric: tabular-nums;
  transform: translateY(-3px);
  pointer-events: none;
}
.apollo-chart__label {
  position: absolute;
  bottom: -22px;
  font-size: 10.5px;
  color: #8b999e;
  text-transform: capitalize;
}
.apollo-chart__leyenda {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  font-size: 11.5px;
  color: #667085;
}
.apollo-chart__leg-sw {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 3px;
  margin-left: 4px;
}
.apollo-chart__leg-sw:first-child {
  margin-left: 0;
}
.apollo-chart__leg-sw--light {
  background: rgba(26, 168, 150, 0.32);
}
.apollo-chart__leg-sw--dark {
  background: #1aa896;
}

/* ── Table ────────────────────────────────────────────────── */
.apollo-table-card {
  margin-top: 20px;
}
.apollo-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.apollo-table thead th {
  text-align: left;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #8b999e;
  padding: 0 12px 12px;
}
.apollo-table tbody tr {
  border-top: 1px solid #f4f7f7;
}
.apollo-table tbody td {
  padding: 12px;
  color: #33424a;
}
.apollo-table__num {
  color: #8b999e;
  font-variant-numeric: tabular-nums;
}
.apollo-table__person {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #243239;
}
.apollo-table__avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #22b8a6, #0e8d7e);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}
.apollo-table__muted {
  color: #8b999e;
}
.apollo-table__chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 700;
}
.apollo-table__action {
  text-align: right;
}
.apollo-link {
  color: #0e8d7e;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  text-decoration: none;
}

/* ── RESPONSIVE ── */
@media (max-width: 1200px) {
  .apollo-grid { grid-template-columns: 1fr; gap: 20px; }
  .apollo-specialities { grid-template-columns: repeat(3, 1fr); }
  .apollo-kpis { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 900px) {
  .apollo-kpis { grid-template-columns: 1fr; }
  .apollo-specialities { grid-template-columns: repeat(2, 1fr); }
  .apollo-anatomy__gauges { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .apollo-specialities { grid-template-columns: 1fr; }
}
</style>
