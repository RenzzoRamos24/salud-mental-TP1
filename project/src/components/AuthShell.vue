<script setup>
defineProps({
  title:    { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <div class="auth-bg min-h-screen flex items-center justify-center px-4 py-10">
    <div class="w-full max-w-md bg-white rounded-3xl shadow-pastel p-8 sm:p-10 fade-in-up">
      <div class="flex justify-center mb-5">
        <div class="w-14 h-14 rounded-full bg-peach-100 flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4F7256" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22V12"/>
            <path d="M12 12C12 8 9 5 5 5C5 9 8 12 12 12Z" fill="#A8C4A2" fill-opacity="0.5"/>
            <path d="M12 12C12 8 15 5 19 5C19 9 16 12 12 12Z" fill="#A8C4A2" fill-opacity="0.5"/>
          </svg>
        </div>
      </div>

      <div class="text-center mb-7">
        <h1 class="hero-serif text-3xl">{{ title }}</h1>
        <p v-if="subtitle" class="text-sm text-ink-500 mt-1.5">{{ subtitle }}</p>
      </div>

      <slot />

      <div v-if="$slots.footer" class="mt-6">
        <div class="flex items-center gap-3 my-5">
          <span class="flex-1 h-px bg-cream-200"></span>
          <span class="w-1.5 h-1.5 rounded-full bg-cream-200"></span>
          <span class="flex-1 h-px bg-cream-200"></span>
        </div>
        <div class="text-center">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-bg {
  background: linear-gradient(110deg, #FCE4D6 0%, #FAF0E4 35%, #EAF2DE 70%, #D9EBD2 100%);
}
</style>
