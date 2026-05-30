<script setup>
import { ref, onMounted, computed, reactive } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import PageHeader from "../components/PageHeader.vue";
import StatCard from "../components/StatCard.vue";
import RiskBadge from "../components/RiskBadge.vue";

const router = useRouter();

const estudiantes = ref([]);
const stats = ref(null);
const citas = ref([]);
const cargando = ref(true);
const error = ref("");
const filtro = ref("");

// Modal cita
const modalCita = reactive({
  abierto: false,
  estudiante: null,
  fecha: "",
  hora: "",
  modalidad: "presencial",
  notas: "",
  es_crisis: false,
  guardando: false,
  error: "",
});

// Modal "completar sesión" — pide resumen para el estudiante
const modalCompletar = reactive({
  abierto: false,
  cita: null,
  resumen: "",
  guardando: false,
  error: "",
});

function abrirModalCompletar(cita) {
  modalCompletar.abierto = true;
  modalCompletar.cita = cita;
  modalCompletar.resumen = cita.resumen_para_estudiante || "";
  modalCompletar.error = "";
}
function cerrarModalCompletar() {
  modalCompletar.abierto = false;
  modalCompletar.cita = null;
}

async function confirmarCompletar() {
  modalCompletar.error = "";
  modalCompletar.guardando = true;
  try {
    await api.actualizarCita(modalCompletar.cita.id, {
      estado: "completada",
      resumen_para_estudiante: modalCompletar.resumen.trim() || null,
    });
    cerrarModalCompletar();
    await cargarTodo();
  } catch (e) {
    modalCompletar.error = e.response?.data?.detail || e.message;
  } finally {
    modalCompletar.guardando = false;
  }
}

async function cargarTodo() {
  try {
    cargando.value = true;
    const [s, st, c] = await Promise.all([
      api.listarEstudiantes(),
      api.dashboardStats().catch(() => null),
      api.listarCitas().catch(() => []),
    ]);
    estudiantes.value = s;
    stats.value = st;
    citas.value = c;
  } catch (e) {
    error.value = e.response?.data?.detail || e.message;
  } finally {
    cargando.value = false;
  }
}

onMounted(cargarTodo);

const filtrados = computed(() => {
  const q = filtro.value.trim().toLowerCase();
  if (!q) return estudiantes.value;
  return estudiantes.value.filter(
    (e) =>
      e.nombre.toLowerCase().includes(q) ||
      e.apellido.toLowerCase().includes(q) ||
      e.email.toLowerCase().includes(q),
  );
});

const alertas = computed(() => stats.value?.estudiantes_en_alerta || []);
const distribucion = computed(() => stats.value?.distribucion_riesgo || {});
const citasProximas = computed(() =>
  (citas.value || []).filter((c) => c.estado !== "cancelada").slice(0, 6),
);

function fechaCorta(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function abrirHistorial(student_id) {
  router.push(`/psicologo/estudiante/${student_id}`);
}

function abrirModalCita(est) {
  modalCita.abierto = true;
  modalCita.estudiante = est;
  modalCita.fecha = "";
  modalCita.hora = "";
  modalCita.modalidad = "presencial";
  modalCita.notas = "";
  modalCita.es_crisis = false;
  modalCita.error = "";
}
function cerrarModal() {
  modalCita.abierto = false;
}

async function guardarCita() {
  modalCita.error = "";
  if (!modalCita.fecha || !modalCita.hora) {
    modalCita.error = "Fecha y hora son obligatorias";
    return;
  }
  modalCita.guardando = true;
  try {
    await api.crearCita({
      estudiante_id: modalCita.estudiante.id,
      fecha: modalCita.fecha,
      hora: modalCita.hora,
      modalidad: modalCita.modalidad,
      notas: modalCita.notas || null,
      es_crisis: modalCita.es_crisis,
    });
    cerrarModal();
    await cargarTodo();
  } catch (e) {
    modalCita.error = e.response?.data?.detail || e.message;
  } finally {
    modalCita.guardando = false;
  }
}

async function actualizarEstadoCita(c, estado) {
  try {
    await api.actualizarCita(c.id, { estado });
    await cargarTodo();
  } catch (e) {
    alert(e.response?.data?.detail || e.message);
  }
}
async function cancelarCita(c) {
  if (!confirm("¿Cancelar esta cita?")) return;
  try {
    await api.cancelarCita(c.id);
    await cargarTodo();
  } catch (e) {
    alert(e.response?.data?.detail || e.message);
  }
}
</script>

<template>
  <div class="page-shell-wide">
    <PageHeader
      title="Panel"
      accent="clínico"
      subtitle="Cómo está cada estudiante y tus próximas citas."
      tone="brand"
    />

    <div v-if="cargando" class="text-center text-ink-500 py-12">
      Cargando panel…
    </div>
    <p v-else-if="error" class="banner-danger">{{ error }}</p>

    <template v-else>
      <!-- Métricas (HU-15) -->
      <section
        v-if="stats"
        class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-6"
      >
        <StatCard label="Total" :value="stats.total_estudiantes" tone="brand" />
        <StatCard
          label="CRÍTICO"
          :value="distribucion['CRÍTICO'] || 0"
          tone="risk-critico"
        />
        <StatCard
          label="ALTO"
          :value="distribucion['ALTO'] || 0"
          tone="risk-alto"
        />
        <StatCard
          label="MEDIO"
          :value="distribucion['MEDIO'] || 0"
          tone="risk-medio"
        />
        <StatCard
          label="BAJO / Sin eval"
          :value="(distribucion['BAJO'] || 0) + (distribucion['SIN_EVAL'] || 0)"
          tone="risk-bajo"
        />
      </section>

      <!-- Alertas tempranas (HU-16) -->
      <section
        v-if="alertas.length > 0"
        class="card border-red-200 border-l-4 p-6 mb-6 fade-in-up"
      >
        <h2 class="section-title text-risk-critico">
          Necesitan atención ahora
        </h2>
        <p class="section-subtitle mb-4">
          {{ alertas.length }} estudiante(s) en riesgo crítico o alto.
        </p>
        <div class="space-y-2">
          <div
            v-for="est in alertas"
            :key="est.id"
            class="flex items-center justify-between gap-3 p-3 bg-red-50 border border-red-100 rounded-xl"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div class="avatar-md bg-red-100 text-risk-critico shrink-0">
                {{ (est.nombre[0] + (est.apellido[0] || "")).toUpperCase() }}
              </div>
              <div class="min-w-0">
                <p class="font-semibold text-ink-900 truncate">
                  {{ est.nombre }} {{ est.apellido }}
                </p>
                <p class="text-xs text-ink-500 truncate">{{ est.email }}</p>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <RiskBadge :nivel="est.ultimo_riesgo" />
              <button @click="abrirModalCita(est)" class="btn-primary btn-sm">
                Agendar
              </button>
              <button
                @click="abrirHistorial(est.id)"
                class="btn-secondary btn-sm"
              >
                Historial
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Próximas citas (HU-19) -->
      <section v-if="citasProximas.length > 0" class="card p-6 mb-6 fade-in-up">
        <h2 class="section-title">Próximas citas</h2>
        <div class="space-y-2 mt-3">
          <div
            v-for="c in citasProximas"
            :key="c.id"
            class="flex items-center justify-between gap-3 p-3 rounded-xl border border-ink-100"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div class="avatar-md bg-green-50"></div>
              <div class="min-w-0">
                <p class="font-semibold text-ink-900 truncate flex items-center gap-2">
                  {{ c.estudiante_nombre }} {{ c.estudiante_apellido }}
                  <span
                    v-if="c.es_crisis"
                    class="text-[10px] uppercase tracking-wider bg-red-100 text-red-800 px-1.5 py-0.5 rounded font-semibold"
                  >
                    Crisis
                  </span>
                </p>
                <p class="text-xs text-ink-500">
                  {{ c.fecha }} · {{ c.hora }} ·
                  <span class="capitalize">{{ c.modalidad }}</span>
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span
                class="chip"
                :class="{
                  'chip-mint': c.estado === 'confirmada',
                  'chip-brand': c.estado === 'pendiente',
                  'chip-ink': c.estado === 'completada',
                  'chip-peach': c.estado === 'cancelada',
                }"
                >{{ c.estado }}</span
              >
              <button
                v-if="c.estado === 'pendiente'"
                @click="actualizarEstadoCita(c, 'confirmada')"
                class="btn-mint btn-sm"
              >
                Confirmar
              </button>
              <button
                v-if="c.estado === 'confirmada'"
                @click="abrirModalCompletar(c)"
                class="btn-secondary btn-sm"
              >
                Completada
              </button>
              <button
                v-if="c.estado !== 'cancelada' && c.estado !== 'completada'"
                @click="cancelarCita(c)"
                class="btn-ghost btn-sm"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Estudiantes -->
      <section class="card overflow-hidden fade-in-up">
        <div
          class="p-5 flex items-center justify-between gap-3 border-b border-ink-100 flex-wrap"
        >
          <div>
            <h2 class="section-title !mb-0">Estudiantes a tu cargo</h2>
            <p class="section-subtitle">{{ estudiantes.length }} en total</p>
          </div>
          <input
            v-model="filtro"
            type="text"
            placeholder="Buscar por nombre o correo"
            class="input w-72"
          />
        </div>

        <p v-if="filtrados.length === 0" class="text-center text-ink-500 py-12">
          No se encontraron estudiantes.
        </p>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead
              class="bg-white text-ink-500 text-left text-xs uppercase tracking-wider"
            >
              <tr>
                <th class="px-5 py-3">Estudiante</th>
                <th class="px-5 py-3">Correo</th>
                <th class="px-5 py-3 text-center">Entradas diario</th>
                <th class="px-5 py-3">Último riesgo</th>
                <th class="px-5 py-3">Última entrada</th>
                <th class="px-5 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-ink-100">
              <tr
                v-for="e in filtrados"
                :key="e.id"
                class="hover:bg-green-50/50 transition"
              >
                <td class="px-5 py-3">
                  <div class="flex items-center gap-3">
                    <div class="avatar-sm">
                      {{ (e.nombre[0] + (e.apellido[0] || "")).toUpperCase() }}
                    </div>
                    <p class="font-semibold text-ink-900">
                      {{ e.nombre }} {{ e.apellido }}
                    </p>
                  </div>
                </td>
                <td class="px-5 py-3 text-ink-600 font-mono text-xs">
                  {{ e.email }}
                </td>
                <td class="px-5 py-3 text-center">
                  <span class="text-ink-900 font-semibold">{{
                    e.total_entradas_diario || 0
                  }}</span>
                </td>
                <td class="px-5 py-3">
                  <RiskBadge :nivel="e.ultimo_riesgo" />
                </td>
                <td class="px-5 py-3 text-ink-600">
                  {{ fechaCorta(e.ultima_evaluacion) }}
                </td>
                <td class="px-5 py-3 text-right whitespace-nowrap">
                  <button
                    @click="abrirModalCita(e)"
                    class="btn-secondary btn-sm mr-2"
                  >
                    Agendar
                  </button>
                  <button
                    @click="abrirHistorial(e.id)"
                    class="btn-primary btn-sm"
                  >
                    Historial
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>

    <!-- Modal cita -->
    <Teleport to="body">
      <div
        v-if="modalCita.abierto"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm fade-in-up"
        @click.self="cerrarModal"
      >
        <div class="card-hero w-full max-w-md p-6">
          <h2 class="text-xl font-bold text-ink-900 mb-1">Agendar cita</h2>
          <p class="text-sm text-ink-500 mb-5">
            Estudiante:
            <strong
              >{{ modalCita.estudiante?.nombre }}
              {{ modalCita.estudiante?.apellido }}</strong
            >
          </p>

          <div class="space-y-3">
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="label">Fecha</label>
                <input v-model="modalCita.fecha" type="date" class="input" />
              </div>
              <div>
                <label class="label">Hora</label>
                <input v-model="modalCita.hora" type="time" class="input" />
              </div>
            </div>
            <div>
              <label class="label">Modalidad</label>
              <select v-model="modalCita.modalidad" class="input">
                <option value="presencial">Presencial</option>
                <option value="virtual">Virtual</option>
              </select>
            </div>
            <div>
              <label class="label"
                >Notas
                <span class="text-ink-400 font-normal">(opcional)</span></label
              >
              <textarea
                v-model="modalCita.notas"
                rows="3"
                class="input resize-none"
                placeholder="Motivo, acuerdos, link de la sesión virtual…"
              ></textarea>
            </div>

            <label
              class="flex items-start gap-3 rounded-md border border-ink-100 p-3 cursor-pointer hover:border-red-400"
              :class="modalCita.es_crisis ? 'border-red-500 bg-red-50' : ''"
            >
              <input
                type="checkbox"
                v-model="modalCita.es_crisis"
                class="mt-0.5"
              />
              <span class="text-sm leading-snug">
                <strong class="text-red-800">Atención de crisis</strong>
                <span class="block text-ink-600 mt-0.5">
                  Marca solo si esta cita responde a una situación de
                  riesgo. Al completarla, adelanta el cierre del ciclo en
                  curso.
                </span>
              </span>
            </label>

            <p v-if="modalCita.error" class="field-error">
              {{ modalCita.error }}
            </p>

            <div class="flex gap-2 pt-2">
              <button
                @click="cerrarModal"
                :disabled="modalCita.guardando"
                class="btn-ghost flex-1"
              >
                Cancelar
              </button>
              <button
                @click="guardarCita"
                :disabled="modalCita.guardando"
                class="btn-primary flex-1"
              >
                {{ modalCita.guardando ? "Guardando…" : "Agendar" }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Modal: completar sesión y dejar resumen para el estudiante -->
    <Teleport to="body">
      <div
        v-if="modalCompletar.abierto"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 backdrop-blur-sm fade-in-up"
        @click.self="cerrarModalCompletar"
      >
        <div class="card-hero w-full max-w-lg p-6">
          <h2 class="text-xl font-bold text-ink-900 mb-1">Cerrar sesión</h2>
          <p class="text-sm text-ink-500 mb-4">
            Con
            <strong>
              {{ modalCompletar.cita?.estudiante_nombre }}
              {{ modalCompletar.cita?.estudiante_apellido }}
            </strong>
            · {{ modalCompletar.cita?.fecha }} ·
            {{ modalCompletar.cita?.hora?.slice(0, 5) }}
          </p>

          <label class="label">Resumen para el estudiante</label>
          <p class="text-xs text-ink-500 mb-2 leading-relaxed">
            Lo que escribas acá lo verá el estudiante en su panel "Mi proceso".
            Frases cortas, claras, acuerdos concretos. NO incluyas
            diagnósticos ni notas clínicas privadas.
          </p>
          <textarea
            v-model="modalCompletar.resumen"
            rows="5"
            maxlength="2000"
            class="input resize-none"
            placeholder="Ej: Conversamos sobre el agotamiento por exámenes. Acordamos: dormir antes de las 12, ejercicio dos veces por semana, volver a vernos en 14 días."
          ></textarea>
          <p class="text-xs text-ink-500 mt-1 text-right">
            {{ modalCompletar.resumen.length }}/2000
          </p>

          <p v-if="modalCompletar.error" class="field-error mt-2">
            {{ modalCompletar.error }}
          </p>

          <div class="flex gap-2 pt-4">
            <button
              @click="cerrarModalCompletar"
              :disabled="modalCompletar.guardando"
              class="btn-ghost flex-1"
            >
              Cancelar
            </button>
            <button
              @click="confirmarCompletar"
              :disabled="modalCompletar.guardando"
              class="btn-primary flex-1"
            >
              {{ modalCompletar.guardando ? "Guardando…" : "Marcar como completada" }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
