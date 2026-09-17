<script setup>
import { computed, ref, onMounted } from "vue";
import { api } from "../api";

const contenidos = ref([]);
const cargando = ref(true);
const error = ref("");
const aviso = ref("");

// Valores permitidos por el modelo `EducationalContent`.
const TIPOS = ["articulo", "video", "infografia", "audio"];
const CATEGORIAS = [
  "ansiedad",
  "depresion",
  "estres",
  "sueño",
  "autocuidado",
  "crisis",
];

const FORM_VACIO = {
  titulo: "",
  descripcion: "",
  tipo: "articulo",
  categoria: "",
  url: "",
  contenido: "",
  autor: "",
  icono: "📄",
  activo: true,
};

const form = ref({ ...FORM_VACIO });
const editandoId = ref(null);
const mostrarForm = ref(false);
const guardando = ref(false);

const editando = computed(() => editandoId.value !== null);

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
    contenidos.value = await api.adminListarTodosContenidos();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

onMounted(cargar);

function nuevo() {
  form.value = { ...FORM_VACIO };
  editandoId.value = null;
  mostrarForm.value = true;
  aviso.value = "";
}

function editar(c) {
  form.value = {
    titulo: c.titulo || "",
    descripcion: c.descripcion || "",
    tipo: c.tipo || "articulo",
    categoria: c.categoria || "",
    url: c.url || "",
    contenido: c.contenido || "",
    autor: c.autor || "",
    icono: c.icono || "📄",
    activo: c.activo !== false,
  };
  editandoId.value = c.id;
  mostrarForm.value = true;
  aviso.value = "";
}

function cancelar() {
  mostrarForm.value = false;
  editandoId.value = null;
  form.value = { ...FORM_VACIO };
}

const formValido = computed(
  () =>
    form.value.titulo.trim().length >= 3 &&
    form.value.descripcion.trim().length >= 3,
);

async function guardar() {
  if (!formValido.value || guardando.value) return;
  guardando.value = true;
  error.value = "";
  // Los opcionales vacíos viajan como null, no como "".
  const payload = {
    ...form.value,
    titulo: form.value.titulo.trim(),
    descripcion: form.value.descripcion.trim(),
    categoria: form.value.categoria || null,
    url: form.value.url.trim() || null,
    contenido: form.value.contenido.trim() || null,
    autor: form.value.autor.trim() || null,
  };
  try {
    if (editando.value) {
      await api.adminActualizarContenido(editandoId.value, payload);
      aviso.value = "Contenido actualizado.";
    } else {
      await api.adminCrearContenido(payload);
      aviso.value = "Contenido publicado.";
    }
    cancelar();
    await cargar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo guardar.";
  } finally {
    guardando.value = false;
  }
}

async function eliminar(c) {
  if (
    !window.confirm(
      `¿Eliminar “${c.titulo}”? Dejará de verse en Recursos de apoyo.`,
    )
  )
    return;
  error.value = "";
  try {
    await api.adminEliminarContenido(c.id);
    aviso.value = "Contenido eliminado.";
    await cargar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo eliminar.";
  }
}

async function alternarActivo(c) {
  error.value = "";
  try {
    await api.adminActualizarContenido(c.id, {
      titulo: c.titulo,
      descripcion: c.descripcion,
      tipo: c.tipo,
      categoria: c.categoria,
      url: c.url,
      contenido: c.contenido,
      autor: c.autor,
      icono: c.icono,
      activo: !c.activo,
    });
    await cargar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo actualizar.";
  }
}
</script>

<template>
  <div class="page-shell">
    <header class="mb-6 flex items-start justify-between gap-4">
      <div>
        <p class="eyebrow mb-2">Contenidos</p>
        <h1 class="hero-serif text-[28px]">
          Material <span class="hero-mint">psicoeducativo</span>
        </h1>
        <p class="text-sm text-ink-500 mt-1">
          Lo que se publique aquí es lo que el alumno ve en Recursos de apoyo.
        </p>
      </div>
      <button v-if="!mostrarForm" class="btn-primary shrink-0" @click="nuevo">
        Nuevo contenido
      </button>
    </header>

    <div v-if="aviso" class="banner-success mb-4">{{ aviso }}</div>
    <div v-if="error" class="banner-danger mb-4">{{ error }}</div>

    <!-- Formulario alta / edición -->
    <form v-if="mostrarForm" class="card p-5 mb-6 grid gap-4" @submit.prevent="guardar">
      <p class="font-semibold text-green-900">
        {{ editando ? "Editar contenido" : "Nuevo contenido" }}
      </p>

      <div class="grid gap-1">
        <label class="text-sm font-medium" for="c-titulo">Título</label>
        <input
          id="c-titulo"
          v-model="form.titulo"
          class="input"
          maxlength="200"
          required
          placeholder="Técnicas de respiración para momentos de ansiedad"
        />
      </div>

      <div class="grid gap-1">
        <label class="text-sm font-medium" for="c-desc">Descripción</label>
        <textarea
          id="c-desc"
          v-model="form.descripcion"
          class="input"
          rows="2"
          required
          placeholder="Breve resumen de para qué sirve este recurso."
        ></textarea>
      </div>

      <div class="grid sm:grid-cols-3 gap-4">
        <div class="grid gap-1">
          <label class="text-sm font-medium" for="c-tipo">Tipo</label>
          <select id="c-tipo" v-model="form.tipo" class="input">
            <option v-for="t in TIPOS" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <div class="grid gap-1">
          <label class="text-sm font-medium" for="c-cat">Categoría</label>
          <select id="c-cat" v-model="form.categoria" class="input">
            <option value="">— Sin categoría —</option>
            <option v-for="c in CATEGORIAS" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="grid gap-1">
          <label class="text-sm font-medium" for="c-icono">Icono</label>
          <input id="c-icono" v-model="form.icono" class="input" maxlength="10" />
        </div>
      </div>

      <div class="grid sm:grid-cols-2 gap-4">
        <div class="grid gap-1">
          <label class="text-sm font-medium" for="c-url">Enlace (opcional)</label>
          <input
            id="c-url"
            v-model="form.url"
            class="input"
            type="url"
            placeholder="https://…"
          />
        </div>
        <div class="grid gap-1">
          <label class="text-sm font-medium" for="c-autor">Autor (opcional)</label>
          <input id="c-autor" v-model="form.autor" class="input" maxlength="120" />
        </div>
      </div>

      <div class="grid gap-1">
        <label class="text-sm font-medium" for="c-cuerpo">
          Cuerpo del artículo (opcional)
        </label>
        <textarea
          id="c-cuerpo"
          v-model="form.contenido"
          class="input"
          rows="5"
          placeholder="Si el recurso se lee dentro de Sami, escribe aquí el texto."
        ></textarea>
      </div>

      <label class="flex items-center gap-2 text-sm">
        <input v-model="form.activo" type="checkbox" />
        Visible para los alumnos
      </label>

      <div class="flex gap-3">
        <button class="btn-primary" type="submit" :disabled="!formValido || guardando">
          {{ guardando ? "Guardando…" : editando ? "Guardar cambios" : "Publicar" }}
        </button>
        <button class="btn-ghost" type="button" @click="cancelar">Cancelar</button>
      </div>
    </form>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>

    <div v-else>
      <div v-if="contenidos.length === 0" class="card p-6 text-ink-500">
        Todavía no hay contenidos. Publica el primero para que aparezca en
        Recursos de apoyo.
      </div>
      <div v-else class="grid gap-3">
        <div
          v-for="c in contenidos"
          :key="c.id"
          class="card p-4 flex items-start justify-between gap-4"
        >
          <div class="min-w-0">
            <p class="text-xs text-ink-400">
              {{ c.icono }} {{ c.tipo }}<span v-if="c.categoria"> · {{ c.categoria }}</span>
              <span v-if="!c.activo" class="ml-2 text-amber-600">· oculto</span>
            </p>
            <p class="font-semibold text-green-900">{{ c.titulo }}</p>
            <p v-if="c.descripcion" class="text-sm text-ink-500 mt-1">
              {{ c.descripcion }}
            </p>
          </div>
          <div class="flex gap-2 shrink-0">
            <button class="btn-ghost" type="button" @click="alternarActivo(c)">
              {{ c.activo ? "Ocultar" : "Mostrar" }}
            </button>
            <button class="btn-ghost" type="button" @click="editar(c)">Editar</button>
            <button class="btn-coral" type="button" @click="eliminar(c)">
              Eliminar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
