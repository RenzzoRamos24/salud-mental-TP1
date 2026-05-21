<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";
import { api } from "../api";

const route = useRoute();
const abierto = ref(false);
const mensaje = ref("");
const enviando = ref(false);
const enviado = ref(false);
const respuesta = ref(null);

function origenActual() {
  const path = (route?.path || "").toLowerCase();
  if (path.includes("chat")) return "chat";
  if (path.includes("resultado")) return "resultados";
  if (path.includes("historial")) return "historial";
  return "menu";
}

async function activar() {
  if (enviando.value) return;
  enviando.value = true;
  try {
    respuesta.value = await api.activarSOS({
      origen: origenActual(),
      mensaje: mensaje.value || null,
    });
    enviado.value = true;
  } catch (_) {
    respuesta.value = {
      mensaje: "No pudimos registrar tu SOS, pero llama a la Línea 113 ahora.",
    };
    enviado.value = true;
  } finally {
    enviando.value = false;
  }
}

function cerrar() {
  abierto.value = false;
  setTimeout(() => {
    mensaje.value = "";
    enviado.value = false;
    respuesta.value = null;
  }, 200);
}
</script>

<template>
  <button v-if="!abierto" @click="abierto = true" class="sos-fab">SOS</button>

  <Teleport to="body">
    <div
      v-if="abierto"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/40 fade-in-up"
      @click.self="cerrar"
    >
      <div
        class="bg-white rounded-xl border border-ink-200 w-full max-w-md p-6"
      >
        <h2 class="text-lg font-semibold text-ink-900">
          ¿Necesitas ayuda ahora?
        </h2>
        <p class="text-sm text-ink-600 mt-1">
          No estás solo/a. Estos canales atienden 24/7.
        </p>

        <div v-if="!enviado" class="mt-5 space-y-3">
          <a
            href="tel:113"
            class="block rounded-md border border-ink-200 hover:border-green-500 p-4 transition"
          >
            <p
              class="text-[11px] uppercase tracking-wider text-ink-500 font-medium"
            >
              Línea Nacional MINSA
            </p>
            <p class="text-2xl font-semibold text-ink-900 mt-0.5">
              113 — opción 5
            </p>
          </a>
          <a
            href="tel:106"
            class="block rounded-md border border-ink-200 hover:border-green-500 p-4 transition"
          >
            <p
              class="text-[11px] uppercase tracking-wider text-ink-500 font-medium"
            >
              Emergencia inmediata
            </p>
            <p class="text-xl font-semibold text-ink-900 mt-0.5">106</p>
          </a>

          <div>
            <label class="label"
              >¿Quieres contarnos algo?
              <span class="text-ink-400 font-normal">(opcional)</span></label
            >
            <textarea
              v-model="mensaje"
              rows="3"
              class="input resize-none"
              placeholder="Lo que escribas llegará al psicólogo del colegio."
            ></textarea>
          </div>

          <div class="flex gap-2 pt-2">
            <button
              @click="cerrar"
              :disabled="enviando"
              class="btn-ghost flex-1"
            >
              Cerrar
            </button>
            <button
              @click="activar"
              :disabled="enviando"
              class="btn-danger flex-1"
            >
              {{ enviando ? "Enviando…" : "Pedir apoyo ahora" }}
            </button>
          </div>
        </div>

        <div v-else class="text-center py-4">
          <p class="text-base font-semibold text-green-700">Te escuchamos</p>
          <p class="text-sm text-ink-700 mt-2 leading-relaxed">
            {{ respuesta?.mensaje }}
          </p>
          <button @click="cerrar" class="btn-primary mt-5">Entendido</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
