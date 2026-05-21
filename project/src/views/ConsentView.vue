<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import { authStore } from "../store/auth";

const router = useRouter();

const VERSION = "1.0";
const aceptado = ref(false);
const cargando = ref(false);
const error = ref("");

async function aceptar() {
  if (!aceptado.value) {
    error.value = "Debes marcar la casilla para continuar";
    return;
  }
  cargando.value = true;
  error.value = "";
  try {
    await api.aceptarConsentimiento(VERSION);
    authStore.setUser({
      consentimiento_aceptado: true,
      consentimiento_version: VERSION,
    });
    router.push("/menu");
  } catch (e) {
    error.value =
      e.response?.data?.detail || "Error registrando consentimiento";
  } finally {
    cargando.value = false;
  }
}
</script>

<template>
  <div class="min-h-screen py-10 px-4">
    <div class="max-w-3xl mx-auto fade-in-up">
      <div class="text-center mb-8">
        <p class="sami-wordmark text-xl">
          Sami <span class="accent">· Salud Mental Juvenil</span>
        </p>
        <h1 class="hero-serif text-3xl sm:text-4xl mt-4">Antes de empezar</h1>
        <p class="text-ink-500 text-sm mt-3">
          Léelo con calma. Versión {{ VERSION }}.
        </p>
      </div>

      <div
        class="bg-white rounded-xl border border-ink-200 shadow-soft p-6 sm:p-8"
      >
        <div class="space-y-4 text-ink-700 leading-relaxed">
          <p>
            Esto es un espacio para que cuentes cómo te sientes y recibas una
            orientación. Antes de que empieces, queremos que sepas tres cosas.
          </p>

          <div class="card-pastel p-5">
            <h3 class="section-title !mb-2">
              <span class="dsm5-tag">1</span>
              Esto no es un diagnóstico
            </h3>
            <p class="text-sm">
              Sami lee tus respuestas y te da una orientación general. No
              reemplaza a un psicólogo o psicóloga de verdad. Si algo te
              preocupa, lo conversamos con un profesional.
            </p>
          </div>

          <div class="card-pastel p-5">
            <h3 class="section-title !mb-2">
              <span class="dsm5-tag">2</span>
              Qué pasa con lo que escribes
            </h3>
            <ul
              class="list-disc list-inside text-sm space-y-1 marker:text-green-400"
            >
              <li>
                Lo guardamos de forma confidencial. No lo ven tus compañeros ni
                tus profesores.
              </li>
              <li>Puede revisarlo la psicóloga del colegio que te acompañe.</li>
              <li>No se lo compartimos a nadie más.</li>
              <li>
                Si en algún momento quieres que borremos todo, nos avisas y lo
                hacemos.
              </li>
            </ul>
          </div>

          <div class="card-mint p-5">
            <h3 class="section-title !mb-2">
              <span class="dsm5-tag">3</span>
              Tú decides
            </h3>
            <p class="text-sm">
              No tienes que terminar la conversación si no quieres. Puedes parar
              cuando lo necesites, sin que pase nada.
            </p>
          </div>

          <div class="banner-danger">
            <div>
              <p class="font-semibold mb-1">Si lo necesitas ahora</p>
              <p class="text-sm">
                Llama a la <strong>Línea 113, opción 5</strong> — atienden a
                cualquier hora — o ve a la emergencia más cercana.
              </p>
            </div>
          </div>
        </div>

        <div class="mt-6 border-t border-ink-100 pt-6">
          <label
            class="flex items-start gap-3 cursor-pointer p-4 rounded-xl bg-green-50 border border-green-100 hover:border-green-200 transition"
          >
            <input
              v-model="aceptado"
              type="checkbox"
              class="mt-1 w-5 h-5 rounded border-ink-300 text-green-500 focus:ring-green-400"
              :disabled="cargando"
            />
            <span class="text-ink-800 text-sm">
              Lo leí y entiendo. Acepto que mis respuestas se usen como se
              describe arriba.
            </span>
          </label>

          <p v-if="error" class="field-error mt-3">{{ error }}</p>

          <button
            @click="aceptar"
            :disabled="cargando || !aceptado"
            class="btn-mint w-full mt-4 py-3 text-base"
          >
            {{ cargando ? "Guardando…" : "Aceptar y continuar" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
