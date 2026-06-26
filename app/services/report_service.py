"""
Generación de reportes en PDF para psicólogas y administración.

- HU-34: reporte individual de un estudiante.
- HU-18: reporte mensual agregado para autoridades del colegio.

Usa ReportLab Platypus (sin templates externos). Devuelve bytes listos
para servir como `application/pdf`.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.bank import AplicacionCuestionario, PlantillaCuestionario
from app.models.clinical_note import ClinicalNote
from app.models.cita import Cita

logger = logging.getLogger(__name__)

_TEAL = "#0e8d7e"
_TEAL_SOFT = "#e3f3ef"
_INK = "#243239"
_MUTED = "#8b999e"


def _import_rl():
    """Import perezoso para no obligar reportlab en cold start."""
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
        "title": rl["ParagraphStyle"](
            "T", parent=base["Title"], fontSize=22, textColor=_INK,
            spaceAfter=4, leading=26,
        ),
        "subtitle": rl["ParagraphStyle"](
            "S", parent=base["Normal"], fontSize=10, textColor=_MUTED,
            spaceAfter=12,
        ),
        "h2": rl["ParagraphStyle"](
            "H2", parent=base["Heading2"], fontSize=13, textColor=_TEAL,
            spaceBefore=10, spaceAfter=6,
        ),
        "body": rl["ParagraphStyle"](
            "B", parent=base["Normal"], fontSize=10, textColor=_INK, leading=14,
        ),
        "muted": rl["ParagraphStyle"](
            "M", parent=base["Normal"], fontSize=9, textColor=_MUTED, leading=12,
        ),
    }


# ── HU-34: reporte individual del estudiante ──────────────────────────────
def reporte_individual_pdf(db: Session, estudiante_id: str) -> bytes:
    rl = _import_rl()
    s = _estilos(rl)

    est = db.query(User).filter(User.id == estudiante_id, User.role == "estudiante").first()
    if not est:
        raise ValueError("Estudiante no encontrado")

    aplicaciones = (
        db.query(AplicacionCuestionario)
        .filter(AplicacionCuestionario.estudiante_id == estudiante_id)
        .order_by(AplicacionCuestionario.asignada_at.desc())
        .all()
    )
    notas = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.estudiante_id == estudiante_id)
        .order_by(ClinicalNote.timestamp.desc())
        .limit(10)
        .all()
    )
    citas = (
        db.query(Cita)
        .filter(Cita.estudiante_id == estudiante_id)
        .order_by(Cita.fecha.desc(), Cita.hora.desc())
        .limit(10)
        .all()
    )

    buf = io.BytesIO()
    doc = rl["SimpleDocTemplate"](
        buf, pagesize=rl["A4"],
        leftMargin=2.0 * rl["cm"], rightMargin=2.0 * rl["cm"],
        topMargin=1.8 * rl["cm"], bottomMargin=1.8 * rl["cm"],
        title=f"Reporte clínico — {est.nombre} {est.apellido}",
        author="Sami — Salud Mental",
    )
    story = []

    # Header
    story.append(rl["Paragraph"]("Sami · Reporte clínico individual", s["title"]))
    story.append(rl["Paragraph"](
        f"Generado el {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC · "
        "Documento de uso clínico — confidencial.", s["subtitle"]
    ))

    # Datos del estudiante
    story.append(rl["Paragraph"]("Identificación del estudiante", s["h2"]))
    datos = [
        ["Nombre completo", f"{est.nombre} {est.apellido}"],
        ["Correo", est.email],
        ["Grado / curso", est.grado or "—"],
        ["Estado del caso", (est.estado_caso or "activo").title()],
        ["Cuenta creada", est.created_at.strftime("%d/%m/%Y")],
    ]
    t = rl["Table"](datos, colWidths=[5 * rl["cm"], 11 * rl["cm"]])
    t.setStyle(rl["TableStyle"]([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), rl["colors"].HexColor(_MUTED)),
        ("TEXTCOLOR", (1, 0), (1, -1), rl["colors"].HexColor(_INK)),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, rl["colors"].HexColor("#eef1f2")),
    ]))
    story.append(t)
    story.append(rl["Spacer"](1, 12))

    # Cuestionarios
    story.append(rl["Paragraph"]("Historial de cuestionarios", s["h2"]))
    if aplicaciones:
        # Cache plantilla_id -> nombre
        ids = list({a.plantilla_id for a in aplicaciones if a.plantilla_id})
        nombres = {
            p.id: p.nombre
            for p in db.query(PlantillaCuestionario).filter(
                PlantillaCuestionario.id.in_(ids)
            ).all()
        }
        tabla = [["Fecha asignación", "Plantilla", "Estado", "Riesgo global"]]
        for a in aplicaciones[:20]:
            riesgo = a.riesgo_global or "—"
            tabla.append([
                a.asignada_at.strftime("%d/%m/%Y"),
                (nombres.get(a.plantilla_id) or "—")[:40],
                a.estado.capitalize(),
                riesgo,
            ])
        t = rl["Table"](tabla, colWidths=[3.5 * rl["cm"], 7 * rl["cm"], 3 * rl["cm"], 3 * rl["cm"]])
        t.setStyle(rl["TableStyle"]([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor(_TEAL_SOFT)),
            ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].HexColor(_TEAL)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#e7ecec")),
        ]))
        story.append(t)
    else:
        story.append(rl["Paragraph"]("Sin cuestionarios respondidos aún.", s["muted"]))
    story.append(rl["Spacer"](1, 12))

    # Citas
    story.append(rl["Paragraph"]("Citas recientes", s["h2"]))
    if citas:
        tabla = [["Fecha", "Hora", "Modalidad", "Estado"]]
        for c in citas:
            tabla.append([c.fecha, c.hora, c.modalidad.capitalize(), c.estado.capitalize()])
        t = rl["Table"](tabla, colWidths=[3 * rl["cm"], 3 * rl["cm"], 5 * rl["cm"], 5.5 * rl["cm"]])
        t.setStyle(rl["TableStyle"]([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor(_TEAL_SOFT)),
            ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].HexColor(_TEAL)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#e7ecec")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
    else:
        story.append(rl["Paragraph"]("Sin citas registradas.", s["muted"]))
    story.append(rl["Spacer"](1, 12))

    # Notas clínicas
    story.append(rl["Paragraph"]("Notas clínicas (últimas 10)", s["h2"]))
    if notas:
        for n in notas:
            etiqueta = f" · {n.etiqueta}" if n.etiqueta else ""
            story.append(rl["Paragraph"](
                f"<b>{n.timestamp.strftime('%d/%m/%Y')}</b>{etiqueta}", s["body"]
            ))
            story.append(rl["Paragraph"](n.texto, s["body"]))
            story.append(rl["Spacer"](1, 6))
    else:
        story.append(rl["Paragraph"]("Sin notas clínicas registradas.", s["muted"]))

    story.append(rl["Spacer"](1, 18))
    story.append(rl["Paragraph"](
        "Este documento contiene información sensible protegida por la Ley 29733. "
        "Su uso está restringido al ejercicio profesional psicológico autorizado.",
        s["muted"]
    ))

    doc.build(story)
    return buf.getvalue()


# ── HU-18: reporte mensual agregado ───────────────────────────────────────
def reporte_mensual_pdf(db: Session, anio: int, mes: int) -> bytes:
    rl = _import_rl()
    s = _estilos(rl)

    desde = datetime(anio, mes, 1)
    if mes == 12:
        hasta = datetime(anio + 1, 1, 1)
    else:
        hasta = datetime(anio, mes + 1, 1)

    aps = (
        db.query(AplicacionCuestionario)
        .filter(AplicacionCuestionario.asignada_at >= desde)
        .filter(AplicacionCuestionario.asignada_at < hasta)
        .all()
    )

    total = len(aps)
    por_estado: dict[str, int] = {}
    por_riesgo: dict[str, int] = {}
    crisis = 0
    for a in aps:
        por_estado[a.estado] = por_estado.get(a.estado, 0) + 1
        if a.riesgo_global:
            por_riesgo[a.riesgo_global] = por_riesgo.get(a.riesgo_global, 0) + 1
        if a.crisis_activada:
            crisis += 1

    n_alumnos_activos = db.query(User).filter(
        User.role == "estudiante", User.activo.is_(True)
    ).count()
    n_psicologas = db.query(User).filter(
        User.role == "psicologo", User.activo.is_(True)
    ).count()

    buf = io.BytesIO()
    doc = rl["SimpleDocTemplate"](
        buf, pagesize=rl["A4"],
        leftMargin=2 * rl["cm"], rightMargin=2 * rl["cm"],
        topMargin=1.8 * rl["cm"], bottomMargin=1.8 * rl["cm"],
        title=f"Reporte mensual {mes:02d}/{anio}", author="Sami",
    )
    story = []

    meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    story.append(rl["Paragraph"]("Sami · Reporte mensual", s["title"]))
    story.append(rl["Paragraph"](
        f"Periodo: {meses[mes]} {anio} · Generado el "
        f"{datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC", s["subtitle"]
    ))

    # Resumen general
    story.append(rl["Paragraph"]("Resumen general", s["h2"]))
    resumen = [
        ["Estudiantes activos", str(n_alumnos_activos)],
        ["Psicólogas activas", str(n_psicologas)],
        ["Cuestionarios asignados", str(total)],
        ["Casos con bandera de crisis", str(crisis)],
    ]
    t = rl["Table"](resumen, colWidths=[8 * rl["cm"], 8 * rl["cm"]])
    t.setStyle(rl["TableStyle"]([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (0, 0), (0, -1), rl["colors"].HexColor(_MUTED)),
        ("TEXTCOLOR", (1, 0), (1, -1), rl["colors"].HexColor(_INK)),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, rl["colors"].HexColor("#eef1f2")),
    ]))
    story.append(t)
    story.append(rl["Spacer"](1, 14))

    # Por estado
    story.append(rl["Paragraph"]("Cuestionarios por estado", s["h2"]))
    if por_estado:
        rows = [["Estado", "Cantidad", "%"]]
        for k, v in sorted(por_estado.items()):
            rows.append([k.capitalize(), str(v), f"{(v/total*100) if total else 0:.1f}%"])
        t = rl["Table"](rows, colWidths=[8 * rl["cm"], 4 * rl["cm"], 4 * rl["cm"]])
        t.setStyle(rl["TableStyle"]([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor(_TEAL_SOFT)),
            ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].HexColor(_TEAL)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#e7ecec")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
    else:
        story.append(rl["Paragraph"]("Sin cuestionarios en el periodo.", s["muted"]))
    story.append(rl["Spacer"](1, 14))

    # Por nivel de riesgo
    story.append(rl["Paragraph"]("Distribución por nivel de riesgo (cuestionarios cerrados)", s["h2"]))
    cerrados = sum(por_riesgo.values())
    if cerrados:
        ORDEN = ["CRITICO", "ALTO", "MEDIO", "BAJO", "SIN_RIESGO", "—"]
        rows = [["Nivel", "Cantidad", "%"]]
        for nivel in ORDEN:
            v = por_riesgo.get(nivel)
            if not v:
                continue
            rows.append([nivel, str(v), f"{v/cerrados*100:.1f}%"])
        t = rl["Table"](rows, colWidths=[8 * rl["cm"], 4 * rl["cm"], 4 * rl["cm"]])
        t.setStyle(rl["TableStyle"]([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), rl["colors"].HexColor(_TEAL_SOFT)),
            ("TEXTCOLOR", (0, 0), (-1, 0), rl["colors"].HexColor(_TEAL)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.3, rl["colors"].HexColor("#e7ecec")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)
    else:
        story.append(rl["Paragraph"](
            "Aún no hay cuestionarios cerrados en este periodo.", s["muted"]
        ))

    story.append(rl["Spacer"](1, 18))
    story.append(rl["Paragraph"](
        "Reporte agregado y anonimizado. No incluye datos personales identificables. "
        "Cumple Ley 29733 — Protección de Datos Personales del Perú.",
        s["muted"]
    ))

    doc.build(story)
    return buf.getvalue()
