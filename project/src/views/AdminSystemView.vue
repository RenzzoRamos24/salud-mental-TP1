<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import PageHeader from "../components/PageHeader.vue";

const router = useRouter();
const tab = ref("diario");

// Modelo del diario: información fija que describe cómo funciona el
// sistema actual (read-only). El admin no edita las preguntas porque
// ya no hay encuesta: el análisis se infiere del texto libre.
const TABLA_JOHNSON = [
  { dias: "0 días", puntos: "0 puntos", frase: "Nunca" },
  { dias: "1 – 7 días", puntos: "1 punto", frase: "Algunos días" },
  { dias: "8 – 11 días", puntos: "2 puntos", frase: "Más de la mitad de los días" },
  { dias: "12 – 14 días", puntos: "3 puntos", frase: "Casi todos los días" },
];

const ITEMS_PHQA = [
  { id: "phq9_1", criterio: "Pérdida de interés (anhedonia)" },
  { id: "phq9_2", criterio: "Ánimo deprimido" },
  { id: "phq9_3", criterio: "Alteración del sueño" },
  { id: "phq9_4", criterio: "Fatiga / pérdida de energía" },
  { id: "phq9_5", criterio: "Cambios en apetito o peso" },
  { id: "phq9_6", criterio: "Sentimientos de inutilidad o culpa" },
  { id: "phq9_7", criterio: "Dificultad para concentrarse" },
  { id: "phq9_8", criterio: "Enlentecimiento o agitación psicomotora" },
  { id: "phq9_9", criterio: "Ideación suicida o de autolesión (crítico)" },
];

const ITEMS_GAD = [
  { id: "gad7_1", criterio: "Ansiedad o nerviosismo" },
  { id: "gad7_2", criterio: "Dificultad para controlar la preocupación" },
  { id: "gad7_3", criterio: "Preocupación por múltiples temas" },
  { id: "gad7_4", criterio: "Tensión / no relajarse" },
  { id: "gad7_5", criterio: "Inquietud" },
  { id: "gad7_6", criterio: "Irritabilidad" },
  { id: "gad7_7", criterio: "Sensación de catástrofe inminente" },
];

const SEVERIDAD_PHQA = [
  { rango: "0 – 4", nivel: "Mínima" },
  { rango: "5 – 9", nivel: "Leve" },
  { rango: "10 – 14", nivel: "Moderada" },
  { rango: "15 – 19", nivel: "Moderada-severa" },
  { rango: "20 – 27", nivel: "Severa" },
];

const SEVERIDAD_GAD = [
  { rango: "0 – 4", nivel: "Mínima" },
  { rango: "5 – 9", nivel: "Leve" },
  { rango: "10 – 14", nivel: "Moderada" },
  { rango: "15 – 21", nivel: "Severa" },
];

const logs = ref([]);
async function cargarLogs() {
  const res = await api.adminGetAuditLogs({ limit: 50, offset: 0 });
  logs.value = res.logs;
}

const backups = ref([]);
const backupCreando = ref(false);
const backupMensaje = ref("");
async function cargarBackups() {
  backups.value = await api.adminListarBackups();
}
async function crearBackup() {
  backupCreando.value = true;
  backupMensaje.value = "";
  try {
    const res = await api.adminCrearBackup();
    backupMensaje.value = `Respaldo creado: ${res.archivo}`;
    await cargarBackups();
  } catch (e) {
    backupMensaje.value = "Error: " + (e.response?.data?.detail || e.message);
  } finally {
    backupCreando.value = false;
  }
}

const modeloInfo = ref(null);
const umbrales = ref(null);
const bertMensaje = ref("");

const CONDICION_LABELS = {
  depresion: "Depresión",
  ansiedad: "Ansiedad",
  tdah: "TDAH",
  estres_academico: "Estrés escolar",
  soledad: "Soledad",
  riesgo_suicida: "Riesgo suicida",
  estabilidad: "Estabilidad emocional",
};
async function cargarBert() {
  const [info, u] = await Promise.all([
    api.adminGetModeloInfo(),
    api.adminGetUmbrales(),
  ]);
  modeloInfo.value = info;
  umbrales.value = u;
}
async function guardarUmbrales() {
  bertMensaje.value = "";
  try {
    await api.adminUpdateUmbrales(umbrales.value);
    bertMensaje.value = "Umbrales actualizados.";
  } catch (e) {
    bertMensaje.value = "Error: " + (e.response?.data?.detail || e.message);
  }
}
async function recargarModelo() {
  bertMensaje.value = "";
  try {
    const res = await api.adminRecargarModelo();
    bertMensaje.value = res.mensaje;
    modeloInfo.value = await api.adminGetModeloInfo();
  } catch (e) {
    bertMensaje.value = "Error: " + (e.response?.data?.detail || e.message);
  }
}

function statusChip(code) {
  if (code >= 200 && code < 300) return "chip-mint";
  if (code >= 300 && code < 400) return "chip-brand";
  if (code >= 400 && code < 500) return "chip-peach";
  return "chip bg-coral-100 text-risk-critico";
}

onMounted(async () => {
  await Promise.all([cargarLogs(), cargarBackups(), cargarBert()]);
});

const TABS = [
  ["diario", "Diario y ciclos", ""],
  ["auditoria", "Auditoría", ""],
  ["backups", "Respaldos", ""],
  ["bert", "Motor de análisis", ""],
];
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">
      Volver al menú
    </button>

    <PageHeader
      title="Configuración"
      subtitle="Modelo del diario, auditoría, respaldos y motor de análisis."
      tone="sky2"
    />

    <!-- Tabs -->
    <nav
      class="flex gap-1 bg-white rounded-xl border border-ink-100 p-1 shadow-soft mb-6 overflow-x-auto fade-in-up"
    >
      <button
        v-for="[key, label] in TABS"
        :key="key"
        @click="tab = key"
        :class="[
          'px-4 py-2 rounded-xl text-sm font-semibold transition whitespace-nowrap',
          tab === key
            ? 'bg-green-600 text-white shadow-soft'
            : 'text-ink-600 hover:bg-green-50',
        ]"
      >
        {{ label }}
      </button>
    </nav>

    <!-- Diario y ciclos (informativo) -->
    <section v-if="tab === 'diario'" class="space-y-6 fade-in-up">
      <!-- Resumen del modelo -->
      <div class="card p-6">
        <h2 class="section-title">Modelo del diario</h2>
        <p class="section-subtitle mb-5">
          Sami trabaja con un diario libre. El alumno no responde un
          cuestionario: escribe, y el sistema infiere los ítems clínicos
          desde su texto.
        </p>
        <div class="grid sm:grid-cols-3 gap-4">
          <div class="card p-4">
            <p
              class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
            >
              Duración del ciclo
            </p>
            <p class="text-2xl font-semibold text-ink-900 mt-1">14 días</p>
            <p class="text-xs text-ink-500 mt-1">
              Ventana del DSM-5 / PHQ-A / GAD-7
            </p>
          </div>
          <div class="card p-4">
            <p
              class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
            >
              Inicio del ciclo
            </p>
            <p class="text-2xl font-semibold text-ink-900 mt-1">
              Primera entrada
            </p>
            <p class="text-xs text-ink-500 mt-1">
              Reloj personal por alumno
            </p>
          </div>
          <div class="card p-4">
            <p
              class="text-[11px] uppercase tracking-wider text-ink-500 font-semibold"
            >
              Cierre del ciclo
            </p>
            <p class="text-2xl font-semibold text-ink-900 mt-1">
              Automático
            </p>
            <p class="text-xs text-ink-500 mt-1">
              Adelantado si hay cita de crisis
            </p>
          </div>
        </div>
      </div>

      <!-- Tabla Johnson 2002 -->
      <div class="card p-6">
        <h2 class="section-title">Tabla días-con-síntoma → puntos Likert</h2>
        <p class="section-subtitle mb-4">
          Traducción literal de las frases oficiales del PHQ-A (Johnson, 2002).
          Esta tabla es la base del scoring del ciclo y NO es editable.
        </p>
        <table class="w-full text-sm">
          <thead
            class="text-xs uppercase tracking-wider text-ink-500 text-left"
          >
            <tr class="border-b border-ink-100">
              <th class="py-2 pr-3 font-medium">Días con el síntoma</th>
              <th class="py-2 pr-3 font-medium">Puntos</th>
              <th class="py-2 font-medium">Frase oficial</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in TABLA_JOHNSON"
              :key="r.dias"
              class="border-b border-ink-50 last:border-0"
            >
              <td class="py-2 pr-3 text-ink-900 font-medium">{{ r.dias }}</td>
              <td class="py-2 pr-3 font-semibold text-green-700">
                {{ r.puntos }}
              </td>
              <td class="py-2 text-ink-700">{{ r.frase }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Severidad -->
      <div class="grid md:grid-cols-2 gap-6">
        <div class="card p-6">
          <h2 class="section-title">Severidad PHQ-A (0 – 27)</h2>
          <p class="section-subtitle mb-4">
            Puntos de corte oficiales (Kroenke & Spitzer, 2001).
          </p>
          <table class="w-full text-sm">
            <thead
              class="text-xs uppercase tracking-wider text-ink-500 text-left"
            >
              <tr class="border-b border-ink-100">
                <th class="py-2 pr-3 font-medium">Rango</th>
                <th class="py-2 font-medium">Nivel</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in SEVERIDAD_PHQA"
                :key="r.rango"
                class="border-b border-ink-50 last:border-0"
              >
                <td class="py-2 pr-3 font-mono tabular-nums">{{ r.rango }}</td>
                <td class="py-2 text-ink-700">{{ r.nivel }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="card p-6">
          <h2 class="section-title">Severidad GAD-7 (0 – 21)</h2>
          <p class="section-subtitle mb-4">
            Puntos de corte oficiales (Spitzer & Löwe, 2006).
          </p>
          <table class="w-full text-sm">
            <thead
              class="text-xs uppercase tracking-wider text-ink-500 text-left"
            >
              <tr class="border-b border-ink-100">
                <th class="py-2 pr-3 font-medium">Rango</th>
                <th class="py-2 font-medium">Nivel</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="r in SEVERIDAD_GAD"
                :key="r.rango"
                class="border-b border-ink-50 last:border-0"
              >
                <td class="py-2 pr-3 font-mono tabular-nums">{{ r.rango }}</td>
                <td class="py-2 text-ink-700">{{ r.nivel }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Ítems PHQ-A / GAD-7 -->
      <div class="grid md:grid-cols-2 gap-6">
        <div class="card p-6">
          <h2 class="section-title">Ítems PHQ-A (depresión)</h2>
          <p class="section-subtitle mb-4">
            9 ítems alineados a criterios del DSM-5.
          </p>
          <ul class="space-y-2 text-sm">
            <li
              v-for="it in ITEMS_PHQA"
              :key="it.id"
              class="flex items-start gap-2"
            >
              <span class="dsm5-tag shrink-0">{{ it.id }}</span>
              <span class="text-ink-800">{{ it.criterio }}</span>
            </li>
          </ul>
        </div>
        <div class="card p-6">
          <h2 class="section-title">Ítems GAD-7 (ansiedad)</h2>
          <p class="section-subtitle mb-4">
            7 ítems alineados a criterios del DSM-5.
          </p>
          <ul class="space-y-2 text-sm">
            <li
              v-for="it in ITEMS_GAD"
              :key="it.id"
              class="flex items-start gap-2"
            >
              <span class="dsm5-tag shrink-0">{{ it.id }}</span>
              <span class="text-ink-800">{{ it.criterio }}</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- Criterios DSM-5 -->
      <div class="card p-6">
        <h2 class="section-title">Criterios DSM-5 que el sistema verifica</h2>
        <p class="section-subtitle mb-4">
          El sistema marca "posible riesgo" cuando el patrón coincide
          con los umbrales mínimos del manual. NO emite diagnóstico.
        </p>
        <div class="grid md:grid-cols-2 gap-4">
          <div class="bg-ink-50 rounded-xl p-4">
            <p class="font-semibold text-ink-900 mb-1">
              Posible riesgo de Episodio Depresivo Mayor
            </p>
            <p class="text-sm text-ink-700">
              ≥ 5 ítems PHQ-A con puntaje ≥ 2 y al menos uno debe ser
              ánimo deprimido (phq9_2) o anhedonia (phq9_1).
            </p>
          </div>
          <div class="bg-ink-50 rounded-xl p-4">
            <p class="font-semibold text-ink-900 mb-1">
              Posible riesgo de Trastorno de Ansiedad Generalizada
            </p>
            <p class="text-sm text-ink-700">
              Ítems gad7_1 (ansiedad) y gad7_2 (no controla la
              preocupación) cumplidos, y ≥ 3 ítems GAD-7 con puntaje ≥ 2.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Auditoría -->
    <section v-if="tab === 'auditoria'" class="card p-6 fade-in-up">
      <h2 class="section-title">Auditoría</h2>
      <p class="section-subtitle mb-4">Las últimas 50 llamadas a la API.</p>

      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead
            class="bg-white text-xs uppercase tracking-wider text-ink-500 text-left"
          >
            <tr>
              <th class="px-4 py-3">Hora</th>
              <th class="px-4 py-3">Usuario</th>
              <th class="px-4 py-3">Método</th>
              <th class="px-4 py-3">Endpoint</th>
              <th class="px-4 py-3">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-ink-100">
            <tr
              v-for="l in logs"
              :key="l.id"
              class="hover:bg-green-50/40 transition"
            >
              <td
                class="px-4 py-3 text-xs font-mono text-ink-500 whitespace-nowrap"
              >
                {{ new Date(l.timestamp).toLocaleString("es-PE") }}
              </td>
              <td class="px-4 py-3 text-sm">
                {{ l.email || "—" }}
                <span v-if="l.role" class="text-xs text-ink-400"
                  >· {{ l.role }}</span
                >
              </td>
              <td
                class="px-4 py-3 text-xs font-mono font-semibold text-green-700"
              >
                {{ l.method }}
              </td>
              <td
                class="px-4 py-3 text-xs font-mono truncate max-w-[280px] text-ink-700"
              >
                {{ l.endpoint }}
              </td>
              <td class="px-4 py-3">
                <span :class="statusChip(l.status_code)">{{
                  l.status_code
                }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Backups -->
    <section v-if="tab === 'backups'" class="card p-6 fade-in-up">
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 class="section-title">Respaldos</h2>
          <p class="section-subtitle">Copias locales de la base de datos.</p>
        </div>
        <button
          @click="crearBackup"
          :disabled="backupCreando"
          class="btn-primary"
        >
          {{ backupCreando ? "Creando…" : "+ Crear respaldo ahora" }}
        </button>
      </div>

      <p v-if="backupMensaje" class="text-sm text-ink-600 mt-3">
        {{ backupMensaje }}
      </p>

      <ul class="mt-5 divide-y divide-ink-100 border-t border-ink-100">
        <li
          v-for="b in backups"
          :key="b.archivo"
          class="py-3 flex justify-between items-center text-sm"
        >
          <div class="flex items-center gap-3 min-w-0">
            <span class="font-mono text-ink-700 truncate">{{ b.archivo }}</span>
          </div>
          <span class="chip-ink"
            >{{ (b.tamanio_bytes / 1024).toFixed(1) }} KB</span
          >
        </li>
        <li
          v-if="backups.length === 0"
          class="py-6 text-center text-ink-400 text-sm"
        >
          No hay respaldos aún.
        </li>
      </ul>
    </section>

    <!-- Motor de análisis -->
    <section v-if="tab === 'bert'" class="space-y-6 fade-in-up">
      <div class="card p-6">
        <h2 class="section-title">Motor de análisis</h2>
        <div v-if="modeloInfo" class="mt-3 space-y-2 text-sm">
          <div class="flex items-start gap-3 flex-wrap">
            <span class="dsm5-tag">{{
              modeloInfo.cargado ? "Cargado" : "No cargado"
            }}</span>
            <p class="text-ink-700">
              <strong>Modelo:</strong>
              <span class="font-mono text-xs">{{ modeloInfo.modelo }}</span>
            </p>
          </div>
          <button @click="recargarModelo" class="btn-secondary mt-3">
            Recargar modelo
          </button>
        </div>
      </div>

      <div class="card p-6">
        <h2 class="section-title">Umbrales por categoría</h2>
        <p class="section-subtitle mb-4">
          Porcentaje de confianza a partir del cual se eleva una alerta. El
          riesgo suicida tiene umbral más bajo por seguridad clínica.
        </p>

        <div v-if="umbrales" class="space-y-3">
          <div
            v-for="(cfg, clave) in umbrales"
            :key="clave"
            class="card-pastel p-4 flex items-center gap-4 flex-wrap"
          >
            <label class="flex-1 text-sm font-semibold text-ink-900">{{
              CONDICION_LABELS[clave] || clave
            }}</label>
            <input
              v-model.number="cfg.umbral"
              type="range"
              min="0"
              max="1"
              step="0.05"
              class="flex-1 max-w-xs accent-brand-500"
            />
            <input
              v-model.number="cfg.umbral"
              type="number"
              step="0.05"
              min="0"
              max="1"
              class="input w-24"
            />
            <span class="dsm5-tag w-16 justify-center"
              >{{ Math.round(cfg.umbral * 100) }}%</span
            >
          </div>
        </div>

        <button @click="guardarUmbrales" class="btn-primary mt-4">
          Guardar umbrales
        </button>
        <p v-if="bertMensaje" class="text-sm text-ink-600 mt-3">
          {{ bertMensaje }}
        </p>
      </div>
    </section>
  </div>
</template>
