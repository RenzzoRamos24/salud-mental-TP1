<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ResultsScreen from '../components/ResultsScreen.vue'

const router = useRouter()
const resultado = ref(null)

onMounted(() => {
  const raw = sessionStorage.getItem('sm_upc_resultado')
  if (!raw) {
    router.replace('/chat')
    return
  }
  try {
    resultado.value = JSON.parse(raw)
  } catch {
    router.replace('/chat')
  }
})

function reiniciar() {
  sessionStorage.removeItem('sm_upc_resultado')
  router.push('/chat')
}
</script>

<template>
  <ResultsScreen v-if="resultado" :resultado="resultado" @reset="reiniciar" />
</template>
