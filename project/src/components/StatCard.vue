<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  hint: { type: String, default: "" },
  tone: { type: String, default: "brand" },
});

const toneBg = {
  brand: "text-green-700",
  peach: "text-coral-500",
  mint: "text-green-700",
  sky2: "text-ink-700",
  "risk-critico": "text-coral-600",
  "risk-alto": "text-coral-500",
  "risk-medio": "text-coral-500",
  "risk-bajo": "text-green-700",
};
</script>

<template>
  <div class="card p-6">
    <p class="label-kicker">{{ label }}</p>
    <p
      class="font-bold mt-2 leading-none tabular gb text-[34px] tracking-tightish"
      :class="toneBg[tone]"
    >
      {{ value }}
    </p>
    <p v-if="hint" class="text-[12.5px] text-ink-400 mt-2">{{ hint }}</p>
  </div>
</template>
