# -*- coding: utf-8 -*-
"""
Genera los dos entregables de la Semana 3:

    SAMI_HU.xlsx  — Historias de Usuario (con criterios de aceptación Gherkin)
    SAMI_CP.xlsx  — Casos de Prueba (un CP por escenario Gherkin)

Fuente única de verdad: scripts/criterios_aceptacion.py (redactado contra el
código real) + Product_Backlog_Sprints_v4.xlsx (rol, épica, SP, prioridad).

Uso:  venv/bin/python -m scripts.generar_hu_cp
"""
from pathlib import Path
import re

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

import sys

from scripts.criterios_aceptacion import CRITERIOS, ESTADO

# El entregable de Test Estático se revisa como artefacto, no contra el código:
# no lleva columna de estado de implementación. Con --con-estado se produce la
# versión interna de auditoría.
CON_ESTADO = "--con-estado" in sys.argv

# ── Identidad del entregable ────────────────────────────────────────────
CODIGO = "SAMI"
PROYECTO = "Sami — Sistema inteligente de detección temprana de señales de depresión y ansiedad en estudiantes de secundaria"
BACKLOG = Path("Product_Backlog_Sprints_v4.xlsx")

AZUL_TITULO = "1F4E79"
AZUL_HEADER = "2E5F8F"
GRIS_SUAVE = "F2F6FA"
BLANCO = "FFFFFF"
VERDE = "1E7A5A"
AMBAR = "B45309"
ROJO = "B91C1C"

thin = Side(style="thin", color="D9E2EC")
BORDE = Border(left=thin, right=thin, top=thin, bottom=thin)

EPICAS = {
    "EPICA0001": "Autenticación, registro y seguridad de cuentas",
    "EPICA0002": "Interacción del estudiante con el sistema",
    "EPICA0003": "Atención y seguimiento profesional (psicólogo)",
    "EPICA0004": "Gestión integral del sistema (administrador)",
    "EPICA0005": "Procesamiento de lenguaje natural (BETO zero-shot)",
    "EPICA0006": "Banco clínico, plantillas y evaluación de cuestionarios",
    "EPICA0007": "Modelo de aprendizaje automático (SVM)",
    "EPICA0008": "Despliegue, infraestructura y operación",
    "EPICA0009": "Acompañamiento del padre o tutor",
}

OBJETIVO_SPRINT = {
    1: "Cimientos del sistema: autenticación y consentimiento informado",
    2: "Onboarding del estudiante y gestión de usuarios",
    3: "Núcleo funcional: cuestionarios validados + BETO sobre frases incompletas",
    4: "Cierre del valor para el estudiante: recursos, SOS y satisfacción",
    5: "Panel del psicólogo: monitoreo, alertas y atención profesional",
    6: "Administración: auditoría, respaldos y observabilidad",
    7: "Proceso del alumno: línea de tiempo, citas y cierre de ciclos",
    8: "Reportes clínicos e institucionales y gestión de contenidos",
    9: "Sistema de cuestionarios: banco, plantillas, asignación y evaluación",
    10: "SVM, OAuth, rediseño de paneles y despliegue en Azure",
    11: "Panel de padres, firma digital y reportes descargables",
}


# ── Utilidades ──────────────────────────────────────────────────────────
def num_sprint(txt) -> int:
    m = re.search(r"(\d+)", str(txt or ""))
    return int(m.group(1)) if m else 99


def bloque_gherkin(pasos) -> str:
    return "\n".join(pasos)


def partir_pasos(pasos):
    """Separa los pasos en precondiciones (Dado), acciones (Cuando) y
    resultados esperados (Entonces). Los pasos 'Y' heredan el bloque anterior."""
    secc = {"Dado": [], "Cuando": [], "Entonces": []}
    actual = "Dado"
    for p in pasos:
        limpio = p.strip()
        if limpio.startswith("Dado"):
            actual = "Dado"
        elif limpio.startswith("Cuando"):
            actual = "Cuando"
        elif limpio.startswith("Entonces"):
            actual = "Entonces"
        secc[actual].append(limpio)
    return secc["Dado"], secc["Cuando"], secc["Entonces"]


NEG_CODIGOS = re.compile(r"\b(400|401|403|404|409|410|422|423|429|500)\b")
SEG_PATRON = re.compile(
    r"403|401|no autorizad|sin permiso|otro psicólogo|otra psicóloga|ajeno|no vinculad|"
    r"token|jwt|rol\b|privacidad|nunca ve|no puede ver|no expone|fuga|auditor",
    re.IGNORECASE)
NEG_PATRON = re.compile(
    r"inválid|invalid|incorrect|no se crea|no se emite|rechaz|error|falla|expirad|"
    r"duplicad|ya registrad|no existe|vací|sin |no cumple|bloquea|impide|no permite|"
    r"no se guarda|no se envía|conflicto",
    re.IGNORECASE)
BORDE_PATRON = re.compile(
    r"límite|limite|máximo|maximo|mínimo|minimo|exactamente|corte|umbral|"
    r"punto de corte|frontera|\b0\b|caso borde|vací|cero",
    re.IGNORECASE)


def tipo_caso(titulo, pasos) -> str:
    texto = titulo + " " + " ".join(pasos)
    if SEG_PATRON.search(texto) and (NEG_CODIGOS.search(texto) or "privacidad" in texto.lower()
                                     or "nunca ve" in texto.lower() or "no puede ver" in texto.lower()):
        return "Seguridad / Permisos"
    if NEG_CODIGOS.search(texto) or NEG_PATRON.search(titulo):
        return "Negativo"
    if BORDE_PATRON.search(titulo):
        return "Frontera / Límite"
    return "Positivo"


def tecnica(tipo) -> str:
    return {
        "Positivo": "Partición de equivalencia (clase válida)",
        "Negativo": "Partición de equivalencia (clase inválida)",
        "Frontera / Límite": "Análisis de valores límite",
        "Seguridad / Permisos": "Prueba de control de acceso basada en rol",
    }[tipo]


def prioridad_cp(prio_hu, idx) -> str:
    if idx == 1:
        return "Alta"
    if str(prio_hu or "").strip().lower() == "alta":
        return "Alta" if idx <= 2 else "Media"
    return "Media" if idx <= 2 else "Baja"


# ── Estilos ─────────────────────────────────────────────────────────────
def titulo_hoja(ws, texto, subtitulo, ancho_merge):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ancho_merge)
    c = ws.cell(1, 1, texto)
    c.font = Font(bold=True, size=14, color=BLANCO)
    c.fill = PatternFill("solid", fgColor=AZUL_TITULO)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ancho_merge)
    c = ws.cell(2, 2 - 1, subtitulo)
    c.font = Font(size=10, italic=True, color="44546A")
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 20


def cabecera(ws, fila, encabezados, anchos):
    for i, (h, w) in enumerate(zip(encabezados, anchos), 1):
        c = ws.cell(fila, i, h)
        c.font = Font(bold=True, size=10.5, color=BLANCO)
        c.fill = PatternFill("solid", fgColor=AZUL_HEADER)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDE
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[fila].height = 34
    ws.freeze_panes = ws.cell(fila + 1, 1)


def pintar_fila(ws, fila, valores, zebra=False, wrap_cols=()):
    for c, v in enumerate(valores, 1):
        cel = ws.cell(fila, c, v)
        cel.font = Font(size=10, color="222222")
        cel.border = BORDE
        cel.alignment = Alignment(
            wrap_text=True, vertical="top",
            horizontal="left" if c in wrap_cols else "left")
        if zebra:
            cel.fill = PatternFill("solid", fgColor=GRIS_SUAVE)
    return fila + 1


def color_estado(ws, fila, col, estado):
    cel = ws.cell(fila, col)
    color = {"Implementado": VERDE, "Parcial": AMBAR, "No implementado": ROJO}.get(estado, "222222")
    cel.font = Font(size=10, bold=True, color=color)
    cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def autofiltro(ws, fila_cab, ultima_fila, ultima_col):
    ws.auto_filter.ref = f"A{fila_cab}:{get_column_letter(ultima_col)}{ultima_fila}"


def portada(ws, titulo, pares, nota):
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 92
    ws.merge_cells("A1:B1")
    c = ws.cell(1, 1, titulo)
    c.font = Font(bold=True, size=16, color=BLANCO)
    c.fill = PatternFill("solid", fgColor=AZUL_TITULO)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 36

    r = 3
    for k, v in pares:
        if k == "":
            r += 1
            continue
        ck = ws.cell(r, 1, k)
        ck.font = Font(bold=True, size=10.5, color=BLANCO)
        ck.fill = PatternFill("solid", fgColor=AZUL_HEADER)
        ck.alignment = Alignment(vertical="center", indent=1)
        ck.border = BORDE
        cv = ws.cell(r, 2, v)
        cv.font = Font(size=10.5)
        cv.alignment = Alignment(wrap_text=True, vertical="center", indent=1)
        cv.border = BORDE
        ws.row_dimensions[r].height = max(20, 15 * (1 + str(v).count("\n")))
        r += 1

    r += 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
    c = ws.cell(r, 1, nota)
    c.font = Font(size=9.5, italic=True, color="44546A")
    c.alignment = Alignment(wrap_text=True, vertical="top", indent=1)
    ws.row_dimensions[r].height = 60


# ── Carga de datos ──────────────────────────────────────────────────────
def leer_backlog():
    wb = openpyxl.load_workbook(BACKLOG)
    ws = wb["Product Backlog"]
    filas = []
    for r in range(4, ws.max_row + 1):
        hu = ws.cell(r, 2).value
        if not hu or not str(hu).startswith("HU-"):
            continue
        filas.append({
            "id": str(hu).strip(),
            "rol": ws.cell(r, 3).value,
            "historia": ws.cell(r, 4).value,
            "epica": ws.cell(r, 5).value,
            "sp": ws.cell(r, 6).value,
            "prio": ws.cell(r, 7).value,
            "sprint": ws.cell(r, 8).value,
            "notas": ws.cell(r, 9).value,
        })
    filas.sort(key=lambda f: (num_sprint(f["sprint"]), int(re.search(r"\d+", f["id"]).group())))
    return filas


# ── Documento 1: Historias de Usuario ───────────────────────────────────
def generar_hu(filas):
    wb = openpyxl.Workbook()

    # Portada
    ws = wb.active
    ws.title = "Portada"
    total_sp = sum(int(f["sp"] or 0) for f in filas)
    sprints = sorted({num_sprint(f["sprint"]) for f in filas})
    impl = sum(1 for f in filas if ESTADO.get(f["id"]) == "Implementado")
    portada(ws, f"{CODIGO}_HU — Historias de Usuario", [
        ("Código del proyecto", CODIGO),
        ("Proyecto", PROYECTO),
        ("Entregable", "Historias de Usuario con criterios de aceptación en formato Gherkin"),
        ("Semana de entrega", "Semana 3 — según cronograma del curso"),
        ("Documento relacionado", f"{CODIGO}_CP — Casos de Prueba (un caso por escenario Gherkin)"),
        ("", ""),
        ("Total de historias de usuario", str(len(filas))),
        ("Total de épicas", str(len(EPICAS))),
        ("Total de story points", str(total_sp)),
        ("Sprints planificados", f"{len(sprints)} (Sprint {min(sprints)} a Sprint {max(sprints)})"),
        ("Escenarios de aceptación (Gherkin)", str(sum(len(CRITERIOS[f['id']]) for f in filas))),
    ] + ([("Estado de implementación", f"{impl} implementadas · "
           f"{sum(1 for f in filas if ESTADO.get(f['id']) == 'Parcial')} parciales · "
           f"{sum(1 for f in filas if ESTADO.get(f['id']) == 'No implementado')} no implementadas")]
         if CON_ESTADO else []) + [
        ("", ""),
        ("Formato de la historia", "Como <rol> quiero <funcionalidad> para <beneficio>"),
        ("Formato del criterio", "Escenario: <título>\nDado <contexto>\nCuando <acción>\nEntonces <resultado esperado>"),
    ],
        "Nota metodológica: cada historia de usuario se expresa en el formato «Como / quiero / para» y se acompaña de uno o "
        "más criterios de aceptación redactados en Gherkin (Dado / Cuando / Entonces), de modo que todo criterio sea "
        "verificable de forma objetiva. Cada escenario de esta planilla tiene su caso de prueba correspondiente en el "
        f"documento {CODIGO}_CP, enlazado por el identificador de la historia.")

    # Hoja de historias
    ws = wb.create_sheet("Historias de Usuario")
    enc = ["#", "ID HU", "Épica", "Sprint", "Rol / Actor", "Historia de Usuario",
           "Prioridad", "SP", "Criterios de aceptación (Gherkin)"]
    anchos = [5, 9, 12, 10, 14, 62, 10, 5, 95]
    if CON_ESTADO:
        enc.append("Estado")
        anchos.append(15)
    titulo_hoja(ws, f"{CODIGO}_HU — Historias de Usuario",
                "Formato: Como <rol> quiero <funcionalidad> para <beneficio>. "
                "Criterios de aceptación en Gherkin (Dado / Cuando / Entonces).", len(enc))
    cabecera(ws, 4, enc, anchos)

    r = 5
    for i, f in enumerate(filas, 1):
        escenarios = CRITERIOS[f["id"]]
        partes = []
        for j, e in enumerate(escenarios, 1):
            partes.append(f"Escenario {j}: {e['titulo']}")
            partes.extend(f"  {p}" for p in e["pasos"])
            if j < len(escenarios):
                partes.append("")
        estado = ESTADO.get(f["id"], "Sin verificar")
        valores = [i, f["id"], f["epica"], f["sprint"], f["rol"], f["historia"],
                   f["prio"], f["sp"], "\n".join(partes)]
        if CON_ESTADO:
            valores.append(estado)
        r = pintar_fila(ws, r, valores, zebra=(i % 2 == 0))
        if CON_ESTADO:
            color_estado(ws, r - 1, 10, estado)
        for col in (1, 2, 3, 4, 7, 8):
            ws.cell(r - 1, col).alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
    autofiltro(ws, 4, r - 1, len(enc))

    # Hoja de épicas
    ws = wb.create_sheet("Épicas")
    enc = ["ID Épica", "Objetivo de la épica", "N.º de HU", "Story points", "HU asociadas"]
    titulo_hoja(ws, f"{CODIGO}_HU — Épicas del proyecto",
                "Agrupación funcional de las historias de usuario.", len(enc))
    cabecera(ws, 4, enc, [12, 52, 11, 13, 78])
    r = 5
    for i, (eid, obj) in enumerate(sorted(EPICAS.items()), 1):
        hs = [f for f in filas if f["epica"] == eid]
        r = pintar_fila(ws, r, [eid, obj, len(hs), sum(int(h["sp"] or 0) for h in hs),
                                ", ".join(h["id"] for h in hs)], zebra=(i % 2 == 0))
        for col in (1, 3, 4):
            ws.cell(r - 1, col).alignment = Alignment(horizontal="center", vertical="center")

    # Hoja de sprints
    ws = wb.create_sheet("Sprints")
    enc = ["Sprint", "Objetivo del sprint", "N.º de HU", "Story points", "HU asignadas"]
    titulo_hoja(ws, f"{CODIGO}_HU — Distribución por sprint",
                "Planificación incremental de las historias de usuario.", len(enc))
    cabecera(ws, 4, enc, [10, 58, 11, 13, 72])
    r = 5
    for i, s in enumerate(sorted({num_sprint(f["sprint"]) for f in filas}), 1):
        hs = [f for f in filas if num_sprint(f["sprint"]) == s]
        r = pintar_fila(ws, r, [f"Sprint {s}", OBJETIVO_SPRINT.get(s, ""), len(hs),
                                sum(int(h["sp"] or 0) for h in hs),
                                ", ".join(h["id"] for h in hs)], zebra=(i % 2 == 0))
        for col in (1, 3, 4):
            ws.cell(r - 1, col).alignment = Alignment(horizontal="center", vertical="center")

    destino = Path(f"{CODIGO}_HU.xlsx")
    wb.save(destino)
    return destino


# ── Documento 2: Casos de Prueba ────────────────────────────────────────
def construir_casos(filas):
    casos = []
    n = 0
    for f in filas:
        for idx, esc in enumerate(CRITERIOS[f["id"]], 1):
            n += 1
            dado, cuando, entonces = partir_pasos(esc["pasos"])
            tipo = tipo_caso(esc["titulo"], esc["pasos"])
            casos.append({
                "cp": f"CP-{n:03d}",
                "hu": f["id"],
                "sprint": f["sprint"],
                "epica": f["epica"],
                "rol": f["rol"],
                "titulo": esc["titulo"],
                "tipo": tipo,
                "tecnica": tecnica(tipo),
                "prio": prioridad_cp(f["prio"], idx),
                "precond": "\n".join(dado) or "El sistema se encuentra desplegado y operativo.",
                "pasos": "\n".join(cuando) or "(acción implícita en el contexto)",
                "esperado": "\n".join(entonces),
                "gherkin": f"Escenario: {esc['titulo']}\n" + "\n".join(f"  {p}" for p in esc["pasos"]),
                "estado_hu": ESTADO.get(f["id"], "Sin verificar"),
            })
    return casos


def generar_cp(filas, casos):
    wb = openpyxl.Workbook()

    # Portada
    ws = wb.active
    ws.title = "Portada"
    por_tipo = {}
    for c in casos:
        por_tipo[c["tipo"]] = por_tipo.get(c["tipo"], 0) + 1
    por_prio = {}
    for c in casos:
        por_prio[c["prio"]] = por_prio.get(c["prio"], 0) + 1
    portada(ws, f"{CODIGO}_CP — Casos de Prueba", [
        ("Código del proyecto", CODIGO),
        ("Proyecto", PROYECTO),
        ("Entregable", "Casos de prueba funcionales en formato Gherkin"),
        ("Semana de entrega", "Semana 3 — según cronograma del curso"),
        ("Documento relacionado", f"{CODIGO}_HU — Historias de Usuario"),
        ("", ""),
        ("Total de casos de prueba", str(len(casos))),
        ("Historias de usuario cubiertas", f"{len({c['hu'] for c in casos})} de {len(filas)} (100 % de cobertura)"),
        ("Promedio de casos por historia", f"{len(casos) / len(filas):.1f}"),
        ("Distribución por tipo", "\n".join(f"{k}: {v}" for k, v in sorted(por_tipo.items(), key=lambda x: -x[1]))),
        ("Distribución por prioridad", "  ·  ".join(f"{k}: {por_prio.get(k, 0)}" for k in ("Alta", "Media", "Baja"))),
        ("", ""),
        ("Nivel de prueba", "Pruebas funcionales de sistema (caja negra), sobre la API REST y la interfaz web."),
        ("Técnicas aplicadas", "Partición de equivalencia · Análisis de valores límite · Pruebas de control de acceso por rol"),
        ("Criterio de aprobación", "Un caso se marca «Aprobado» cuando el resultado obtenido coincide íntegramente "
                                   "con el resultado esperado; cualquier desviación se registra como defecto."),
    ],
        "Cómo se ejecuta: por cada fila de la hoja «Casos de Prueba», reproducir las precondiciones, ejecutar los pasos "
        "y comparar contra el resultado esperado. Registrar el desenlace en las columnas «Estado de ejecución», "
        "«Resultado obtenido», «Fecha» y «Defecto asociado», que se entregan en blanco de forma deliberada. "
        "La hoja «Trazabilidad HU–CP» permite verificar que ninguna historia de usuario quedó sin cobertura de prueba.")

    # Hoja de casos
    ws = wb.create_sheet("Casos de Prueba")
    enc = ["ID CP", "HU", "Sprint", "Épica", "Actor", "Título del caso de prueba",
           "Tipo", "Técnica de diseño", "Prioridad", "Precondiciones (Dado)",
           "Pasos de ejecución (Cuando)", "Resultado esperado (Entonces)",
           "Escenario Gherkin completo", "Estado de ejecución", "Resultado obtenido",
           "Fecha", "Defecto asociado"]
    anchos = [9, 9, 10, 12, 14, 48, 17, 30, 10, 46, 44, 52, 82, 16, 30, 12, 16]
    titulo_hoja(ws, f"{CODIGO}_CP — Casos de Prueba",
                "Un caso de prueba por cada escenario de aceptación. "
                "Las cuatro últimas columnas se completan durante la ejecución.", len(enc))
    cabecera(ws, 4, enc, anchos)

    r = 5
    for i, c in enumerate(casos, 1):
        r = pintar_fila(ws, r, [
            c["cp"], c["hu"], c["sprint"], c["epica"], c["rol"], c["titulo"],
            c["tipo"], c["tecnica"], c["prio"], c["precond"], c["pasos"],
            c["esperado"], c["gherkin"], "No ejecutado", "", "", "",
        ], zebra=(i % 2 == 0))
        for col in (1, 2, 3, 4, 7, 9, 14, 16):
            ws.cell(r - 1, col).alignment = Alignment(horizontal="center", vertical="top", wrap_text=True)
        ws.cell(r - 1, 1).font = Font(size=10, bold=True, color=AZUL_TITULO)
        pr = ws.cell(r - 1, 9)
        pr.font = Font(size=10, bold=True,
                       color={"Alta": ROJO, "Media": AMBAR, "Baja": "44546A"}[c["prio"]])
        ws.cell(r - 1, 14).font = Font(size=10, italic=True, color="6B7280")
    autofiltro(ws, 4, r - 1, len(enc))

    # Trazabilidad
    ws = wb.create_sheet("Trazabilidad HU–CP")
    enc = ["ID HU", "Sprint", "Épica", "Historia de Usuario", "N.º de CP",
           "Casos de prueba asociados", "Cobertura"]
    if CON_ESTADO:
        enc.append("Estado de la HU")
    titulo_hoja(ws, f"{CODIGO}_CP — Matriz de trazabilidad Historia ↔ Caso de prueba",
                "Verifica que toda historia de usuario tenga al menos un caso de prueba que la cubra.", len(enc))
    cabecera(ws, 4, enc, [9, 10, 12, 66, 9, 40, 12] + ([16] if CON_ESTADO else []))
    r = 5
    for i, f in enumerate(filas, 1):
        cps = [c["cp"] for c in casos if c["hu"] == f["id"]]
        estado = ESTADO.get(f["id"], "Sin verificar")
        valores = [f["id"], f["sprint"], f["epica"], f["historia"],
                   len(cps), ", ".join(cps), "Cubierta" if cps else "SIN COBERTURA"]
        if CON_ESTADO:
            valores.append(estado)
        r = pintar_fila(ws, r, valores, zebra=(i % 2 == 0))
        for col in (1, 2, 3, 5, 7, 8):
            ws.cell(r - 1, col).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.cell(r - 1, 7).font = Font(size=10, bold=True, color=VERDE if cps else ROJO)
        if CON_ESTADO:
            color_estado(ws, r - 1, 8, estado)
    autofiltro(ws, 4, r - 1, len(enc))

    # Resumen de ejecución
    ws = wb.create_sheet("Resumen de ejecución")
    enc = ["Indicador", "Valor", "Observación"]
    titulo_hoja(ws, f"{CODIGO}_CP — Resumen de ejecución",
                "Tablero de control de la campaña de pruebas. Se actualiza al cerrar la ejecución.", len(enc))
    cabecera(ws, 4, enc, [44, 16, 74])
    datos = [
        ("Casos de prueba diseñados", len(casos), "Un caso por escenario de aceptación."),
        ("Casos ejecutados", "", "Completar al cierre de la campaña de pruebas."),
        ("Casos aprobados", "", "Resultado obtenido = resultado esperado."),
        ("Casos fallidos", "", "Generan un defecto en la columna «Defecto asociado»."),
        ("Casos bloqueados", "", "No ejecutables por dependencia o entorno."),
        ("Porcentaje de aprobación", "", "Aprobados / Ejecutados."),
        ("Historias de usuario cubiertas", f"{len({c['hu'] for c in casos})} / {len(filas)}",
         "Cobertura de trazabilidad: 100 %."),
    ]
    for k, v in por_tipo.items():
        datos.append((f"Casos de tipo «{k}»", v, tecnica(k)))
    for k in ("Alta", "Media", "Baja"):
        datos.append((f"Casos de prioridad {k}", por_prio.get(k, 0),
                      "Se ejecutan primero." if k == "Alta" else ""))
    r = 5
    for i, (k, v, o) in enumerate(datos, 1):
        r = pintar_fila(ws, r, [k, v, o], zebra=(i % 2 == 0))
        ws.cell(r - 1, 1).font = Font(size=10, bold=True, color="222222")
        ws.cell(r - 1, 2).alignment = Alignment(horizontal="center", vertical="center")

    destino = Path(f"{CODIGO}_CP.xlsx")
    wb.save(destino)
    return destino


def main():
    filas = leer_backlog()
    casos = construir_casos(filas)
    d1 = generar_hu(filas)
    d2 = generar_cp(filas, casos)
    modo = "auditoría interna (con estado)" if CON_ESTADO else "entrega al curso (sin estado)"
    print(f"Modo: {modo}")
    print(f"OK  {d1}  — {len(filas)} HU, {sum(len(CRITERIOS[f['id']]) for f in filas)} escenarios")
    print(f"OK  {d2}  — {len(casos)} casos de prueba, {len({c['hu'] for c in casos})} HU cubiertas")


if __name__ == "__main__":
    main()
