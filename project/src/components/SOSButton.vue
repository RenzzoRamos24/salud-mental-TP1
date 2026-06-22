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
  if (path.includes("diario")) return "diario";
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
      mensaje:
        "No pudimos registrar tu mensaje. Llama a la Línea 113 ahora.",
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
  <button
    v-if="!abierto"
    @click="abierto = true"
    class="sos-fab"
    type="button"
  >
    SOS
  </button>

  <Teleport to="body">
    <div
      v-if="abierto"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 fade-in-up"
      style="background: rgba(36, 58, 44, 0.4)"
      @click.self="cerrar"
    >
      <div class="card-hero w-full max-w-md p-7">
        <h2 class="hero-serif text-[22px]">¿Necesitas ayuda ahora?</h2>
        <p class="text-sm text-ink-500 mt-2">
          Estos canales atienden 24/7.
        </p>

        <div v-if="!enviado" class="mt-5 space-y-3">
          <a
            href="tel:113"
            class="block rounded-[16px] p-5 transition card-flat hover:-translate-y-0.5"
          >
            <p class="label-kicker">Línea 113 · MINSA</p>
            <p
              class="text-[26px] font-bold text-green-800 mt-1 tracking-tightish gb"
            >
              113 — opción 5
            </p>
          </a>
          <a
            href="tel:106"
            class="block rounded-[16px] p-5 transition card-flat hover:-translate-y-0.5"
          >
            <p class="label-kicker">Emergencia</p>
            <p
              class="text-[26px] font-bold text-coral-500 mt-1 tracking-tightish gb"
            >
              106
            </p>
          </a>

          <div>
            <label class="label"
              >¿Quieres contarnos algo?
              <span class="text-ink-300 font-normal">(opcional)</span></label
            >
            <textarea
              v-model="mensaje"
              rows="3"
              class="input resize-none"
              placeholder="Lo que escribas llega a la psicóloga del colegio."
            ></textarea>
          </div>

          <div class="flex gap-2 pt-1">
            <button
              @click="cerrar"
              :disabled="enviando"
              class="btn-ghost flex-1"
              type="button"
            >
              Cerrar
            </button>
            <button
              @click="activar"
              :disabled="enviando"
              class="btn-coral flex-1"
              type="button"
            >
              {{ enviando ? "Enviando…" : "Pedir apoyo" }}
            </button>
          </div>
        </div>

        <div v-else class="text-center py-4">
          <p class="text-base font-semibold text-green-700">Te escuchamos.</p>
          <p class="text-sm text-ink-700 mt-2 leading-relaxed">
            {{ respuesta?.mensaje }}
          </p>
          <button @click="cerrar" class="btn-primary mt-5" type="button">
            Entendido
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
