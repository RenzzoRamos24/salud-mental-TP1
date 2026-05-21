<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  accent: { type: String, default: "" },
  icon: { type: String, default: "" },
  tone: { type: String, default: "mint" },
});
</script>

<template>
  <div class="mb-8">
    <div class="flex items-end gap-4 justify-between">
      <div class="min-w-0">
        <h1 class="hero-serif text-2xl sm:text-3xl">
          {{ title }}
          <span v-if="accent" class="hero-mint">{{ accent }}</span>
        </h1>
        <p
          v-if="subtitle"
          class="mt-2 text-ink-600 max-w-2xl text-sm sm:text-base"
        >
          {{ subtitle }}
        </p>
        <slot name="actions" />
      </div>
      <div class="hidden sm:block shrink-0">
        <slot name="aside" />
      </div>
    </div>
  </div>
</template>
