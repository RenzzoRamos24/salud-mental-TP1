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
        <div class="flex items-center justify-center gap-2.5">
          <img src="/sentir-isotipo.svg" class="h-8" alt="SENTIR" />
          <p class="sami-wordmark">Sami</p>
        </div>
        <h1 class="hero-serif text-[28px] sm:text-[37px] mt-5">
          Antes de empezar
        </h1>
        <p class="text-ink-400 text-[13px] mt-3">
          Léelo con calma. Versión {{ VERSION }}.
        </p>
      </div>

      <div class="card-hero p-7 sm:p-9">
        <div class="space-y-4 text-ink-700 leading-relaxed text-[15px]">
          <p>
            Este es tu espacio para escribir cómo te sientes. Antes de empezar,
            tres cosas.
          </p>

          <div class="card-mint p-5">
            <p class="label-kicker">01</p>
            <h3 class="gb text-[17px] font-semibold text-green-900 mt-1.5 mb-1.5">
              Esto no es un diagnóstico
            </h3>
            <p class="text-[14px] text-ink-700">
              Lo que escribes te da una orientación. No reemplaza a tu psicóloga
              ni a tu médica. Si algo te preocupa, lo conversamos con un
              profesional.
            </p>
          </div>

          <div class="card-mint p-5">
            <p class="label-kicker">02</p>
            <h3 class="gb text-[17px] font-semibold text-green-900 mt-1.5 mb-1.5">
              Qué pasa con lo que escribes
            </h3>
            <ul class="text-[14px] text-ink-700 space-y-1.5">
              <li>· Lo guardamos de forma confidencial.</li>
              <li>· No lo ven tus compañeros ni tus profesores.</li>
              <li>· Puede revisarlo la psicóloga del colegio que te acompañe.</li>
              <li>· Si quieres que borremos todo, nos avisas y lo hacemos.</li>
            </ul>
            <p class="text-[12px] text-ink-400 mt-3 leading-relaxed">
              Tratamiento de datos conforme a la <strong>Ley N° 29733</strong>
              de Protección de Datos Personales del Perú.
            </p>
          </div>

          <div class="card-mint p-5">
            <p class="label-kicker">03</p>
            <h3 class="gb text-[17px] font-semibold text-green-900 mt-1.5 mb-1.5">
              Tú decides
            </h3>
            <p class="text-[14px] text-ink-700">
              Puedes parar cuando quieras. No tienes que terminar nada.
            </p>
          </div>

          <div class="banner-danger">
            <div>
              <p class="gb font-semibold mb-1">Si lo necesitas ahora</p>
              <p class="text-[14px]">
                Llama a la <strong>Línea 113, opción 5</strong> — 24/7 — o ve a
                la emergencia más cercana.
              </p>
            </div>
          </div>
        </div>

        <div class="mt-7 pt-6" style="border-top: 1px solid #eef2ea">
          <label
            class="flex items-start gap-3 cursor-pointer p-4 rounded-[16px] transition"
            style="background: #e2eadc"
          >
            <input
              v-model="aceptado"
              type="checkbox"
              class="mt-1 w-[18px] h-[18px] rounded text-green-600 focus:ring-green-300"
              style="border: 1.5px solid #4c6b53"
              :disabled="cargando"
            />
            <span class="text-ink-800 text-[14px]">
              Lo leí y entiendo. Acepto que mis respuestas se usen como se
              describe arriba.
            </span>
          </label>

          <p v-if="error" class="field-error mt-3">{{ error }}</p>

          <button
            @click="aceptar"
            :disabled="cargando || !aceptado"
            class="btn-primary w-full mt-4"
          >
            {{ cargando ? "Guardando…" : "Aceptar y continuar" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
