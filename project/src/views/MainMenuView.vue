<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { authStore } from "../store/auth";
import { api } from "../api";
import {
  fmtLong,
  dowAb,
  dayNum,
  fromBackend,
  todayIso,
  saludo,
} from "../composables/samiHelpers";

const router = useRouter();
const user = computed(() => authStore.state.user);
const rol = computed(() => authStore.rol.value);
const esEstudiante = computed(() => rol.value === "estudiante");

const primerNombre = computed(() => {
  const n = (user.value?.nombre || "").trim();
  return n.split(" ")[0] || "";
});

// ─── Datos del estudiante (vista Sami "Hoy") ───────────────────────────
const entradas = ref([]);
const ciclo = ref(null);
const encuesta = ref(null);

const hoyIso = todayIso();

onMounted(async () => {
  if (!esEstudiante.value) return;
  try {
    const [e, c, enc] = await Promise.all([
      api.listarMisEntradasDiario(),
      api.miCiclo().catch(() => null),
      api.encuestaPendiente().catch(() => null),
    ]);
    entradas.value = (e || []).map(fromBackend);
    ciclo.value = c;
    encuesta.value = enc?.pendiente ? enc.encuesta : null;
  } catch (_) {}
});

const entradaHoy = computed(() =>
  entradas.value.find((e) => e.date === hoyIso),
);
const recientes = computed(() =>
  entradas.value.filter((e) => e.date !== hoyIso).slice(0, 4),
);

const PROMPTS = [
  "¿Qué fue lo que más espacio ocupó en tu cabeza hoy?",
  "¿Hubo algún momento del día en que te sentiste tranquilo/a?",
  "Si pudieras repetir una hora de hoy, ¿cuál sería?",
  "¿Qué te gustaría soltar antes de dormir?",
  "¿Qué tienes en la cabeza hoy?",
  "Si tuvieras que nombrar tu día con una palabra, ¿cuál sería?",
  "¿Hubo un momento en que respiraste tranquilo?",
  "¿Qué cosa pequeña te gustó del día?",
];
const promptDelDia = computed(
  () => PROMPTS[new Date().getDate() % PROMPTS.length],
);

// ─── Ciclo strip ──────────────────────────────────────────────────────
const cicloLength = 14;
const cicloDia = computed(() => {
  if (!ciclo.value?.ciclo_actual) return 0;
  return Math.min(ciclo.value.ciclo_actual.dia_actual || 0, cicloLength);
});
const cicloNumero = computed(() => ciclo.value?.ciclo_actual?.numero || 1);
const cicloDone = computed(() => cicloDia.value >= cicloLength);

function irNuevaEntrada() {
  if (entradaHoy.value) {
    router.push({ path: "/diario", query: { entry: entradaHoy.value.id } });
  } else {
    router.push({ path: "/diario", query: { compose: "1" } });
  }
}
function verEntrada(id) {
  router.push({ path: "/diario", query: { entry: id } });
}
function verTodas() {
  router.push("/diario");
}
function irEncuesta() {
  router.push({ path: "/diario", query: { encuesta: "1" } });
}

// ─── Vista psicólogo / admin (sin cambios) ────────────────────────────
const opcionesPsicologo = [
  { titulo: "Panel de estudiantes", desc: "Cómo está cada uno, alertas y citas.", destino: "/psicologo" },
  { titulo: "Recursos", desc: "Material clínico y líneas de apoyo.", destino: "/recursos" },
  { titulo: "Mi cuenta", desc: "Datos y contraseña.", destino: "/perfil" },
];

const opcionesAdmin = [
  { titulo: "Usuarios", desc: "Estudiantes, psicólogas y administradores.", destino: "/admin" },
  { titulo: "Configuración", desc: "Parámetros del diario y respaldos.", destino: "/admin/sistema" },
  { titulo: "Contenidos", desc: "Lo que ven los estudiantes en lecturas.", destino: "/admin/contenidos" },
  { titulo: "Reportes", desc: "Cómo va el sistema en general.", destino: "/admin/reportes" },
  { titulo: "Auditoría", desc: "Registro de accesos.", destino: "/admin/logs" },
];

const opciones = computed(() => {
  if (rol.value === "admin") return opcionesAdmin;
  if (rol.value === "psicologo") return opcionesPsicologo;
  return [];
});

const tituloHero = computed(() => {
  if (rol.value === "admin") return ["Panel de", "administración"];
  if (rol.value === "psicologo") return ["Tu panel", "clínico"];
  return ["Tu espacio", "para escribir"];
});
</script>

<template>
  <!-- ════════════════════════════════════════════════════════════════ -->
  <!-- ESTUDIANTE — Inicio · Hoy (estilo Sami / Day One)               -->
  <!-- ════════════════════════════════════════════════════════════════ -->
  <div v-if="esEstudiante" class="page" data-screen-label="Inicio · Hoy">
    <div class="page-inner">
      <p class="sub" style="margin-bottom: 2px">{{ fmtLong(hoyIso) }}</p>
      <h1>{{ saludo() }}, {{ primerNombre || "tú" }}</h1>
      <div style="height: 24px"></div>

      <div
        style="
          display: grid;
          grid-template-columns: 1.4fr 1fr;
          gap: 14px;
          align-items: start;
        "
      >
        <div style="display: flex; flex-direction: column; gap: 14px">
          <div class="card" style="padding: 24px">
            <template v-if="entradaHoy">
              <p style="margin: 0 0 4px; font-size: 12.5px; color: var(--ink-3)">
                La entrada de hoy
              </p>
              <h3 style="margin: 0 0 8px; font-size: 17px; font-weight: 700">
                {{ entradaHoy.title || "Sin título" }}
              </h3>
              <p
                style="
                  margin: 0 0 18px;
                  font-size: 13.5px;
                  color: var(--ink-2);
                  line-height: 1.55;
                "
              >
                {{ (entradaHoy.body || entradaHoy.title || "").slice(0, 150)
                }}{{
                  (entradaHoy.body || entradaHoy.title || "").length > 150
                    ? "…"
                    : ""
                }}
              </p>
              <button class="btn primary" type="button" @click="irNuevaEntrada">
                Seguir escribiendo
              </button>
            </template>
            <template v-else>
              <p style="margin: 0 0 4px; font-size: 12.5px; color: var(--ink-3)">
                Pregunta del día
              </p>
              <h3
                style="
                  margin: 0 0 18px;
                  font-size: 18px;
                  font-weight: 700;
                  letter-spacing: -0.01em;
                  line-height: 1.35;
                "
              >
                {{ promptDelDia }}
              </h3>
              <button class="btn primary" type="button" @click="irNuevaEntrada">
                Escribir la entrada de hoy
              </button>
            </template>
          </div>

          <div class="card" style="padding: 16px 24px">
            <div
              style="
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
              "
            >
              <span style="font-size: 12.5px; color: var(--ink-3)">
                {{
                  cicloDone
                    ? `Ciclo ${cicloNumero} · 14 días completados`
                    : `Ciclo del diario · día ${cicloDia} de ${cicloLength}`
                }}
              </span>
              <span class="cycle-progress">
                <i
                  v-for="i in cicloLength"
                  :key="i"
                  :class="i <= cicloDia ? 'done' : ''"
                ></i>
              </span>
              <button
                v-if="encuesta"
                class="linkbtn"
                type="button"
                @click="irEncuesta"
              >
                Responder encuesta de cierre →
              </button>
            </div>
          </div>
        </div>

        <div class="card">
          <div
            style="
              padding: 14px 18px 10px;
              border-bottom: 1px solid var(--line-soft);
              display: flex;
              justify-content: space-between;
              align-items: baseline;
            "
          >
            <strong style="font-size: 13.5px">Entradas recientes</strong>
            <button class="linkbtn" type="button" @click="verTodas">
              Ver todas
            </button>
          </div>
          <div class="rowlist">
            <button
              v-for="e in recientes"
              :key="e.id"
              class="entry-row"
              type="button"
              @click="verEntrada(e.id)"
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
              v-if="!recientes.length"
              style="
                padding: 22px 18px;
                font-size: 13px;
                color: var(--ink-3);
                text-align: center;
              "
            >
              Todavía no hay entradas anteriores.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ════════════════════════════════════════════════════════════════ -->
  <!-- PSICÓLOGO / ADMIN — vista original                              -->
  <!-- ════════════════════════════════════════════════════════════════ -->
  <div v-else class="page-shell-wide">
    <section class="mb-8">
      <p class="eyebrow mb-2">Hola, {{ primerNombre || "tú" }}</p>
      <h1 class="hero-serif text-[32px] sm:text-[37px]">
        {{ tituloHero[0] }} <span class="hero-mint">{{ tituloHero[1] }}</span>
      </h1>
    </section>

    <div class="grid gap-4 sm:grid-cols-2">
      <button
        v-for="(op, i) in opciones"
        :key="i"
        @click="router.push(op.destino)"
        class="group menu-card text-left"
      >
        <span class="menu-card-arrow">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.6"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12" />
            <polyline points="12 5 19 12 12 19" />
          </svg>
        </span>
        <p class="label-kicker mb-3 tabular">
          {{ String(i + 1).padStart(2, "0") }}
        </p>
        <h3 class="gb text-[19px] font-semibold text-green-900 leading-snug">
          {{ op.titulo }}
        </h3>
        <p class="text-[14px] text-ink-500 mt-1.5 leading-relaxed">
          {{ op.desc }}
        </p>
      </button>
    </div>
  </div>
</template>
