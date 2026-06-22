<script setup>
import { onMounted, ref } from "vue";

const estado = ref("Procesando…");

function parsearHash(hash) {
  const limpio = (hash || "").replace(/^#/, "");
  const params = new URLSearchParams(limpio);
  const obj = {};
  for (const [k, v] of params.entries()) obj[k] = v;
  return obj;
}

onMounted(() => {
  const hashParams = parsearHash(window.location.hash);
  const queryParams = Object.fromEntries(
    new URLSearchParams(window.location.search),
  );
  const datos = { ...queryParams, ...hashParams };

  const error = datos.error || datos.error_description;
  if (error) {
    estado.value = `Error: ${error}`;
    if (window.opener) {
      window.opener.postMessage(
        { source: "sami-oauth", error: datos.error_description || datos.error },
        window.location.origin,
      );
    }
    setTimeout(() => window.close(), 600);
    return;
  }

  const id_token = datos.id_token || null;
  const access_token = datos.access_token || null;
  const state = datos.state || "";

  if (window.opener) {
    window.opener.postMessage(
      { source: "sami-oauth", id_token, access_token, state },
      window.location.origin,
    );
    estado.value = "Listo. Cerrando…";
    setTimeout(() => window.close(), 300);
  } else {
    estado.value =
      "No se detectó la ventana original. Cierra esta pestaña y vuelve a intentar.";
  }
});
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center px-4"
    style="background: #edf1e8"
  >
    <div class="card-flat p-6 text-center">
      <p class="text-[14px] text-ink-700">{{ estado }}</p>
    </div>
  </div>
</template>
