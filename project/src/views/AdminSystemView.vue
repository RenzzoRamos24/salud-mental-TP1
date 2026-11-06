<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "../api";

const modelo = ref(null);
const backups = ref([]);
const stats = ref(null);
const statsCuest = ref(null);
const cargando = ref(true);
const error = ref("");
const procesando = ref(false);
const scheduler = ref(null);
const parametros = ref([]);
const edicion = ref({});          // clave -> valor tecleado
const errorParam = ref({});       // clave -> mensaje de validación
const mensajeParam = ref("");
const auditoria = ref([]);

async function cargarParametros() {
  const [ps, au, sch] = await Promise.all([
    api.adminListarConfiguracion().catch(() => []),
    api.adminAuditoriaConfiguracion(20).catch(() => []),
    api.adminSchedulerInfo().catch(() => null),
  ]);
  parametros.value = ps || [];
  auditoria.value = au || [];
  scheduler.value = sch;
  edicion.value = Object.fromEntries((ps || []).map((p) => [p.clave, p.valor]));
}

async function guardarParametro(p) {
  errorParam.value = { ...errorParam.value, [p.clave]: "" };
  mensajeParam.value = "";
  const valor = Number(edicion.value[p.clave]);
  if (!Number.isInteger(valor)) {
    errorParam.value = { ...errorParam.value, [p.clave]: "Debe ser un número entero." };
    return;
  }
  try {
    const r = await api.adminActualizarConfiguracion(p.clave, valor);
    mensajeParam.value = r.cambio
      ? `${p.etiqueta}: guardado (${r.anterior} → ${r.valor} ${p.unidad}).`
      : `${p.etiqueta}: sin cambios.`;
    await cargarParametros();
  } catch (e) {
    errorParam.value = {
      ...errorParam.value,
      [p.clave]: e?.response?.data?.detail || "No se pudo guardar.",
    };
  }
}

function fmtFecha(iso) {
  if (!iso) return "—";
  return new Date(iso.endsWith("Z") ? iso : iso + "Z").toLocaleString("es-PE");
}

async function cargar() {
  cargando.value = true;
  try {
    const [m, b, s, sc] = await Promise.all([
      api.adminGetModeloInfo().catch(() => null),
      api.adminListarBackups().catch(() => []),
      api.statsUsuarios().catch(() => null),
      api.adminStatsCuestionarios().catch(() => null),
    ]);
    await cargarParametros();
    modelo.value = m;
    backups.value = b || [];
    stats.value = s;
    statsCuest.value = sc;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

async function crearBackup() {
  procesando.value = true;
  try {
    await api.adminCrearBackup();
    backups.value = await api.adminListarBackups();
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo crear backup.");
  } finally {
    procesando.value = false;
  }
}

async function recargarModelo() {
  procesando.value = true;
  try {
    await api.adminRecargarModelo();
    modelo.value = await api.adminGetModeloInfo();
    alert("Modelo BETO recargado correctamente.");
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo recargar.");
  } finally {
    procesando.value = false;
  }
}

onMounted(cargar);

const ultimoBackup = computed(() => {
  if (!backups.value.length) return null;
  return backups.value[0];
});

function fmt(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fmtBytes(n) {
  if (!n) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Sistema</p>
      <h1 class="hero-serif text-[28px]">
        Configuración y <span class="hero-mint">monitoreo</span>
      </h1>
      <p class="text-ink-500 mt-2 text-sm">
        Estado de los componentes técnicos del sistema Sami, modelos de
        inteligencia artificial, respaldos automáticos y métricas operacionales.
      </p>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <!-- ── KPIs generales ────────────────────────────────────── -->
      <div class="grid sm:grid-cols-4 gap-3 mb-6">
        <div class="card p-4">
          <p class="text-xs text-ink-400">Estado de la plataforma</p>
          <p class="text-lg font-semibold text-green-700 mt-1">
            🟢 Operativa
          </p>
          <p class="text-xs text-ink-500 mt-1">Azure App Service Linux B2</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Modelo NLP (BETO)</p>
          <p class="text-lg font-semibold mt-1" :class="modelo?.cargado ? 'text-green-700' : 'text-amber-600'">
            {{ modelo?.cargado ? "🟢 Cargado" : "⚪ En espera" }}
          </p>
          <p class="text-xs text-ink-500 mt-1">
            {{ (modelo?.categorias || []).length }} categorías emocionales
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Modelo SVM (DASS-21)</p>
          <p class="text-lg font-semibold text-green-700 mt-1">🟢 Activo</p>
          <p class="text-xs text-ink-500 mt-1">Segunda opinión clínica</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Último respaldo</p>
          <p class="text-sm font-semibold mt-1">
            {{ ultimoBackup ? fmt(ultimoBackup.fecha) : "Sin respaldos" }}
          </p>
          <p class="text-xs text-ink-500 mt-1">
            Backup automático diario a las 02:00
          </p>
        </div>
      </div>

      <!-- ── Resumen operativo ─────────────────────────────────── -->
      <h2 class="text-lg font-semibold mb-3 text-green-900">
        Resumen operativo del sistema
      </h2>
      <div class="grid sm:grid-cols-3 gap-3 mb-6">
        <div class="card p-4">
          <p class="text-xs text-ink-400">Usuarios totales</p>
          <p class="text-xl font-semibold">{{ stats?.total || 0 }}</p>
          <p class="text-xs text-ink-500 mt-1">
            {{ stats?.estudiantes || 0 }} estudiantes ·
            {{ stats?.psicologos || 0 }} psicólogas ·
            {{ stats?.admins || 0 }} admins
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Cuestionarios aplicados</p>
          <p class="text-xl font-semibold">{{ statsCuest?.total_asignados || 0 }}</p>
          <p class="text-xs text-ink-500 mt-1">
            {{ statsCuest?.total_plantillas || 0 }} plantillas activas ·
            {{ statsCuest?.tasa_completitud_pct || 0 }}% completitud
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Banco clínico</p>
          <p class="text-xl font-semibold">7 instrumentos</p>
          <p class="text-xs text-ink-500 mt-1">
            PHQ-A, GAD-7, SRQ-20, RSES, WHO-5, UCLA-3, DASS-21
          </p>
        </div>
      </div>

      <!-- ── Modelo NLP (BETO) ─────────────────────────────────── -->
      <div class="card p-6 mb-4">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-green-900">
            Modelo de NLP — BETO (zero-shot multilabel)
          </h2>
          <button
            class="btn-ghost btn-sm"
            :disabled="procesando"
            @click="recargarModelo"
          >
            {{ procesando ? "Procesando…" : "Recargar modelo" }}
          </button>
        </div>
        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <p class="text-xs text-ink-400">Identificador</p>
            <p class="text-sm font-mono mt-1">{{ modelo?.modelo || "—" }}</p>
          </div>
          <div>
            <p class="text-xs text-ink-400">Estado</p>
            <p class="text-sm mt-1">
              {{ modelo?.cargado ? "🟢 Cargado en memoria" : "⚪ Se cargará al primer uso" }}
            </p>
          </div>
          <div class="sm:col-span-2">
            <p class="text-xs text-ink-400">Categorías de clasificación</p>
            <p class="text-sm mt-1">
              {{ (modelo?.categorias || []).join(" · ") || "—" }}
            </p>
          </div>
        </div>
      </div>

      <!-- ── Modelo SVM ─────────────────────────────────────────── -->
      <div class="card p-6 mb-4">
        <h2 class="text-lg font-semibold mb-3 text-green-900">
          Modelo de Machine Learning — SVM sobre DASS-21
        </h2>
        <div class="grid sm:grid-cols-2 gap-4">
          <div>
            <p class="text-xs text-ink-400">Algoritmo</p>
            <p class="text-sm mt-1">SVC con kernel RBF + StandardScaler</p>
          </div>
          <div>
            <p class="text-xs text-ink-400">Dataset de entrenamiento</p>
            <p class="text-sm mt-1">
              DASS-42 (Open Psychometrics) · 7 269 adolescentes 13–17 años
            </p>
          </div>
          <div>
            <p class="text-xs text-ink-400">Métricas (test held-out 20 %)</p>
            <p class="text-sm mt-1">
              F1-macro <span class="font-semibold">0.92</span> · ROC-AUC
              <span class="font-semibold">0.998</span> · Accuracy
              <span class="font-semibold">0.97</span>
            </p>
          </div>
          <div>
            <p class="text-xs text-ink-400">Rol clínico</p>
            <p class="text-sm mt-1">
              Segunda opinión sobre escala DASS-21 — no reemplaza criterio
              profesional
            </p>
          </div>
        </div>
      </div>

      <!-- ── Tareas programadas (estado real del planificador) ─────── -->
      <div class="card p-6 mb-4">
        <h2 class="text-lg font-semibold mb-3 text-green-900">
          Tareas programadas (APScheduler)
        </h2>
        <p v-if="!scheduler" class="text-sm text-ink-500">
          No se pudo consultar el estado del planificador.
        </p>
        <template v-else>
          <p class="text-sm mb-3">
            Estado:
            <strong :class="scheduler.activo ? 'text-green-700' : 'text-red-700'">
              {{ scheduler.activo ? "activo" : "detenido" }}
            </strong>
            <span v-if="scheduler.activo" class="text-ink-500">
              · respaldo diario a las {{ String(scheduler.hora_diaria).padStart(2, "0") }}:00
              · retención {{ scheduler.retencion_dias }} días
            </span>
          </p>
          <ul v-if="scheduler.jobs?.length" class="text-sm space-y-2">
            <li
              v-for="j in scheduler.jobs"
              :key="j.id"
              class="flex justify-between py-2 border-b border-cream-200 last:border-0"
            >
              <span>{{ j.name }}</span>
              <span class="text-ink-500 text-xs">próxima ejecución: {{ fmtFecha(j.next_run) }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-ink-500">No hay tareas registradas.</p>
        </template>
      </div>

      <!-- ── Parámetros generales (HU0021) ─────────────────────────── -->
      <div class="card p-6 mb-4" data-testid="parametros-generales">
        <h2 class="text-lg font-semibold mb-1 text-green-900">Parámetros generales</h2>
        <p class="text-xs text-ink-500 mb-4">
          Cada valor tiene un rango permitido. Los cambios quedan registrados.
        </p>
        <p v-if="mensajeParam" class="banner-success mb-3">{{ mensajeParam }}</p>
        <div class="grid gap-4">
          <form
            v-for="p in parametros"
            :key="p.clave"
            class="grid sm:grid-cols-[1fr_auto] gap-3 items-end"
            @submit.prevent="guardarParametro(p)"
          >
            <div>
              <label class="label" :for="`par-${p.clave}`">
                {{ p.etiqueta }} ({{ p.unidad }})
              </label>
              <input
                :id="`par-${p.clave}`"
                v-model.number="edicion[p.clave]"
                type="number"
                class="input"
                :min="p.min"
                :max="p.max"
              />
              <p class="field-hint">
                {{ p.descripcion }} Rango {{ p.min }}–{{ p.max }}; por defecto {{ p.por_defecto }}.
              </p>
              <p v-if="errorParam[p.clave]" class="field-error">{{ errorParam[p.clave] }}</p>
            </div>
            <button type="submit" class="btn-primary">Guardar</button>
          </form>
        </div>

        <h3 class="text-sm font-semibold mt-6 mb-2 text-green-900">
          Auditoría de cambios (últimos 20)
        </h3>
        <p v-if="!auditoria.length" class="text-sm text-ink-500">
          Todavía no hay cambios de configuración.
        </p>
        <table v-else class="w-full text-sm" data-testid="auditoria-configuracion">
          <thead>
            <tr class="text-left text-xs text-ink-400">
              <th class="py-1">Fecha</th><th>Parámetro</th><th>Antes</th><th>Después</th><th>Quién</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in auditoria" :key="a.id" class="border-t border-cream-200">
              <td class="py-1">{{ fmtFecha(a.timestamp) }}</td>
              <td>{{ a.etiqueta }}</td>
              <td>{{ a.valor_anterior }}</td>
              <td>{{ a.valor_nuevo }}</td>
              <td>{{ a.usuario || "—" }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ── Respaldos ─────────────────────────────────────────── -->
      <div class="card p-6">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-green-900">
            Respaldos de la base de datos
          </h2>
          <button class="btn-mint btn-sm" :disabled="procesando" @click="crearBackup">
            {{ procesando ? "Creando…" : "+ Crear respaldo manual" }}
          </button>
        </div>
        <div v-if="backups.length === 0" class="text-sm text-ink-500">
          No hay respaldos registrados todavía.
        </div>
        <ul v-else class="text-sm space-y-1">
          <li
            v-for="b in backups.slice(0, 10)"
            :key="b.archivo"
            class="flex justify-between border-b border-cream-200 py-2"
          >
            <span class="font-mono text-xs">{{ b.archivo }}</span>
            <span class="text-xs text-ink-400 flex gap-3">
              <span>{{ fmtBytes(b.tamanio_bytes) }}</span>
              <span>{{ fmt(b.fecha) }}</span>
            </span>
          </li>
        </ul>
        <p v-if="backups.length > 10" class="text-xs text-ink-400 mt-2">
          Mostrando 10 de {{ backups.length }} respaldos
        </p>
      </div>
    </template>
  </div>
</template>
