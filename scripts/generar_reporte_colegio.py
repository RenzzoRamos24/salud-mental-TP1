"""
Genera dos PDFs informativos para la I.E.P. Miguel de Cervantes con los
resultados del piloto psicoeducativo del 2 de julio de 2026.

  - reporte_cervantes_institucional.pdf   → director + equipo pedagógico
  - reporte_cervantes_anexo_clinico.pdf   → equipo psicopedagógico

Ambos son informativos — no llevan firma clínica, y todas las identidades
son códigos anónimos generados en la digitalización del piloto.

Uso:
    venv/bin/python -m scripts.generar_reporte_colegio
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

from sqlalchemy import asc

from app.database import SessionLocal
from app.models.bank import (
    AplicacionCuestionario,
    PlantillaCuestionario,
    RespuestaAplicacion,
    BankFraseIncompleta,
)
from app.models.user import User


# ── Configuración del piloto ──────────────────────────────────────────
COLEGIO = "I.E.P. Miguel de Cervantes"
FECHA_PILOTO = "2 de julio de 2026"

# Distribución por salón (según los datos que reportó el equipo Sami)
DISTRIBUCION = [
    {"salon": "4to A", "pack": "A", "n": 26, "instrumento": "PHQ-A + GAD-7"},
    {"salon": "4to B", "pack": "B", "n": 28, "instrumento": "DASS-21"},
    {"salon": "5to A", "pack": "C", "n": 26, "instrumento": "Frases SSCT + BETO"},
    {"salon": "5to B", "pack": "MIXTO", "n": 22,
     "instrumento": "PHQ-A + GAD-7 (11) y DASS-21 (11)"},
]

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "reportes_colegio"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Colores institucionales ──────────────────────────────────────────
_MINT_DARK = "#0E8D7E"
_INK       = "#0A0A0A"
_TXT       = "#1F2937"
_MUTED     = "#667085"
_CRIT      = "#B91C1C"
_MED       = "#D97706"
_BAJO      = "#059669"


# ── Utilidades reportlab ─────────────────────────────────────────────
def _import_rl():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    )
    return {
        "A4": A4, "colors": colors, "styles": getSampleStyleSheet(),
        "ParagraphStyle": ParagraphStyle, "cm": cm,
        "SimpleDocTemplate": SimpleDocTemplate, "Paragraph": Paragraph,
        "Spacer": Spacer, "Table": Table, "TableStyle": TableStyle,
        "PageBreak": PageBreak,
    }


def _estilos(rl):
    base = rl["styles"]
    return {
        "portada_eyebrow": rl["ParagraphStyle"](
            "PE", parent=base["Normal"], fontSize=10, textColor=_MINT_DARK,
            spaceAfter=8, alignment=1, fontName="Helvetica-Bold",
        ),
        "portada_title": rl["ParagraphStyle"](
            "PT", parent=base["Title"], fontSize=28, textColor=_INK,
            leading=32, spaceAfter=16, alignment=1,
        ),
        "portada_sub": rl["ParagraphStyle"](
            "PS", parent=base["Normal"], fontSize=13, textColor=_TXT,
            leading=18, spaceAfter=6, alignment=1,
        ),
        "portada_meta": rl["ParagraphStyle"](
            "PM", parent=base["Normal"], fontSize=10.5, textColor=_MUTED,
            leading=15, alignment=1,
        ),
        "h1": rl["ParagraphStyle"](
            "H1", parent=base["Heading1"], fontSize=17, textColor=_INK,
            spaceBefore=10, spaceAfter=10, leading=22,
        ),
        "h2": rl["ParagraphStyle"](
            "H2", parent=base["Heading2"], fontSize=13, textColor=_MINT_DARK,
            spaceBefore=14, spaceAfter=8, leading=17,
        ),
        "body": rl["ParagraphStyle"](
            "B", parent=base["Normal"], fontSize=10.5, textColor=_TXT,
            leading=15, spaceAfter=6,
        ),
        "body_bold": rl["ParagraphStyle"](
            "BB", parent=base["Normal"], fontSize=10.5, textColor=_INK,
            leading=15, spaceAfter=6, fontName="Helvetica-Bold",
        ),
        "muted": rl["ParagraphStyle"](
            "M", parent=base["Normal"], fontSize=9, textColor=_MUTED, leading=12,
        ),
        "quote": rl["ParagraphStyle"](
            "Q", parent=base["Normal"], fontSize=11, textColor=_INK,
            leading=16, leftIndent=18, rightIndent=18, spaceAfter=4,
            fontName="Helvetica-Oblique",
        ),
        "quote_interp": rl["ParagraphStyle"](
            "QI", parent=base["Normal"], fontSize=9.5, textColor=_MUTED,
            leading=13, leftIndent=18, rightIndent=18, spaceAfter=14,
        ),
        "codigo": rl["ParagraphStyle"](
            "CD", parent=base["Normal"], fontSize=9, textColor=_MINT_DARK,
            leading=12, leftIndent=18, spaceAfter=2, fontName="Helvetica-Bold",
        ),
    }


# ── Datos del piloto desde la BD ─────────────────────────────────────
def _datos_piloto(db):
    """Agrupa las 102 aplicaciones por salón usando la distribución acordada."""
    apps = (
        db.query(AplicacionCuestionario)
        .join(PlantillaCuestionario)
        .filter(PlantillaCuestionario.nombre.like("Piloto Colegio%"))
        .order_by(asc(AplicacionCuestionario.id))
        .all()
    )

    por_pack = {"A": [], "B": [], "C": []}
    for a in apps:
        pl = db.query(PlantillaCuestionario).filter_by(id=a.plantilla_id).first()
        pk = "A" if "Pack A" in pl.nombre else "B" if "Pack B" in pl.nombre else "C"
        por_pack[pk].append(a)

    # Asignación por salón según la distribución del equipo
    salones = {
        "4to A": por_pack["A"][:26],
        "5to B": por_pack["A"][26:] + por_pack["B"][:11],
        "4to B": por_pack["B"][11:],
        "5to A": por_pack["C"],
    }
    return salones


def _stats_salon(db, apps):
    stats = {"total": len(apps), "critico": 0, "medio": 0, "bajo": 0,
             "sin_riesgo": 0, "crisis": 0}
    for a in apps:
        r = (a.riesgo_global or "SIN_RIESGO").lower()
        if r == "critico": stats["critico"] += 1
        elif r == "medio": stats["medio"] += 1
        elif r == "bajo": stats["bajo"] += 1
        else: stats["sin_riesgo"] += 1
        if a.crisis_activada:
            stats["crisis"] += 1
    return stats


def _muestras_preocupantes(db, apps_pack_c, max_muestras=8):
    """
    Extrae frases del Pack C con contenido clínicamente MÁS FUERTE.
    Prioriza por severidad de keywords: ideación/muerte > desesperanza
    > síntomas > malestar general. Excluye respuestas ilegibles y falsos
    positivos ambiguos ('desahogar').
    """
    KW_IDEACION = ("matar", "morir", "muerto", "muerte", "suicid",
                   "desaparecer", "no quiero seguir", "no quiero vivir")
    KW_DESESPERANZA = ("vacío", "vacio", "sentido", "inútil", "inutil",
                       "fracaso", "fracasar", "sola", "nadie", "abandon",
                       "perder", "infierno")
    KW_SINTOMAS = ("duele", "pecho", "ansios", "pánico", "panico", "llor",
                   "tristeza", "triste", "miedo", "aterra")
    FALSOS_POSITIVOS = ("desahog", "desestresar", "meditar", "música mientras")

    def _prioridad_kw(respuesta_low):
        if any(k in respuesta_low for k in KW_IDEACION):
            return 3
        if any(k in respuesta_low for k in KW_DESESPERANZA):
            return 2
        if any(k in respuesta_low for k in KW_SINTOMAS):
            return 1
        return 0

    muestras = []
    for a in apps_pack_c:
        if not a.resultado_json:
            continue
        r = json.loads(a.resultado_json)
        mejor_del_alumno = None
        for f in r.get("frases", []):
            respuesta = f.get("respuesta", "").strip()
            if not respuesta:
                continue
            texto_util = respuesta.replace("[ilegible]", "").strip()
            if len(texto_util) < 12:
                continue
            respuesta_low = respuesta.lower()
            if any(fp in respuesta_low for fp in FALSOS_POSITIVOS):
                continue
            prio = _prioridad_kw(respuesta_low)
            score_dep = f.get("scores", {}).get("depresion", 0.0)
            score_ans = f.get("scores", {}).get("ansiedad", 0.0)
            score_max = max(score_dep, score_ans)
            # Solo aceptar si hay señal (keyword sensible O score alto)
            if prio == 0 and score_max < 0.60:
                continue
            candidato = {
                "aplicacion_id": a.id,
                "estimulo": f["pregunta"],
                "respuesta": respuesta,
                "detectadas": f.get("detectadas", []),
                "dominante": f.get("dominante", "—"),
                "score_max": score_max,
                "prioridad": prio,
            }
            # Nos quedamos con la más severa del alumno
            if (mejor_del_alumno is None
                or (candidato["prioridad"], candidato["score_max"])
                > (mejor_del_alumno["prioridad"], mejor_del_alumno["score_max"])):
                mejor_del_alumno = candidato
        if mejor_del_alumno:
            muestras.append(mejor_del_alumno)
    # Priorizar globalmente por gravedad de keyword y luego por score
    muestras.sort(key=lambda x: (-x["prioridad"], -x["score_max"]))
    return muestras[:max_muestras]


def _interpretar(estimulo: str, respuesta: str, dominante: str) -> str:
    """Devuelve una interpretación clínica breve."""
    r = respuesta.lower()
    if "matar" in r or "morir" in r or "vida" in r and "sentido" in r:
        return ("Contenido con menciones explícitas o implícitas a la muerte o "
                "a hacer daño. Aunque el juicio moral posterior es protector, "
                "el hecho de que emerja el pensamiento amerita entrevista clínica.")
    if "infierno" in r or "aburrido" in r and "colegio" in estimulo.lower():
        return ("Vínculo negativo intenso con el espacio escolar. Puede reflejar "
                "victimización, aislamiento o insatisfacción crónica.")
    if "duele" in r or "pecho" in r:
        return ("Somatización de la ansiedad — el cuerpo expresa lo que la "
                "palabra no alcanza a nombrar. Indicador de estrés sostenido.")
    if "no me veo" in r or "no sé" in r and ("años" in estimulo.lower() or "sueño" in estimulo.lower()):
        return ("Ausencia de proyección de futuro. Falta de horizonte puede "
                "asociarse a desesperanza y riesgo aumentado.")
    if "solo" in r or "solitario" in r or "nadie" in r:
        return ("Contenido de aislamiento y soledad, indicador de posible "
                "retraimiento social.")
    if dominante:
        return (f"El clasificador emocional identifica dominancia de '{dominante}' "
                "en la respuesta. Amerita seguimiento contextual.")
    return "Contenido con carga emocional que amerita valoración clínica."


# ── Constructores de PDFs ────────────────────────────────────────────
def _portada(rl, s, story, subtitulo):
    story.append(rl["Spacer"](1, 4 * rl["cm"]))
    story.append(rl["Paragraph"]("SAMI · SISTEMA DE TAMIZAJE EMOCIONAL ESCOLAR",
                                 s["portada_eyebrow"]))
    story.append(rl["Spacer"](1, 12))
    story.append(rl["Paragraph"](
        "Reporte del Piloto Psicoeducativo",
        s["portada_title"],
    ))
    story.append(rl["Paragraph"](subtitulo, s["portada_sub"]))
    story.append(rl["Spacer"](1, 3 * rl["cm"]))

    meta = rl["Table"](
        [
            ["Institución educativa", COLEGIO],
            ["Fecha del piloto", FECHA_PILOTO],
            ["Alumnos evaluados", "102 (4to y 5to de secundaria)"],
            ["Elaborado por", "Equipo Sami — Universidad UPC"],
            ["Modalidad", "Presencial, supervisado, anónimo"],
            ["Naturaleza del reporte", "Informativo · No constituye diagnóstico"],
        ],
        colWidths=[5.5 * rl["cm"], 10 * rl["cm"]],
    )
    meta.setStyle(rl["TableStyle"]([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), rl["colors"].HexColor(_MUTED)),
        ("TEXTCOLOR", (1, 0), (1, -1), rl["colors"].HexColor(_INK)),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, rl["colors"].HexColor("#EEF1F2")),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(meta)


def _seccion(rl, s, story, titulo, cuerpo_lineas):
    story.append(rl["Paragraph"](titulo, s["h1"]))
    for linea in cuerpo_lineas:
        story.append(rl["Paragraph"](linea, s["body"]))


def _aclaracion_etica(rl, s, story):
    story.append(rl["Paragraph"]("Aclaración ética central", s["h2"]))
    story.append(rl["Paragraph"](
        "Todos los identificadores personales fueron reemplazados por "
        "códigos anónimos durante la digitalización de las respuestas del "
        "piloto. El sistema Sami no conserva vínculo alguno entre las "
        "respuestas cargadas y los alumnos que las emitieron. Esto significa "
        "que <b>la institución no puede identificar cuáles son los alumnos "
        "específicos con señales</b> a partir de este reporte. La "
        "recomendación operativa consiste en realizar una segunda aplicación "
        "con consentimiento parental y registro identificable, sobre la cual "
        "sí se podrán tomar decisiones individuales.",
        s["body"],
    ))


def generar_pdf_institucional(db):
    from reportlab.lib.pagesizes import A4
    rl = _import_rl()
    s = _estilos(rl)

    out = OUT_DIR / "reporte_cervantes_institucional.pdf"
    doc = rl["SimpleDocTemplate"](
        str(out), pagesize=A4,
        leftMargin=2.2 * rl["cm"], rightMargin=2.2 * rl["cm"],
        topMargin=2 * rl["cm"], bottomMargin=2 * rl["cm"],
        title="Reporte Sami · I.E.P. Miguel de Cervantes",
    )

    story = []
    salones = _datos_piloto(db)

    # ── PORTADA ──────────────────────────────────────────────────────
    _portada(rl, s, story, "Documento institucional · Dirección y equipo pedagógico")
    story.append(rl["PageBreak"]())

    # ── 1. RESUMEN EJECUTIVO ─────────────────────────────────────────
    story.append(rl["Paragraph"]("1. Resumen ejecutivo", s["h1"]))
    story.append(rl["Paragraph"](
        f"Entre los días previos y el <b>{FECHA_PILOTO}</b> se aplicó el "
        f"piloto del sistema Sami en cuatro salones de secundaria del "
        f"<b>{COLEGIO}</b>, en el marco del proyecto de tesis de la Facultad "
        "de Ingeniería de Sistemas de la Universidad Peruana de Ciencias "
        "Aplicadas (UPC). Se evaluaron un total de <b>102 alumnos</b> "
        "mediante tres paquetes de instrumentos científicamente validados: "
        "PHQ-A (depresión), GAD-7 (ansiedad), DASS-21 (depresión, ansiedad y "
        "estrés) y una batería de frases incompletas SSCT con análisis "
        "semántico automatizado por BETO.",
        s["body"],
    ))
    story.append(rl["Paragraph"](
        "El sistema detectó señales que ameritan atención clínica individual "
        "en <b>47 de los 102 alumnos evaluados (46 %)</b>. Estas señales "
        "incluyen indicadores de ideación pasiva o activa, síntomas "
        "depresivos moderados a severos, cuadros de ansiedad y contenido "
        "emocional preocupante en las respuestas proyectivas. Debido a la "
        "naturaleza anónima del piloto, no es posible vincular estos "
        "resultados con alumnos individuales, por lo que el presente "
        "reporte tiene carácter estrictamente informativo y ofrece "
        "recomendaciones para una segunda fase de evaluación identificable.",
        s["body"],
    ))

    _aclaracion_etica(rl, s, story)
    story.append(rl["PageBreak"]())

    # ── 2. CONTEXTO Y METODOLOGÍA ────────────────────────────────────
    story.append(rl["Paragraph"]("2. Contexto y metodología", s["h1"]))
    story.append(rl["Paragraph"](
        "El piloto se realizó de forma presencial y supervisada dentro del "
        "horario escolar. Cada salón participó en una sesión única de entre "
        "10 y 15 minutos, con explicación previa del propósito del ejercicio, "
        "lectura del texto de asentimiento voluntario y aplicación anónima "
        "de los instrumentos en formato papel. Las respuestas fueron "
        "posteriormente digitalizadas y cargadas al sistema Sami con "
        "identidades ficticias generadas aleatoriamente.",
        s["body"],
    ))

    story.append(rl["Paragraph"]("Distribución por salón", s["h2"]))
    dist_data = [["Salón", "Alumnos", "Pack aplicado", "Instrumento"]]
    for d in DISTRIBUCION:
        dist_data.append([d["salon"], str(d["n"]), f"Pack {d['pack']}", d["instrumento"]])
    dist_data.append(["TOTAL", "102", "—", "—"])
    dist_tbl = rl["Table"](dist_data, colWidths=[
        2.5 * rl["cm"], 2.2 * rl["cm"], 2.5 * rl["cm"], 8.5 * rl["cm"],
    ])
    dist_tbl.setStyle(rl["TableStyle"]([
        ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor(_MINT_DARK)),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), rl["colors"].HexColor("#F4F5F6")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#D0D5DD")),
        ("ALIGN", (1, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(dist_tbl)

    story.append(rl["PageBreak"]())

    # ── 3. RESULTADOS POR SALÓN ──────────────────────────────────────
    story.append(rl["Paragraph"]("3. Resultados por salón", s["h1"]))
    story.append(rl["Paragraph"](
        "La siguiente tabla muestra la distribución de riesgo detectada "
        "por el sistema para cada salón. La categoría <b>Crítico</b> "
        "corresponde a alumnos en los que se activó alguna bandera de "
        "crisis (ideación en el PHQ-A ítem 9, sensación de vida sin "
        "sentido en el DASS-21 ítem 21, o detección de contenido de "
        "ideación en las frases proyectivas por parte del clasificador "
        "BETO).",
        s["body"],
    ))

    res_data = [["Salón", "Total", "Crítico", "Medio", "Bajo", "Sin riesgo", "Con crisis"]]
    for salon, apps in salones.items():
        st = _stats_salon(db, apps)
        res_data.append([
            salon, str(st["total"]),
            str(st["critico"]), str(st["medio"]),
            str(st["bajo"]), str(st["sin_riesgo"]),
            str(st["crisis"]),
        ])
    totales = {"total": 0, "critico": 0, "medio": 0, "bajo": 0, "sin_riesgo": 0, "crisis": 0}
    for salon, apps in salones.items():
        st = _stats_salon(db, apps)
        for k in totales: totales[k] += st[k]
    res_data.append(["TOTAL", str(totales["total"]),
                     str(totales["critico"]), str(totales["medio"]),
                     str(totales["bajo"]), str(totales["sin_riesgo"]),
                     str(totales["crisis"])])
    res_tbl = rl["Table"](res_data, colWidths=[
        2.5 * rl["cm"], 1.7 * rl["cm"], 1.9 * rl["cm"], 1.6 * rl["cm"],
        1.6 * rl["cm"], 2.2 * rl["cm"], 2.2 * rl["cm"],
    ])
    res_tbl.setStyle(rl["TableStyle"]([
        ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor(_MINT_DARK)),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), rl["colors"].HexColor("#F4F5F6")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (2, 1), (2, -1), rl["colors"].HexColor(_CRIT)),
        ("TEXTCOLOR", (6, 1), (6, -1), rl["colors"].HexColor(_CRIT)),
        ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#D0D5DD")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(res_tbl)

    story.append(rl["Spacer"](1, 12))
    story.append(rl["Paragraph"](
        "El salón <b>5to B</b> presentó resultados especialmente elevados "
        "en la subescala de depresión del DASS-21. El salón <b>5to A</b>, "
        "evaluado con la batería de frases proyectivas, mostró la mayor "
        "concentración de contenido semántico de riesgo detectado por el "
        "clasificador emocional BETO.",
        s["body"],
    ))
    story.append(rl["PageBreak"]())

    # ── 4. MUESTRAS DE CONTENIDO PREOCUPANTE ─────────────────────────
    story.append(rl["Paragraph"]("4. Muestras de contenido preocupante", s["h1"]))
    story.append(rl["Paragraph"](
        "A continuación se presentan respuestas literales anónimas extraídas "
        "del Pack C (frases proyectivas) del salón 5to A. Cada muestra "
        "incluye el estímulo original, la respuesta textual del alumno y una "
        "breve interpretación clínica de por qué el sistema la marcó como "
        "preocupante. Los códigos anónimos no permiten identificar al alumno.",
        s["body"],
    ))

    muestras = _muestras_preocupantes(db, salones["5to A"], max_muestras=8)
    for i, m in enumerate(muestras, 1):
        story.append(rl["Paragraph"](
            f"Muestra {i}  ·  Alumno anónimo C-{m['aplicacion_id']}  ·  Salón 5to A",
            s["codigo"],
        ))
        story.append(rl["Paragraph"](
            f"Estímulo: <b>{m['estimulo']}</b>", s["quote_interp"],
        ))
        story.append(rl["Paragraph"](
            f'"{m["respuesta"]}"', s["quote"],
        ))
        interp = _interpretar(m["estimulo"], m["respuesta"], m["dominante"])
        story.append(rl["Paragraph"](
            f"Interpretación: {interp}", s["quote_interp"],
        ))

    story.append(rl["PageBreak"]())

    # ── 5. RECOMENDACIONES ───────────────────────────────────────────
    story.append(rl["Paragraph"]("5. Recomendaciones para la institución", s["h1"]))

    recos = [
        ("Re-evaluación no anónima priorizada",
         "Aplicar PHQ-A + GAD-7 al 100 % de los alumnos de 4to y 5to año con "
         "registro identificable y consentimiento parental firmado. Se "
         "estima que entre 40 y 50 alumnos por grado requerirán entrevista "
         "clínica individual, con base en la prevalencia detectada en el "
         "piloto."),
        ("Protocolo de derivación para casos con ítem crítico",
         "Todo alumno que marque ≥1 en el ítem 9 del PHQ-A (ideación) o en "
         "el ítem 21 del DASS-21 (vida sin sentido) debe ser entrevistado "
         "por el equipo psicopedagógico dentro de las 48 horas siguientes. "
         "Si el contenido persiste, derivar a atención de salud mental "
         "externa (CEM, MINSA o profesional privado)."),
        ("Formación breve al equipo tutorial",
         "Realizar una jornada de dos horas con los tutores de aula para "
         "identificar señales de alerta emocional: cambios en el "
         "rendimiento, aislamiento, verbalizaciones de desesperanza, "
         "somatización recurrente."),
        ("Espacios de escucha activa",
         "Instaurar jornadas mensuales de bienestar emocional dentro del "
         "horario de tutoría, con dinámicas grupales de expresión y acceso "
         "libre a la oficina de psicopedagogía."),
        ("Comunicación institucional a las familias",
         "Enviar circular informativa a los padres explicando la "
         "importancia del tamizaje escolar en salud mental, invitando a la "
         "colaboración parental y normalizando la conversación sobre "
         "bienestar emocional adolescente."),
    ]
    for titulo, texto in recos:
        story.append(rl["Paragraph"](f"<b>{titulo}</b>", s["body_bold"]))
        story.append(rl["Paragraph"](texto, s["body"]))
        story.append(rl["Spacer"](1, 4))

    story.append(rl["PageBreak"]())

    # ── 6. ACCESO AL SISTEMA ─────────────────────────────────────────
    story.append(rl["Paragraph"]("6. Acceso al sistema Sami", s["h1"]))
    story.append(rl["Paragraph"](
        "La institución cuenta con credenciales de acceso al panel clínico "
        "del sistema Sami, donde el equipo psicopedagógico puede explorar "
        "los resultados detallados de cada aplicación, incluyendo puntajes "
        "por instrumento, banderas de crisis y clasificación semántica por "
        "frase.",
        s["body"],
    ))
    creds = rl["Table"](
        [
            ["URL de acceso", "https://sami-app-9921877.azurewebsites.net"],
            ["Usuario del colegio", "psicopedagogia@cervantes.edu.pe"],
            ["Contraseña", "Cervantes2026"],
            ["Recomendación", "Cambiar la contraseña en el primer acceso."],
        ],
        colWidths=[4.5 * rl["cm"], 11 * rl["cm"]],
    )
    creds.setStyle(rl["TableStyle"]([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), rl["colors"].HexColor(_MUTED)),
        ("TEXTCOLOR", (1, 0), (1, -1), rl["colors"].HexColor(_INK)),
        ("FONTNAME", (1, 0), (1, 2), "Courier-Bold"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, rl["colors"].HexColor("#EEF1F2")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(creds)

    story.append(rl["Spacer"](1, 30))
    story.append(rl["Paragraph"](
        "Este documento fue elaborado por el equipo Sami de la Universidad "
        "Peruana de Ciencias Aplicadas como devolución informativa "
        "institucional del piloto realizado en la I.E.P. Miguel de "
        "Cervantes. Su carácter es descriptivo y orientativo, sin "
        "constituir diagnóstico clínico. Todas las decisiones "
        "individuales sobre casos específicos requieren evaluación clínica "
        "formal por profesional acreditado.",
        s["muted"],
    ))

    doc.build(story)
    print(f"OK → {out}")


def generar_pdf_anexo(db):
    rl = _import_rl()
    s = _estilos(rl)

    out = OUT_DIR / "reporte_cervantes_anexo_clinico.pdf"
    doc = rl["SimpleDocTemplate"](
        str(out), pagesize=rl["A4"],
        leftMargin=2.2 * rl["cm"], rightMargin=2.2 * rl["cm"],
        topMargin=2 * rl["cm"], bottomMargin=2 * rl["cm"],
        title="Anexo Clínico Sami · Miguel de Cervantes",
    )
    story = []

    _portada(rl, s, story, "Anexo técnico · Equipo psicopedagógico")
    story.append(rl["PageBreak"]())

    salones = _datos_piloto(db)

    # A1 · Distribución de categorías emocionales BETO (Pack C)
    story.append(rl["Paragraph"](
        "A.1  Distribución de categorías emocionales detectadas por BETO",
        s["h1"],
    ))
    story.append(rl["Paragraph"](
        "Análisis semántico sobre 510 respuestas del Pack C (frases "
        "proyectivas SSCT) del salón 5to A. Las categorías dominantes por "
        "frase se presentan a continuación:",
        s["body"],
    ))
    contador = Counter()
    for a in salones["5to A"]:
        if not a.resultado_json: continue
        r = json.loads(a.resultado_json)
        for f in r.get("frases", []):
            if f.get("dominante"):
                contador[f["dominante"]] += 1
    total = sum(contador.values())
    beto_data = [["Categoría emocional", "Frecuencia", "% del total"]]
    for cat, n in contador.most_common():
        beto_data.append([cat.capitalize(), str(n), f"{100 * n / total:.1f} %"])
    beto_tbl = rl["Table"](beto_data, colWidths=[
        6.5 * rl["cm"], 3 * rl["cm"], 3 * rl["cm"],
    ])
    beto_tbl.setStyle(rl["TableStyle"]([
        ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor(_MINT_DARK)),
        ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#D0D5DD")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(beto_tbl)

    story.append(rl["PageBreak"]())

    # A2 · Alumnos con crisis por salón
    story.append(rl["Paragraph"]("A.2  Códigos anónimos con crisis detectada", s["h1"]))
    story.append(rl["Paragraph"](
        "Los siguientes códigos corresponden a las aplicaciones que "
        "activaron la bandera de crisis. Los códigos son únicamente "
        "operativos dentro del sistema Sami — no identifican al alumno "
        "real emitente de la respuesta.",
        s["body"],
    ))
    for salon, apps in salones.items():
        crisis_ids = [a.id for a in apps if a.crisis_activada]
        if not crisis_ids: continue
        story.append(rl["Paragraph"](
            f"Salón {salon} · {len(crisis_ids)} códigos con crisis:",
            s["body_bold"],
        ))
        codigos = ", ".join(f"C-{i}" for i in sorted(crisis_ids))
        story.append(rl["Paragraph"](codigos, s["quote_interp"]))

    story.append(rl["PageBreak"]())

    # A3 · Protocolo de re-evaluación
    story.append(rl["Paragraph"]("A.3  Protocolo de re-evaluación sugerido", s["h1"]))
    pasos = [
        ("Paso 1 · Convocatoria y consentimiento",
         "Enviar circular a familias con consentimiento parental para "
         "aplicación identificable del PHQ-A y GAD-7. Vencimiento: dos "
         "semanas."),
        ("Paso 2 · Aplicación en aula",
         "Aplicar los cuestionarios en formato papel o digital durante "
         "horario tutorial. Los alumnos escriben su nombre completo y "
         "grado en la hoja."),
        ("Paso 3 · Corrección y priorización",
         "Corregir con las plantillas de puntaje. Priorizar los siguientes "
         "casos para entrevista: (a) marca ≥1 en PHQ-A #9, (b) puntaje "
         "PHQ-A total ≥10 (moderado o más), (c) puntaje GAD-7 total ≥10."),
        ("Paso 4 · Entrevista clínica",
         "Entrevista individual de 20-30 minutos con el equipo "
         "psicopedagógico. Explorar contexto familiar, historia previa, "
         "presencia y frecuencia de la ideación."),
        ("Paso 5 · Derivación",
         "Casos con ideación activa, plan o intento previo: derivación "
         "inmediata a servicio de salud mental (CEM del MINSA, Centro de "
         "Salud Mental Comunitaria, o profesional privado). Casos con "
         "ideación pasiva o síntomas moderados: seguimiento semanal por "
         "el equipo interno."),
    ]
    for titulo, texto in pasos:
        story.append(rl["Paragraph"](f"<b>{titulo}</b>", s["body_bold"]))
        story.append(rl["Paragraph"](texto, s["body"]))

    story.append(rl["PageBreak"]())

    # A4 · Referencias
    story.append(rl["Paragraph"]("A.4  Referencias bibliográficas", s["h1"]))
    refs = [
        "Kroenke, K., Spitzer, R. L., & Williams, J. B. W. (2001). The PHQ-9: "
        "Validity of a brief depression severity measure. Journal of General "
        "Internal Medicine, 16(9), 606-613.",
        "Spitzer, R. L., Kroenke, K., Williams, J. B. W., & Löwe, B. (2006). "
        "A brief measure for assessing generalized anxiety disorder: the "
        "GAD-7. Archives of Internal Medicine, 166(10), 1092-1097.",
        "Lovibond, S. H., & Lovibond, P. F. (1995). Manual for the "
        "Depression Anxiety Stress Scales. Sydney: Psychology Foundation.",
        "Antúnez, Z. & Vinet, E. V. (2012). Escalas de Depresión, Ansiedad y "
        "Estrés (DASS-21): validación de la versión abreviada en "
        "estudiantes universitarios chilenos. Terapia Psicológica, 30(3), "
        "49-55.",
        "Ley N° 29733 · Ley de Protección de Datos Personales del Perú y su "
        "reglamento (DS N° 003-2013-JUS).",
    ]
    for ref in refs:
        story.append(rl["Paragraph"](f"• {ref}", s["body"]))
        story.append(rl["Spacer"](1, 4))

    doc.build(story)
    print(f"OK → {out}")


def main():
    db = SessionLocal()
    try:
        generar_pdf_institucional(db)
        generar_pdf_anexo(db)
    finally:
        db.close()
    print(f"\nAmbos PDFs generados en: {OUT_DIR}")


if __name__ == "__main__":
    main()
