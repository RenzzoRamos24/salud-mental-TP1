"""
Genera un documento Word consolidado con los resultados anonimizados de
los 26 alumnos del piloto por Pack:
  - Pack A (PHQ-A + GAD-7) — 37 alumnos, 26 seleccionados
  - Pack B (DASS-21 + clasificación SVM) — 39 alumnos, 26 seleccionados
  - Pack C (Frases SSCT + análisis BETO) — 26 alumnos, todas las respuestas

Cada alumno se identifica solo por código anónimo (A01..A26).
Salida: docs/reportes_colegio/consolidado_alumnos.docx
"""
from __future__ import annotations
import json
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from app.database import SessionLocal
from app.models.bank import (
    AplicacionCuestionario, PlantillaCuestionario,
    RespuestaAplicacion, PlantillaBloque, BankItem,
)
from app.models.user import User

# Subescala del DASS-21 por número de ítem (1..21).
# Fuente: Lovibond & Lovibond 1995 (versión corta).
DASS21_SUB = {
    3: "depresion", 5: "depresion", 10: "depresion", 13: "depresion",
    16: "depresion", 17: "depresion", 21: "depresion",
    2: "ansiedad", 4: "ansiedad", 7: "ansiedad", 9: "ansiedad",
    15: "ansiedad", 19: "ansiedad", 20: "ansiedad",
    1: "estres", 6: "estres", 8: "estres", 11: "estres",
    12: "estres", 14: "estres", 18: "estres",
}

OUT = Path("docs/reportes_colegio/consolidado_alumnos.docx")

INK = RGBColor(0x1A, 0x21, 0x24)
MUTED = RGBColor(0x64, 0x70, 0x77)
ACCENT = RGBColor(0x08, 0x8E, 0x76)


def _severidad_phq_a(pts: int) -> str:
    if pts >= 20: return "SEVERA"
    if pts >= 15: return "moderadamente severa"
    if pts >= 10: return "moderada"
    if pts >= 5: return "leve"
    return "mínima"


def _severidad_gad7(pts: int) -> str:
    if pts >= 15: return "SEVERA"
    if pts >= 10: return "moderada"
    if pts >= 5: return "leve"
    return "mínima"


def _severidad_dass_sub(pts: int, escala: str) -> str:
    """DASS-21 subescalas: puntaje del sub × 2. Cortes de Lovibond."""
    total = pts * 2
    cortes = {
        "depresion": [(28, "EXTREMA"), (21, "SEVERA"), (14, "moderada"),
                      (10, "leve"), (0, "normal")],
        "ansiedad": [(20, "EXTREMA"), (15, "SEVERA"), (10, "moderada"),
                     (8, "leve"), (0, "normal")],
        "estres":  [(34, "EXTREMA"), (26, "SEVERA"), (19, "moderada"),
                    (15, "leve"), (0, "normal")],
    }[escala]
    for umbral, etiqueta in cortes:
        if total >= umbral:
            return f"{total} — {etiqueta}"
    return f"{total} — normal"


def _add_h1(doc, texto):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    r = p.add_run(texto)
    r.font.size = Pt(16)
    r.font.bold = True
    r.font.color.rgb = ACCENT


def _add_h2(doc, texto):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(texto)
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.color.rgb = INK


def _add_p(doc, texto, size=10, muted=False, bold=False, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(texto)
    r.font.size = Pt(size)
    r.font.color.rgb = MUTED if muted else INK
    r.font.bold = bold
    r.font.italic = italic
    return p


def _bloques_pack_a(res):
    """Extrae {PHQ-A: pts, GAD-7: pts} del resultado."""
    out = {"PHQ-A": None, "GAD-7": None, "crisis_activada": res.get("crisis_activada", False)}
    for b in res.get("bloques", []):
        codigo = b.get("codigo") or b.get("nombre", "")
        pts = b.get("puntaje", 0)
        if "PHQ-A" in codigo or "PHQ" in codigo:
            out["PHQ-A"] = pts
        elif "GAD-7" in codigo or "GAD" in codigo:
            out["GAD-7"] = pts
    return out


def _dass21_sub(res):
    """Extrae puntajes subescalas DASS-21 (dep/ans/est) sumando por dominio."""
    out = {"depresion_sub": 0, "ansiedad_sub": 0, "estres_sub": 0}
    # El sistema evalúa DASS-21 como bloque único, pero guarda respuestas por ítem.
    # Aquí re-calculamos por subescala usando los ítems ya conocidos.
    return out


def build():
    db = SessionLocal()
    doc = Document()

    # Márgenes
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2)
        section.right_margin = Cm(2)

    # Portada
    portada = doc.add_paragraph()
    portada.alignment = WD_ALIGN_PARAGRAPH.CENTER
    portada.paragraph_format.space_before = Pt(60)
    r = portada.add_run("SAMI · REPORTE CONSOLIDADO DE PILOTO")
    r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = MUTED

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(24)
    r = p.add_run("Resultados anonimizados alumno por alumno")
    r.font.size = Pt(22); r.font.bold = True; r.font.color.rgb = INK

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("I.E.P. Miguel de Cervantes · 3 packs · n = 102")
    r.font.size = Pt(12); r.font.color.rgb = MUTED

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(80)
    r = p.add_run(
        "Este documento presenta los resultados textuales y cuantitativos "
        "obtenidos por cada alumno en los 3 instrumentos del piloto. Los "
        "identificadores personales fueron reemplazados por códigos anónimos."
    )
    r.font.size = Pt(10); r.font.color.rgb = MUTED; r.italic = True

    doc.add_page_break()

    # ── PACK A: PHQ-A + GAD-7 ───────────────────────────────────
    _add_h1(doc, "Pack A — PHQ-A + GAD-7")
    _add_p(doc,
        "Puntajes de tamizaje cuantitativo. PHQ-A rango 0–27 (depresión); "
        "GAD-7 rango 0–21 (ansiedad generalizada). Se muestran los primeros "
        "26 alumnos para paridad con Pack C.",
        muted=True)

    apps_a = (
        db.query(AplicacionCuestionario)
        .join(PlantillaCuestionario)
        .filter(PlantillaCuestionario.nombre.like("%Pack A%"))
        .order_by(AplicacionCuestionario.id)
        .limit(26).all()
    )
    tabla = doc.add_table(rows=1, cols=5)
    tabla.style = "Light Grid Accent 1"
    hdr = tabla.rows[0].cells
    hdr[0].text = "Código"
    hdr[1].text = "PHQ-A"
    hdr[2].text = "Severidad depresión"
    hdr[3].text = "GAD-7"
    hdr[4].text = "Severidad ansiedad"

    for i, a in enumerate(apps_a, 1):
        if not a.resultado_json:
            continue
        r = json.loads(a.resultado_json)
        bl = _bloques_pack_a(r)
        row = tabla.add_row().cells
        row[0].text = f"A-{i:02}"
        phq = bl['PHQ-A'] if bl['PHQ-A'] is not None else 0
        gad = bl['GAD-7'] if bl['GAD-7'] is not None else 0
        row[1].text = str(phq)
        row[2].text = _severidad_phq_a(phq)
        row[3].text = str(gad)
        row[4].text = _severidad_gad7(gad)

    doc.add_page_break()

    # ── PACK B: DASS-21 + SVM ──────────────────────────────────
    _add_h1(doc, "Pack B — DASS-21 + clasificación SVM")
    _add_p(doc,
        "DASS-21 evalúa depresión, ansiedad y estrés en 21 ítems (7 por "
        "subescala). Los puntajes de subescala se multiplican por 2 para "
        "comparar contra los cortes de Lovibond & Lovibond. El SVM (RBF, "
        "entrenado con 7,269 adolescentes de Open Psychometrics) da una "
        "clasificación de segunda opinión.",
        muted=True)

    apps_b = (
        db.query(AplicacionCuestionario)
        .join(PlantillaCuestionario)
        .filter(PlantillaCuestionario.nombre.like("%Pack B%"))
        .order_by(AplicacionCuestionario.id)
        .limit(26).all()
    )
    tabla = doc.add_table(rows=1, cols=6)
    tabla.style = "Light Grid Accent 1"
    hdr = tabla.rows[0].cells
    hdr[0].text = "Código"
    hdr[1].text = "Depresión ×2"
    hdr[2].text = "Ansiedad ×2"
    hdr[3].text = "Estrés ×2"
    hdr[4].text = "Riesgo global"
    hdr[5].text = "SVM"

    for i, a in enumerate(apps_b, 1):
        if not a.resultado_json:
            continue
        res = json.loads(a.resultado_json)
        row = tabla.add_row().cells
        row[0].text = f"B-{i:02}"
        # Calcular subescalas sumando las respuestas por ítem DASS-21.
        # origen tiene formato "INSTR:DASS-21:<numero>".
        respuestas = (
            db.query(RespuestaAplicacion)
            .filter(RespuestaAplicacion.aplicacion_id == a.id,
                    RespuestaAplicacion.origen.like("INSTR:DASS-21:%"))
            .all()
        )
        sub = {"depresion": 0, "ansiedad": 0, "estres": 0}
        for r_ in respuestas:
            if r_.valor_num is None:
                continue
            try:
                numero = int(r_.origen.rsplit(":", 1)[-1])
            except ValueError:
                continue
            escala = DASS21_SUB.get(numero)
            if escala:
                sub[escala] += int(r_.valor_num)
        row[1].text = _severidad_dass_sub(sub["depresion"], "depresion")
        row[2].text = _severidad_dass_sub(sub["ansiedad"], "ansiedad")
        row[3].text = _severidad_dass_sub(sub["estres"], "estres")
        row[4].text = res.get("riesgo_global") or "—"
        svm = res.get("svm_segunda_opinion") or {}
        svm_txt = (
            f"{svm.get('clase', '—')} (p={svm.get('probabilidad', 0):.2f})"
            if svm else "—"
        )
        row[5].text = svm_txt

    doc.add_page_break()

    # ── PACK C: Frases SSCT + BETO ─────────────────────────────
    _add_h1(doc, "Pack C — Frases proyectivas SSCT + análisis BETO")
    _add_p(doc,
        "Cada alumno completó 20 frases incompletas (adaptación SSCT). "
        "BETO (zero-shot, 4 categorías: depresión, ansiedad, adaptativo, "
        "neutral) clasifica cada respuesta. Se listan a continuación TODAS "
        "las respuestas legibles de los 26 alumnos, agrupadas por código.",
        muted=True)

    apps_c = (
        db.query(AplicacionCuestionario)
        .join(PlantillaCuestionario)
        .filter(PlantillaCuestionario.nombre.like("%Pack C%"))
        .order_by(AplicacionCuestionario.id)
        .all()
    )
    for i, a in enumerate(apps_c, 1):
        if not a.resultado_json:
            continue
        res = json.loads(a.resultado_json)
        _add_h2(doc, f"C-{i:02}  ·  Riesgo global: {res.get('riesgo_global') or '—'}"
                     + ("  ·  BANDERA DE CRISIS" if res.get('crisis_activada') else ""))
        frases = res.get("frases", [])
        legibles = [f for f in frases
                    if f.get("respuesta", "").strip()
                    and len(f["respuesta"].replace("[ilegible]", "").strip()) >= 4]
        for f in legibles:
            resp = f.get("respuesta", "").strip()
            dom = f.get("dominante", "")
            s = f.get("scores", {})
            marca = ""
            if dom == "depresion":
                marca = f"  [DEP {s.get('depresion',0):.2f}]"
            elif dom == "ansiedad":
                marca = f"  [ANS {s.get('ansiedad',0):.2f}]"
            elif dom == "adaptativo":
                marca = f"  [adaptativo]"
            # Estímulo
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.3)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(f"{f.get('pregunta','')}")
            r.font.size = Pt(9); r.font.color.rgb = MUTED; r.italic = True
            # Respuesta
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(0.6)
            p.paragraph_format.space_after = Pt(4)
            r = p.add_run(f"“{resp}”")
            r.font.size = Pt(10); r.font.color.rgb = INK
            if marca:
                r2 = p.add_run(marca)
                r2.font.size = Pt(8); r2.font.color.rgb = MUTED

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"Guardado en {OUT.resolve()}")


if __name__ == "__main__":
    build()
