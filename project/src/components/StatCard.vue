<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint:  { type: String, default: '' },
  icon:  { type: String, default: '' },
  tone:  { type: String, default: 'brand' }, // brand | peach | mint | sky2 | risk-critico | risk-alto | risk-medio | risk-bajo
})

const toneBg = {
  'brand':        'bg-brand-100 text-brand-700',
  'peach':        'bg-peach-100 text-peach-600',
  'mint':         'bg-mint-100 text-mint-600',
  'sky2':         'bg-sky2-100 text-sky2-500',
  'risk-critico': 'bg-red-100 text-risk-critico',
  'risk-alto':    'bg-peach-100 text-peach-600',
  'risk-medio':   'bg-amber-100 text-amber-700',
  'risk-bajo':    'bg-mint-100 text-mint-600',
}
</script>

<template>
  <div class="card p-5 flex items-start gap-4">
    <div
      v-if="icon"
      class="w-12 h-12 rounded-2xl flex items-center justify-center text-xl shrink-0"
      :class="toneBg[tone]"
    >
      {{ icon }}
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-xs uppercase tracking-wider font-semibold text-ink-400">{{ label }}</p>
      <p class="text-2xl sm:text-3xl font-bold text-ink-900 mt-0.5">{{ value }}</p>
      <p v-if="hint" class="text-xs text-ink-500 mt-1">{{ hint }}</p>
    </div>
  </div>
</template>
