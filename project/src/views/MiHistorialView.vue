<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import {
  MESES,
  DIAS_AB,
  parseIso,
  isoDeFecha,
  fmtLong,
  dowAb,
  dayNum,
  fromBackend,
  todayIso,
} from "../composables/samiHelpers";

const router = useRouter();

const ciclo = ref(null);
const encuesta = ref(null);
const entradas = ref([]);
const cargando = ref(true);

const hoy = todayIso();

onMounted(async () => {
  try {
    const [c, e, enc] = await Promise.all([
      api.miCiclo().catch(() => null),
      api.listarMisEntradasDiario().catch(() => []),
      api.encuestaPendiente().catch(() => null),
    ]);
    ciclo.value = c;
    entradas.value = (e || []).map(fromBackend);
    encuesta.value = enc?.pendiente ? enc.encuesta : null;
  } finally {
    cargando.value = false;
  }
});

function fmtRango(startIso, endIso) {
  const a = parseIso(startIso);
  const b = parseIso(endIso);
  if (a.getMonth() === b.getMonth() && a.getFullYear() === b.getFullYear()) {
    return `${a.getDate()} – ${b.getDate()} de ${MESES[b.getMonth()]} de ${b.getFullYear()}`;
  }
  if (a.getFullYear() === b.getFullYear()) {
    return `${a.getDate()} de ${MESES[a.getMonth()]} – ${b.getDate()} de ${MESES[b.getMonth()]} de ${b.getFullYear()}`;
  }
  return `${a.getDate()} de ${MESES[a.getMonth()]} de ${a.getFullYear()} – ${b.getDate()} de ${MESES[b.getMonth()]} de ${b.getFullYear()}`;
}

// Lista de ciclos: actual + sesiones cerradas (ordenadas desc).
const ciclos = computed(() => {
  if (!ciclo.value) return [];
  const out = [];
  const actual = ciclo.value.ciclo_actual;
  if (actual) {
    out.push({
      id: actual.numero,
      nombre: `Ciclo ${actual.numero}`,
      start: actual.inicio,
      end: actual.fecha_limite,
      rango: fmtRango(actual.inicio, actual.fecha_limite),
      cierre: hoy >= actual.fecha_limite,
      actual: true,
    });
  }
  for (const s of [...(ciclo.value.sesiones_cerradas || [])].reverse()) {
    out.push({
      id: s.numero,
      nombre: `Ciclo ${s.numero}`,
      start: s.inicio_ciclo,
      end: s.fecha_cierre,
      rango: fmtRango(s.inicio_ciclo, s.fecha_cierre),
      cierre: true,
      actual: false,
    });
  }
  return out;
});

const cicloSelId = ref(null);
const cicloSel = computed(
  () => ciclos.value.find((c) => c.id === cicloSelId.value) || ciclos.value[0],
);

// Auto-select el primero cuando cargan los ciclos
watch(
  ciclos,
  (lista) => {
    if (lista.length && !lista.find((c) => c.id === cicloSelId.value)) {
      cicloSelId.value = lista[0].id;
    }
  },
  { immediate: true },
);

function setCicloSel(id) {
  cicloSelId.value = Number(id);
}

const porFecha = computed(() => {
  const out = {};
  for (const e of entradas.value) if (!out[e.date]) out[e.date] = e;
  return out;
});

function enCiclo(iso, c) {
  return c && iso >= c.start && iso <= c.end;
}

const celdas = computed(() => {
  const c = cicloSel.value;
  if (!c) return [];
  const ini = parseIso(c.start);
  const fin = parseIso(c.end);
  const desde = new Date(ini);
  desde.setDate(desde.getDate() - desde.getDay()); // domingo previo
  const hasta = new Date(fin);
  hasta.setDate(hasta.getDate() + (6 - hasta.getDay())); // sábado posterior

  const out = [];
  for (let d = new Date(desde); d <= hasta; d.setDate(d.getDate() + 1)) {
    out.push({ iso: isoDeFecha(d), dia: d.getDate() });
  }
  return out;
});

const tituloMes = computed(() => {
  const c = cicloSel.value;
  if (!c) return "";
  const a = parseIso(c.start);
  const b = parseIso(c.end);
  if (a.getMonth() === b.getMonth()) {
    return `${MESES[a.getMonth()][0].toUpperCase()}${MESES[a.getMonth()].slice(1)} ${a.getFullYear()}`;
  }
  return `${MESES[a.getMonth()][0].toUpperCase()}${MESES[a.getMonth()].slice(1)} – ${MESES[b.getMonth()]} ${b.getFullYear()}`;
});

const delCiclo = computed(() => {
  const c = cicloSel.value;
  if (!c) return [];
  return entradas.value
    .filter((e) => enCiclo(e.date, c))
    .sort((a, b) => (a.date < b.date ? -1 : 1));
});

function abrirEntrada(id) {
  router.push({ path: "/diario", query: { entry: id } });
}
function irEncuesta() {
  router.push({ path: "/diario", query: { encuesta: "1" } });
}

const encuestaResp = computed(() => !encuesta.value);
</script>

<template>
  <div class="page" data-screen-label="Mi historial">
    <div class="page-inner" style="max-width: 880px">
      <h1>Mi historial</h1>
      <p class="sub">
        Elegí un período y mirá qué días escribiste. Esto solo lo ves vos.
      </p>

      <div
        v-if="cargando"
        style="padding: 60px 0; text-align: center; color: var(--ink-3)"
      >
        Cargando…
      </div>

      <div
        v-else-if="!ciclos.length"
        class="card"
        style="padding: 24px; text-align: center"
      >
        <h3 style="margin: 0 0 6px; font-size: 16px; font-weight: 700">
          Todavía no empezaste un ciclo.
        </h3>
        <p style="font-size: 13px; color: var(--ink-3); margin: 0 0 14px">
          Cuando escribas tu primera entrada, ese día se convierte en el día 1.
        </p>
        <button
          class="btn primary"
          type="button"
          @click="router.push('/diario')"
        >
          Abrir el diario
        </button>
      </div>

      <div
        v-else
        style="
          display: grid;
          grid-template-columns: 1.2fr 1fr;
          gap: 28px;
          align-items: start;
        "
      >
        <div class="card" style="padding: 20px 24px 22px">
          <div class="field" style="margin-bottom: 18px">
            <label for="periodo">Período</label>
            <select
              id="periodo"
              :value="cicloSel?.id"
              @change="setCicloSel($event.target.value)"
            >
              <option v-for="c in ciclos" :key="c.id" :value="c.id">
                {{ c.nombre }} · {{ c.rango }}
              </option>
            </select>
          </div>

          <div class="cal-title" style="margin-top: 4px">{{ tituloMes }}</div>
          <div class="cal-grid">
            <div v-for="d in DIAS_AB" :key="d" class="cal-dow">{{ d }}</div>
            <template v-for="c in celdas" :key="c.iso">
              <button
                v-if="enCiclo(c.iso, cicloSel) && porFecha[c.iso]"
                class="cal-cell entry"
                type="button"
                :class="c.iso === hoy ? 'today' : ''"
                @click="abrirEntrada(porFecha[c.iso].id)"
              >
                {{ c.dia }}
              </button>
              <div
                v-else
                :class="[
                  'cal-cell',
                  !enCiclo(c.iso, cicloSel) ? 'future' : 'range',
                  c.iso === hoy ? 'today' : '',
                ]"
              >
                {{ c.dia }}
              </div>
            </template>
          </div>

          <div
            style="
              display: flex;
              gap: 18px;
              margin-top: 16px;
              font-size: 12px;
              color: var(--ink-3);
              align-items: center;
              flex-wrap: wrap;
            "
          >
            <span style="display: inline-flex; align-items: center; gap: 6px">
              <i
                style="
                  width: 12px;
                  height: 12px;
                  border-radius: 4px;
                  background: var(--accent);
                  display: inline-block;
                "
              ></i>
              Escribiste — clic para releer
            </span>
            <span style="display: inline-flex; align-items: center; gap: 6px">
              <i
                style="
                  width: 12px;
                  height: 12px;
                  border-radius: 4px;
                  background: color-mix(in srgb, var(--accent) 11%, #fff);
                  display: inline-block;
                "
              ></i>
              Días del ciclo
            </span>
          </div>
        </div>

        <div class="card">
          <div
            style="
              padding: 16px 20px 14px;
              border-bottom: 1px solid var(--line-soft);
            "
          >
            <div style="font-size: 14.5px; font-weight: 700">
              {{ cicloSel?.nombre }}
            </div>
            <div
              style="font-size: 12.5px; color: var(--ink-3); margin-top: 2px"
            >
              {{ cicloSel?.rango }}
            </div>
            <div
              style="
                font-size: 13px;
                color: var(--ink-2);
                margin-top: 8px;
                line-height: 1.55;
              "
            >
              <template v-if="cicloSel?.actual && !cicloSel?.cierre">
                Estás en este ciclo.
              </template>
              <template v-else-if="cicloSel?.cierre">
                Cerraste este ciclo.
              </template>
              Escribiste {{ delCiclo.length }} de 14 días.
            </div>
            <button
              v-if="cicloSel?.cierre"
              class="linkbtn"
              type="button"
              style="margin-top: 10px"
              @click="irEncuesta"
            >
              {{
                encuestaResp
                  ? "Encuesta de cierre respondida"
                  : "Contale a Sami cómo te fue →"
              }}
            </button>
          </div>
          <div
            style="
              padding: 10px 20px 6px;
              font-size: 11.5px;
              font-weight: 700;
              text-transform: uppercase;
              letter-spacing: 0.06em;
              color: var(--ink-3);
            "
          >
            Entradas de este período
          </div>
          <div class="rowlist">
            <button
              v-for="e in delCiclo"
              :key="e.id"
              class="entry-row"
              type="button"
              @click="abrirEntrada(e.id)"
            >
              <span class="datebox">
                <span class="dow">{{ dowAb(e.date) }}</span>
                <span class="num">{{ dayNum(e.date) }}</span>
              </span>
              <span class="meta">
                <span class="t">{{ e.title || "Sin título" }}</span>
                <span class="x">{{
                  (e.body || e.title || "").split("\n")[0]
                }}</span>
              </span>
            </button>
            <p
              v-if="!delCiclo.length"
              style="padding: 18px 20px; font-size: 13px; color: var(--ink-3)"
            >
              No escribiste en este período.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
