"""Eleccion de modelo SVM segun el instrumento del cuestionario.

Hay dos .joblib (PHQ-A entrenado con ENDES, DASS-21 con Open
Psychometrics) y el evaluador tiene que elegir el que corresponde. Si
elige mal, el vector de entrada no significa nada: 9 items contra una
frontera aprendida sobre 21.

Cubre: eleccion por instrumento, prioridad de DASS-21 cuando vienen los
dos, y que no opine con respuestas incompletas en lugar de imputar.

Uso:  PYTHONPATH=. venv/bin/python tests/test_svm_segunda_opinion.py
"""
import os, tempfile, warnings

warnings.filterwarnings("ignore")
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"

from app.services.evaluator_service import EvaluatorService
from app.services.svm_service import SVMService

fallos = []


def check(nombre, cond):
    print(f"{nombre} ....... {'OK' if cond else 'FALLO'}")
    if not cond:
        fallos.append(nombre)


class Resp:
    """Stand-in de RespuestaAplicacion: el evaluador solo lee valor_num."""
    def __init__(self, v):
        self.valor_num = v
        self.valor_texto = None


def phq(valor):
    return {f"INSTR:PHQ-A:{i}": Resp(valor) for i in range(1, 10)}


def dass(valor):
    return {f"INSTR:DASS-21:{i}": Resp(valor) for i in range(1, 22)}


def opinar(resp, codigos, riesgo="BAJO", crisis=False):
    return EvaluatorService._segunda_opinion_svm(
        resp_por_origen=resp,
        bloques_resultado=[{"codigo": c} for c in codigos],
        riesgo_global=riesgo,
        crisis_activada=crisis,
    )


print("Segunda opinion SVM — eleccion de modelo\n")

check("0. Los dos modelos cargan",
      SVMService.disponible() and SVMService.disponible_phq())

# ── PHQ-A ──────────────────────────────────────────────────────────────
r = opinar(phq(0), ["PHQ-A", "GAD-7"])
check("1. PHQ-A todo 0 -> sin_riesgo",
      r is not None and r["clase"] == "sin_riesgo")
check("2. ... y se reporta el instrumento",
      r["instrumento"] == "PHQ-A" and "ENDES" in r["dataset"])

# Suma 9: justo debajo del corte estandar del PHQ-9 (>= 10).
check("3. PHQ-A suma 9 (bajo el corte) -> sin_riesgo",
      opinar(phq(1), ["PHQ-A"])["clase"] == "sin_riesgo")
check("4. PHQ-A suma 18 -> en_riesgo",
      opinar(phq(2), ["PHQ-A"])["clase"] == "en_riesgo")

# ── Discrepancia con las reglas ────────────────────────────────────────
r = opinar(phq(2), ["PHQ-A"], riesgo="BAJO")
check("5. SVM dice riesgo y las reglas no -> discrepancia",
      r["discrepancia_con_reglas"] is True)
r = opinar(phq(2), ["PHQ-A"], riesgo="ALTO")
check("6. Los dos dicen riesgo -> sin discrepancia",
      r["discrepancia_con_reglas"] is False)
r = opinar(phq(0), ["PHQ-A"], crisis=True)
check("7. Crisis cuenta como riesgo por reglas",
      r["reglas_marcan_riesgo"] is True and r["discrepancia_con_reglas"] is True)

# ── DASS-21 y prioridad ────────────────────────────────────────────────
r = opinar(dass(1), ["DASS-21"])
check("8. DASS-21 usa su propio modelo",
      r is not None and r["instrumento"] == "DASS-21")

mezcla = {**dass(1), **phq(3)}
check("9. Con los dos instrumentos manda DASS-21",
      opinar(mezcla, ["DASS-21", "PHQ-A"])["instrumento"] == "DASS-21")

# ── Cuando no debe opinar ──────────────────────────────────────────────
incompleto = {f"INSTR:PHQ-A:{i}": Resp(2) for i in range(1, 9)}   # 8 de 9
check("10. Falta un item -> no opina (no imputa)",
      opinar(incompleto, ["PHQ-A"]) is None)

sin_valor = phq(2)
sin_valor["INSTR:PHQ-A:5"] = Resp(None)
check("11. Item presente pero vacio -> no opina",
      opinar(sin_valor, ["PHQ-A"]) is None)

check("12. Cuestionario de solo frases -> no opina",
      opinar({}, ["FRASES"]) is None)

print()
if fallos:
    print(f"FALLARON {len(fallos)}: " + ", ".join(fallos))
    raise SystemExit(1)
print("TODO OK - el evaluador elige el modelo correcto.")
