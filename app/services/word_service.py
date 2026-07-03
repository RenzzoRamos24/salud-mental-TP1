"""
Generación de informes en formato Word (.docx).

- HU-57: reporte individual de un estudiante en Word.
- HU-58: informe firmado por la psicóloga, dirigido al padre.

Reutiliza la misma información que report_service.reporte_individual_pdf
pero la entrega en .docx para que la psicóloga pueda editarlo si quiere
antes de imprimirlo o enviarlo.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.bank import AplicacionCuestionario, PlantillaCuestionario
from app.models.clinical_note import ClinicalNote
from app.models.cita import Cita

logger = logging.getLogger(__name__)


def _import_docx():
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    return {
        "Document": Document, "Pt": Pt, "Cm": Cm, "RGBColor": RGBColor,
        "Inches": Inches, "WD_ALIGN_PARAGRAPH": WD_ALIGN_PARAGRAPH,
    }


def _h2(doc, texto, d):
    p = doc.add_paragraph()
    run = p.add_run(texto)
    run.bold = True
    run.font.size = d["Pt"](13)
    run.font.color.rgb = d["RGBColor"](0x0E, 0x8D, 0x7E)
    return p


def _meta_line(doc, texto, d):
    p = doc.add_paragraph()
    run = p.add_run(texto)
    run.font.size = d["Pt"](9)
    run.font.color.rgb = d["RGBColor"](0x8B, 0x99, 0x9E)
    return p


def reporte_individual_docx(db: Session, estudiante_id: str) -> bytes:
    """Genera un .docx con la misma estructura que el PDF clínico (HU-34)."""
    d = _import_docx()
    Document = d["Document"]

    est = db.query(User).filter(
        User.id == estudiante_id, User.role == "estudiante"
    ).first()
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

    doc = Document()

    # Título
    title = doc.add_paragraph()
    run = title.add_run("Sami · Reporte clínico individual")
    run.bold = True
    run.font.size = d["Pt"](22)
    run.font.color.rgb = d["RGBColor"](0x24, 0x32, 0x39)

    _meta_line(
        doc,
        f"Generado el {datetime.utcnow().strftime('%d/%m/%Y %H:%M')} UTC · "
        "Documento de uso clínico — confidencial.",
        d,
    )

    # Datos
    _h2(doc, "Identificación del estudiante", d)
    tabla = doc.add_table(rows=5, cols=2)
    filas = [
        ("Nombre completo", f"{est.nombre} {est.apellido}"),
        ("Correo", est.email),
        ("Grado / curso", est.grado or "—"),
        ("Estado del caso", (est.estado_caso or "activo").title()),
        ("Cuenta creada", est.created_at.strftime("%d/%m/%Y")),
    ]
    for i, (k, v) in enumerate(filas):
        tabla.rows[i].cells[0].text = k
        tabla.rows[i].cells[1].text = v

    # Cuestionarios
    _h2(doc, "Historial de cuestionarios", d)
    if aplicaciones:
        ids = list({a.plantilla_id for a in aplicaciones if a.plantilla_id})
        nombres = {
            p.id: p.nombre
            for p in db.query(PlantillaCuestionario).filter(
                PlantillaCuestionario.id.in_(ids)
            ).all()
        }
        t = doc.add_table(rows=1, cols=4)
        for i, h in enumerate(["Fecha", "Plantilla", "Estado", "Riesgo global"]):
            t.rows[0].cells[i].text = h
        for a in aplicaciones[:20]:
            r = t.add_row().cells
            r[0].text = a.asignada_at.strftime("%d/%m/%Y")
            r[1].text = (nombres.get(a.plantilla_id) or "—")[:40]
            r[2].text = a.estado.capitalize()
            r[3].text = a.riesgo_global or "—"
    else:
        doc.add_paragraph("Sin cuestionarios respondidos aún.")

    # Citas
    _h2(doc, "Citas recientes", d)
    if citas:
        t = doc.add_table(rows=1, cols=4)
        for i, h in enumerate(["Fecha", "Hora", "Modalidad", "Estado"]):
            t.rows[0].cells[i].text = h
        for c in citas:
            r = t.add_row().cells
            r[0].text = c.fecha
            r[1].text = c.hora
            r[2].text = c.modalidad.capitalize()
            r[3].text = c.estado.capitalize()
    else:
        doc.add_paragraph("Sin citas registradas.")

    # Notas
    _h2(doc, "Notas clínicas (últimas 10)", d)
    if notas:
        for n in notas:
            p = doc.add_paragraph()
            etiqueta = f" · {n.etiqueta}" if n.etiqueta else ""
            run = p.add_run(f"{n.timestamp.strftime('%d/%m/%Y')}{etiqueta}")
            run.bold = True
            doc.add_paragraph(n.texto)
    else:
        doc.add_paragraph("Sin notas clínicas registradas.")

    _meta_line(
        doc,
        "Este documento contiene información sensible protegida por la "
        "Ley 29733. Su uso está restringido al ejercicio profesional "
        "psicológico autorizado.",
        d,
    )

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def informe_para_padre_docx(db: Session, estudiante_id: str) -> bytes:
    """
    Informe NO clínico, para el padre. Solo dice:
      - identidad del hijo
      - cuántos cuestionarios respondió
      - estado del caso
      - mensaje de la psicóloga (último resumen_para_estudiante o nota)
      - firma de la psicóloga (imagen)
    NO incluye puntajes ni banderas de crisis — son confidencialidad clínica.
    """
    d = _import_docx()

    est = db.query(User).filter(
        User.id == estudiante_id, User.role == "estudiante"
    ).first()
    if not est:
        raise ValueError("Estudiante no encontrado")

    psi = None
    if est.psicologo_id:
        psi = db.query(User).filter(User.id == est.psicologo_id).first()

    aplicaciones = (
        db.query(AplicacionCuestionario)
        .filter(
            AplicacionCuestionario.estudiante_id == estudiante_id,
            AplicacionCuestionario.estado.in_(["completado", "revisado"]),
        )
        .order_by(AplicacionCuestionario.asignada_at.desc())
        .all()
    )
    ultima_cita = (
        db.query(Cita)
        .filter(
            Cita.estudiante_id == estudiante_id,
            Cita.resumen_para_estudiante.isnot(None),
        )
        .order_by(Cita.fecha.desc(), Cita.hora.desc())
        .first()
    )

    doc = d["Document"]()

    p = doc.add_paragraph()
    run = p.add_run("Sami · Informe para padre o tutor")
    run.bold = True
    run.font.size = d["Pt"](20)
    run.font.color.rgb = d["RGBColor"](0x24, 0x32, 0x39)

    _meta_line(
        doc,
        f"Generado el {datetime.utcnow().strftime('%d/%m/%Y')} · "
        "Documento informativo sin datos clínicos sensibles.",
        d,
    )

    _h2(doc, "Su estudiante", d)
    doc.add_paragraph(f"Nombre: {est.nombre} {est.apellido}")
    doc.add_paragraph(f"Grado / curso: {est.grado or '—'}")
    doc.add_paragraph(f"Estado del seguimiento: {(est.estado_caso or 'activo').title()}")

    _h2(doc, "Resumen de actividad", d)
    if aplicaciones:
        doc.add_paragraph(
            f"Su estudiante ha completado {len(aplicaciones)} cuestionario(s) "
            f"de bienestar. El último se completó el "
            f"{aplicaciones[0].asignada_at.strftime('%d/%m/%Y')}."
        )
    else:
        doc.add_paragraph(
            "Su estudiante aún no ha completado cuestionarios. La psicóloga le "
            "asignará uno cuando corresponda."
        )

    _h2(doc, "Mensaje de la psicóloga", d)
    if ultima_cita and ultima_cita.resumen_para_estudiante:
        doc.add_paragraph(ultima_cita.resumen_para_estudiante)
    else:
        doc.add_paragraph(
            "La psicóloga aún no ha dejado un mensaje. Cuando lo haga, "
            "aparecerá en este informe."
        )

    # Firma
    _h2(doc, "Firma", d)
    if psi and psi.firma_path and Path(psi.firma_path).exists():
        try:
            doc.add_picture(psi.firma_path, width=d["Cm"](5))
        except Exception as e:
            logger.warning("No se pudo insertar la firma: %s", e)
    doc.add_paragraph(
        f"{(psi.nombre + ' ' + psi.apellido) if psi else 'Equipo Sami'}\n"
        f"Psicóloga responsable"
    )

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
