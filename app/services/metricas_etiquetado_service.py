"""
Métricas del etiquetado clínico — cuánto se equivocó el modelo.

Todo se calcula contra las etiquetas humanas como patrón de oro. Dos
principios que explican las decisiones de este módulo:

1. **La muestra es estratificada, no aleatoria simple.** Los estratos
   clínicos están sobre-representados a propósito (si no, con 2.7 % de
   prevalencia una muestra aleatoria traería 3 positivos y el recall sería
   incalculable). Consecuencia: sobre la muestra, el *recall* se lee tal
   cual, pero *prevalencia* y *precisión* están infladas. Por eso cada
   matriz se reporta dos veces: cruda y proyectada al corpus con los pesos
   del estrato.

2. **Los estadísticos se calculan a mano, no con sklearn.** No es purismo:
   κ, κ ponderado y AUC son diez líneas cada uno, y en una tesis conviene
   poder mostrar exactamente de qué cuatro números sale cada métrica.

Las fórmulas son las estándar. κ de Cohen: (po - pe) / (1 - pe). κ ponderado
lineal: 1 - Σw·O / Σw·E con w = |i-j|/(k-1). AUC por el estadístico de
Mann-Whitney (proporción de pares concordantes, empates = 0.5).
"""
from __future__ import annotations

import json
import logging
from collections import Counter

from sqlalchemy.orm import Session

from app.models.etiquetado import CATEGORIAS, RIESGOS, EtiquetaCaso, EtiquetaFrase

logger = logging.getLogger(__name__)

# Orden ordinal del riesgo — hace falta para el κ ponderado y para binarizar.
ORDEN_RIESGO = {r: i for i, r in enumerate(RIESGOS)}
# "Zona de alerta" = MEDIO o peor. Es el corte con el que el EvaluatorService
# considera que hay señal, así que es el que corresponde binarizar.
CORTE_ALERTA = ORDEN_RIESGO["MEDIO"]


def _div(a: float, b: float) -> float | None:
    return round(a / b, 4) if b else None


# ══════════════════════════════════════════════════════════════════════
# Estadísticos
# ══════════════════════════════════════════════════════════════════════


def matriz_binaria(pares: list[tuple[int, int, float]]) -> dict:
    """pares = [(y_humano, y_modelo, peso)] → conteos crudos y ponderados."""
    crudo = {"VP": 0, "FP": 0, "VN": 0, "FN": 0}
    pond = {"VP": 0.0, "FP": 0.0, "VN": 0.0, "FN": 0.0}
    for y, p, w in pares:
        k = "VP" if (y and p) else "FN" if y else "FP" if p else "VN"
        crudo[k] += 1
        pond[k] += w
    return {
        "crudo": crudo,
        "ponderado": {k: round(v, 2) for k, v in pond.items()},
    }


def derivadas(c: dict) -> dict:
    VP, FP, VN, FN = c["VP"], c["FP"], c["VN"], c["FN"]
    n = VP + FP + VN + FN
    return {
        **{k: round(v, 2) if isinstance(v, float) else v for k, v in c.items()},
        "n": round(n, 2),
        "prevalencia": _div(VP + FN, n),
        "recall_sensibilidad": _div(VP, VP + FN),
        "especificidad": _div(VN, VN + FP),
        "precision_vpp": _div(VP, VP + FP),
        "vpn": _div(VN, VN + FN),
        "exactitud": _div(VP + VN, n),
        "f1": _div(2 * VP, 2 * VP + FP + FN),
    }


def bloque_binario(nombre: str, descripcion: str, pares: list) -> dict:
    m = matriz_binaria(pares)
    return {
        "nombre": nombre,
        "descripcion": descripcion,
        "muestra": derivadas(m["crudo"]),
        "proyectado_al_corpus": derivadas(m["ponderado"]),
    }


def kappa_cohen(pares: list[tuple[str, str]], categorias: list[str]) -> dict:
    """κ de Cohen sobre categorías nominales."""
    n = len(pares)
    if n == 0:
        return {"kappa": None, "n": 0, "acuerdo_observado": None}
    acuerdos = sum(1 for a, b in pares if a == b)
    po = acuerdos / n
    ca = Counter(a for a, _ in pares)
    cb = Counter(b for _, b in pares)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in categorias)
    kappa = (po - pe) / (1 - pe) if pe < 1 else None
    return {
        "kappa": round(kappa, 4) if kappa is not None else None,
        "n": n,
        "acuerdo_observado": round(po, 4),
        "acuerdo_esperado": round(pe, 4),
        "interpretacion": _interpretar_kappa(kappa),
    }


def kappa_ponderado_lineal(pares: list[tuple[str, str]]) -> dict:
    """
    κ ponderado lineal para el riesgo, que es ordinal.

    Confundir ALTO con CRÍTICO no es el mismo error que confundir SIN_RIESGO
    con CRÍTICO, y el κ simple los castiga igual. El lineal pesa el
    desacuerdo por la distancia entre categorías.
    """
    pares = [(a, b) for a, b in pares if a in ORDEN_RIESGO and b in ORDEN_RIESGO]
    n = len(pares)
    k = len(RIESGOS)
    if n == 0:
        return {"kappa_ponderado": None, "n": 0}

    ca = Counter(ORDEN_RIESGO[a] for a, _ in pares)
    cb = Counter(ORDEN_RIESGO[b] for _, b in pares)

    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = abs(i - j) / (k - 1)
            observado = sum(
                1 for a, b in pares
                if ORDEN_RIESGO[a] == i and ORDEN_RIESGO[b] == j
            ) / n
            esperado = (ca[i] / n) * (cb[j] / n)
            num += w * observado
            den += w * esperado
    kappa = 1 - num / den if den else None
    return {
        "kappa_ponderado": round(kappa, 4) if kappa is not None else None,
        "n": n,
        "interpretacion": _interpretar_kappa(kappa),
    }


def _interpretar_kappa(k: float | None) -> str | None:
    """Escala de Landis & Koch (1977)."""
    if k is None:
        return None
    if k < 0:
        return "peor que el azar"
    if k < 0.21:
        return "leve"
    if k < 0.41:
        return "aceptable"
    if k < 0.61:
        return "moderada"
    if k < 0.81:
        return "sustancial"
    return "casi perfecta"


def auc_roc(y: list[int], scores: list[float]) -> float | None:
    """
    AUC por Mann-Whitney: proporción de pares (positivo, negativo) en que el
    positivo tiene score mayor. Los empates cuentan 0.5.
    """
    pos = [s for yi, s in zip(y, scores) if yi == 1 and s is not None]
    neg = [s for yi, s in zip(y, scores) if yi == 0 and s is not None]
    if not pos or not neg:
        return None
    mejores = sum(
        1.0 if p > n else 0.5 if p == n else 0.0
        for p in pos for n in neg
    )
    return round(mejores / (len(pos) * len(neg)), 4)


def matriz_nxn(pares: list[tuple[str, str]], categorias: list[str]) -> dict:
    """Matriz humano × modelo, para reportarla completa."""
    filas = {
        h: {m: 0 for m in categorias + ["(otro)"]} for h in categorias
    }
    for h, m in pares:
        if h not in filas:
            continue
        filas[h][m if m in categorias else "(otro)"] += 1
    return {
        "categorias": categorias,
        "filas": [{"humano": h, **cols} for h, cols in filas.items()],
    }


# ══════════════════════════════════════════════════════════════════════
# Servicio
# ══════════════════════════════════════════════════════════════════════


class MetricasEtiquetadoService:

    @staticmethod
    def metricas(
        db: Session,
        evaluador_id: str | None = None,
        incluir_cruzado: bool = True,
    ) -> dict:
        """
        Reporte completo. Con `evaluador_id` se restringe a un etiquetador;
        sin él se usan todas las etiquetas (y si hay más de uno, la primera
        por frase, para no contar dos veces).

        `incluir_cruzado=False` quita todo lo que exponga el juicio de OTRA
        persona: el acuerdo inter-evaluador y la adjudicación de
        discrepancias, que lista el riesgo y el comentario textual por caso.
        Se usa para los evaluadores: si una psicóloga pudiera leer lo que
        puso la otra antes de terminar, su criterio dejaría de ser
        independiente y el κ entre ellas no mediría nada. El filtro vive acá
        y no en el endpoint para que no se pueda olvidar.
        """
        casos = MetricasEtiquetadoService._casos(db, evaluador_id)
        if not incluir_cruzado:
            casos.pop("adjudicacion_discrepancias", None)

        return {
            "frases_beto": MetricasEtiquetadoService._frases(db, evaluador_id),
            "casos_reglas_svm": casos,
            "inter_evaluador": (
                MetricasEtiquetadoService._inter_evaluador(db)
                if incluir_cruzado else
                {
                    "visible": False,
                    "nota": (
                        "El acuerdo entre evaluadores solo lo ve un "
                        "administrador: incluye el juicio de la otra persona, "
                        "y verlo antes de terminar contaminaría tu criterio."
                    ),
                }
            ),
            "alcance": (
                "todas las etiquetas" if incluir_cruzado else "solo tus etiquetas"
            ),
            "nota_metodologica": (
                "La muestra es estratificada: el recall se lee tal cual, pero "
                "prevalencia y precisión sobre la muestra están infladas a "
                "propósito. Para esos dos usar la columna proyectada."
            ),
        }

    # ── BETO, nivel frase ─────────────────────────────────────────────

    @staticmethod
    def _frases(db: Session, evaluador_id: str | None) -> dict:
        from app.services.etiquetado_service import ids_evaluadores_prueba

        q = db.query(EtiquetaFrase)
        if evaluador_id:
            q = q.filter(EtiquetaFrase.evaluador_id == evaluador_id)
        todas = q.order_by(EtiquetaFrase.created_at).all()
        # Las cuentas de prueba etiquetan para ensayar el flujo; sus etiquetas
        # no son juicio clínico y arruinarían cualquier métrica.
        prueba = ids_evaluadores_prueba(db)
        n_prueba = sum(1 for e in todas if e.evaluador_id in prueba)
        todas = [e for e in todas if e.evaluador_id not in prueba]

        # Una etiqueta por frase: si hay dos evaluadores, la primera. El
        # acuerdo entre ellos se reporta aparte, no se promedia acá.
        vistas: set[tuple[int, int]] = set()
        filas = []
        for e in todas:
            clave = (e.aplicacion_id, e.frase_numero)
            if clave in vistas:
                continue
            vistas.add(clave)
            filas.append(e)

        muestra = [e for e in filas if e.es_muestra_metrica]
        if not muestra:
            return {
                "n_etiquetadas": len(filas),
                "n_muestra_metrica": 0,
                "n_descartadas_prueba": n_prueba,
                "listo": False,
                "motivo": (
                    "Todavía no hay etiquetas de la muestra de medición. Las "
                    "métricas se calculan sobre esa muestra porque es la única "
                    "con probabilidad de inclusión conocida."
                ),
            }

        def peso(e) -> float:
            return float(e.peso or 1.0)

        # (1) La bandera de crisis contra ideación suicida — la métrica ética.
        pares_ideacion = [
            (int(e.ideacion_presente), int(bool(e.modelo_crisis)), peso(e))
            for e in muestra
        ]
        # (2) La bandera contra su propia definición. La hipótesis de
        #     'depresion' es compuesta: ideas de muerte O desesperanza total O
        #     sentimientos incapacitantes. Medirla solo contra ideación cuenta
        #     como falso positivo cada acierto sobre desesperanza severa.
        # `categoria == 'depresion'` cuenta como positivo del criterio amplio.
        # Eso permite que el formulario quede en dos preguntas: si el
        # psicólogo clasificó la frase como depresión clínica, eso ya es el
        # "sufrimiento grave" que la hipótesis declara detectar, y no hace
        # falta un campo aparte para preguntarlo.
        pares_amplio = [
            (
                int(
                    e.ideacion_presente
                    or e.sufrimiento_grave
                    or e.categoria == "depresion"
                ),
                int(bool(e.modelo_crisis)),
                peso(e),
            )
            for e in muestra
        ]

        bloques = [
            bloque_binario(
                "Bandera de crisis vs. ideación suicida",
                "Criterio estricto: solo cuenta como positivo la ideación. "
                "Es la métrica con umbral preregistrado (recall ≥ 0.90).",
                pares_ideacion,
            ),
            bloque_binario(
                "Bandera de crisis vs. depresión clínica (criterio amplio)",
                "Positivo = ideación, o la frase clasificada como depresión. "
                "Es lo que la hipótesis declara detectar: ideas de muerte O "
                "desesperanza total O inutilidad incapacitante.",
                pares_amplio,
            ),
        ]

        return {
            "n_etiquetadas": len(filas),
            "n_muestra_metrica": len(muestra),
            "n_descartadas_prueba": n_prueba,
            "listo": True,
            "umbral_objetivo_recall": 0.90,
            "bloques": bloques,
            "barrido_umbral": MetricasEtiquetadoService._barrido(muestra),
            "categoria": MetricasEtiquetadoService._categoria(muestra),
            "distribucion_estratos": dict(
                Counter(e.estrato for e in muestra)
            ),
            "etiquetas_confianza_baja": sum(
                1 for e in muestra if e.confianza == "baja"
            ),
        }

    @staticmethod
    def _barrido(muestra: list) -> dict:
        """
        Recall y precisión variando el umbral de `depresion`.

        Es lo más accionable de todo el reporte: dice si 0.55 es el corte
        correcto. Hoy ese valor está "calibrado" sin ningún número detrás, y
        con las etiquetas se puede elegir con evidencia. Dos variantes porque
        la regla de producción exige además que `depresion` domine.
        """
        datos = []
        for e in muestra:
            try:
                scores = json.loads(e.modelo_scores_json or "{}")
            except (ValueError, TypeError):
                scores = {}
            dep = scores.get("depresion")
            if dep is None:
                continue
            datos.append({
                "y": int(e.ideacion_presente),
                "dep": float(dep),
                "domina": e.modelo_dominante == "depresion",
                "w": float(e.peso or 1.0),
            })
        if not datos:
            return {"disponible": False}

        filas = []
        for i in range(1, 20):
            u = round(i * 0.05, 2)
            con_dom = [
                (d["y"], int(d["domina"] and d["dep"] >= u), d["w"]) for d in datos
            ]
            sin_dom = [(d["y"], int(d["dep"] >= u), d["w"]) for d in datos]
            m1 = derivadas(matriz_binaria(con_dom)["crudo"])
            m2 = derivadas(matriz_binaria(sin_dom)["crudo"])
            filas.append({
                "umbral": u,
                "con_dominancia": {
                    "recall": m1["recall_sensibilidad"],
                    "precision": m1["precision_vpp"],
                    "f1": m1["f1"],
                    "VP": m1["VP"], "FP": m1["FP"], "FN": m1["FN"],
                },
                "sin_dominancia": {
                    "recall": m2["recall_sensibilidad"],
                    "precision": m2["precision_vpp"],
                    "f1": m2["f1"],
                    "VP": m2["VP"], "FP": m2["FP"], "FN": m2["FN"],
                },
            })

        # Recomendaciones: el umbral que maximiza F1, y el más alto que
        # todavía cumple el recall preregistrado (el más alto, porque entre
        # dos que cumplen conviene el que genera menos falsas alarmas).
        con_f1 = [f for f in filas if f["con_dominancia"]["f1"] is not None]
        mejor_f1 = max(con_f1, key=lambda f: f["con_dominancia"]["f1"]) if con_f1 else None
        cumplen = [
            f for f in filas
            if (f["con_dominancia"]["recall"] or 0) >= 0.90
        ]
        return {
            "disponible": True,
            "umbral_actual": 0.55,
            "filas": filas,
            "mejor_f1": (
                {"umbral": mejor_f1["umbral"], **mejor_f1["con_dominancia"]}
                if mejor_f1 else None
            ),
            "umbral_max_con_recall_90": (
                max(f["umbral"] for f in cumplen) if cumplen else None
            ),
            "auc_score_depresion": auc_roc(
                [d["y"] for d in datos], [d["dep"] for d in datos]
            ),
        }

    @staticmethod
    def _categoria(muestra: list) -> dict:
        """κ entre la categoría del psicólogo y la dominante del modelo."""
        pares = [
            (e.categoria, e.modelo_dominante)
            for e in muestra
            if e.categoria and e.modelo_dominante
        ]
        if not pares:
            return {"disponible": False}
        return {
            "disponible": True,
            **kappa_cohen(pares, list(CATEGORIAS)),
            "matriz": matriz_nxn(pares, list(CATEGORIAS)),
        }

    # ── Reglas y SVM, nivel caso ──────────────────────────────────────

    @staticmethod
    def _casos(db: Session, evaluador_id: str | None) -> dict:
        from app.services.etiquetado_service import ids_evaluadores_prueba

        q = db.query(EtiquetaCaso)
        if evaluador_id:
            q = q.filter(EtiquetaCaso.evaluador_id == evaluador_id)
        todas = q.order_by(EtiquetaCaso.created_at).all()
        prueba = ids_evaluadores_prueba(db)
        todas = [e for e in todas if e.evaluador_id not in prueba]

        vistas: set[int] = set()
        filas = []
        for e in todas:
            if e.aplicacion_id in vistas:
                continue
            vistas.add(e.aplicacion_id)
            filas.append(e)

        if not filas:
            return {"n": 0, "listo": False, "motivo": "Todavía no hay casos etiquetados."}

        def norm_riesgo(r: str | None) -> str | None:
            if not r:
                return None
            k = r.upper().replace("Í", "I")
            return k if k in ORDEN_RIESGO else None

        # ── Reglas vs. psicólogo ──────────────────────────────────────
        pares_riesgo = [
            (e.riesgo_clinico, norm_riesgo(e.modelo_riesgo))
            for e in filas
            if norm_riesgo(e.modelo_riesgo)
        ]
        binarias_reglas = [
            (
                int(ORDEN_RIESGO[h] >= CORTE_ALERTA),
                int(ORDEN_RIESGO[m] >= CORTE_ALERTA),
                1.0,
            )
            for h, m in pares_riesgo
        ]

        # Falsos negativos en CRÍTICO: el psicólogo dice CRÍTICO y el sistema
        # no lo marcó ni como crisis ni como CRÍTICO. Es la métrica ética del
        # nivel caso, umbral preregistrado ≤ 0.05 e ideal 0.
        criticos_humanos = [e for e in filas if e.riesgo_clinico == "CRITICO"]
        fn_criticos = [
            e for e in criticos_humanos
            if norm_riesgo(e.modelo_riesgo) != "CRITICO" and not e.modelo_crisis
        ]

        reglas = {
            "kappa": kappa_cohen(pares_riesgo, list(RIESGOS)),
            "kappa_ponderado": kappa_ponderado_lineal(pares_riesgo),
            "binarizado_medio_o_peor": bloque_binario(
                "Reglas vs. psicólogo (binarizado en MEDIO)",
                "Zona de alerta = MEDIO o peor, el mismo corte que usa el "
                "EvaluatorService para contar señales.",
                binarias_reglas,
            ),
            "matriz_5x5": matriz_nxn(pares_riesgo, list(RIESGOS)),
            "falsos_negativos_criticos": {
                "n_criticos_segun_psicologo": len(criticos_humanos),
                "n_no_detectados": len(fn_criticos),
                "tasa": _div(len(fn_criticos), len(criticos_humanos)),
                "umbral_objetivo": 0.05,
                "aplicaciones": [e.aplicacion_id for e in fn_criticos],
            },
        }

        # ── SVM vs. psicólogo ─────────────────────────────────────────
        # Si el .joblib no está en el servidor, el SVM no opinó nunca y no va
        # a opinar: conviene decirlo en vez de mostrar "todavía no hay datos",
        # que sugiere que falta etiquetar. En Azure el paquete de deploy no
        # incluye `models/`, así que ahí está desinstalado.
        from app.services.svm_service import SVMService
        # Cualquiera de los dos modelos sirve: DASS-21 para el piloto de
        # julio, PHQ-9/ENDES para la cohorte de septiembre.
        svm_instalado = SVMService.disponible() or SVMService.disponible_phq()

        con_svm = [e for e in filas if e.modelo_svm_clase]
        svm = {"n": len(con_svm), "listo": False, "instalado": svm_instalado}
        if con_svm:
            pares_svm = [
                (
                    int(ORDEN_RIESGO[e.riesgo_clinico] >= CORTE_ALERTA),
                    int(e.modelo_svm_clase == "en_riesgo"),
                    1.0,
                )
                for e in con_svm
            ]
            pares_svm_deriv = [
                (
                    int(e.requiere_derivacion),
                    int(e.modelo_svm_clase == "en_riesgo"),
                    1.0,
                )
                for e in con_svm
            ]
            svm = {
                "n": len(con_svm),
                "listo": True,
                "instalado": svm_instalado,
                "vs_riesgo_medio_o_peor": bloque_binario(
                    "SVM vs. psicólogo (riesgo ≥ MEDIO)",
                    "Primera validación del SVM contra un patrón que NO sale "
                    "de los cortes de Lovibond con los que se entrenó.",
                    pares_svm,
                ),
                "vs_derivacion": bloque_binario(
                    "SVM vs. psicólogo (requiere derivación)",
                    "Binarización alternativa, sobre la decisión clínica real.",
                    pares_svm_deriv,
                ),
                "auc_contra_juicio_humano": auc_roc(
                    [p[0] for p in pares_svm],
                    [e.modelo_svm_prob for e in con_svm],
                ),
                "kappa": kappa_cohen(
                    [
                        ("en_riesgo" if p[0] else "sin_riesgo",
                         "en_riesgo" if p[1] else "sin_riesgo")
                        for p in pares_svm
                    ],
                    ["en_riesgo", "sin_riesgo"],
                ),
            }

        return {
            "n": len(filas),
            "listo": True,
            "reglas": reglas,
            "svm": svm,
            "adjudicacion_discrepancias": (
                MetricasEtiquetadoService._adjudicar(filas)
            ),
        }

    @staticmethod
    def _adjudicar(filas: list) -> dict:
        """
        Dónde el SVM y las reglas no coinciden, ¿a quién le dio la razón el
        psicólogo?

        Es el análisis de más valor del piloto: hay 14 discrepancias en los 38
        casos con DASS-21, y son lo que convierte "el SVM aporta" en una
        afirmación con evidencia en vez de una intuición.
        """
        casos = []
        for e in filas:
            if not e.modelo_svm_clase or not e.modelo_riesgo:
                continue
            k = (e.modelo_riesgo or "").upper().replace("Í", "I")
            reglas_riesgo = bool(e.modelo_crisis) or (
                ORDEN_RIESGO.get(k, 0) >= CORTE_ALERTA
            )
            svm_riesgo = e.modelo_svm_clase == "en_riesgo"
            if reglas_riesgo == svm_riesgo:
                continue
            humano_riesgo = ORDEN_RIESGO[e.riesgo_clinico] >= CORTE_ALERTA
            casos.append({
                "aplicacion_id": e.aplicacion_id,
                "psicologo": e.riesgo_clinico,
                "psicologo_en_riesgo": humano_riesgo,
                "reglas": e.modelo_riesgo,
                "svm": e.modelo_svm_clase,
                "svm_prob": e.modelo_svm_prob,
                "le_dio_razon_a": (
                    "SVM" if humano_riesgo == svm_riesgo else "reglas"
                ),
                "comentario": e.comentario,
            })
        razon_svm = sum(1 for c in casos if c["le_dio_razon_a"] == "SVM")
        return {
            "n_discrepancias_etiquetadas": len(casos),
            "razon_al_svm": razon_svm,
            "razon_a_las_reglas": len(casos) - razon_svm,
            "casos": casos,
        }

    # ── Acuerdo entre evaluadores ─────────────────────────────────────

    @staticmethod
    def _inter_evaluador(db: Session) -> dict:
        """
        κ entre dos psicólogos sobre lo que etiquetaron en común.

        Es el techo de interpretación: el sistema no puede concordar con el
        criterio clínico mejor de lo que dos clínicos concuerdan entre sí. Sin
        esto, el patrón de oro es un criterio individual y hay que declararlo
        como limitación.
        """
        from app.services.etiquetado_service import ids_evaluadores_prueba
        prueba = ids_evaluadores_prueba(db)

        por_frase: dict[tuple[int, int], dict[str, int]] = {}
        for e in db.query(EtiquetaFrase).all():
            if e.evaluador_id in prueba:
                continue
            por_frase.setdefault(
                (e.aplicacion_id, e.frase_numero), {}
            )[e.evaluador_id] = int(e.ideacion_presente)

        solapadas = [v for v in por_frase.values() if len(v) >= 2]
        frases_kappa = None
        if solapadas:
            pares = []
            for v in solapadas:
                ids = sorted(v)
                a, b = v[ids[0]], v[ids[1]]
                pares.append((str(a), str(b)))
            frases_kappa = kappa_cohen(pares, ["0", "1"])

        por_caso: dict[int, dict[str, str]] = {}
        for e in db.query(EtiquetaCaso).all():
            if e.evaluador_id in prueba:
                continue
            por_caso.setdefault(e.aplicacion_id, {})[e.evaluador_id] = e.riesgo_clinico
        solapados_caso = [v for v in por_caso.values() if len(v) >= 2]
        casos_kappa = None
        if solapados_caso:
            pares = []
            for v in solapados_caso:
                ids = sorted(v)
                pares.append((v[ids[0]], v[ids[1]]))
            casos_kappa = {
                **kappa_cohen(pares, list(RIESGOS)),
                **kappa_ponderado_lineal(pares),
            }

        n_evaluadores = len(({
            e[0] for e in db.query(EtiquetaFrase.evaluador_id).distinct().all()
        } | {
            e[0] for e in db.query(EtiquetaCaso.evaluador_id).distinct().all()
        }) - prueba)
        return {
            "n_evaluadores": n_evaluadores,
            "frases_solapadas": len(solapadas),
            "kappa_frases_ideacion": frases_kappa,
            "casos_solapados": len(solapados_caso),
            "kappa_casos_riesgo": casos_kappa,
            "nota": (
                "Con un solo evaluador no hay acuerdo inter-evaluador y el "
                "patrón de oro es un criterio individual: declararlo como "
                "limitación."
                if n_evaluadores < 2 else
                "Este κ es el techo contra el cual interpretar la "
                "concordancia del sistema."
            ),
        }
