<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
});
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center bg-white px-4 py-10"
  >
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <p class="sami-wordmark">
          Sami <span class="accent">— Salud Mental Juvenil</span>
        </p>
      </div>

      <div class="bg-white border border-ink-200 rounded-xl p-8 sm:p-10">
        <div class="text-center mb-6">
          <h1 class="hero-serif text-2xl">{{ title }}</h1>
          <p v-if="subtitle" class="text-sm text-ink-500 mt-1.5">
            {{ subtitle }}
          </p>
        </div>

        <slot />

        <div
          v-if="$slots.footer"
          class="mt-8 pt-6 border-t border-ink-100 text-center"
        >
          <slot name="footer" />
        </div>
      </div>
    </div>
  </div>
</template>
