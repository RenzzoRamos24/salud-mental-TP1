<script setup>
import { ref, onMounted, computed } from "vue";
import { api } from "../api";
import { authStore } from "../store/auth";

const datos = ref(null);
const progreso = ref(null);
const cargando = ref(true);
const error = ref("");
const soloMias = ref(false);

// Generar la muestra es cosa de admin: hay que hacerlo una vez, antes de que
// alguien empiece a etiquetar.
const esAdmin = computed(() => authStore.state.user?.role === "admin");
const generando = ref(false);
const avisoMuestra = ref("");

async function cargar() {
  cargando.value = true;
  error.value = "";
  try {
    const [m, p] = await Promise.all([
      api.etiquetadoMetricas({ soloMias: soloMias.value }),
      api.etiquetadoProgreso(),
    ]);
    datos.value = m;
    progreso.value = p;
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo cargar.";
  } finally {
    cargando.value = false;
  }
}

async function generarMuestra() {
  generando.value = true;
  avisoMuestra.value = "";
  try {
    const r = await api.etiquetadoGenerarMuestra({ n: 100 });
    avisoMuestra.value = r.creada
      ? `Muestra creada: ${r.n} frases de un corpus de ${r.n_corpus}.`
      : r.motivo;
    await cargar();
  } catch (e) {
    error.value = e?.response?.data?.detail || "No se pudo generar la muestra.";
  } finally {
    generando.value = false;
  }
}

onMounted(cargar);

const frases = computed(() => datos.value?.frases_beto);
const casos = computed(() => datos.value?.casos_reglas_svm);
const inter = computed(() => datos.value?.inter_evaluador);

function pct(x) {
  return x === null || x === undefined ? "—" : (x * 100).toFixed(1) + "%";
}
function num(x) {
  return x === null || x === undefined ? "—" : x;
}
// Verde si cumple el umbral preregistrado, rojo si no. Sin umbral, neutro.
function colorMeta(valor, meta) {
  if (valor === null || valor === undefined) return "text-ink-400";
  return valor >= meta ? "text-green-700 font-semibold" : "text-red-700 font-semibold";
}
</script>

<template>
  <div class="page-shell-wide">
    <header class="mb-6">
      <p class="eyebrow mb-2">Validación</p>
      <h1 class="hero-serif text-[28px]">
        Resultados del <span class="hero-mint">etiquetado</span>
      </h1>
      <p class="text-sm text-ink-500 mt-2">
        Cuánto se equivocó el modelo, medido contra el criterio clínico como
        patrón de oro.
      </p>
    </header>

    <div v-if="cargando" class="card p-8 text-center text-ink-500">Cargando…</div>
    <div v-else-if="error" class="banner-danger">{{ error }}</div>

    <template v-else>
      <div class="banner-warn mb-5 text-sm">
        Conviene mirar esta pantalla <strong>después</strong> de cerrar el
        etiquetado. Consultarla a mitad de camino y seguir etiquetando es tocar
        el resultado: el criterio deja de ser independiente de lo que ya se vio.
      </div>

      <!-- Progreso -->
      <div v-if="progreso" class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <div class="card p-4">
          <p class="text-xs text-ink-500">Muestra de medición</p>
          <p class="text-2xl font-semibold text-green-900">
            {{ progreso.frases.muestra_hechas }}/{{ progreso.frases.muestra_total }}
          </p>
          <p class="text-[11px] text-ink-400">frases etiquetadas</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Resto del corpus</p>
          <p class="text-2xl font-semibold text-green-900">
            {{ progreso.frases.corpus_hechas }}/{{ progreso.frases.corpus_total }}
          </p>
          <p class="text-[11px] text-ink-400">solo reentrenamiento</p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Casos</p>
          <p class="text-2xl font-semibold text-green-900">
            {{ progreso.casos.hechas }}/{{ progreso.casos.total }}
          </p>
        </div>
        <div class="card p-4">
          <p class="text-xs text-ink-500">Evaluadores</p>
          <p class="text-2xl font-semibold text-green-900">
            {{ progreso.evaluadores_activos }}
          </p>
          <p class="text-[11px] text-ink-400">
            {{ progreso.frases.ideacion_marcadas }} frases con ideación
          </p>
        </div>
      </div>

      <!-- Sin muestra todavía -->
      <div v-if="!progreso?.muestra_generada" class="card p-6 mb-5">
        <p class="font-semibold text-green-900 mb-1">
          Falta generar la muestra de medición.
        </p>
        <p class="text-sm text-ink-500 mb-3">
          Es un sorteo estratificado por el score del modelo. Hay que hacerlo
          <strong>antes</strong> de empezar a etiquetar: si se regenera después,
          los pesos dejan de corresponder a lo etiquetado y las métricas
          proyectadas al corpus pierden validez.
        </p>
        <button
          v-if="esAdmin"
          class="btn-primary btn-sm"
          :disabled="generando"
          @click="generarMuestra"
        >
          {{ generando ? "Generando…" : "Generar muestra (100 frases)" }}
        </button>
        <p v-else class="text-xs text-ink-400">
          Lo tiene que hacer un administrador.
        </p>
        <p v-if="avisoMuestra" class="text-xs text-green-700 mt-2">
          {{ avisoMuestra }}
        </p>
      </div>

      <label class="flex items-center gap-2 text-xs text-ink-600 mb-4">
        <input v-model="soloMias" type="checkbox" @change="cargar" />
        Solo mis etiquetas
      </label>

      <!-- ── BETO ───────────────────────────────────────────────── -->
      <section class="mb-8">
        <h2 class="text-lg font-semibold text-green-900 mb-1">
          BETO — bandera de crisis sobre frases
        </h2>
        <p class="text-xs text-ink-500 mb-3">
          {{ frases?.n_etiquetadas || 0 }} frases etiquetadas,
          {{ frases?.n_muestra_metrica || 0 }} de la muestra de medición.
        </p>

        <div v-if="!frases?.listo" class="card p-5 text-sm text-ink-500">
          {{ frases?.motivo || "Todavía no hay datos." }}
        </div>

        <template v-else>
          <div v-for="b in frases.bloques" :key="b.nombre" class="card p-5 mb-3">
            <p class="font-semibold text-green-900">{{ b.nombre }}</p>
            <p class="text-xs text-ink-500 mb-3">{{ b.descripcion }}</p>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="text-left text-xs text-ink-500 border-b border-cream-300">
                    <th class="py-2 pr-3"></th>
                    <th class="py-2 px-2">VP</th>
                    <th class="py-2 px-2">FP</th>
                    <th class="py-2 px-2">VN</th>
                    <th class="py-2 px-2">FN</th>
                    <th class="py-2 px-2">Recall</th>
                    <th class="py-2 px-2">Precisión</th>
                    <th class="py-2 px-2">Especificidad</th>
                    <th class="py-2 px-2">Prevalencia</th>
                  </tr>
                </thead>
                <tbody>
                  <tr class="border-b border-cream-200">
                    <td class="py-2 pr-3 text-xs text-ink-500">Muestra</td>
                    <td class="px-2">{{ b.muestra.VP }}</td>
                    <td class="px-2">{{ b.muestra.FP }}</td>
                    <td class="px-2">{{ b.muestra.VN }}</td>
                    <td class="px-2 font-semibold text-red-700">{{ b.muestra.FN }}</td>
                    <td class="px-2" :class="colorMeta(b.muestra.recall_sensibilidad, 0.9)">
                      {{ pct(b.muestra.recall_sensibilidad) }}
                    </td>
                    <td class="px-2">{{ pct(b.muestra.precision_vpp) }}</td>
                    <td class="px-2">{{ pct(b.muestra.especificidad) }}</td>
                    <td class="px-2 text-ink-400">{{ pct(b.muestra.prevalencia) }}</td>
                  </tr>
                  <tr>
                    <td class="py-2 pr-3 text-xs text-ink-500">Proyectado al corpus</td>
                    <td class="px-2">{{ b.proyectado_al_corpus.VP }}</td>
                    <td class="px-2">{{ b.proyectado_al_corpus.FP }}</td>
                    <td class="px-2">{{ b.proyectado_al_corpus.VN }}</td>
                    <td class="px-2 font-semibold text-red-700">
                      {{ b.proyectado_al_corpus.FN }}
                    </td>
                    <td class="px-2">{{ pct(b.proyectado_al_corpus.recall_sensibilidad) }}</td>
                    <td class="px-2">{{ pct(b.proyectado_al_corpus.precision_vpp) }}</td>
                    <td class="px-2">{{ pct(b.proyectado_al_corpus.especificidad) }}</td>
                    <td class="px-2 text-ink-400">
                      {{ pct(b.proyectado_al_corpus.prevalencia) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <p class="text-[11px] text-ink-400 mb-4">
            {{ datos.nota_metodologica }}
            El recall se compara contra el umbral preregistrado de 90 %.
          </p>

          <!-- Barrido de umbral -->
          <div v-if="frases.barrido_umbral?.disponible" class="card p-5">
            <p class="font-semibold text-green-900">
              ¿Es 0.55 el umbral correcto?
            </p>
            <p class="text-xs text-ink-500 mb-3">
              Recall y precisión variando el corte de <code>depresion</code>.
              Hoy el 0.55 está elegido sin ningún número detrás; con estas
              etiquetas se puede elegir con evidencia. AUC del score contra el
              juicio clínico:
              <strong>{{ num(frases.barrido_umbral.auc_score_depresion) }}</strong>.
            </p>

            <div class="grid sm:grid-cols-2 gap-3 mb-4">
              <div class="banner-info text-sm">
                <strong>Mejor F1:</strong>
                umbral {{ num(frases.barrido_umbral.mejor_f1?.umbral) }} —
                recall {{ pct(frases.barrido_umbral.mejor_f1?.recall) }},
                precisión {{ pct(frases.barrido_umbral.mejor_f1?.precision) }}
              </div>
              <div
                class="text-sm"
                :class="
                  frases.barrido_umbral.umbral_max_con_recall_90
                    ? 'banner-success'
                    : 'banner-danger'
                "
              >
                <template v-if="frases.barrido_umbral.umbral_max_con_recall_90">
                  <strong>Recall ≥ 90 %</strong> se alcanza hasta un umbral de
                  {{ frases.barrido_umbral.umbral_max_con_recall_90 }}.
                </template>
                <template v-else>
                  <strong>Ningún umbral alcanza recall ≥ 90 %.</strong>
                  Con este clasificador el objetivo ético no se cumple variando
                  el corte: hay que cambiar el modelo o la entrada.
                </template>
              </div>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-ink-500 border-b border-cream-300">
                    <th class="py-2 pr-3">Umbral</th>
                    <th class="py-2 px-2">Recall</th>
                    <th class="py-2 px-2">Precisión</th>
                    <th class="py-2 px-2">F1</th>
                    <th class="py-2 px-2">VP</th>
                    <th class="py-2 px-2">FP</th>
                    <th class="py-2 px-2">FN</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="f in frases.barrido_umbral.filas"
                    :key="f.umbral"
                    class="border-b border-cream-100"
                    :class="f.umbral === 0.55 ? 'bg-green-50 font-semibold' : ''"
                  >
                    <td class="py-1.5 pr-3">
                      {{ f.umbral }}
                      <span v-if="f.umbral === 0.55" class="text-green-700">← actual</span>
                    </td>
                    <td class="px-2">{{ pct(f.con_dominancia.recall) }}</td>
                    <td class="px-2">{{ pct(f.con_dominancia.precision) }}</td>
                    <td class="px-2">{{ pct(f.con_dominancia.f1) }}</td>
                    <td class="px-2">{{ f.con_dominancia.VP }}</td>
                    <td class="px-2">{{ f.con_dominancia.FP }}</td>
                    <td class="px-2">{{ f.con_dominancia.FN }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Categoría -->
          <div v-if="frases.categoria?.disponible" class="card p-5 mt-3">
            <p class="font-semibold text-green-900">
              Categoría dominante — κ = {{ num(frases.categoria.kappa) }}
              <span class="text-xs font-normal text-ink-500">
                ({{ frases.categoria.interpretacion }}, n =
                {{ frases.categoria.n }})
              </span>
            </p>
            <p class="text-xs text-ink-500 mb-3">
              Acuerdo entre la categoría del psicólogo y la dominante del modelo.
              Acuerdo observado {{ pct(frases.categoria.acuerdo_observado) }},
              esperado por azar {{ pct(frases.categoria.acuerdo_esperado) }}.
            </p>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-ink-500 border-b border-cream-300">
                    <th class="py-2 pr-3">Humano \ modelo</th>
                    <th
                      v-for="c in frases.categoria.matriz.categorias"
                      :key="c"
                      class="py-2 px-2"
                    >{{ c }}</th>
                    <th class="py-2 px-2">(otro)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in frases.categoria.matriz.filas"
                    :key="row.humano"
                    class="border-b border-cream-100"
                  >
                    <td class="py-1.5 pr-3 font-semibold">{{ row.humano }}</td>
                    <td
                      v-for="c in frases.categoria.matriz.categorias"
                      :key="c"
                      class="px-2"
                      :class="c === row.humano ? 'bg-green-50 font-semibold' : ''"
                    >{{ row[c] }}</td>
                    <td class="px-2 text-ink-400">{{ row['(otro)'] }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </section>

      <!-- ── Casos: reglas y SVM ────────────────────────────────── -->
      <section class="mb-8">
        <h2 class="text-lg font-semibold text-green-900 mb-1">
          Reglas y SVM — nivel caso
        </h2>
        <p class="text-xs text-ink-500 mb-3">{{ casos?.n || 0 }} casos etiquetados.</p>

        <div v-if="!casos?.listo" class="card p-5 text-sm text-ink-500">
          {{ casos?.motivo || "Todavía no hay datos." }}
        </div>

        <template v-else>
          <div class="grid md:grid-cols-3 gap-3 mb-3">
            <div class="card p-4">
              <p class="text-xs text-ink-500">κ de Cohen (5 clases)</p>
              <p class="text-2xl font-semibold" :class="colorMeta(casos.reglas.kappa.kappa, 0.6)">
                {{ num(casos.reglas.kappa.kappa) }}
              </p>
              <p class="text-[11px] text-ink-400">
                {{ casos.reglas.kappa.interpretacion }} · meta ≥ 0.60
              </p>
            </div>
            <div class="card p-4">
              <p class="text-xs text-ink-500">κ ponderado lineal</p>
              <p
                class="text-2xl font-semibold"
                :class="colorMeta(casos.reglas.kappa_ponderado.kappa_ponderado, 0.7)"
              >
                {{ num(casos.reglas.kappa_ponderado.kappa_ponderado) }}
              </p>
              <p class="text-[11px] text-ink-400">meta ≥ 0.70</p>
            </div>
            <div class="card p-4">
              <p class="text-xs text-ink-500">Falsos negativos en CRÍTICO</p>
              <p
                class="text-2xl font-semibold"
                :class="
                  casos.reglas.falsos_negativos_criticos.n_no_detectados === 0
                    ? 'text-green-700'
                    : 'text-red-700'
                "
              >
                {{ casos.reglas.falsos_negativos_criticos.n_no_detectados }}/{{
                  casos.reglas.falsos_negativos_criticos.n_criticos_segun_psicologo
                }}
              </p>
              <p class="text-[11px] text-ink-400">la métrica ética · ideal 0</p>
            </div>
          </div>

          <!-- Reglas binarizadas -->
          <div class="card p-5 mb-3">
            <p class="font-semibold text-green-900">
              {{ casos.reglas.binarizado_medio_o_peor.nombre }}
            </p>
            <p class="text-xs text-ink-500 mb-3">
              {{ casos.reglas.binarizado_medio_o_peor.descripcion }}
            </p>
            <div class="flex flex-wrap gap-4 text-sm">
              <span>
                Sensibilidad
                <strong :class="colorMeta(casos.reglas.binarizado_medio_o_peor.muestra.recall_sensibilidad, 0.85)">
                  {{ pct(casos.reglas.binarizado_medio_o_peor.muestra.recall_sensibilidad) }}
                </strong>
                <span class="text-ink-400 text-xs">(meta 85 %)</span>
              </span>
              <span>
                Especificidad
                <strong :class="colorMeta(casos.reglas.binarizado_medio_o_peor.muestra.especificidad, 0.75)">
                  {{ pct(casos.reglas.binarizado_medio_o_peor.muestra.especificidad) }}
                </strong>
                <span class="text-ink-400 text-xs">(meta 75 %)</span>
              </span>
              <span>
                VPP <strong>{{ pct(casos.reglas.binarizado_medio_o_peor.muestra.precision_vpp) }}</strong>
              </span>
              <span>
                VPN <strong>{{ pct(casos.reglas.binarizado_medio_o_peor.muestra.vpn) }}</strong>
              </span>
            </div>
          </div>

          <!-- SVM -->
          <div class="card p-5 mb-3">
            <p class="font-semibold text-green-900">
              SVM contra el juicio clínico
              <span class="text-xs font-normal text-ink-500">(n = {{ casos.svm.n }})</span>
            </p>
            <p v-if="!casos.svm.listo" class="text-sm text-ink-500 mt-2">
              Todavía no hay casos con DASS-21 etiquetados — son los únicos
              donde el SVM opina.
            </p>
            <template v-else>
              <p class="text-xs text-ink-500 mb-3">
                Primera validación del SVM contra un patrón que no sale de los
                cortes de Lovibond con los que se entrenó. AUC contra el juicio
                humano:
                <strong>{{ num(casos.svm.auc_contra_juicio_humano) }}</strong>.
              </p>
              <div class="flex flex-wrap gap-4 text-sm">
                <span>
                  Sensibilidad
                  <strong>{{ pct(casos.svm.vs_riesgo_medio_o_peor.muestra.recall_sensibilidad) }}</strong>
                </span>
                <span>
                  Especificidad
                  <strong>{{ pct(casos.svm.vs_riesgo_medio_o_peor.muestra.especificidad) }}</strong>
                </span>
                <span>
                  VPP <strong>{{ pct(casos.svm.vs_riesgo_medio_o_peor.muestra.precision_vpp) }}</strong>
                </span>
                <span>
                  κ <strong>{{ num(casos.svm.kappa.kappa) }}</strong>
                </span>
              </div>
            </template>
          </div>

          <!-- Adjudicación -->
          <div
            v-if="casos.adjudicacion_discrepancias.n_discrepancias_etiquetadas"
            class="card p-5"
          >
            <p class="font-semibold text-green-900">
              Discrepancias SVM vs. reglas — ¿a quién le dio la razón?
            </p>
            <p class="text-xs text-ink-500 mb-3">
              {{ casos.adjudicacion_discrepancias.n_discrepancias_etiquetadas }}
              casos donde el SVM y las reglas no coincidían. El psicólogo le dio
              la razón al <strong>SVM en
              {{ casos.adjudicacion_discrepancias.razon_al_svm }}</strong> y a las
              <strong>reglas en
              {{ casos.adjudicacion_discrepancias.razon_a_las_reglas }}</strong>.
              Es el análisis que convierte "el SVM aporta" en una afirmación con
              evidencia.
            </p>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-ink-500 border-b border-cream-300">
                    <th class="py-2 pr-3">Caso</th>
                    <th class="py-2 px-2">Psicólogo</th>
                    <th class="py-2 px-2">Reglas</th>
                    <th class="py-2 px-2">SVM</th>
                    <th class="py-2 px-2">Razón a</th>
                    <th class="py-2 px-2">Comentario</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="c in casos.adjudicacion_discrepancias.casos"
                    :key="c.aplicacion_id"
                    class="border-b border-cream-100"
                  >
                    <td class="py-1.5 pr-3 font-mono">CASO-{{ c.aplicacion_id }}</td>
                    <td class="px-2">{{ c.psicologo }}</td>
                    <td class="px-2">{{ c.reglas }}</td>
                    <td class="px-2">
                      {{ c.svm }}
                      <span class="text-ink-400">
                        ({{ Math.round((c.svm_prob || 0) * 100) }}%)
                      </span>
                    </td>
                    <td
                      class="px-2 font-semibold"
                      :class="c.le_dio_razon_a === 'SVM' ? 'text-green-700' : 'text-amber-700'"
                    >{{ c.le_dio_razon_a }}</td>
                    <td class="px-2 text-ink-500">{{ c.comentario || "—" }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </section>

      <!-- ── Inter-evaluador ────────────────────────────────────── -->
      <section class="mb-8">
        <h2 class="text-lg font-semibold text-green-900 mb-1">
          Acuerdo entre evaluadores
        </h2>
        <div class="card p-5 text-sm">
          <p class="text-ink-600 mb-2">
            {{ inter.n_evaluadores }} evaluador(es).
            {{ inter.frases_solapadas }} frases y
            {{ inter.casos_solapados }} casos etiquetados por más de uno.
          </p>
          <p v-if="inter.kappa_frases_ideacion" class="mb-1">
            κ en ideación entre evaluadores:
            <strong>{{ num(inter.kappa_frases_ideacion.kappa) }}</strong>
            ({{ inter.kappa_frases_ideacion.interpretacion }})
          </p>
          <p v-if="inter.kappa_casos_riesgo" class="mb-1">
            κ en riesgo entre evaluadores:
            <strong>{{ num(inter.kappa_casos_riesgo.kappa) }}</strong>
          </p>
          <p class="text-xs text-ink-500 mt-2">{{ inter.nota }}</p>
        </div>
      </section>

      <!-- ── Dataset ────────────────────────────────────────────── -->
      <section>
        <h2 class="text-lg font-semibold text-green-900 mb-1">
          Datos para reentrenar
        </h2>
        <div class="card p-5">
          <p class="text-sm text-ink-600 mb-3">
            Las etiquetas con el texto completo y los scores que el modelo había
            dado. Sirven para recalibrar el umbral, entrenar un clasificador
            sobre los cuatro scores, o —en el caso de los casos— reentrenar el
            SVM contra criterio clínico en vez de contra la fórmula de Lovibond
            con la que ya se entrenó.
          </p>
          <div class="flex flex-wrap gap-2">
            <a
              class="btn-mint btn-sm"
              :href="api.etiquetadoDatasetUrl('frases')"
              download
            >Descargar etiquetas de frases</a>
            <a
              class="btn-mint btn-sm"
              :href="api.etiquetadoDatasetUrl('casos')"
              download
            >Descargar etiquetas de casos</a>
          </div>
          <p class="text-[11px] text-ink-400 mt-3">
            La descarga directa necesita sesión en el navegador; si el servidor
            responde 401, abrir los endpoints desde la app o usar el token.
          </p>
        </div>
      </section>
    </template>
  </div>
</template>
