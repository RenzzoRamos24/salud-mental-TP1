<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const cargando = ref(true);
const tieneFirma = ref(false);
const url = ref("");
const error = ref("");
const exito = ref("");
const subiendo = ref(false);
const dragActive = ref(false);
const fileInput = ref(null);

async function refrescar() {
  cargando.value = true;
  try {
    const info = await api.firmaInfo();
    tieneFirma.value = info.tiene_firma;
    url.value = info.url || "";
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar la firma.";
  } finally {
    cargando.value = false;
  }
}
onMounted(refrescar);

async function procesarArchivo(f) {
  if (!f) return;
  if (!["image/png", "image/jpeg"].includes(f.type)) {
    error.value = "Solo se aceptan imágenes PNG o JPG.";
    return;
  }
  if (f.size > 2 * 1024 * 1024) {
    error.value = "La firma no puede pesar más de 2 MB.";
    return;
  }
  error.value = "";
  exito.value = "";
  subiendo.value = true;
  try {
    await api.subirFirma(f);
    exito.value = "Firma actualizada correctamente.";
    await refrescar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo subir la firma.";
  } finally {
    subiendo.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
}

function onFile(e) {
  procesarArchivo(e.target.files?.[0]);
}

function onDrop(e) {
  e.preventDefault();
  dragActive.value = false;
  procesarArchivo(e.dataTransfer.files?.[0]);
}

function onDragOver(e) {
  e.preventDefault();
  dragActive.value = true;
}

function onDragLeave() {
  dragActive.value = false;
}

async function eliminar() {
  if (!confirm("¿Eliminar tu firma actual? Los próximos informes se firmarán con línea en blanco.")) return;
  try {
    await api.eliminarFirma();
    exito.value = "Firma eliminada.";
    await refrescar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo eliminar.";
  }
}
</script>

<template>
  <div class="firma-page">
    <div class="firma-container">
      <!-- Header con eyebrow + título grande -->
      <header class="firma-header">
        <p class="firma-eyebrow">Sami · Mi firma</p>
        <h1 class="firma-title">Firma para tus informes clínicos</h1>
        <p class="firma-desc">
          Sube tu firma escaneada y se anexará automáticamente al pie de
          cada informe clínico que descarguen las familias o el equipo pedagógico.
        </p>
      </header>

      <!-- Banners de estado -->
      <transition name="banner">
        <div v-if="error" class="firma-banner firma-banner--err">
          <span class="firma-banner__ico">⚠</span>
          <span>{{ error }}</span>
        </div>
      </transition>
      <transition name="banner">
        <div v-if="exito" class="firma-banner firma-banner--ok">
          <span class="firma-banner__ico">✓</span>
          <span>{{ exito }}</span>
        </div>
      </transition>

      <!-- Loading -->
      <div v-if="cargando" class="firma-loading">Cargando tu firma…</div>

      <!-- Firma existente -->
      <section v-else-if="tieneFirma" class="firma-card">
        <p class="firma-card__label">Tu firma actual:</p>
        <div class="firma-preview">
          <img :src="url" alt="firma actual" class="firma-preview__img" />
        </div>
        <div class="firma-preview__linea"></div>
        <p class="firma-preview__hint">Así se verá al pie de los informes.</p>

        <div class="firma-actions">
          <label class="firma-btn firma-btn--primary">
            <span>Cambiar firma</span>
            <input
              type="file"
              accept="image/png,image/jpeg"
              ref="fileInput"
              :disabled="subiendo"
              hidden
              @change="onFile"
            />
          </label>
          <button class="firma-btn firma-btn--ghost" @click="eliminar" :disabled="subiendo">
            Eliminar firma
          </button>
        </div>
      </section>

      <!-- Estado vacío con drop zone -->
      <section
        v-else
        class="firma-dropzone"
        :class="{ 'firma-dropzone--active': dragActive }"
        @drop="onDrop"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
      >
        <div class="firma-dropzone__ico">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M12 3v14M5 10l7-7 7 7" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M5 21h14" stroke-linecap="round"/>
          </svg>
        </div>
        <p class="firma-dropzone__titulo">
          Aún no has subido tu firma
        </p>
        <p class="firma-dropzone__sub">
          Arrastra la imagen aquí o hacé click para elegirla
        </p>
        <label class="firma-btn firma-btn--primary firma-btn--lg">
          <span>{{ subiendo ? "Subiendo…" : "Elegir archivo" }}</span>
          <input
            type="file"
            accept="image/png,image/jpeg"
            ref="fileInput"
            :disabled="subiendo"
            hidden
            @change="onFile"
          />
        </label>
        <p class="firma-dropzone__specs">
          PNG o JPG · máximo 2 MB · fondo blanco recomendado
        </p>
      </section>

      <!-- Tip formal -->
      <aside class="firma-tip">
        <p class="firma-tip__titulo">Cómo obtener una firma nítida</p>
        <ol class="firma-tip__lista">
          <li>Firmá con lapicera o plumón negro sobre una hoja blanca.</li>
          <li>Tomá la foto o escaneala con buena luz y sin sombras.</li>
          <li>Recortá la imagen dejando poco margen alrededor del trazo.</li>
          <li>Guardala como PNG con fondo transparente si podés — se ve mejor en el informe.</li>
        </ol>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.firma-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8faf9 0%, #f0f5f3 100%);
  font-family: "Work Sans", system-ui, sans-serif;
  padding: 48px 20px 80px;
  display: flex;
  justify-content: center;
}
.firma-container {
  width: 100%;
  max-width: 720px;
}

/* ── Header ────────────────────────────────────────────────── */
.firma-header {
  margin-bottom: 32px;
}
.firma-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #0e8d7e;
  margin-bottom: 10px;
}
.firma-title {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 32px;
  color: #0a0a0a;
  letter-spacing: -0.015em;
  line-height: 1.15;
  margin-bottom: 12px;
}
.firma-desc {
  color: #475467;
  font-size: 15px;
  line-height: 1.6;
  max-width: 520px;
}

/* ── Banners ───────────────────────────────────────────────── */
.firma-banner {
  padding: 14px 18px;
  border-radius: 12px;
  font-size: 14px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.firma-banner__ico {
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}
.firma-banner--err {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}
.firma-banner--ok {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}
.banner-enter-active, .banner-leave-active { transition: opacity 0.2s, transform 0.2s; }
.banner-enter-from, .banner-leave-to { opacity: 0; transform: translateY(-4px); }

/* ── Loading ───────────────────────────────────────────────── */
.firma-loading {
  padding: 40px;
  text-align: center;
  color: #667085;
  background: #fff;
  border: 1px solid #eaecf0;
  border-radius: 16px;
}

/* ── Vista con firma existente ────────────────────────────── */
.firma-card {
  background: #fff;
  border: 1px solid #eaecf0;
  border-radius: 18px;
  padding: 32px 32px 28px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
}
.firma-card__label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #667085;
  font-weight: 600;
  margin-bottom: 16px;
}
.firma-preview {
  background: #fafbfa;
  border: 1px solid #e5eae7;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 140px;
}
.firma-preview__img {
  max-width: 100%;
  max-height: 180px;
  object-fit: contain;
}
.firma-preview__linea {
  height: 1px;
  background: #cbd5cc;
  margin: 4px 40px 8px;
}
.firma-preview__hint {
  text-align: center;
  font-size: 12.5px;
  color: #98a2b3;
  font-style: italic;
  margin-bottom: 24px;
}
.firma-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

/* ── Estado vacío / dropzone ──────────────────────────────── */
.firma-dropzone {
  background: #fff;
  border: 2px dashed #c5e1dc;
  border-radius: 18px;
  padding: 56px 32px;
  text-align: center;
  transition: all 0.2s ease;
}
.firma-dropzone--active {
  border-color: #45988c;
  background: #f0f9f6;
  transform: scale(1.005);
}
.firma-dropzone__ico {
  width: 72px;
  height: 72px;
  background: #e3f3ef;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0e8d7e;
  margin: 0 auto 20px;
}
.firma-dropzone__titulo {
  font-family: "Newsreader", Georgia, serif;
  font-size: 20px;
  color: #0a0a0a;
  margin-bottom: 4px;
}
.firma-dropzone__sub {
  color: #667085;
  font-size: 14px;
  margin-bottom: 24px;
}
.firma-dropzone__specs {
  margin-top: 20px;
  font-size: 12px;
  color: #98a2b3;
}

/* ── Botones ───────────────────────────────────────────────── */
.firma-btn {
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  padding: 11px 22px;
  border-radius: 12px;
  border: 1.6px solid transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.15s ease;
  text-decoration: none;
}
.firma-btn--lg {
  padding: 13px 28px;
  font-size: 14.5px;
}
.firma-btn--primary {
  background: #45988c;
  color: #fff;
}
.firma-btn--primary:hover:not(:disabled) {
  background: #0e8d7e;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(14, 141, 126, 0.18);
}
.firma-btn--ghost {
  background: #fff;
  border-color: #d1d5db;
  color: #344054;
}
.firma-btn--ghost:hover:not(:disabled) {
  border-color: #b42318;
  color: #b42318;
}
.firma-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── Tip ───────────────────────────────────────────────────── */
.firma-tip {
  margin-top: 28px;
  background: #fdfcf7;
  border: 1px solid #f0e9d6;
  border-radius: 14px;
  padding: 20px 24px;
}
.firma-tip__titulo {
  font-weight: 600;
  color: #344054;
  font-size: 14px;
  margin-bottom: 10px;
}
.firma-tip__lista {
  color: #667085;
  font-size: 13.5px;
  line-height: 1.65;
  padding-left: 20px;
  margin: 0;
}
.firma-tip__lista li {
  margin-bottom: 4px;
}
</style>
