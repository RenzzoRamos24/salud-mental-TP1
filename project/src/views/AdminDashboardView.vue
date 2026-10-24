<script setup>
import { ref, computed, onMounted } from "vue";
import { api } from "../api";

const stats = ref(null);
const usuarios = ref([]);
const cargando = ref(true);
const error = ref("");
const filtroRol = ref("");
const procesando = ref(null);

async function cargar() {
  cargando.value = true;
  try {
    const [s, u] = await Promise.all([
      api.statsUsuarios(),
      api.listarUsuarios(),
    ]);
    stats.value = s;
    usuarios.value = u;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

const psicologas = computed(() =>
  usuarios.value.filter((u) => u.role === "psicologo" && u.activo),
);

const estudiantes = computed(() =>
  usuarios.value.filter((u) => u.role === "estudiante"),
);

const filtrados = computed(() => {
  if (!filtroRol.value) return usuarios.value;
  return usuarios.value.filter((u) => u.role === filtroRol.value);
});

// Dos columnas (psicólogas | alumnos), 30 por página cada una. Con 232
// alumnos, una lista única tapaba todo lo demás.
const POR_PAGINA = 30;
const pagPsico = ref(1);
const pagAlum = ref(1);
const totalPagPsico = computed(() =>
  Math.max(1, Math.ceil(todasPsicologas.value.length / POR_PAGINA)),
);
const totalPagAlum = computed(() =>
  Math.max(1, Math.ceil(estudiantes.value.length / POR_PAGINA)),
);
const psicoPagina = computed(() =>
  todasPsicologas.value.slice((pagPsico.value - 1) * POR_PAGINA, pagPsico.value * POR_PAGINA),
);
const alumPagina = computed(() =>
  estudiantes.value.slice((pagAlum.value - 1) * POR_PAGINA, pagAlum.value * POR_PAGINA),
);
function rango(pag, total) {
  if (!total) return "0";
  const desde = (pag - 1) * POR_PAGINA + 1;
  const hasta = Math.min(pag * POR_PAGINA, total);
  return `${desde}–${hasta} de ${total}`;
}

// Todas las cuentas de psicóloga, activas o no (la de `psicologas` de arriba
// filtra activas porque alimenta el selector de asignación).
const todasPsicologas = computed(() =>
  usuarios.value.filter((u) => u.role === "psicologo"),
);

// Las cuentas por código las crea el propio sistema con un correo interno
// (admin.py: "@piloto.sami.local" para alumnos, "@evaluador.sami.local" para
// evaluadoras). Entran solo con el código, así que no tiene sentido
// ofrecerles un reset de contraseña.
function esCuentaCodigo(u) {
  return (u.email || "").endsWith(".sami.local");
}

async function asignarPsico(est, psicologo_id) {
  procesando.value = est.id;
  try {
    await api.asignarPsicologo(est.id, psicologo_id || null);
    est.psicologo_id = psicologo_id || null;
  } catch (e) {
    alert(e?.response?.data?.detail || "No se pudo asignar.");
  } finally {
    procesando.value = null;
  }
}

// ── Restablecer contraseña ──────────────────────────────────────────────
// El admin fija una clave nueva; nunca ve la anterior (bcrypt no se revierte).
const resetTarget = ref(null);
const resetPwd = ref("");
const resetPwd2 = ref("");
const resetBusy = ref(false);
const resetError = ref("");
const resetOk = ref("");

// ── Crear psicóloga (con equipo opcional) ──────────────────────────────
// Candidatas a titular: psicólogas que entran con correo (no evaluadoras por
// código) y que no son a su vez integrantes de otro equipo.
const titulares = computed(() =>
  todasPsicologas.value.filter((p) => !esCuentaCodigo(p) && !p.equipo_titular_id),
);
// Por defecto, la titular con más alumnos a cargo (en el piloto, el Equipo
// Psicopedagógico Cervantes): es a quien se suelen sumar las nuevas.
const titularSugerida = computed(() => {
  const conteo = {};
  for (const e of estudiantes.value) {
    if (e.psicologo_id) conteo[e.psicologo_id] = (conteo[e.psicologo_id] || 0) + 1;
  }
  const ids = new Set(titulares.value.map((p) => p.id));
  let mejor = null;
  for (const [id, n] of Object.entries(conteo)) {
    if (ids.has(id) && (!mejor || n > mejor.n)) mejor = { id, n };
  }
  return mejor?.id || "";
});
function nombreDe(id) {
  const p = usuarios.value.find((u) => u.id === id);
  return p ? `${p.nombre} ${p.apellido}` : "—";
}

const nueva = ref(null); // null = formulario cerrado
const nuevaPwd2 = ref("");
const creando = ref(false);
const errorNueva = ref("");
const okNueva = ref("");

function abrirNueva() {
  nueva.value = {
    nombre: "",
    apellido: "",
    email: "",
    password: "",
    equipo_titular_id: titularSugerida.value,
  };
  nuevaPwd2.value = "";
  errorNueva.value = "";
  okNueva.value = "";
}
async function crearPsicologa() {
  errorNueva.value = "";
  okNueva.value = "";
  const n = nueva.value;
  if (!n.nombre.trim() || !n.apellido.trim() || !n.email.trim()) {
    errorNueva.value = "Completa nombre, apellido y correo.";
    return;
  }
  if (n.password.length < 8) {
    errorNueva.value = "La contraseña debe tener al menos 8 caracteres.";
    return;
  }
  if (n.password !== nuevaPwd2.value) {
    errorNueva.value = "Las dos contraseñas no coinciden.";
    return;
  }
  creando.value = true;
  try {
    const r = await api.adminCrearPsicologa({
      ...n,
      equipo_titular_id: n.equipo_titular_id || null,
    });
    const msg =
      `Cuenta creada: ${r.nombre} (${r.email})` +
      (r.equipo_titular_id ? ` · equipo de ${nombreDe(r.equipo_titular_id)}` : "") +
      ".";
    await cargar();
    // Deja el formulario listo para la siguiente, con el mismo equipo.
    const equipo = n.equipo_titular_id;
    abrirNueva(); // limpia campos y mensajes
    nueva.value.equipo_titular_id = equipo;
    okNueva.value = msg;
  } catch (e) {
    errorNueva.value = e?.response?.data?.detail || "No se pudo crear la cuenta.";
  } finally {
    creando.value = false;
  }
}

function abrirReset(u) {
  resetTarget.value = u;
  resetPwd.value = "";
  resetPwd2.value = "";
  resetError.value = "";
  resetOk.value = "";
}
function cerrarReset() {
  resetTarget.value = null;
}
async function confirmarReset() {
  resetError.value = "";
  if (resetPwd.value.length < 8) {
    resetError.value = "Mínimo 8 caracteres.";
    return;
  }
  if (resetPwd.value !== resetPwd2.value) {
    resetError.value = "Las dos contraseñas no coinciden.";
    return;
  }
  resetBusy.value = true;
  try {
    const r = await api.adminResetPassword(resetTarget.value.id, resetPwd.value);
    resetOk.value = `Contraseña restablecida para ${r.usuario}.`;
    setTimeout(cerrarReset, 1400);
  } catch (e) {
    resetError.value = e?.response?.data?.detail || "No se pudo restablecer.";
  } finally {
    resetBusy.value = false;
  }
}

function nombrePsico(id) {
  if (!id) return "Sin asignar";
  const p = psicologas.value.find((x) => x.id === id);
  return p ? `${p.nombre} ${p.apellido}` : id;
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Administración</p>
      <h1 class="hero-serif text-[28px]">
        Gestión de <span class="hero-mint">usuarios</span>
      </h1>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <div class="grid sm:grid-cols-4 gap-3 mb-6">
        <div class="card p-4">
          <p class="text-xs text-ink-400">Total</p>
          <p class="text-2xl font-semibold">{{ stats?.total || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Estudiantes</p>
          <p class="text-2xl font-semibold">{{ stats?.estudiantes || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Psicólogas</p>
          <p class="text-2xl font-semibold">{{ stats?.psicologos || 0 }}</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-400">Admins</p>
          <p class="text-2xl font-semibold">{{ stats?.admins || 0 }}</p>
        </div>
      </div>

      <div class="grid lg:grid-cols-2 gap-6 items-start">
        <!-- ── Columna: psicólogas ─────────────────────────────── -->
        <section>
          <div class="flex items-baseline justify-between mb-3">
            <h2 class="text-lg font-semibold">Psicólogas</h2>
            <div class="flex items-center gap-3">
              <span class="text-xs text-ink-400">{{ rango(pagPsico, todasPsicologas.length) }}</span>
              <button v-if="!nueva" class="btn-mint btn-sm" @click="abrirNueva">
                + Crear psicóloga
              </button>
            </div>
          </div>

          <div v-if="okNueva && !nueva" class="banner-success mb-3">{{ okNueva }}</div>
          <div v-if="nueva" class="card p-4 mb-3 text-sm">
            <h3 class="font-semibold mb-3">Nueva psicóloga</h3>
            <div class="grid grid-cols-2 gap-2">
              <input v-model="nueva.nombre" class="input" placeholder="Nombre" />
              <input v-model="nueva.apellido" class="input" placeholder="Apellido" />
            </div>
            <input
              v-model="nueva.email"
              type="email"
              class="input w-full mt-2"
              placeholder="Correo (con este entra)"
              autocomplete="off"
            />
            <div class="grid grid-cols-2 gap-2 mt-2">
              <input
                v-model="nueva.password"
                type="text"
                class="input"
                placeholder="Contraseña (mín. 8)"
                autocomplete="off"
              />
              <input
                v-model="nuevaPwd2"
                type="text"
                class="input"
                placeholder="Repetir contraseña"
                autocomplete="off"
              />
            </div>
            <label class="block text-xs text-ink-500 mt-3 mb-1">
              Equipo psicopedagógico (ve los alumnos de esa psicóloga)
            </label>
            <select v-model="nueva.equipo_titular_id" class="input w-full">
              <option value="">Sin equipo: solo verá los alumnos que se le asignen</option>
              <option v-for="t in titulares" :key="t.id" :value="t.id">
                Equipo de {{ t.nombre }} {{ t.apellido }}
              </option>
            </select>
            <p v-if="errorNueva" class="text-red-600 mt-2">{{ errorNueva }}</p>
            <p v-if="okNueva" class="text-green-700 mt-2">{{ okNueva }}</p>
            <div class="flex justify-end gap-2 mt-3">
              <button class="btn-ghost btn-sm" :disabled="creando" @click="nueva = null">
                Cerrar
              </button>
              <button class="btn-mint btn-sm" :disabled="creando" @click="crearPsicologa">
                {{ creando ? "Creando…" : "Crear cuenta" }}
              </button>
            </div>
          </div>
          <div v-if="todasPsicologas.length === 0" class="card p-6 text-ink-500">
            No hay cuentas de psicóloga.
          </div>
          <div v-else class="grid gap-2">
            <div v-for="u in psicoPagina" :key="u.id" class="card p-3 text-sm">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <p class="font-semibold truncate">{{ u.nombre }} {{ u.apellido }}</p>
                  <p class="text-xs text-ink-500 truncate">{{ u.email }}</p>
                  <p v-if="u.equipo_titular_id" class="text-[11px] text-green-800 mt-0.5 truncate">
                    Equipo de {{ nombreDe(u.equipo_titular_id) }}
                  </p>
                </div>
                <span
                  v-if="u.activo"
                  class="px-2 py-0.5 rounded-full text-xs bg-green-50 text-green-700 border border-green-200 shrink-0"
                >activo</span>
                <span
                  v-else
                  class="px-2 py-0.5 rounded-full text-xs bg-gray-50 text-gray-700 border border-gray-200 shrink-0"
                >inactivo</span>
              </div>
              <div class="mt-2 flex justify-end">
                <span
                  v-if="esCuentaCodigo(u)"
                  class="px-2 py-0.5 rounded-full text-xs bg-cream-100 text-ink-600 border border-cream-200 whitespace-nowrap"
                  title="Entra solo con su código de acceso; no usa contraseña."
                >entra con código</span>
                <button
                  v-else
                  class="btn-ghost px-2 py-1 text-xs whitespace-nowrap"
                  @click="abrirReset(u)"
                >Restablecer contraseña</button>
              </div>
            </div>
          </div>
          <div v-if="totalPagPsico > 1" class="flex flex-wrap gap-1 mt-3">
            <button
              v-for="n in totalPagPsico"
              :key="n"
              class="w-8 h-8 rounded-lg text-xs border transition"
              :class="n === pagPsico
                ? 'bg-green-700 text-white border-green-700'
                : 'bg-white text-ink-600 border-cream-200 hover:border-green-400'"
              @click="pagPsico = n"
            >{{ n }}</button>
          </div>
        </section>

        <!-- ── Columna: alumnos (con su psicóloga asignada) ───────── -->
        <section>
          <div class="flex items-baseline justify-between mb-3">
            <h2 class="text-lg font-semibold">Alumnos</h2>
            <span class="text-xs text-ink-400">{{ rango(pagAlum, estudiantes.length) }}</span>
          </div>
          <div v-if="estudiantes.length === 0" class="card p-6 text-ink-500">
            No hay estudiantes registrados todavía.
          </div>
          <div v-else class="grid gap-2">
            <div v-for="e in alumPagina" :key="e.id" class="card p-3 text-sm">
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0">
                  <p class="font-semibold truncate">{{ e.nombre }} {{ e.apellido }}</p>
                  <p class="text-xs text-ink-500 truncate">{{ e.email }}</p>
                </div>
                <span
                  v-if="e.activo"
                  class="px-2 py-0.5 rounded-full text-xs bg-green-50 text-green-700 border border-green-200 shrink-0"
                >activo</span>
                <span
                  v-else
                  class="px-2 py-0.5 rounded-full text-xs bg-gray-50 text-gray-700 border border-gray-200 shrink-0"
                >inactivo</span>
              </div>
              <div class="mt-2 flex items-center justify-between gap-2">
                <select
                  class="input text-xs py-1"
                  style="max-width: 60%"
                  :value="e.psicologo_id || ''"
                  :disabled="procesando === e.id"
                  :title="'Psicóloga asignada: ' + nombrePsico(e.psicologo_id)"
                  @change="asignarPsico(e, $event.target.value)"
                >
                  <option value="">Sin psicóloga asignada</option>
                  <option v-for="p in psicologas" :key="p.id" :value="p.id">
                    {{ p.nombre }} {{ p.apellido }}
                  </option>
                </select>
                <span
                  v-if="esCuentaCodigo(e)"
                  class="px-2 py-0.5 rounded-full text-xs bg-cream-100 text-ink-600 border border-cream-200 whitespace-nowrap"
                  title="Entra solo con su código de acceso; no usa contraseña."
                >entra con código</span>
                <button
                  v-else
                  class="btn-ghost px-2 py-1 text-xs whitespace-nowrap"
                  @click="abrirReset(e)"
                >Restablecer contraseña</button>
              </div>
            </div>
          </div>
          <div v-if="totalPagAlum > 1" class="flex flex-wrap gap-1 mt-3">
            <button
              v-for="n in totalPagAlum"
              :key="n"
              class="w-8 h-8 rounded-lg text-xs border transition"
              :class="n === pagAlum
                ? 'bg-green-700 text-white border-green-700'
                : 'bg-white text-ink-600 border-cream-200 hover:border-green-400'"
              @click="pagAlum = n"
            >{{ n }}</button>
          </div>
        </section>
      </div>
    </template>

    <!-- Modal: restablecer contraseña -->
    <div
      v-if="resetTarget"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      style="background: rgba(15, 30, 25, 0.45)"
      @click.self="cerrarReset"
    >
      <div class="card p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold">Restablecer contraseña</h3>
        <p class="text-sm text-ink-500 mt-1">
          {{ resetTarget.nombre }} {{ resetTarget.apellido }} ·
          {{ resetTarget.email }}
        </p>
        <p class="text-xs text-ink-400 mt-2">
          Se fija una contraseña nueva. La anterior no se recupera ni se
          muestra. Comunícala por un canal seguro; la persona puede cambiarla
          al entrar.
        </p>

        <label class="block text-sm font-medium mt-4 mb-1">Nueva contraseña</label>
        <input
          v-model="resetPwd"
          type="text"
          autocomplete="off"
          class="input w-full"
          placeholder="Mínimo 8 caracteres"
          @keyup.enter="confirmarReset"
        />
        <label class="block text-sm font-medium mt-3 mb-1">Repetir</label>
        <input
          v-model="resetPwd2"
          type="text"
          autocomplete="off"
          class="input w-full"
          @keyup.enter="confirmarReset"
        />

        <p v-if="resetError" class="text-sm text-red-600 mt-3">{{ resetError }}</p>
        <p v-if="resetOk" class="text-sm text-green-700 mt-3">{{ resetOk }}</p>

        <div class="flex justify-end gap-2 mt-5">
          <button class="btn-ghost" :disabled="resetBusy" @click="cerrarReset">
            Cancelar
          </button>
          <button
            class="btn-primary"
            :disabled="resetBusy"
            @click="confirmarReset"
          >
            {{ resetBusy ? "Guardando…" : "Restablecer" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
