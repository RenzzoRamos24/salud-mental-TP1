<script setup>
defineProps({
  title:    { type: String, required: true },
  subtitle: { type: String, default: '' },
  accent:   { type: String, default: '' }, // segmento del título en mint
  icon:     { type: String, default: '' },
  tone:     { type: String, default: 'mint' }, // mint | peach | brand | sky
})
</script>

<template>
  <div class="mb-8 fade-in-up">
    <div class="flex items-start gap-4">
      <div
        v-if="icon"
        class="icon-box shrink-0"
        :class="{
          'icon-box-mint':  tone === 'mint',
          'icon-box-peach': tone === 'peach',
          'icon-box-brand': tone === 'brand',
          'icon-box-sky':   tone === 'sky' || tone === 'sky2',
          'icon-box-amber': tone === 'amber',
        }"
      >{{ icon }}</div>
      <div class="flex-1 min-w-0">
        <h1 class="hero-serif text-3xl sm:text-4xl">
          {{ title }}<template v-if="accent"> <span class="hero-mint">{{ accent }}</span></template>
        </h1>
        <p v-if="subtitle" class="mt-2 text-ink-500 leading-relaxed max-w-2xl">{{ subtitle }}</p>
        <slot name="actions" />
      </div>
      <div class="hidden sm:block">
        <slot name="aside" />
      </div>
    </div>
  </div>
</template>
