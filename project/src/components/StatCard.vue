<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: "" },
  icon: { type: String, default: "" },
  tone: { type: String, default: "brand" }, // brand | peach | mint | sky2 | risk-critico | risk-alto | risk-medio | risk-bajo
});

const toneBg = {
  brand: "bg-green-50 text-green-700",
  peach: "bg-ink-100 text-ink-700",
  mint: "bg-green-100 text-green-600",
  sky2: "bg-ink-100 text-ink-700",
  "risk-critico": "bg-red-100 text-risk-critico",
  "risk-alto": "bg-ink-100 text-ink-700",
  "risk-medio": "bg-ink-100 text-ink-700",
  "risk-bajo": "bg-green-100 text-green-600",
};
</script>

<template>
  <div class="card p-5 flex items-start gap-4">
    <div
      v-if="icon"
      class="w-12 h-12 rounded-xl flex items-center justify-center text-xl shrink-0"
      :class="toneBg[tone]"
    >
      {{ icon }}
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-xs uppercase tracking-wider font-semibold text-ink-400">
        {{ label }}
      </p>
      <p class="text-2xl sm:text-3xl font-bold text-ink-900 mt-0.5">
        {{ value }}
      </p>
      <p v-if="hint" class="text-xs text-ink-500 mt-1">{{ hint }}</p>
    </div>
  </div>
</template>
