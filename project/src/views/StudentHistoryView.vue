<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";
import {
  avatarColor,
  nivelPhqa,
  nivelGad7,
  labelClinico,
  riesgoEstudiante,
  pHaceCuanto,
  pRango,
  pCorto,
  ITEMS_PHQA,
  ITEMS_GAD7,
  desglose,
} from "../composables/samiPsicoHelpers";
import SevChip from "../components/SevChip.vue";
import EvolChart from "../components/EvolChart.vue";
import CondicionesChart from "../components/CondicionesChart.vue";
import MoodChart from "../components/MoodChart.vue";

const route = useRoute();
const router = useRouter();
const studentId = computed(() => route.params.id);

const cargando = ref(true);
const student = ref(null);
const notas = ref([]);
const draft = ref("");
const abierto = ref(-1); // índice del ciclo abierto
const cicloDetalle = ref({}); // cache de detalle por número de ciclo
const toast = ref("");
let toastTimer = null;

function showToast(msg) {
  toast.value = msg;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (toast.value = ""), 2400);
}
onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
});

async function cargar() {
  cargando.value = true;
  try {
    const [overview, notasResp] = await Promise.all([
      api.resumenEstudiantes().catch(() => []),
      api.listarNotas(studentId.value).catch(() => []),
    ]);
    student.value =
      (overview || []).find((s) => String(s.id) === String(studentId.value)) ||
      null;
    notas.value = (notasResp || []).map((n) => ({
      id: n.id,
      fecha: (n.created_at || n.fecha || "").slice(0, 10),
      autor: n.autor_nombre || n.autor || "—",
      texto: n.texto,
      propia: true,
    }));
    // Abre el último ciclo CON datos por defecto (no el en-curso vacío)
    if (student.value?.cycles?.length) {
      const cycles = student.value.cycles;
      const conDatos = cycles.map((c, i) => ({ c, i })).filter(({ c }) => !c.encurso || c.dias > 0);
      abierto.value = conDatos.length ? conDatos[conDatos.length - 1].i : cycles.length - 1;
    }
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const last = computed(() => {
  const cs = student.value?.cycles || [];
  if (!cs.length) return null;
  // Preferir último ciclo cerrado con datos sobre el ciclo en curso vacío
  const conDatos = cs.filter((c) => !c.encurso || c.dias > 0);
  return conDatos[conDatos.length - 1] || cs[cs.length - 1];
});

const riesgo = computed(() =>
  student.value
    ? riesgoEstudiante(student.value)
    : { rank: 0, label: "—", cls: "minima" },
);

const ultimaAct = computed(() =>
  student.value?.ultimaActividad
    ? pHaceCuanto(student.value.ultimaActividad)
    : "—",
);

// Helpers de severidad para big-number en cabecera de gráfico
function phqaSev(v) {
  if (v <= 9)  return { label: "Leve o mínima", color: "#2BB673", bg: "#E8F8EF" };
  if (v <= 14) return { label: "Moderada",       color: "#E8B04B", bg: "#FDF4E1" };
  return               { label: "Severa",         color: "#E25555", bg: "#FDEAEA" };
}
function gad7Sev(v) {
  if (v <= 9)  return { label: "Leve o mínima", color: "#2BB673", bg: "#E8F8EF" };
  if (v <= 14) return { label: "Moderada",       color: "#E8B04B", bg: "#FDF4E1" };
  return               { label: "Severa",         color: "#E25555", bg: "#FDEAEA" };
}

const phqaBands = [
  { hasta: 27, color: "#f6dfdc" },
  { hasta: 19, color: "#f6e6d6" },
  { hasta: 14, color: "#f7eed9" },
  { hasta: 9, color: "#e7eef8" },
  { hasta: 4, color: "#e9f1ea" },
];
const gad7Bands = [
  { hasta: 21, color: "#f6dfdc" },
  { hasta: 14, color: "#f7eed9" },
  { hasta: 9, color: "#e7eef8" },
  { hasta: 4, color: "#e9f1ea" },
];

const ciclosDesc = computed(() => {
  if (!student.value?.cycles) return [];
  return [...student.value.cycles].map((c, i) => ({ ...c, _i: i })).reverse();
});

async function toggleCiclo(idx) {
  abierto.value = abierto.value === idx ? -1 : idx;
  if (abierto.value === idx && !cicloDetalle.value[idx]) {
    // Tratamos de traer el desglose real desde el backend.
    const c = student.value.cycles[idx];
    try {
      const detalle = await api.reporteCicloEstudiante(studentId.value, c.n);
      cicloDetalle.value = { ...cicloDetalle.value, [idx]: detalle };
    } catch (_) {
      cicloDetalle.value = { ...cicloDetalle.value, [idx]: null };
    }
  }
}

function detalleCiclo(idx) {
  const c = student.value.cycles[idx];
  const det = cicloDetalle.value[idx];
  let phqaVals;
  let gad7Vals;
  if (det && Array.isArray(det.items_detalle) && det.items_detalle.length) {
    // El backend devuelve sólo los ítems con score ≥ 1; rellena con ceros.
    const mapaP = {};
    const mapaG = {};
    for (const it of det.items_detalle) {
      if ((it.modulo || "").toUpperCase().startsWith("PHQ")) {
        const i = parseInt((it.item || "").split("_")[1], 10) - 1;
        if (!Number.isNaN(i)) mapaP[i] = it.puntos;
      } else if ((it.modulo || "").toUpperCase().startsWith("GAD")) {
        const i = parseInt((it.item || "").split("_")[1], 10) - 1;
        if (!Number.isNaN(i)) mapaG[i] = it.puntos;
      }
    }
    phqaVals = ITEMS_PHQA.map((_, i) => mapaP[i] ?? 0);
    gad7Vals = ITEMS_GAD7.map((_, i) => mapaG[i] ?? 0);
  } else {
    // Fallback: aproximación que suma el total (mismo enfoque del prototipo).
    phqaVals = desglose(c.phqa || 0, 9, 3, c.crisis);
    gad7Vals = desglose(c.gad7 || 0, 7, 3, false);
  }
  return { phqaVals, gad7Vals };
}

function back() {
  router.push("/psicologo");
}

async function guardarNota() {
  const texto = draft.value.trim();
  if (!texto) return;
  try {
    const n = await api.crearNota(studentId.value, { texto });
    notas.value = [
      {
        id: n.id,
        fecha: (n.created_at || "").slice(0, 10),
        autor: n.autor_nombre || "tú",
        texto: n.texto,
        propia: true,
      },
      ...notas.value,
    ];
    draft.value = "";
    showToast("Nota guardada en la ficha");
  } catch (e) {
    showToast(e.response?.data?.detail || "No pude guardar la nota");
  }
}

async function contactar() {
  showToast("Abriendo conversación con el estudiante…");
}

function agendar() {
  showToast("Agenda abierta (demo)");
}

const sinDatos = computed(
  () => !cargando.value && (!student.value || !student.value.cycles?.length),
);

// ── Filtro por año ────────────────────────────────────────────────────
const anioSeleccionado = ref(new Date().getFullYear());

const aniosDisponibles = computed(() => {
  const set = new Set(
    (student.value?.cycles || [])
      .map((c) => c.start?.slice(0, 4))
      .filter(Boolean)
      .map(Number),
  );
  return [...set].sort();
});

// Para gráficos: filtrar por año seleccionado y excluir ciclos vacíos
const ciclosConDatos = computed(() =>
  (student.value?.cycles || []).filter((c) => {
    const anio = Number(c.start?.slice(0, 4));
    return anio === anioSeleccionado.value && (!c.encurso || c.dias > 0);
  }),
);
const phqaCycles = computed(() => ciclosConDatos.value);
const gad7Cycles = computed(() => ciclosConDatos.value);
</script>

<template>
  <div class="page" data-screen-label="Ficha clínica">
    <div class="page-inner" style="max-width: 920px">
      <button class="back-link" type="button" @click="back">
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
          <path d="M15 18l-6-6 6-6" />
        </svg>
        Volver
      </button>

      <div v-if="cargando" style="padding: 40px 0; color: var(--ink-3); text-align: center">
        Cargando…
      </div>

      <div
        v-else-if="!student"
        class="panel-card"
        style="padding: 28px; text-align: center"
      >
        <p style="font-size: 13px; color: var(--ink-3)">
          No encontramos a este estudiante.
        </p>
      </div>

      <template v-else>
        <div class="ficha-head">
          <span class="avatar" :style="{ background: avatarColor(student.id) }">
            {{ student.initials }}
          </span>
          <div>
            <h1>{{ student.name }}</h1>
            <div class="meta">
              {{ student.carrera || "—"
              }}{{ student.anio ? " · " + student.anio : "" }} ·
              {{ student.email }}
            </div>
            <div
              style="
                margin-top: 8px;
                display: flex;
                gap: 8px;
                align-items: center;
              "
            >
              <span v-if="last && last.crisis" class="crisis-flag">
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
                Señal de crisis
              </span>
              <SevChip v-else :nivel="riesgo.label" />
              <span style="font-size: 12.5px; color: var(--ink-3)">
                Última actividad {{ ultimaAct }}
              </span>
            </div>
          </div>
          <div class="actions">
            <button class="btn" type="button" @click="contactar">
              Contactar
            </button>
            <button class="btn primary" type="button" @click="agendar">
              Agendar sesión
            </button>
          </div>
        </div>

        <div v-if="last && last.crisis" class="crisis-banner">
          <span class="ic">
            <svg
              width="20"
              height="20"
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
          </span>
          <div>
            <h3>Protocolo de crisis activado</h3>
            <p>
              En la encuesta del ciclo {{ last.n }},
              {{ student.name.split(" ")[0] }} marcó pensamientos de hacerse
              daño. Contactar hoy y registrar la gestión en las notas. Si hay
              riesgo inminente, derivar a la Línea 113 (opción 5) o a
              urgencias.
            </p>
          </div>
        </div>

        <div v-if="sinDatos" class="panel-card" style="padding: 28px">
          <p style="font-size: 13px; color: var(--ink-3); text-align: center">
            Este estudiante todavía no tiene ciclos cerrados.
          </p>
        </div>

        <div v-else style="display: flex; flex-direction: column; gap: 18px">

          <!-- ── Filtro de año ──────────────────────────────────────────── -->
          <div style="display:flex;align-items:center;gap:10px">
            <label style="font-size:13px;font-weight:600;color:#374151">Año</label>
            <select v-model="anioSeleccionado" class="year-select">
              <option v-for="a in aniosDisponibles" :key="a" :value="a">{{ a }}</option>
            </select>
            <span style="font-size:12px;color:#6b7280">
              {{ ciclosConDatos.length }} ciclo{{ ciclosConDatos.length !== 1 ? 's' : '' }} con datos
            </span>
          </div>

          <!-- ══ Grilla 2×2 de gráficos ══════════════════════════════════ -->
          <div class="charts-grid">

            <!-- Tarjeta 1: PHQ-A depresión -->
            <div class="chart-card">
              <div class="cc-head">
                <div class="cc-title">Depresión · PHQ-A</div>
                <div class="cc-badge"
                  :style="{ background: phqaSev(last?.phqa ?? 0).bg,
                             color: phqaSev(last?.phqa ?? 0).color }">
                  {{ phqaSev(last?.phqa ?? 0).label }}
                </div>
              </div>
              <div class="cc-bignum" :style="{ color: phqaSev(last?.phqa ?? 0).color }">
                {{ last?.phqa ?? 0 }}<span class="cc-denom">/27</span>
              </div>
              <div class="cc-sub">último ciclo con datos</div>
              <EvolChart :cycles="phqaCycles" metric-key="phqa" :max="27" :bands="phqaBands" />
              <div class="cc-hint">Verde = mínima · Amarillo = leve · Naranja = moderada · Rojo = severa</div>
            </div>

            <!-- Tarjeta 2: GAD-7 ansiedad -->
            <div class="chart-card">
              <div class="cc-head">
                <div class="cc-title">Ansiedad · GAD-7</div>
                <div class="cc-badge"
                  :style="{ background: gad7Sev(last?.gad7 ?? 0).bg,
                             color: gad7Sev(last?.gad7 ?? 0).color }">
                  {{ gad7Sev(last?.gad7 ?? 0).label }}
                </div>
              </div>
              <div class="cc-bignum" :style="{ color: gad7Sev(last?.gad7 ?? 0).color }">
                {{ last?.gad7 ?? 0 }}<span class="cc-denom">/21</span>
              </div>
              <div class="cc-sub">último ciclo con datos</div>
              <EvolChart :cycles="gad7Cycles" metric-key="gad7" :max="21" :bands="gad7Bands" />
              <div class="cc-hint">Verde = mínima · Amarillo = leve · Naranja = moderada · Rojo = severa</div>
            </div>

            <!-- Tarjeta 3: Condiciones BETO -->
            <div class="chart-card">
              <div class="cc-head">
                <div class="cc-title">Condiciones detectadas</div>
                <div class="cc-badge" style="background:#ede9fe;color:#6d28d9">RoBERTa · orientativo</div>
              </div>
              <div class="cc-sub" style="margin-bottom:14px">
                Confianza promedio por condición detectada en los textos del diario
              </div>
              <CondicionesChart :cycles="phqaCycles" />
            </div>

            <!-- Tarjeta 4: Adherencia + Ánimo -->
            <div class="chart-card">
              <div class="cc-head">
                <div class="cc-title">Adherencia y ánimo</div>
              </div>
              <div class="cc-sub" style="margin-bottom:12px">
                Días escritos por ciclo · Ausencia prolongada es señal clínica temprana
              </div>
              <!-- adherencia -->
              <div class="adh-mini" v-for="c in phqaCycles" :key="c.n">
                <span class="adh-lbl">C{{ c.n }}</span>
                <div class="adh-track">
                  <div class="adh-fill"
                    :style="{
                      width: Math.min((c.dias/14)*100,100)+'%',
                      background: c.dias >= 10 ? '#22c55e' : c.dias >= 5 ? '#f59e0b' : '#ef4444'
                    }"></div>
                </div>
                <span class="adh-num"
                  :style="{ color: c.dias >= 10 ? '#16a34a' : c.dias >= 5 ? '#b45309' : '#dc2626' }">
                  {{ c.dias }}/14
                </span>
              </div>
              <div style="margin-top:16px; border-top:1px solid #f3f4f6; padding-top:14px">
                <div class="cc-sub" style="margin-bottom:8px">Estado de ánimo auto-reportado</div>
                <MoodChart :cycles="phqaCycles" />
              </div>
            </div>

          </div>

          <!-- ══ Ciclos completados (acordeón) ══════════════════════════ -->
          <div class="panel-card">
            <div class="h">Detalle por ciclo</div>
              <div
                v-for="c in ciclosDesc"
                :key="c.n"
                class="cyc-item"
              >
                <button
                  class="cyc-row"
                  type="button"
                  @click="toggleCiclo(c._i)"
                >
                  <span class="cn">
                    Ciclo {{ c.n
                    }}<span
                      v-if="c.encurso"
                      style="font-weight: 500; color: var(--accent)"
                      > · en curso</span
                    >
                  </span>
                  <span class="cd">
                    {{ pRango(c.start, c.end) }} · {{ c.dias }} de 14 días
                  </span>
                  <span class="cyc-scores">
                    <span v-if="c.crisis" class="crisis-flag">
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
                    <span class="s">
                      <span class="v" :style="{ color: phqaSev(c.phqa ?? 0).color }">{{ c.phqa }}</span
                      ><span class="k">PHQ-A</span>
                    </span>
                    <span class="s">
                      <span class="v" :style="{ color: gad7Sev(c.gad7 ?? 0).color }">{{ c.gad7 }}</span
                      ><span class="k">GAD-7</span>
                    </span>
                    <span
                      :style="{
                        transform:
                          abierto === c._i ? 'rotate(90deg)' : 'none',
                        color: '#0D9488',
                        transition: 'transform .15s',
                      }"
                    >
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
                  </span>
                </button>
                <template v-if="abierto === c._i">
                  <div class="cyc-body">

                    <!-- ── Interpretación clínica ──────────────────────── -->
                    <div class="clinico-banner"
                      :style="{
                        background: (c.phqa > 14 || c.gad7 > 14) ? '#FBEBD7' : '#E6F3F1',
                        borderColor: (c.phqa > 14 || c.gad7 > 14) ? '#CFE6E2' : '#CFE6E2'
                      }">
                      <div class="clinico-chips">
                        <SevChip :nivel="nivelPhqa(c.phqa).nivel" />
                        <SevChip :nivel="nivelGad7(c.gad7).nivel" />
                      </div>
                      <div class="clinico-labels">
                        <span v-if="labelClinico('depresion', nivelPhqa(c.phqa))" class="label-clinico">
                          {{ labelClinico('depresion', nivelPhqa(c.phqa)) }}
                        </span>
                        <span v-if="labelClinico('ansiedad', nivelGad7(c.gad7))" class="label-clinico">
                          {{ labelClinico('ansiedad', nivelGad7(c.gad7)) }}
                        </span>
                        <span v-if="!labelClinico('depresion', nivelPhqa(c.phqa)) && !labelClinico('ansiedad', nivelGad7(c.gad7))"
                              style="font-size:12px;color:#16a34a;font-weight:600">
                          Sin indicadores clínicos significativos en este ciclo
                        </span>
                      </div>
                      <p class="disclaimer-clinico">
                        Indicadores orientativos según criterios DSM-5. El diagnóstico es competencia exclusiva del profesional de salud mental.
                      </p>
                    </div>

                    <!-- ── PHQ-A ítem por ítem (datos reales del diario) ── -->
                    <div class="items-section">
                      <div class="items-head">
                        <span class="items-title">PHQ-A · Depresión</span>
                        <span class="items-score">{{ c.phqa }}<span class="items-max">/27</span></span>
                      </div>
                      <div v-if="c.items_detalle?.filter(i => i.modulo?.startsWith('PHQ')).length">
                        <div
                          v-for="it in c.items_detalle.filter(i => i.modulo?.startsWith('PHQ')).sort((a,b)=>b.puntos-a.puntos)"
                          :key="it.item"
                          class="item-line"
                        >
                          <span class="q">{{ it.criterio_dsm5 || it.item }}</span>
                          <div class="bar-wrap">
                            <div class="bar-fill"
                              :style="{ width: (it.puntos/3*100)+'%',
                                        background: it.puntos>=2?'#ef4444':it.puntos===1?'#f59e0b':'#22c55e' }">
                            </div>
                          </div>
                          <span class="sc" :style="{color: it.puntos>=2?'#dc2626':it.puntos===1?'#d97706':'#16a34a'}">
                            {{ it.puntos }}/3
                          </span>
                          <span class="likert">{{ it.frase_likert }}</span>
                        </div>
                      </div>
                      <p v-else class="items-empty">No se detectaron síntomas de depresión en este ciclo</p>
                    </div>

                    <!-- ── GAD-7 ítem por ítem ─────────────────────────── -->
                    <div class="items-section">
                      <div class="items-head">
                        <span class="items-title">GAD-7 · Ansiedad</span>
                        <span class="items-score">{{ c.gad7 }}<span class="items-max">/21</span></span>
                      </div>
                      <div v-if="c.items_detalle?.filter(i => i.modulo?.startsWith('GAD')).length">
                        <div
                          v-for="it in c.items_detalle.filter(i => i.modulo?.startsWith('GAD')).sort((a,b)=>b.puntos-a.puntos)"
                          :key="it.item"
                          class="item-line"
                        >
                          <span class="q">{{ it.criterio_dsm5 || it.item }}</span>
                          <div class="bar-wrap">
                            <div class="bar-fill"
                              :style="{ width: (it.puntos/3*100)+'%',
                                        background: it.puntos>=2?'#ef4444':it.puntos===1?'#f59e0b':'#22c55e' }">
                            </div>
                          </div>
                          <span class="sc" :style="{color: it.puntos>=2?'#dc2626':it.puntos===1?'#d97706':'#16a34a'}">
                            {{ it.puntos }}/3
                          </span>
                          <span class="likert">{{ it.frase_likert }}</span>
                        </div>
                      </div>
                      <p v-else class="items-empty">No se detectaron síntomas de ansiedad en este ciclo</p>
                    </div>

                    <!-- ── Fragmentos del diario ───────────────────────── -->
                    <div v-if="c.entradas_muestra?.length" class="evidencia-section">
                      <div class="items-title" style="margin-bottom:10px">
                        Lo que escribió · base de la detección
                      </div>
                      <div v-for="(e, ei) in c.entradas_muestra" :key="ei" class="entrada-frag">
                        <span class="frag-fecha">{{ pCorto(e.fecha) }}</span>
                        <blockquote class="frag-texto">"{{ e.fragmento }}…"</blockquote>
                      </div>
                    </div>

                  </div>
                </template>
              </div>
            </div>

          <!-- ══ Notas clínicas ════════════════════════════════════ -->
          <div class="panel-card">
              <div class="h">Notas clínicas</div>
              <div class="b">
                <textarea
                  v-model="draft"
                  class="nota-input"
                  placeholder="Anotá observaciones de la sesión, acuerdos, derivaciones…"
                ></textarea>
                <div
                  style="
                    display: flex;
                    justify-content: flex-end;
                    margin-top: 8px;
                  "
                >
                  <button
                    class="btn primary"
                    type="button"
                    :disabled="!draft.trim()"
                    :style="{ opacity: draft.trim() ? 1 : 0.5 }"
                    @click="guardarNota"
                  >
                    Guardar nota
                  </button>
                </div>
                <div style="margin-top: 16px">
                  <p
                    v-if="!notas.length"
                    style="font-size: 12.5px; color: var(--ink-3); margin: 0"
                  >
                    Todavía no hay notas en esta ficha.
                  </p>
                  <div v-for="n in notas" :key="n.id" class="nota">
                    <div class="meta">
                      {{ pCorto(n.fecha) }} · {{ n.autor
                      }}{{ n.propia ? " (tú)" : "" }}
                    </div>
                    <div class="txt">{{ n.texto }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="panel-card">
              <div class="h">Diario del estudiante</div>
              <div class="b">
                <div class="privacy-note">
                  <span style="color: var(--ink-3)">
                    <svg
                      width="15"
                      height="15"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.7"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <rect x="4" y="10" width="16" height="11" rx="2" />
                      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
                    </svg>
                  </span>
                  <span>
                    <template v-if="student.entradasCompartidas">
                      {{ student.name.split(" ")[0] }} eligió compartir sus
                      entradas contigo. Léelas con cuidado: son su espacio
                      privado.
                    </template>
                    <template v-else>
                      El contenido del diario es privado. Solo ves los
                      resultados de las encuestas, no lo que
                      {{ student.name.split(" ")[0] }} escribe.
                    </template>
                  </span>
                </div>
                <button
                  v-if="student.entradasCompartidas"
                  class="btn"
                  type="button"
                  style="margin-top: 12px; width: 100%; justify-content: center"
                  @click="showToast('Entradas compartidas (demo)')"
                >
                  Ver entradas compartidas
                </button>
              </div>
            </div>

        </div>
      </template>
    </div>

    <Teleport to="body">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </Teleport>
  </div>
</template>

<style scoped>
/* ── Grilla 2×2 de gráficos ──────────────────────────────────── */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 640px) {
  .charts-grid { grid-template-columns: 1fr; }
}
.chart-card {
  background: #fff;
  border: 1px solid var(--line, #E4EBE9);
  border-radius: 16px;
  padding: 18px 20px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  box-shadow: 0 1px 2px rgba(20,50,48,.04), 0 8px 28px -16px rgba(20,50,48,.12);
}
.cc-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2px;
}
.cc-title {
  font-size: 13px;
  font-weight: 700;
  color: #143230;
  font-family: 'Gabarito', sans-serif;
}
.cc-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 99px;
}
.cc-bignum {
  font-size: 42px;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -1px;
  margin: 4px 0 0;
  font-family: 'Gabarito', sans-serif;
}
.cc-denom {
  font-size: 16px;
  font-weight: 500;
  color: #6b7280;
}
.cc-sub {
  font-size: 11.5px;
  color: #6b7280;
  margin-bottom: 2px;
}
.cc-hint {
  font-size: 10.5px;
  color: #9ca3af;
  margin-top: 6px;
}

/* ── Adherencia mini ─────────────────────────────────────────── */
.adh-mini {
  display: grid;
  grid-template-columns: 24px 1fr 42px;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.adh-lbl { font-size: 11.5px; font-weight: 700; color: #374151; }
.adh-track {
  height: 10px;
  background: #f3f4f6;
  border-radius: 99px;
  overflow: hidden;
}
.adh-fill {
  height: 100%;
  border-radius: 99px;
  transition: width .4s ease;
}
.adh-num { font-size: 11.5px; font-weight: 700; text-align: right; }

/* ── Chip (kept for backwards compat) ───────────────────────── */
.chip-high { background: #d1fae5; color: #065f46; }
.chip-mid  { background: #fef3c7; color: #92400e; }
.chip-low  { background: #fee2e2; color: #991b1b; }
.adh-legend {
  display: flex;
  gap: 16px;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}
.adh-key {
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 99px;
}
.adh-key.high { background: #d1fae5; color: #065f46; }
.adh-key.mid  { background: #fef3c7; color: #92400e; }
.adh-key.low  { background: #fee2e2; color: #991b1b; }

/* ── Cuerpo del acordeón de ciclo ────────────────────────── */
.cyc-body {
  padding: 0 20px 18px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ── Banner de interpretación clínica ────────────────────── */
.clinico-banner {
  background: #E6F3F1;
  border: 1px solid #CFE6E2;
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.clinico-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.clinico-labels { display: flex; flex-wrap: wrap; gap: 6px; }
.label-clinico {
  font-size: 12px;
  font-weight: 600;
  color: #0D9488;
  background: #E6F3F1;
  border: 1px solid #CFE6E2;
  border-radius: 6px;
  padding: 3px 10px;
}
.disclaimer-clinico {
  font-size: 11px; color: #9ca3af; margin: 0;
  font-style: italic; line-height: 1.4;
}

/* ── Sección de ítems PHQ-A / GAD-7 ─────────────────────── */
.items-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.items-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 4px;
}
.items-title {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: #143230;
  font-family: 'Gabarito', sans-serif;
}
.items-score {
  font-size: 20px;
  font-weight: 800;
  color: #111827;
}
.items-max { font-size: 11px; font-weight: 500; color: #9ca3af; }
.items-empty { font-size: 12px; color: #9ca3af; margin: 0; font-style: italic; }

.item-line {
  display: grid;
  grid-template-columns: 1fr 80px 36px auto;
  align-items: center;
  gap: 8px;
}
.q { font-size: 12px; color: #374151; }
.bar-wrap {
  height: 8px;
  background: #f3f4f6;
  border-radius: 99px;
  overflow: hidden;
}
.bar-fill { height: 100%; border-radius: 99px; transition: width .4s; }
.sc { font-size: 12px; font-weight: 700; text-align: right; }
.likert {
  font-size: 10.5px;
  color: #6b7280;
  font-style: italic;
  white-space: nowrap;
}

/* ── Fragmentos del diario ───────────────────────────────── */
.evidencia-section {
  border-top: 1px solid #f3f4f6;
  padding-top: 14px;
}
.entrada-frag {
  margin-bottom: 10px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.frag-fecha {
  font-size: 11px;
  font-weight: 700;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: .04em;
}
.frag-texto {
  margin: 0;
  font-size: 12.5px;
  color: #374151;
  font-style: italic;
  line-height: 1.55;
  padding-left: 10px;
  border-left: 3px solid #0D9488;
}

/* ── Label clínico (compat) ──────────────────────────────── */
.label-clinico-wrap { display: flex; flex-wrap: wrap; gap: 6px; }

/* ── Selector de año ─────────────────────────────────────── */
.year-select {
  appearance: none;
  background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") no-repeat right 10px center;
  border: 1px solid #CFE6E2;
  border-radius: 8px;
  padding: 5px 28px 5px 12px;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  cursor: pointer;
}
.year-select:focus { outline: none; border-color: #0D9488; }

@media (max-width: 640px) {
  .item-line { grid-template-columns: 1fr 60px 32px; }
  .likert { display: none; }
}
</style>
