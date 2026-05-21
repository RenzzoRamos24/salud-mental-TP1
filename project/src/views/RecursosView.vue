<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'

const router = useRouter()

const contenidos = ref([])
const cargandoContenidos = ref(true)
const categoriaActiva = ref('todas')

onMounted(async () => {
  try { contenidos.value = await api.listarContenidos() }
  catch (_) { contenidos.value = [] }
  finally { cargandoContenidos.value = false }
})

const categorias = computed(() => {
  const set = new Set(contenidos.value.map(c => c.categoria).filter(Boolean))
  return ['todas', ...set]
})

const filtrados = computed(() =>
  categoriaActiva.value === 'todas'
    ? contenidos.value
    : contenidos.value.filter(c => c.categoria === categoriaActiva.value)
)

const recursosEmergencia = [
  { titulo: 'Línea 113 — Salud Mental MINSA', numero: '113 · opción 5', horario: '24h · 7 días',
    desc: 'Atención gratuita 24/7 en salud mental.', tono: 'red',    icon: '🆘' },
  { titulo: 'SALUDLINE — Emergencias',         numero: '106',          horario: '24h · 7 días',
    desc: 'Crisis aguda o riesgo inmediato.',    tono: 'peach',  icon: '🚑' },
  { titulo: 'Teléfono de la Esperanza',        numero: '717-003-700',  horario: '24h · 7 días',
    desc: 'Apoyo emocional confidencial.',       tono: 'brand',  icon: '🤝' },
]

const consejos = [
  { titulo: 'Sueño reparador',     texto: 'Dormir 8–9 horas mejora el ánimo y la concentración.', icon: '😴' },
  { titulo: 'Mueve el cuerpo',     texto: 'Caminar 30 min al día libera endorfinas.',             icon: '🚶' },
  { titulo: 'Red de apoyo',        texto: 'Habla con alguien de confianza. No tienes que cargar solo.', icon: '🫂' },
  { titulo: 'Respiración 4-7-8',   texto: 'Inhala 4s, sostén 7s, exhala 8s. Reduce la ansiedad.',  icon: '🌬️' },
  { titulo: 'Organiza tus tareas', texto: 'Divide lo grande en pasos pequeños.',                   icon: '🗂️' },
  { titulo: 'Pausa de pantallas',  texto: 'Limita redes antes de dormir.',                         icon: '📵' },
]

const tonoMap = {
  red:   { bg: 'bg-red-50',   border: 'border-red-200',   icon: 'bg-red-100 text-risk-critico' },
  peach: { bg: 'bg-peach-50', border: 'border-peach-200', icon: 'bg-peach-100 text-peach-600' },
  brand: { bg: 'bg-brand-50', border: 'border-brand-200', icon: 'bg-brand-100 text-brand-700' },
}
</script>

<template>
  <div class="page-shell-wide">
    <button @click="router.push('/menu')" class="btn-ghost btn-sm mb-3">← Volver al menú</button>

    <PageHeader
      title="Recursos de salud mental"
      subtitle="Apoyo profesional UPC, líneas de crisis nacionales y consejos de autocuidado."
      icon="🩺"
      tone="peach"
    />

    <!-- Banner crítico -->
    <div class="banner-danger mb-6 fade-in-up">
      <span class="text-2xl">🆘</span>
      <div>
        <p class="font-bold">¿Estás en crisis ahora mismo?</p>
        <p class="text-sm mt-1">
          Llama <strong>ahora</strong> a la Línea 113 opción 5 (MINSA, 24/7) o ve a emergencias.
        </p>
      </div>
    </div>

    <!-- Líneas de crisis -->
    <section class="mb-8 fade-in-up">
      <h2 class="section-title">📞 Líneas de crisis</h2>
      <div class="grid sm:grid-cols-3 gap-4 mt-3">
        <a
          v-for="r in recursosEmergencia"
          :key="r.titulo"
          :href="r.numero.startsWith('113') ? 'tel:113' : (r.numero === '106' ? 'tel:106' : 'tel:' + r.numero.replace(/-/g,''))"
          class="rounded-2xl border-l-4 p-5 shadow-soft transition hover:shadow-pastel"
          :class="[tonoMap[r.tono].bg, tonoMap[r.tono].border]"
        >
          <div class="flex items-start gap-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0" :class="tonoMap[r.tono].icon">
              {{ r.icon }}
            </div>
            <div class="min-w-0">
              <h3 class="font-bold text-ink-900 text-sm">{{ r.titulo }}</h3>
              <p class="text-ink-600 text-xs mt-0.5">{{ r.desc }}</p>
            </div>
          </div>
          <p class="mt-4 text-2xl font-bold text-ink-900 tracking-tight">{{ r.numero }}</p>
          <p class="text-xs text-ink-500">{{ r.horario }}</p>
        </a>
      </div>
    </section>

    <!-- Servicios UPC -->
    <section class="mb-8 fade-in-up">
      <h2 class="section-title">🏛️ Servicios dentro de la UPC</h2>
      <div class="grid sm:grid-cols-2 gap-4 mt-3">
        <div class="card p-5">
          <div class="flex items-center gap-3 mb-3">
            <div class="avatar-md bg-brand-100">🧠</div>
            <h3 class="font-bold text-ink-900">Bienestar Estudiantil UPC</h3>
          </div>
          <ul class="text-sm text-ink-700 space-y-1.5">
            <li><span class="text-ink-400">📍</span> Pabellón D, 2do piso</li>
            <li><span class="text-ink-400">📞</span> (01) 313-3333 anexo 2500</li>
            <li><span class="text-ink-400">🕒</span> Lun a Vie · 8:00 – 18:00</li>
            <li><span class="text-ink-400">✉️</span> bienestar@upc.edu.pe</li>
          </ul>
        </div>
        <div class="card p-5">
          <div class="flex items-center gap-3 mb-3">
            <div class="avatar-md bg-peach-100">⚕️</div>
            <h3 class="font-bold text-ink-900">Centro Médico UPC</h3>
          </div>
          <ul class="text-sm text-ink-700 space-y-1.5">
            <li><span class="text-ink-400">📍</span> Edificio C, 1er piso</li>
            <li><span class="text-ink-400">🕒</span> Lun a Vie · 7:30 – 19:00</li>
            <li><span class="text-ink-400">🩺</span> Atención médica + derivación a psicólogo</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- Biblioteca psicoeducativa -->
    <section v-if="contenidos.length > 0 || cargandoContenidos" class="mb-8 fade-in-up">
      <div class="flex justify-between items-end mb-4 flex-wrap gap-2">
        <div>
          <h2 class="section-title !mb-1">📚 Biblioteca psicoeducativa</h2>
          <p class="section-subtitle">Artículos y recursos curados para cuidarte.</p>
        </div>
        <div v-if="categorias.length > 2" class="flex flex-wrap gap-1.5">
          <button
            v-for="cat in categorias"
            :key="cat"
            @click="categoriaActiva = cat"
            :class="categoriaActiva === cat ? 'chip-brand !bg-brand-500 !text-white' : 'chip-ink hover:chip-brand'"
            class="capitalize"
          >{{ cat }}</button>
        </div>
      </div>
      <p v-if="cargandoContenidos" class="text-sm text-ink-500">Cargando…</p>
      <div v-else class="grid sm:grid-cols-2 gap-4">
        <a
          v-for="c in filtrados"
          :key="c.id"
          :href="c.url || '#'"
          :target="c.url ? '_blank' : '_self'"
          rel="noopener"
          class="card p-5 hover:shadow-pastel hover:border-brand-200 transition"
        >
          <p class="font-semibold text-ink-900">{{ c.titulo }}</p>
          <p class="text-xs text-ink-500 mt-1">{{ c.descripcion }}</p>
          <p v-if="c.categoria" class="dsm5-tag mt-3">{{ c.categoria }}</p>
        </a>
      </div>
    </section>

    <!-- Consejos -->
    <section class="fade-in-up">
      <h2 class="section-title">🌿 Consejos de autocuidado</h2>
      <p class="section-subtitle mb-4">Pequeños hábitos que marcan una gran diferencia.</p>
      <div class="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
        <div v-for="c in consejos" :key="c.titulo" class="card-pastel p-5">
          <p class="text-2xl mb-2">{{ c.icon }}</p>
          <p class="font-semibold text-ink-900 text-sm">{{ c.titulo }}</p>
          <p class="text-xs text-ink-600 mt-1">{{ c.texto }}</p>
        </div>
      </div>
    </section>

    <!-- CTA evaluación -->
    <div class="banner-brand mt-8 flex items-center justify-between gap-4 flex-wrap fade-in-up">
      <div class="flex items-center gap-3">
        <span class="text-2xl">💬</span>
        <div>
          <p class="font-semibold">¿Quieres conocer tu estado emocional?</p>
          <p class="text-sm text-ink-600">Haz tu evaluación con el chatbot — 10 preguntas.</p>
        </div>
      </div>
      <router-link to="/chat" class="btn-mint btn-sm">Iniciar evaluación</router-link>
    </div>
  </div>
</template>
