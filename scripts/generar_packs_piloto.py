"""
Genera los PDFs para la sesión piloto en el colegio, replicando el diseño
de StudentAnswerView.vue (verde mint #45988C, número en cajita, círculos
para marcar, separador con línea y título centrado por bloque).

Salida:
  - docs/piloto_colegio/pack_A_phqa_gad7.pdf  (16 ítems, ~8 min)
  - docs/piloto_colegio/pack_B_dass21.pdf     (21 ítems, ~9 min)
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    Flowable,
)

# ── Paleta extraída de StudentAnswerView.vue ────────────────────────────
MINT       = colors.HexColor("#45988C")  # primary
MINT_DARK  = colors.HexColor("#0E8D7E")  # eyebrow + título de bloque
MINT_LINE  = colors.HexColor("#C5E1DC")  # línea del separador
MINT_SOFT  = colors.HexColor("#E3F3EF")  # número en cajita cuando "done"
INK        = colors.HexColor("#0A0A0A")
TXT        = colors.HexColor("#1F2937")
TXT_2      = colors.HexColor("#344054")
GRAY       = colors.HexColor("#667085")
GRAY_2     = colors.HexColor("#98A2B3")
GRAY_BG    = colors.HexColor("#F4F5F6")  # cajita del número (default)
GRAY_LINE  = colors.HexColor("#EEF1F2")  # separador inferior
WHITE      = colors.white

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "piloto_colegio"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Newsreader y Work Sans no están en reportlab por defecto.
# Caemos en Helvetica (sans) y Times (serif) que ya están embebidas.
SERIF_FONT = "Times-Roman"
SERIF_BOLD = "Times-Bold"
SANS_FONT  = "Helvetica"
SANS_BOLD  = "Helvetica-Bold"

# ── Contenido clínico (texto exacto del sistema) ─────────────────────────
PHQA = [
    "Poco interés o placer en hacer cosas.",
    "Sentirte triste, decaído/a o sin esperanza.",
    "Problemas para dormir, dormir demasiado, o despertarte mucho durante la noche.",
    "Sentirte cansado/a o con poca energía.",
    "Falta de apetito o comer en exceso.",
    "Sentirte mal contigo mismo/a, sentir que eres un/a fracasado/a, o que has fallado a tu familia.",
    "Dificultad para concentrarte en cosas como tareas escolares, leer o ver televisión.",
    "Moverte o hablar tan lento que otras personas lo notan, o estar tan inquieto/a que te mueves mucho más de lo habitual.",
    "Pensar que estarías mejor muerto/a o tener pensamientos de hacerte daño de alguna manera.",
]

GAD7 = [
    "Sentirte nervioso/a, ansioso/a o con los nervios de punta.",
    "No poder dejar de preocuparte o no poder controlar tus preocupaciones.",
    "Preocuparte demasiado por diferentes cosas.",
    "Tener dificultad para relajarte.",
    "Estar tan inquieto/a que te resulta difícil quedarte quieto/a.",
    "Irritarte o enojarte con facilidad.",
    "Sentir miedo como si algo terrible fuera a pasar.",
]

DASS21 = [
    "Me costó mucho relajarme.",
    "Me di cuenta que tenía la boca seca.",
    "No podía sentir ningún sentimiento positivo.",
    "Se me hizo difícil respirar.",
    "Se me hizo difícil tomar la iniciativa para hacer cosas.",
    "Reaccioné exageradamente en ciertas situaciones.",
    "Sentí que mis manos temblaban.",
    "Sentí que tenía muchos nervios.",
    "Estaba preocupado por situaciones en las que podría tener pánico.",
    "Sentí que no tenía nada por que esperar.",
    "Noté que me agitaba.",
    "Se me hizo difícil relajarme.",
    "Me sentí triste y deprimido.",
    "No toleré nada que no me permitiera continuar con lo que hacía.",
    "Sentí que estaba al punto del pánico.",
    "No me pude entusiasmar por nada.",
    "Sentí que valía muy poco como persona.",
    "Sentí que estaba muy irritable.",
    "Sentí los latidos de mi corazón sin haber hecho esfuerzo físico.",
    "Tuve miedo sin razón.",
    "Sentí que la vida no tenía ningún sentido.",
]

# Etiquetas exactas del sistema (OPCIONES["0-3"] de StudentAnswerView.vue)
LABELS_03 = ["Nunca", "Algunos días", "Más de la mitad", "Casi todos los días"]
# Para DASS-21 — el manual original Lovibond. El sistema lo mostraría con
# el mismo "0-3" genérico, pero etiquetas DASS son más fieles al instrumento.
LABELS_DASS = ["No me aplicó", "Un poco", "Bastante", "Mucho"]

BLOQUE_NOMBRES = {
    "PHQ-A":   "Cómo te has sentido",
    "GAD-7":   "Preocupación y tensión",
    "DASS-21": "Cómo te ha ido esta semana",
    "FRASES":  "Completa las frases",
}
BLOQUE_INSTR = {
    "PHQ-A":   "Durante las últimas dos semanas, ¿con qué frecuencia te ha molestado lo siguiente?",
    "GAD-7":   "Durante las últimas dos semanas, ¿con qué frecuencia te has sentido así?",
    "DASS-21": "Por favor lee cada frase y marca cuánto te aplicó esta semana.",
    "FRASES":  "Completa cada frase con lo primero que se te venga a la mente. No hay respuestas correctas.",
}

# 20 frases SSCT — 2-3 por cada una de las 8 áreas del banco.
FRASES_SSCT = [
    "En mi casa yo…",
    "Mis hermanos…",
    "Yo soy…",
    "Lo que más me gusta de mí es…",
    "Cuando me miro al espejo…",
    "El colegio para mí…",
    "Estudiar es…",
    "Mis amigos…",
    "Cuando estoy con otros chicos/as…",
    "Cuando me enojo…",
    "Cuando estoy triste yo…",
    "Cuando algo me preocupa…",
    "Lo que más me da miedo es…",
    "Cuando estoy solo/a…",
    "Dentro de 5 años…",
    "Mi mayor sueño es…",
    "El futuro me…",
    "Si pudiera cambiar algo de mí…",
    "Cuando pienso en quién soy…",
    "Lo que define quién soy es…",
]


# ── Flowables personalizados ────────────────────────────────────────────
class Separador(Flowable):
    """Línea-título-línea como `.sami-block__sep` del CSS."""

    def __init__(self, titulo, width, line_color=MINT_LINE, text_color=MINT_DARK):
        super().__init__()
        self.titulo = titulo
        self.width = width
        self.line_color = line_color
        self.text_color = text_color
        self.height = 18

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFont(SERIF_BOLD, 13)
        text_w = c.stringWidth(self.titulo, SERIF_BOLD, 13)
        pad = 10
        line_y = self.height / 2 - 0.5
        # línea izq
        c.setStrokeColor(self.line_color)
        c.setLineWidth(0.8)
        right_line_start = self.width / 2 + text_w / 2 + pad
        left_line_end = self.width / 2 - text_w / 2 - pad
        c.line(0, line_y, left_line_end, line_y)
        c.line(right_line_start, line_y, self.width, line_y)
        # título centrado
        c.setFillColor(self.text_color)
        c.drawCentredString(self.width / 2, 2, self.titulo)


class Circulo(Flowable):
    """Círculo vacío para marcar (como `.sami-radio` del CSS)."""

    def __init__(self, diametro=10):
        super().__init__()
        self.d = diametro
        self.width = diametro
        self.height = diametro

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setStrokeColor(colors.HexColor("#D1D5DB"))
        c.setLineWidth(1.1)
        c.setFillColor(WHITE)
        r = self.d / 2
        c.circle(r, r, r, stroke=1, fill=1)


class Eyebrow(Flowable):
    """Eyebrow estilo `.sami-eyebrow` (verde, tracking ancho)."""

    def __init__(self, texto, width):
        super().__init__()
        self.texto = texto.upper()
        self.width = width
        self.height = 13

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFont(SANS_BOLD, 8)
        c.setFillColor(MINT_DARK)
        # Tracking ancho: separamos cada letra con un espacio
        c.drawString(0, 2, "  ".join(self.texto))


# ── Composición ─────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN_L = 1.4 * cm
MARGIN_R = 1.4 * cm
MARGIN_T = 1.2 * cm
MARGIN_B = 1.2 * cm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


def encabezado_anonimo():
    """Recuadro de datos anónimos (Código + Edad + Género + Fecha)."""
    style_lbl = ParagraphStyle(
        "lbl", fontName=SANS_BOLD, fontSize=8, textColor=GRAY,
        leading=10, spaceAfter=2,
    )
    style_val = ParagraphStyle(
        "val", fontName=SANS_FONT, fontSize=11, textColor=TXT, leading=14,
    )

    def cell(label, valor):
        return [Paragraph(label.upper(), style_lbl), Paragraph(valor, style_val)]

    fila = [
        cell("Código de participante", "________"),
        cell("Edad", "_____"),
        cell("Género", "M  ·  F  ·  Otro"),
        cell("Fecha", "___ / ___ / 2026"),
    ]
    # Cada celda es una columna con dos paragraph apilados — para eso 1 fila x 4 cols.
    data = [[fila[0], fila[1], fila[2], fila[3]]]
    t = Table(data, colWidths=[CONTENT_W * 0.34, CONTENT_W * 0.14,
                               CONTENT_W * 0.26, CONTENT_W * 0.26])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, MINT_LINE),
        ("ROUNDEDCORNERS", [10, 10, 10, 10]),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
    ]))
    return t


def header_titulo(titulo, descripcion):
    """Eyebrow + título + descripción (como sami-head del Vue)."""
    s_titulo = ParagraphStyle(
        "ttl", fontName=SERIF_BOLD, fontSize=22, textColor=INK,
        leading=24, spaceBefore=6, spaceAfter=6,
    )
    s_desc = ParagraphStyle(
        "desc", fontName=SANS_FONT, fontSize=10.5, textColor=GRAY,
        leading=15, spaceAfter=6,
    )
    return [
        Eyebrow("Sami · Bienestar", CONTENT_W),
        Spacer(1, 4),
        Paragraph(titulo, s_titulo),
        Paragraph(descripcion, s_desc),
    ]


def instruccion_bloque(texto):
    s = ParagraphStyle(
        "instr", fontName=SANS_FONT, fontSize=10, textColor=GRAY,
        leading=14, alignment=1, spaceBefore=6, spaceAfter=14,
    )
    return Paragraph(texto, s)


def tabla_likert(items, labels):
    """Tabla Likert al estilo `.sami-matriz` (número en cajita + texto + círculos)."""
    # Encabezado: vacío + labels
    header_style = ParagraphStyle(
        "h", fontName=SANS_FONT, fontSize=8, textColor=GRAY,
        leading=10, alignment=1,
    )
    text_style = ParagraphStyle(
        "tx", fontName=SANS_FONT, fontSize=10, textColor=TXT_2, leading=13,
    )
    num_style = ParagraphStyle(
        "num", fontName=SANS_BOLD, fontSize=9, textColor=GRAY,
        leading=11, alignment=1,
    )

    n_opts = len(labels)
    # Columnas: número (0.8cm) + texto (resto) + n columnas de opciones
    col_opt = 1.65 * cm
    col_num = 0.8 * cm
    col_text = CONTENT_W - col_num - col_opt * n_opts

    # Fila header
    header_row = ["", ""] + [Paragraph(lbl, header_style) for lbl in labels]
    rows = [header_row]

    for i, texto in enumerate(items, start=1):
        rows.append(
            [
                Paragraph(str(i), num_style),
                Paragraph(texto, text_style),
            ] + [Circulo(diametro=11) for _ in range(n_opts)]
        )

    col_widths = [col_num, col_text] + [col_opt] * n_opts
    t = Table(rows, colWidths=col_widths, repeatRows=1)

    style = [
        # Header
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, GRAY_LINE),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("TOPPADDING", (0, 0), (-1, 0), 0),
        ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
        # Cuerpo
        ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
    ]
    # Separadores entre filas
    for r in range(1, len(rows)):
        style.append(("LINEBELOW", (0, r), (-1, r), 0.4, GRAY_LINE))
        # cajita del número con fondo gris claro
        style.append(("BACKGROUND", (0, r), (0, r), GRAY_BG))
    t.setStyle(TableStyle(style))
    return t


def tabla_frases(items):
    """Layout `.sami-frase`: enunciado arriba + línea para completar abajo."""
    stem_style = ParagraphStyle(
        "stem", fontName=SANS_FONT, fontSize=10.5, textColor=TXT,
        leading=14, spaceAfter=4,
    )
    num_style = ParagraphStyle(
        "num", fontName=SANS_BOLD, fontSize=9, textColor=GRAY,
        leading=11, alignment=1,
    )

    col_num = 0.8 * cm
    col_text = CONTENT_W - col_num

    rows = []
    for i, frase in enumerate(items, start=1):
        # Por frase: dos sub-filas — enunciado + línea para escribir
        rows.append([
            Paragraph(str(i), num_style),
            Paragraph(frase, stem_style),
        ])

    t = Table(rows, colWidths=[col_num, col_text])

    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        # Mucho espacio inferior — ahí escribe el alumno
        ("BOTTOMPADDING", (0, 0), (-1, -1), 34),
    ]
    for r in range(len(rows)):
        # línea subrayada bajo cada enunciado (área para escribir)
        style.append(("LINEBELOW", (1, r), (1, r), 0.8, colors.HexColor("#E5E7EB")))
        # cajita del número
        style.append(("BACKGROUND", (0, r), (0, r), GRAY_BG))
    t.setStyle(TableStyle(style))
    return t


def footer_cierre():
    """Pie de página discreto. Sin botón — es una hoja de papel."""
    s = ParagraphStyle(
        "ft", fontName=SANS_FONT, fontSize=10, textColor=GRAY_2,
        leading=14, alignment=1, spaceBefore=22, spaceAfter=4,
    )
    sep = Table([[""]], colWidths=[CONTENT_W], rowHeights=[1])
    sep.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.6, GRAY_LINE),
    ]))
    msg = Paragraph(
        "Gracias por participar. Cuando termines, levanta la mano para que recojan tu hoja.",
        s,
    )
    return [Spacer(1, 18), sep, msg]


def bloque(codigo, items, labels):
    elems = []
    elems.append(Spacer(1, 14))
    elems.append(Separador(BLOQUE_NOMBRES[codigo], CONTENT_W))
    elems.append(instruccion_bloque(BLOQUE_INSTR[codigo]))
    elems.append(tabla_likert(items, labels))
    return elems


def bloque_frases(items):
    elems = []
    elems.append(Spacer(1, 14))
    elems.append(Separador(BLOQUE_NOMBRES["FRASES"], CONTENT_W))
    elems.append(instruccion_bloque(BLOQUE_INSTR["FRASES"]))
    elems.append(tabla_frases(items))
    return elems


# ── Construcción de los packs ───────────────────────────────────────────
def build_pdf(path, titulo, descripcion, bloques):
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        title=titulo,
    )
    story = []
    story.extend(header_titulo(titulo, descripcion))
    for b in bloques:
        story.extend(b)
    story.extend(footer_cierre())
    doc.build(story)
    print(f"OK -> {path}")


def main():
    build_pdf(
        OUT_DIR / "pack_A_phqa_gad7.pdf",
        titulo="Cuestionario de bienestar",
        descripcion=(
            "Lee con calma y elige lo que más se acerca a cómo te has sentido. "
            "No hay respuestas correctas o incorrectas. Tus respuestas son anónimas."
        ),
        bloques=[
            bloque("PHQ-A", PHQA, LABELS_03),
            bloque("GAD-7", GAD7, LABELS_03),
        ],
    )
    build_pdf(
        OUT_DIR / "pack_B_dass21.pdf",
        titulo="Cuestionario de bienestar",
        descripcion=(
            "Lee con calma y marca cuánto te aplicó cada frase esta semana. "
            "No hay respuestas correctas o incorrectas. Tus respuestas son anónimas."
        ),
        bloques=[
            bloque("DASS-21", DASS21, LABELS_DASS),
        ],
    )
    build_pdf(
        OUT_DIR / "pack_C_frases.pdf",
        titulo="Cuestionario de bienestar",
        descripcion=(
            "Completa cada frase con lo primero que se te venga a la mente. "
            "No hay respuestas correctas o incorrectas. Tus respuestas son anónimas."
        ),
        bloques=[
            bloque_frases(FRASES_SSCT),
        ],
    )


if __name__ == "__main__":
    main()
