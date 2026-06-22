<script setup>
import { useRouter } from "vue-router";

const props = defineProps({
  alert: { type: Object, required: true },
});

const router = useRouter();

function abrir() {
  router.push(`/psicologo/estudiante/${props.alert.studentId}`);
}
</script>

<template>
  <button :class="'alert-row ' + alert.tipo" type="button" @click="abrir">
    <span class="badge-ico">
      <svg
        v-if="alert.tipo === 'idle'"
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.7"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M21 12.8A8 8 0 1 1 11.2 3 6.3 6.3 0 0 0 21 12.8z" />
      </svg>
      <svg
        v-else
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M12 9v4M12 17h.01" />
        <path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" />
      </svg>
    </span>
    <span class="txt">
      <span class="t">{{ alert.t }}</span>
      <span class="s">{{ alert.s }}</span>
    </span>
    <span class="when">{{ alert.when }}</span>
    <span style="color: #0D9488">
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M9 6l6 6-6 6" />
      </svg>
    </span>
  </button>
</template>
