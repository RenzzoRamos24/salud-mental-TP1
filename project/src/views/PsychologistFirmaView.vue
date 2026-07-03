<script setup>
import { ref, onMounted } from "vue";
import { api } from "../api";

const cargando = ref(true);
const tieneFirma = ref(false);
const url = ref("");
const error = ref("");
const exito = ref("");
const subiendo = ref(false);
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

async function onFile(e) {
  const f = e.target.files?.[0];
  if (!f) return;
  if (!["image/png", "image/jpeg"].includes(f.type)) {
    error.value = "Solo se aceptan PNG o JPG.";
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

async function eliminar() {
  if (!confirm("¿Eliminar tu firma actual?")) return;
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
  <div class="firma-bg">
    <div class="firma-sheet">
      <p class="firma-eyebrow">Sami · Mi firma</p>
      <h1 class="firma-title">Firma que aparece en los informes</h1>
      <p class="firma-desc">
        Sube una imagen PNG o JPG de tu firma manuscrita. Esta firma se anexará
        automáticamente al final de cada reporte clínico y de los informes que
        descarguen los padres.
      </p>

      <div v-if="error" class="firma-banner firma-banner--err">{{ error }}</div>
      <div v-if="exito" class="firma-banner firma-banner--ok">{{ exito }}</div>

      <div class="firma-box" v-if="cargando">Cargando…</div>

      <div class="firma-box" v-else-if="tieneFirma">
        <p class="firma-label">Firma actual:</p>
        <img :src="url" alt="firma" class="firma-img" />
        <div class="firma-actions">
          <label class="firma-btn firma-btn--primary">
            Cambiar firma
            <input
              type="file"
              accept="image/png,image/jpeg"
              ref="fileInput"
              :disabled="subiendo"
              hidden
              @change="onFile"
            />
          </label>
          <button class="firma-btn firma-btn--ghost" @click="eliminar">
            Eliminar firma
          </button>
        </div>
      </div>

      <div class="firma-box firma-box--empty" v-else>
        <p>Aún no has subido tu firma.</p>
        <label class="firma-btn firma-btn--primary">
          {{ subiendo ? "Subiendo…" : "Subir firma (PNG/JPG, máx 2 MB)" }}
          <input
            type="file"
            accept="image/png,image/jpeg"
            ref="fileInput"
            :disabled="subiendo"
            hidden
            @change="onFile"
          />
        </label>
      </div>

      <div class="firma-tip">
        <b>Tip:</b> firma sobre una hoja blanca con un plumón negro, escanéala o
        tómale foto con buen contraste, recórtala antes de subir.
      </div>
    </div>
  </div>
</template>

<style scoped>
.firma-bg {
  min-height: 100vh;
  background: #f4f5f6;
  font-family: "Work Sans", system-ui, sans-serif;
  padding: 36px 16px;
  display: flex;
  justify-content: center;
}
.firma-sheet {
  width: 100%;
  max-width: 640px;
  background: #fff;
  border-radius: 22px;
  padding: 40px 44px;
  box-shadow: 0 6px 30px rgba(35, 80, 95, 0.06);
}
.firma-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #0e8d7e;
  margin-bottom: 8px;
}
.firma-title {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 26px;
  color: #0a0a0a;
  letter-spacing: -0.01em;
  margin-bottom: 8px;
}
.firma-desc {
  color: #475467;
  font-size: 14.5px;
  line-height: 1.6;
  margin-bottom: 22px;
}
.firma-banner {
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13.5px;
  margin-bottom: 14px;
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
.firma-box {
  background: #f9fafa;
  border: 1.6px dashed #c5e1dc;
  border-radius: 14px;
  padding: 24px;
  text-align: center;
}
.firma-box--empty p {
  margin-bottom: 14px;
  color: #667085;
}
.firma-label {
  color: #667085;
  font-size: 13px;
  margin-bottom: 12px;
}
.firma-img {
  max-width: 280px;
  max-height: 140px;
  background: #fff;
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 16px;
}
.firma-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}
.firma-btn {
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  padding: 10px 18px;
  border-radius: 12px;
  border: 1.6px solid transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.firma-btn--primary {
  background: #45988c;
  color: #fff;
}
.firma-btn--primary:hover {
  background: #0e8d7e;
}
.firma-btn--ghost {
  background: #fff;
  border-color: #d1d5db;
  color: #344054;
}
.firma-btn--ghost:hover {
  border-color: #b42318;
  color: #b42318;
}
.firma-tip {
  margin-top: 18px;
  font-size: 12.5px;
  color: #98a2b3;
  background: #f4f5f6;
  padding: 10px 14px;
  border-radius: 10px;
}
</style>
