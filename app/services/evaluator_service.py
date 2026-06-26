"""
Evaluator: convierte las respuestas de un cuestionario en un reporte clínico
estructurado para la psicóloga.

Capas:
  1. Puntaje por bloque (PHQ-A, GAD-7, etc.) con cortes de literatura.
  2. Banderas de crisis (PHQ-A #9 ≥ 1, SRQ-20 #17 = 1, BETO ideación ≥ 0.4).
  3. Riesgo compuesto a partir del número de señales en zona de alerta.
  4. BETO sobre frases incompletas — categorías emocionales por respuesta.
  5. SVM (segunda opinión) — solo cuando la plantilla incluye DASS-21.
     Entrenado con datos reales de adolescentes 13-17 años (Open Psychometrics).
     Si discrepa con las reglas → bandera "discrepancia: revisar".
"""
import logging
from sqlalchemy.orm import Session
from app.models.bank import (
    AplicacionCuestionario,
    RespuestaAplicacion,
    PlantillaCuestionario,
    BankInstrumento,
    BankItem,
    BankFraseIncompleta,
    BloqueCustom,
)

logger = logging.getLogger(__name__)


# ── Cortes clínicos por instrumento ─────────────────────────────────────────

PHQA_CORTES = [
    (0, 4, "mínima", False),
    (5, 9, "leve", False),
    (10, 14, "moderada", True),
    (15, 19, "moderadamente severa", True),
    (20, 27, "severa", True),
]
GAD7_CORTES = [
    (0, 4, "mínima", False),
    (5, 9, "leve", False),
    (10, 14, "moderada", True),
    (15, 21, "severa", True),
]
SRQ_CORTES = [
    (0, 7, "sin sospecha", False),
    (8, 20, "sospecha de trastorno mental común", True),
]
RSES_CORTES = [
    (30, 40, "alta", False),
    (26, 29, "media", False),
    (10, 25, "baja", True),
]
WHO5_CORTES = [
    (51, 100, "adecuado", False),
    (29, 50, "posible deterioro", True),
    (0, 28, "probable depresión", True),
]
UCLA_CORTES = [
    (3, 5, "no solitario", False),
    (6, 9, "solitario", True),
]


def _aplicar_cortes(total: int, tabla) -> tuple[str, bool]:
    for lo, hi, etiqueta, alerta in tabla:
        if lo <= total <= hi:
            return etiqueta, alerta
    return "desconocido", False


def _severidad_instrumento(codigo: str, total: int) -> tuple[str, bool]:
    if codigo == "PHQ-A":
        return _aplicar_cortes(total, PHQA_CORTES)
    if codigo == "GAD-7":
        return _aplicar_cortes(total, GAD7_CORTES)
    if codigo == "SRQ-20":
        return _aplicar_cortes(total, SRQ_CORTES)
    if codigo == "RSES":
        return _aplicar_cortes(total, RSES_CORTES)
    if codigo == "WHO-5":
        return _aplicar_cortes(total, WHO5_CORTES)
    if codigo == "UCLA-3":
        return _aplicar_cortes(total, UCLA_CORTES)
    return "desconocido", False


# ── Servicio ────────────────────────────────────────────────────────────────


class EvaluatorService:

    @staticmethod
    def evaluar(db: Session, aplicacion: AplicacionCuestionario) -> dict:
        plantilla = (
            db.query(PlantillaCuestionario)
            .filter(PlantillaCuestionario.id == aplicacion.plantilla_id)
            .first()
        )
        respuestas = (
            db.query(RespuestaAplicacion)
            .filter(RespuestaAplicacion.aplicacion_id == aplicacion.id)
            .all()
        )
        resp_por_origen = {r.origen: r for r in respuestas}

        bloques_resultado = []
        frases_analisis = []
        crisis_activada = False
        senales_alerta = 0

        bloques = sorted(plantilla.bloques, key=lambda b: b.orden)
        for b in bloques:
            if b.tipo == "instrumento":
                res = EvaluatorService._evaluar_instrumento(db, b, resp_por_origen)
                if res is None:
                    continue
                bloques_resultado.append(res)
                if res["bandera_crisis"]:
                    crisis_activada = True
                if res["severidad_alerta"]:
                    senales_alerta += 1
            elif b.tipo == "custom":
                res = EvaluatorService._evaluar_custom(db, b, resp_por_origen)
                if res is None:
                    continue
                bloques_resultado.append(res)
                if res["severidad_alerta"]:
                    senales_alerta += 1
            elif b.tipo == "frases":
                analisis, crisis_aqui = EvaluatorService._evaluar_frases(
                    db, b, resp_por_origen
                )
                frases_analisis.extend(analisis)
                if crisis_aqui:
                    crisis_activada = True

        riesgo_global = EvaluatorService._riesgo_compuesto(
            crisis_activada, senales_alerta, len(bloques_resultado)
        )

        # ── Capa 5: SVM segunda opinión (solo si hay DASS-21) ────────────
        svm_resultado = EvaluatorService._segunda_opinion_svm(
            resp_por_origen, bloques_resultado, riesgo_global, crisis_activada
        )

        return {
            "riesgo_global": riesgo_global,
            "crisis_activada": crisis_activada,
            "n_senales": senales_alerta,
            "n_bloques": len(bloques_resultado),
            "bloques": bloques_resultado,
            "frases": frases_analisis,
            "svm_segunda_opinion": svm_resultado,
        }

    # ── Capa 5: SVM segunda opinión sobre DASS-21 ──────────────────────────
    @staticmethod
    def _segunda_opinion_svm(
        resp_por_origen: dict,
        bloques_resultado: list,
        riesgo_global: str,
        crisis_activada: bool,
    ) -> dict | None:
        """
        Si la aplicación incluye DASS-21, ejecuta el SVM con las 21 respuestas
        y devuelve su predicción + flag de discrepancia con las reglas.
        Si no hay DASS-21 o el SVM no está disponible, devuelve None.
        """
        # Verifica que la plantilla incluyó DASS-21 — su código aparece en los
        # bloques evaluados.
        if not any(b.get("codigo") == "DASS-21" for b in bloques_resultado):
            return None

        # Construye dict { numero (1..21): valor (0..3) } leyendo respuestas.
        respuestas = {}
        for i in range(1, 22):
            r = resp_por_origen.get(f"INSTR:DASS-21:{i}")
            if r is None or r.valor_num is None:
                return None  # Falta alguna respuesta — no opina.
            respuestas[i] = int(r.valor_num)

        from app.services.svm_service import SVMService
        pred = SVMService.predecir(respuestas)
        if pred is None:
            return None

        reglas_marcan_riesgo = (
            crisis_activada or riesgo_global not in ("SIN_RIESGO", "BAJO")
        )
        svm_marca_riesgo = (pred["clase"] == "en_riesgo")
        discrepancia = reglas_marcan_riesgo != svm_marca_riesgo

        return {
            "clase": pred["clase"],
            "probabilidad": pred["probabilidad"],
            "confianza": pred["confianza"],
            "discrepancia_con_reglas": discrepancia,
            "reglas_marcan_riesgo": reglas_marcan_riesgo,
            "dataset": "DASS-21 / Open Psychometrics — adolescentes 13-17",
            "modelo": "SVC RBF + StandardScaler",
        }

    # ── Bloque instrumento ─────────────────────────────────────────────────

    @staticmethod
    def _evaluar_instrumento(db, bloque, resp_por_origen):
        instr = (
            db.query(BankInstrumento)
            .filter(BankInstrumento.id == bloque.instrumento_id)
            .first()
        )
        if not instr:
            return None
        items = sorted(instr.items, key=lambda x: x.numero)
        total = 0
        bandera_crisis = False
        max_total = 0
        respondidos = 0
        for it in items:
            origen = f"INSTR:{instr.codigo}:{it.numero}"
            r = resp_por_origen.get(origen)
            if r is None or r.valor_num is None:
                continue
            respondidos += 1
            valor = int(r.valor_num)
            # Inversión para RSES (items 6-10).
            if int(it.inverso or 0) == 1 and instr.likert_max is not None:
                valor = instr.likert_max + (instr.likert_min or 0) - valor
            total += valor
            if int(it.bandera_crisis or 0) == 1 and valor >= 1:
                bandera_crisis = True

        # WHO-5: total bruto × 4 para estandarizar a 0-100.
        rango_max = (instr.likert_max or 1) * instr.n_items
        if instr.codigo == "WHO-5":
            total = total * 4
            rango_max = 100

        severidad, alerta = _severidad_instrumento(instr.codigo, total)

        return {
            "tipo": "instrumento",
            "codigo": instr.codigo,
            "nombre": instr.nombre,
            "dominio": instr.dominio,
            "puntaje": total,
            "rango_max": rango_max,
            "n_items": instr.n_items,
            "n_respondidos": respondidos,
            "severidad": severidad,
            "severidad_alerta": alerta,
            "bandera_crisis": bandera_crisis,
        }

    # ── Bloque custom ──────────────────────────────────────────────────────

    @staticmethod
    def _evaluar_custom(db, bloque_plantilla, resp_por_origen):
        bc = (
            db.query(BloqueCustom)
            .filter(BloqueCustom.id == bloque_plantilla.bloque_custom_id)
            .first()
        )
        if not bc:
            return None
        items = sorted(bc.items, key=lambda x: x.numero)
        total = 0
        respondidos = 0
        for it in items:
            origen = f"CUSTOM:{bc.id}:{it.numero}"
            r = resp_por_origen.get(origen)
            if r is None or r.valor_num is None:
                continue
            respondidos += 1
            valor = int(r.valor_num)
            if int(it.inverso or 0) == 1 and bc.tipo_escala == "likert":
                valor = bc.likert_max + bc.likert_min - valor
            total += valor

        rango_max = (bc.likert_max if bc.tipo_escala == "likert" else 1) * len(items)
        if total <= bc.corte_sin_alerta_max:
            severidad = "sin alerta"
            alerta = False
        elif total <= bc.corte_posible_max:
            severidad = "posible problema"
            alerta = True
        else:
            severidad = "alto"
            alerta = True

        return {
            "tipo": "custom",
            "codigo": f"CUSTOM:{bc.id}",
            "nombre": bc.nombre,
            "dominio": bc.dominio or "personalizado",
            "puntaje": total,
            "rango_max": rango_max,
            "n_items": len(items),
            "n_respondidos": respondidos,
            "severidad": severidad,
            "severidad_alerta": alerta,
            "bandera_crisis": False,
        }

    # ── Frases incompletas (BETO) ──────────────────────────────────────────

    @staticmethod
    def _evaluar_frases(db, bloque, resp_por_origen):
        from app.services.nlp_service import NLPService

        areas = (bloque.frases_areas or "").split(",")
        areas = [a.strip() for a in areas if a.strip()]
        rows = (
            db.query(BankFraseIncompleta)
            .filter(
                BankFraseIncompleta.area.in_(areas),
                BankFraseIncompleta.activo == 1,
            )
            .order_by(BankFraseIncompleta.numero)
            .all()
        )

        analisis = []
        crisis = False
        for fr in rows:
            origen = f"FRASE:{fr.numero}"
            r = resp_por_origen.get(origen)
            texto = (r.valor_texto if r else None) or ""
            if not texto.strip():
                continue
            try:
                clasif = NLPService.clasificar_frase(texto)
            except Exception as e:
                logger.warning(f"BETO falló en frase {fr.numero}: {e}")
                clasif = {
                    "scores": {}, "detectadas": [], "crisis": False, "dominante": None,
                }
            if clasif.get("crisis"):
                crisis = True
            analisis.append({
                "area": fr.area,
                "numero": fr.numero,
                "pregunta": fr.texto,
                "respuesta": texto,
                "dominante": clasif.get("dominante"),
                "detectadas": clasif.get("detectadas", []),
                "scores": clasif.get("scores", {}),
                "crisis": bool(clasif.get("crisis")),
            })
        return analisis, crisis

    # ── Riesgo compuesto ───────────────────────────────────────────────────

    @staticmethod
    def _riesgo_compuesto(crisis: bool, senales: int, n_bloques: int) -> str:
        if crisis:
            return "CRITICO"
        if n_bloques == 0:
            return "SIN_RIESGO"
        if senales >= 3:
            return "ALTO"
        if senales == 2:
            return "MEDIO"
        if senales == 1:
            return "BAJO"
        return "SIN_RIESGO"
