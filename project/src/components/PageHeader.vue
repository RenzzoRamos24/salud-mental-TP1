<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  accent: { type: String, default: "" },
  eyebrow: { type: String, default: "" },
});
</script>

<template>
  <div class="mb-8">
    <div class="flex items-end gap-4 justify-between">
      <div class="min-w-0">
        <p v-if="eyebrow" class="eyebrow mb-1.5">{{ eyebrow }}</p>
        <h1 class="hero-serif text-[28px] sm:text-[37px]">
          {{ title }}
          <span v-if="accent" class="hero-mint">{{ accent }}</span>
        </h1>
        <p v-if="subtitle" class="mt-3 text-ink-500 max-w-2xl text-[15px]">
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
