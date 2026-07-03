<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "../api";

const route = useRoute();
const router = useRouter();
const hijoId = route.params.id;

const hijo = ref(null);
const cargando = ref(true);
const error = ref("");
const descargando = ref(false);

async function cargar() {
  cargando.value = true;
  try {
    hijo.value = await api.padreDetalleHijo(hijoId);
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar el detalle.";
  } finally {
    cargando.value = false;
  }
}
onMounted(cargar);

async function descargar(tipo) {
  if (descargando.value) return;
  descargando.value = true;
  try {
    const blob =
      tipo === "pdf"
        ? await api.padreInformePDF(hijoId)
        : await api.padreInformeWord(hijoId);
    const url = window.URL.createObjectURL(new Blob([blob]));
    const a = document.createElement("a");
    a.href = url;
    a.download = `informe_${hijo.value.nombre}.${tipo === "pdf" ? "pdf" : "docx"}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo descargar el informe.";
  } finally {
    descargando.value = false;
  }
}
</script>

<template>
  <div class="hd-bg">
    <header class="hd-top">
      <button class="hd-back" @click="router.back()">← Volver</button>
      <span class="hd-pill">Sami · Panel padres</span>
    </header>

    <main class="hd-main">
      <div v-if="cargando" class="hd-status">Cargando…</div>
      <div v-else-if="error" class="hd-err">{{ error }}</div>
      <template v-else-if="hijo">
        <p class="hd-eyebrow">Informe de</p>
        <h1 class="hd-title">{{ hijo.nombre }} {{ hijo.apellido }}</h1>
        <p class="hd-desc">
          Este informe es un resumen sin datos clínicos sensibles. Los puntajes
          y el detalle del seguimiento son confidenciales entre tu hijo/a y la
          psicóloga responsable.
        </p>

        <section class="hd-sheet">
          <div class="hd-row">
            <span class="hd-label">Grado / curso</span>
            <span class="hd-val">{{ hijo.grado || "No registrado" }}</span>
          </div>
          <div class="hd-row">
            <span class="hd-label">Estado del seguimiento</span>
            <span class="hd-val hd-tag">{{ hijo.estado_caso || "activo" }}</span>
          </div>
          <div class="hd-row">
            <span class="hd-label">Cuestionarios completados</span>
            <span class="hd-val">{{ hijo.cuestionarios_completados }}</span>
          </div>
          <div class="hd-row" v-if="hijo.psicologo_nombre">
            <span class="hd-label">Psicóloga responsable</span>
            <span class="hd-val">{{ hijo.psicologo_nombre }}</span>
          </div>

          <div class="hd-mensaje">
            <h3>Mensaje de la psicóloga</h3>
            <p v-if="hijo.mensaje_psicologa">{{ hijo.mensaje_psicologa }}</p>
            <p v-else class="muted">
              La psicóloga aún no ha dejado un mensaje. Cuando lo haga, aparecerá
              aquí y en el informe descargable.
            </p>
          </div>
        </section>

        <section class="hd-actions">
          <h3>Descargar informe firmado</h3>
          <p>
            Descarga el informe oficial firmado por la psicóloga. Puedes usarlo
            como referencia, llevarlo a una cita externa o archivarlo.
          </p>
          <div class="hd-btns">
            <button
              class="hd-btn hd-btn--primary"
              :disabled="descargando"
              @click="descargar('pdf')"
            >
              📄 Descargar PDF
            </button>
            <button
              class="hd-btn hd-btn--ghost"
              :disabled="descargando"
              @click="descargar('docx')"
            >
              📝 Descargar Word
            </button>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.hd-bg {
  min-height: 100vh;
  background: #f4f5f6;
  font-family: "Work Sans", system-ui, sans-serif;
  color: #1f2937;
}
.hd-top {
  background: #fff;
  border-bottom: 1px solid #eef1f2;
  padding: 16px 36px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.hd-back {
  background: transparent;
  border: 0;
  font-family: inherit;
  font-size: 14px;
  cursor: pointer;
  color: #475467;
}
.hd-back:hover {
  color: #0e8d7e;
}
.hd-pill {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #0e8d7e;
  background: #e3f3ef;
  padding: 4px 10px;
  border-radius: 99px;
}
.hd-main {
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 28px 80px;
}
.hd-status,
.hd-err {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
  color: #667085;
}
.hd-err {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}
.hd-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #0e8d7e;
  margin-bottom: 8px;
}
.hd-title {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 32px;
  color: #0a0a0a;
  letter-spacing: -0.01em;
  margin-bottom: 10px;
}
.hd-desc {
  color: #475467;
  font-size: 14.5px;
  line-height: 1.6;
  margin-bottom: 28px;
}
.hd-sheet {
  background: #fff;
  border-radius: 18px;
  padding: 28px 32px;
  box-shadow: 0 6px 30px rgba(35, 80, 95, 0.06);
  margin-bottom: 22px;
}
.hd-row {
  display: flex;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid #f4f5f6;
}
.hd-row:last-of-type {
  border-bottom: 0;
}
.hd-label {
  font-size: 13px;
  color: #667085;
}
.hd-val {
  font-size: 14px;
  color: #1f2937;
  font-weight: 500;
}
.hd-tag {
  background: #e3f3ef;
  color: #0e8d7e;
  padding: 2px 10px;
  border-radius: 99px;
  font-size: 12.5px;
  text-transform: capitalize;
}
.hd-mensaje {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid #eef1f2;
}
.hd-mensaje h3 {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 17px;
  margin-bottom: 10px;
  color: #0e8d7e;
}
.hd-mensaje p {
  color: #344054;
  line-height: 1.6;
  font-size: 14.5px;
}
.muted {
  color: #98a2b3;
  font-style: italic;
}

.hd-actions {
  background: #fff;
  border-radius: 18px;
  padding: 28px 32px;
  box-shadow: 0 6px 30px rgba(35, 80, 95, 0.06);
}
.hd-actions h3 {
  font-family: "Newsreader", Georgia, serif;
  font-weight: 500;
  font-size: 19px;
  color: #0a0a0a;
  margin-bottom: 8px;
}
.hd-actions p {
  color: #667085;
  font-size: 13.5px;
  line-height: 1.55;
  margin-bottom: 18px;
}
.hd-btns {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.hd-btn {
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  padding: 12px 22px;
  border-radius: 12px;
  border: 1.6px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
}
.hd-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.hd-btn--primary {
  background: #45988c;
  color: #fff;
  box-shadow: 0 6px 14px -6px rgba(69, 152, 140, 0.5);
}
.hd-btn--primary:hover:not(:disabled) {
  background: #0e8d7e;
}
.hd-btn--ghost {
  background: #fff;
  border-color: #d1d5db;
  color: #344054;
}
.hd-btn--ghost:hover:not(:disabled) {
  border-color: #45988c;
  color: #0e8d7e;
}
</style>
