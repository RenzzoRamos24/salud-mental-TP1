"""
Servicio que orquesta el análisis BETO sobre una entrada del diario.

Flujo:
    1. Reutiliza NLPService.analizar_respuestas para el análisis multi-condición
       (depresión / ansiedad / TDAH / estrés / soledad / riesgo suicida / estabilidad).
    2. Detecta qué ítems PHQ-9/GAD-7 aparecen vía `keywords_signal` definidos
       en config.py.
    3. Para cada ítem activado, infiere score Likert 0-3 con
       NLPService.proponer_score_likert.
    4. Calcula totales PHQ-9 (0-27) y GAD-7 (0-21) + severidad.
    5. Dispara `crisis_protocolo` si:
         - phq9_9 (ideación suicida) activado con score ≥ 1, o
         - BERT da score de "riesgo_suicida" ≥ umbral configurado.
    6. Persiste en `diario_analisis` y enlaza con `DiarioEntrada.analisis_id`.
    7. Si hay crisis, crea automáticamente un SosEvent para el psicólogo.

Este servicio se invoca desde un BackgroundTask, no en el POST del estudiante.
El estudiante no ve nada del resultado.
"""
import json
import logging
import time

from sqlalchemy.orm import Session

from app.config import settings
from app.models.diario_analisis import DiarioAnalisis
from app.models.diario_entrada import DiarioEntrada
from app.models.sos_event import SosEvent
from app.services.nlp_service import NLPService

logger = logging.getLogger(__name__)


class DiarioAnalisisService:

    # ─────────────────────────────────────────────────────────────────
    # ENTRADA PRINCIPAL
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def analizar_entrada(db: Session, entrada: DiarioEntrada) -> DiarioAnalisis:
        """
        Ejecuta el análisis completo sobre una entrada del diario y persiste
        el resultado. Idempotente: si la entrada ya tenía un análisis previo,
        crea uno nuevo (no se sobreescribe el viejo — útil si se quiere
        re-analizar con un modelo distinto).
        """
        tiempo_inicio = time.time()
        texto = (entrada.texto or "").strip()
        if not texto:
            raise ValueError("La entrada no tiene texto para analizar.")

        logger.info(
            f"📓 Analizando entrada de diario #{entrada.id} "
            f"(user={entrada.user_id}, len={len(texto)}c)"
        )

        # ── 1. Análisis multi-condición (BERT zero-shot) ─────────────
        multi = NLPService.analizar_respuestas([{"respuesta": texto}])

        # ── 2-3. Ítems PHQ-9/GAD-7 activados por keywords + Likert ──
        items_detectados, phq9_total, gad7_total, crisis_por_phq9_9 = (
            DiarioAnalisisService._inferir_items(texto)
        )

        # ── 4. Severidad por escala ──────────────────────────────────
        phq9_sev = DiarioAnalisisService._severidad(phq9_total, settings.PHQ9_SEVERIDAD)
        gad7_sev = DiarioAnalisisService._severidad(gad7_total, settings.GAD7_SEVERIDAD)

        # ── 5. Crisis: phq9_9 con score ≥ 1 O riesgo_suicida BERT alto ──
        umbral_suicida_pct = (
            settings.CONDICIONES["riesgo_suicida"]["umbral"] * 100
        )
        score_riesgo_suicida = multi["scores_completos"].get("riesgo_suicida", 0.0)
        crisis_por_bert = score_riesgo_suicida >= umbral_suicida_pct
        crisis = crisis_por_phq9_9 or crisis_por_bert

        # ── Nivel de riesgo final (crisis fuerza CRÍTICO) ────────────
        nivel = "CRÍTICO" if crisis else multi["nivel_riesgo"]

        # ── Score principal: el de la condición con mayor confianza ──
        detectadas = multi.get("condiciones_detectadas", {})
        if detectadas:
            score_principal = (
                max(d["confianza"] for d in detectadas.values()) / 100.0
            )
        else:
            score_principal = (
                multi["scores_completos"].get("estabilidad", 0.0) / 100.0
            )

        # ── 6. Persistir DiarioAnalisis ──────────────────────────────
        analisis = DiarioAnalisis(
            entrada_id=entrada.id,
            user_id=entrada.user_id,
            nivel_riesgo=nivel,
            score=score_principal,
            explicacion=multi.get("explicacion"),
            phq9_total=phq9_total,
            gad7_total=gad7_total,
            phq9_severidad=phq9_sev["nivel"],
            gad7_severidad=gad7_sev["nivel"],
            crisis_protocolo=crisis,
            condiciones_detectadas_json=json.dumps(detectadas, ensure_ascii=False),
            scores_completos_json=json.dumps(
                multi.get("scores_completos", {}), ensure_ascii=False
            ),
            items_detectados_json=json.dumps(items_detectados, ensure_ascii=False),
            modelo=multi.get("modelo"),
            tiempo_inferencia=round(time.time() - tiempo_inicio, 3),
        )
        db.add(analisis)
        db.commit()
        db.refresh(analisis)

        # Linkear con la entrada
        entrada.analisis_id = analisis.id
        db.commit()

        logger.info(
            f"✅ Análisis diario #{entrada.id} guardado · nivel={nivel} · "
            f"PHQ-9={phq9_total}/27 ({phq9_sev['nivel']}) · "
            f"GAD-7={gad7_total}/21 ({gad7_sev['nivel']}) · "
            f"ítems detectados={len(items_detectados)} · crisis={crisis}"
        )

        # ── 7. Si hay crisis, crear SosEvent automático ─────────────
        if crisis:
            try:
                origen_crisis = []
                if crisis_por_phq9_9:
                    origen_crisis.append("PHQ-9 ítem 9")
                if crisis_por_bert:
                    origen_crisis.append(
                        f"BERT riesgo_suicida {score_riesgo_suicida:.1f}%"
                    )
                sos = SosEvent(
                    user_id=entrada.user_id,
                    origen="diario",
                    mensaje=(
                        f"Crisis detectada en entrada de diario #{entrada.id}. "
                        f"Disparadores: {', '.join(origen_crisis)}."
                    ),
                    estado="abierto",
                )
                db.add(sos)
                db.commit()
                logger.warning(
                    f"🚨 SosEvent creado por crisis en diario #{entrada.id} "
                    f"(user={entrada.user_id})"
                )
            except Exception as e:
                logger.error(f"No se pudo crear SosEvent automático: {e}")
                db.rollback()

        return analisis

    # ─────────────────────────────────────────────────────────────────
    # DETECCIÓN DE ÍTEMS PHQ-9 / GAD-7 DESDE TEXTO LIBRE
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _inferir_items(texto: str):
        """
        Para cada ítem PHQ-9/GAD-7 mira si alguna keyword_signal aparece
        en el texto. Si aparece, corre `proponer_score_likert` para obtener
        un Likert 0-3 (frecuencia inferida). Suma totales por escala.

        Devuelve: (items_detectados[], phq9_total, gad7_total, crisis_por_phq9_9)
        """
        texto_lower = texto.lower()
        items_detectados = []
        phq9_total = 0
        gad7_total = 0
        crisis_por_phq9_9 = False

        todos_los_items = settings.PHQ9_ITEMS + settings.GAD7_ITEMS

        for item in todos_los_items:
            keywords = item.get("keywords_signal", [])
            matches = [kw for kw in keywords if kw in texto_lower]
            if not matches:
                # Ítem no activado → score 0 (no se reporta).
                continue

            # Ítem activado → inferir frecuencia con BERT
            try:
                propuesta = NLPService.proponer_score_likert(texto, item)
                score = int(propuesta.get("score_propuesto", 0))
                confianza = float(propuesta.get("confianza", 0.0))
            except Exception as e:
                logger.warning(
                    f"⚠️ Falló score_likert para {item['id']}: {e} — uso score=1"
                )
                # Si BERT falla, asumimos presencia leve (score=1) porque
                # las keywords ya confirmaron señal del síntoma.
                score = 1
                confianza = 0.0

            # Si BERT propuso 0 pero hay keywords explícitas, elevamos a 1.
            # Las keywords son evidencia léxica fuerte; no las descartamos.
            if score == 0 and matches:
                score = 1

            items_detectados.append(
                {
                    "item": item["id"],
                    "modulo": item["modulo"],
                    "criterio_dsm5": item.get("criterio_dsm5"),
                    "score": score,
                    "confianza": round(confianza, 4),
                    "keywords": matches,
                }
            )

            if item["modulo"] == "PHQ-9":
                phq9_total += score
                if item["id"] == "phq9_9" and score >= 1:
                    crisis_por_phq9_9 = True
            elif item["modulo"] == "GAD-7":
                gad7_total += score

        # Capeo defensivo a los rangos clínicos (no debería excederlos).
        phq9_total = min(phq9_total, 27)
        gad7_total = min(gad7_total, 21)

        return items_detectados, phq9_total, gad7_total, crisis_por_phq9_9

    # ─────────────────────────────────────────────────────────────────
    # AGREGACIÓN PHQ-A / GAD-7 POR CICLO COMPLETO
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def reporte_ciclo(
        db: Session,
        user_id: str,
        ciclo_inicio,
        ciclo_fin,
    ) -> dict:
        """
        Calcula el reporte clínico de un ciclo completo (14 días).

        Para cada ítem PHQ-A/GAD-7, cuenta en cuántos DÍAS DISTINTOS apareció
        y mapea ese número a un puntaje Likert oficial usando la traducción
        literal de las frases del PHQ-A (Johnson, 2002):

            0 días     → 0 puntos  ("Nunca")
            1–7 días   → 1 punto   ("Algunos días")
            8–11 días  → 2 puntos  ("Más de la mitad de los días")
            12–14 días → 3 puntos  ("Casi todos los días")

        Suma todos los ítems → PHQ-A (0-27) y GAD-7 (0-21) → aplica los
        puntos de corte oficiales para el nivel de severidad.

        Confiabilidad por cobertura:
            < 5 días escritos   → "baja" (no se considera para decisión)
            5–9 días            → "media"
            ≥ 10 días           → "alta"
        """
        from collections import defaultdict

        # Cargar entradas del ciclo + sus análisis (los que existan)
        entradas = (
            db.query(DiarioEntrada)
            .filter(
                DiarioEntrada.user_id == user_id,
                DiarioEntrada.fecha >= ciclo_inicio,
                DiarioEntrada.fecha <= ciclo_fin,
            )
            .order_by(DiarioEntrada.fecha.asc())
            .all()
        )

        # Para cada ítem, conjunto de fechas distintas con presencia
        # También acumulamos scores BETO y emojis por entrada
        dias_por_item: dict = defaultdict(set)
        CONDICIONES = ["depresion", "ansiedad", "estres_academico", "soledad", "tdah", "riesgo_suicida"]
        scores_acum: dict = defaultdict(list)
        emojis_count: dict = defaultdict(int)

        for e in entradas:
            # Emoji de estado de ánimo (siempre disponible)
            if e.estado_animo:
                emojis_count[e.estado_animo] += 1

            if not e.analisis_id:
                continue
            a = (
                db.query(DiarioAnalisis)
                .filter(DiarioAnalisis.id == e.analisis_id)
                .first()
            )
            if not a:
                continue

            # Condiciones BETO: acumular scores para promedio
            if a.scores_completos_json:
                try:
                    scores = json.loads(a.scores_completos_json)
                    for cond in CONDICIONES:
                        if cond in scores:
                            scores_acum[cond].append(scores[cond])
                except (ValueError, TypeError):
                    pass

            if not a.items_detectados_json:
                continue
            try:
                items = json.loads(a.items_detectados_json)
            except (ValueError, TypeError):
                continue
            for item in items:
                if item.get("score", 0) >= 1:
                    dias_por_item[item["item"]].add(e.fecha)

        # Promedio de scores BETO por condición en el ciclo (0–100)
        condiciones_ciclo = {
            cond: round(sum(vals) / len(vals)) if vals else 0
            for cond, vals in scores_acum.items()
        }

        # Mapeo días → puntos (tabla Johnson 2002 sobre 14 días)
        def _dias_a_puntos(n: int) -> int:
            if n <= 0:
                return 0
            if n <= 7:
                return 1
            if n <= 11:
                return 2
            return 3

        # Index de metadatos de ítems (para saber módulo y criterio DSM-5)
        meta = {
            it["id"]: it
            for it in (settings.PHQ9_ITEMS + settings.GAD7_ITEMS)
        }

        items_detalle = []
        phqa_total = 0
        gad7_total = 0

        for item_id, fechas in dias_por_item.items():
            n_dias = len(fechas)
            puntos = _dias_a_puntos(n_dias)
            info = meta.get(item_id, {})
            modulo = info.get("modulo", "")
            items_detalle.append({
                "item": item_id,
                "modulo": modulo,
                "criterio_dsm5": info.get("criterio_dsm5"),
                "dias_con_sintoma": n_dias,
                "puntos": puntos,
                "frase_likert": _frase_likert(puntos),
            })
            if modulo == "PHQ-9":
                phqa_total += puntos
            elif modulo == "GAD-7":
                gad7_total += puntos

        # Capeo defensivo
        phqa_total = min(phqa_total, 27)
        gad7_total = min(gad7_total, 21)

        # Confiabilidad por cobertura
        dias_escritos = len({e.fecha for e in entradas if e.fecha})
        dias_ciclo = (ciclo_fin - ciclo_inicio).days + 1
        cobertura_pct = (
            round(100 * dias_escritos / dias_ciclo) if dias_ciclo > 0 else 0
        )
        if dias_escritos < 5:
            confiabilidad = "baja"
        elif dias_escritos < 10:
            confiabilidad = "media"
        else:
            confiabilidad = "alta"

        items_detalle_ordenado = sorted(
            items_detalle, key=lambda x: (-x["puntos"], x["item"])
        )

        return {
            "ciclo_inicio": ciclo_inicio.isoformat(),
            "ciclo_fin": ciclo_fin.isoformat(),
            "dias_ciclo": dias_ciclo,
            "dias_escritos": dias_escritos,
            "cobertura_pct": cobertura_pct,
            "confiabilidad": confiabilidad,
            "phqa_total": phqa_total,
            "phqa_severidad": DiarioAnalisisService._severidad(
                phqa_total, settings.PHQ9_SEVERIDAD
            ),
            "gad7_total": gad7_total,
            "gad7_severidad": DiarioAnalisisService._severidad(
                gad7_total, settings.GAD7_SEVERIDAD
            ),
            "items_detalle": items_detalle_ordenado,
            "criterios_dsm5": _evaluar_criterios_dsm5(items_detalle_ordenado),
            "total_entradas": len(entradas),
            "condiciones_beto": condiciones_ciclo,
            "emojis": dict(emojis_count),
        }

    # ─────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _severidad(total: int, tabla: list) -> dict:
        """Mismo helper que usa ChatService._severidad."""
        for rango in tabla:
            if rango["min"] <= total <= rango["max"]:
                return rango
        return tabla[-1]


def _frase_likert(puntos: int) -> str:
    """Mapea puntos 0-3 a la frase oficial del PHQ-A (Johnson 2002)."""
    return {
        0: "Nunca",
        1: "Algunos días",
        2: "Más de la mitad de los días",
        3: "Casi todos los días",
    }.get(puntos, "")


def _evaluar_criterios_dsm5(items_detalle: list) -> dict:
    """
    Evalúa si los ítems del ciclo cumplen los criterios mínimos del DSM-5
    para Episodio Depresivo Mayor (EDM) y Trastorno de Ansiedad
    Generalizada (TAG). NO emite diagnóstico — solo marca
    "posible_riesgo=True" cuando el patrón observado coincide con el
    umbral del manual. El diagnóstico es competencia exclusiva del
    profesional.

    Regla operativa: un ítem se considera "cumplido" cuando obtuvo
    ≥ 2 puntos en el ciclo (equivale a "más de la mitad de los días"
    según la traducción Johnson 2002 sobre 14 días). Esto refleja el
    criterio clínico estándar: el síntoma debe estar presente la
    mayor parte del tiempo durante la ventana.

    DSM-5 — Episodio Depresivo Mayor:
        ≥ 5 síntomas durante 2 semanas + al menos uno debe ser
        ánimo deprimido (PHQ-9 ítem 2) o anhedonia (PHQ-9 ítem 1).

    DSM-5 — Trastorno de Ansiedad Generalizada:
        Ansiedad excesiva (GAD-7 ítem 1) + dificultad para
        controlar la preocupación (GAD-7 ítem 2) + ≥ 3 síntomas
        asociados en total.
    """
    cumplidos_ids = {it["item"] for it in items_detalle if it.get("puntos", 0) >= 2}

    def _info(items):
        return [
            {
                "item": it["item"],
                "criterio_dsm5": it.get("criterio_dsm5"),
                "puntos": it["puntos"],
                "frase_likert": it.get("frase_likert"),
            }
            for it in items
            if it.get("puntos", 0) >= 2
        ]

    # ── Episodio Depresivo Mayor ─────────────────────────────────────
    phq9_cumplidos = _info(
        [it for it in items_detalle if it.get("modulo") == "PHQ-9"]
    )
    incluye_animo_o_anhedonia = ("phq9_1" in cumplidos_ids) or (
        "phq9_2" in cumplidos_ids
    )
    posible_edm = len(phq9_cumplidos) >= 5 and incluye_animo_o_anhedonia

    # ── Trastorno de Ansiedad Generalizada ───────────────────────────
    gad7_cumplidos = _info(
        [it for it in items_detalle if it.get("modulo") == "GAD-7"]
    )
    nucleo_ansiedad = ("gad7_1" in cumplidos_ids) and (
        "gad7_2" in cumplidos_ids
    )
    posible_tag = nucleo_ansiedad and len(gad7_cumplidos) >= 3

    posibles_riesgos = []
    if posible_edm:
        posibles_riesgos.append("Episodio Depresivo Mayor (DSM-5)")
    if posible_tag:
        posibles_riesgos.append("Trastorno de Ansiedad Generalizada (DSM-5)")

    return {
        "edm": {
            "nombre": "Episodio Depresivo Mayor",
            "items_cumplidos": phq9_cumplidos,
            "n_cumplidos": len(phq9_cumplidos),
            "n_minimo_dsm5": 5,
            "incluye_animo_o_anhedonia": incluye_animo_o_anhedonia,
            "posible_riesgo": posible_edm,
            "nota": (
                "Requiere ≥5 ítems con puntaje ≥2 y al menos uno debe ser "
                "ánimo deprimido (PHQ-9 ítem 2) o anhedonia (PHQ-9 ítem 1)."
            ),
        },
        "tag": {
            "nombre": "Trastorno de Ansiedad Generalizada",
            "items_cumplidos": gad7_cumplidos,
            "n_cumplidos": len(gad7_cumplidos),
            "n_minimo_dsm5": 3,
            "incluye_nucleo_ansiedad": nucleo_ansiedad,
            "posible_riesgo": posible_tag,
            "nota": (
                "Requiere ansiedad (GAD-7 ítem 1) + dificultad para "
                "controlar la preocupación (GAD-7 ítem 2) + ≥3 ítems con "
                "puntaje ≥2."
            ),
        },
        "posibles_riesgos": posibles_riesgos,
        "disclaimer": (
            "Esta sección NO es un diagnóstico. Es un indicador de que el "
            "patrón observado en el diario coincide con los criterios "
            "mínimos del DSM-5 para esta entidad clínica. El diagnóstico "
            "es competencia exclusiva del profesional de salud mental."
        ),
    }


# ═════════════════════════════════════════════════════════════════════
# WRAPPER PARA EJECUTAR EN BACKGROUND
# ═════════════════════════════════════════════════════════════════════
# FastAPI BackgroundTasks no comparte la sesión DB del request, así que
# abrimos una sesión nueva para la tarea.

def analizar_en_background(entrada_id: int) -> None:
    """Función pensada para `BackgroundTasks.add_task(analizar_en_background, ...)`."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        entrada = (
            db.query(DiarioEntrada).filter(DiarioEntrada.id == entrada_id).first()
        )
        if not entrada:
            logger.warning(
                f"BackgroundTask: entrada #{entrada_id} no encontrada — skip."
            )
            return
        DiarioAnalisisService.analizar_entrada(db, entrada)
    except Exception as e:
        logger.error(
            f"❌ BackgroundTask análisis diario entrada #{entrada_id} falló: {e}",
            exc_info=True,
        )
        try:
            db.rollback()
        except Exception:
            pass
    finally:
        db.close()
