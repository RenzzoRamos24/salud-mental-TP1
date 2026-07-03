"""
Genera el diagrama ER de la base de datos como SVG/HTML standalone.

Salida:
    docs/db_erd.svg   — diagrama vectorial listo para insertar en la tesis
    docs/db_erd.html  — versión HTML para abrir en el navegador

Uso:
    venv/bin/python scripts/generar_erd.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import Base
import app.models  # noqa: F401 — registra todos los modelos

OUT_DIR = ROOT / "docs"
OUT_DIR.mkdir(exist_ok=True)

# ── Agrupación por dominio (color, tablas) ─────────────────────────────
DOMAINS = [
    ("Auth & Seguridad", "#fde2e4", "#c64545", [
        "users", "consents", "password_reset_tokens", "access_logs",
    ]),
    ("Banco Clínico", "#e1f3ef", "#0e8d7e", [
        "bank_instrumento", "bank_item", "bank_frase_incompleta",
        "bloque_custom", "bloque_custom_item",
    ]),
    ("Plantillas & Aplicaciones", "#fef3e2", "#d98a1f", [
        "plantilla_cuestionario", "plantilla_bloque",
        "aplicacion_cuestionario", "respuesta_aplicacion",
    ]),
    ("Atención Profesional", "#eaf0fb", "#3a78b3", [
        "citas", "clinical_notes",
    ]),
    ("Servicios al Alumno", "#efeafa", "#7a5cc4", [
        "sos_events", "educational_content", "satisfaction_surveys",
    ]),
    ("Sistema", "#f4f5f6", "#5a6a70", [
        "configuraciones",
    ]),
]

# ── Layout: grilla de 3 columnas × 8 filas ─────────────────────────────
TABLE_W = 280
COL_H = 18
HEAD_H = 32
GAP_X = 60
GAP_Y = 40
MARGIN = 40

# Posición de cada tabla
positions: dict[str, tuple[int, int]] = {}
domain_of: dict[str, tuple[str, str, str]] = {}

# Mejoramos el layout poniendo cada dominio en su propia fila/columna
LAYOUT = [
    # (col, row, table_name)
    (0, 0, "users"),
    (1, 0, "consents"),
    (2, 0, "password_reset_tokens"),
    (0, 1, "access_logs"),

    (0, 2, "bank_instrumento"),
    (1, 2, "bank_item"),
    (2, 2, "bank_frase_incompleta"),
    (0, 3, "bloque_custom"),
    (1, 3, "bloque_custom_item"),

    (2, 3, "plantilla_cuestionario"),
    (0, 4, "plantilla_bloque"),
    (1, 4, "aplicacion_cuestionario"),
    (2, 4, "respuesta_aplicacion"),

    (0, 5, "citas"),
    (1, 5, "clinical_notes"),

    (0, 6, "sos_events"),
    (1, 6, "educational_content"),
    (2, 6, "satisfaction_surveys"),

    (2, 5, "configuraciones"),
]

# Asignar dominios
for nombre, bg, border, tablas in DOMAINS:
    for t in tablas:
        domain_of[t] = (nombre, bg, border)

# Calcular posiciones según LAYOUT y altura real
heights: dict[str, int] = {}
for tname in Base.metadata.tables:
    n_cols = len(Base.metadata.tables[tname].columns)
    heights[tname] = HEAD_H + n_cols * COL_H + 8

# Recorrer LAYOUT por filas para colocar tablas con alturas variables
row_heights = [0] * 10
for col, row, tname in LAYOUT:
    row_heights[row] = max(row_heights[row], heights.get(tname, 0))

row_y_start = [MARGIN]
for h in row_heights[:-1]:
    row_y_start.append(row_y_start[-1] + h + GAP_Y)

for col, row, tname in LAYOUT:
    x = MARGIN + col * (TABLE_W + GAP_X)
    y = row_y_start[row]
    positions[tname] = (x, y)

CANVAS_W = 3 * TABLE_W + 2 * GAP_X + 2 * MARGIN
CANVAS_H = row_y_start[-1] + row_heights[-1] + MARGIN + 100

# ── Construir SVG ──────────────────────────────────────────────────────
def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

svg = []
svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
    f'font-family="Inter, Arial, sans-serif" font-size="11">'
)
svg.append("""
<defs>
  <marker id="fk" viewBox="0 0 12 12" refX="11" refY="6"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M 0 0 L 12 6 L 0 12 Z" fill="#5a6a70"/>
  </marker>
  <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.08"/>
  </filter>
</defs>
""")

# Fondo
svg.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#f5f7f8"/>')

# Título
svg.append(
    f'<text x="{MARGIN}" y="28" font-size="20" font-weight="700" fill="#243239">'
    'Diagrama Entidad–Relación · Sami</text>'
)
svg.append(
    f'<text x="{MARGIN}" y="46" font-size="11" fill="#8b999e">'
    'PostgreSQL 16 · 19 tablas · 22 claves foráneas · 6 dominios funcionales</text>'
)

# Ajustar todo el contenido hacia abajo para hacer lugar al título
SHIFT = 30
for k, (x, y) in positions.items():
    positions[k] = (x, y + SHIFT)
CANVAS_H += SHIFT

# Tablas
for tname, (x, y) in positions.items():
    t = Base.metadata.tables[tname]
    dom = domain_of.get(tname, ("?", "#fff", "#888"))
    bg, border = dom[1], dom[2]

    h = HEAD_H + len(t.columns) * COL_H + 8

    # Caja
    svg.append(
        f'<g filter="url(#shadow)">'
        f'<rect x="{x}" y="{y}" width="{TABLE_W}" height="{h}" rx="8" ry="8" '
        f'fill="#ffffff" stroke="{border}" stroke-width="1.5"/>'
        f'<rect x="{x}" y="{y}" width="{TABLE_W}" height="{HEAD_H}" rx="8" ry="8" '
        f'fill="{bg}" stroke="none"/>'
        f'<rect x="{x}" y="{y + 16}" width="{TABLE_W}" height="{HEAD_H - 16}" '
        f'fill="{bg}" stroke="none"/>'
        f'</g>'
    )
    svg.append(
        f'<text x="{x + 14}" y="{y + 21}" font-size="13" font-weight="700" '
        f'fill="{border}">{tname}</text>'
    )

    cy = y + HEAD_H + 14
    for col in t.columns:
        prefix = ""
        suffix = ""
        weight = "400"
        color = "#33424a"
        if col.primary_key:
            prefix = "🔑 "
            weight = "700"
            color = "#0e8d7e"
        elif col.foreign_keys:
            prefix = "🔗 "
            color = "#3a78b3"
        if not col.nullable and not col.primary_key:
            suffix = " ●"

        tipo = str(col.type)
        # Acortar tipos largos
        for repl in ["VARCHAR(", "CHARACTER VARYING("]:
            if tipo.startswith(repl):
                num = tipo[len(repl):-1]
                tipo = f"VC{num}"
        if len(tipo) > 14:
            tipo = tipo[:13] + "…"

        svg.append(
            f'<text x="{x + 14}" y="{cy}" fill="{color}" font-weight="{weight}">'
            f'{prefix}{esc(col.name)}{suffix}</text>'
        )
        svg.append(
            f'<text x="{x + TABLE_W - 14}" y="{cy}" text-anchor="end" '
            f'fill="#8b999e" font-size="10">{esc(tipo)}</text>'
        )
        cy += COL_H

# Relaciones FK (líneas con flechas)
def punto_anclaje(tx: int, ty: int, w: int, h: int, target_cx: int, target_cy: int):
    """Encuentra punto borde de la caja más cerca del target."""
    cx, cy = tx + w / 2, ty + h / 2
    dx, dy = target_cx - cx, target_cy - cy
    if abs(dx) > abs(dy):
        # Sale por costado vertical
        if dx > 0:
            return tx + w, cy
        else:
            return tx, cy
    else:
        # Sale por arriba/abajo
        if dy > 0:
            return cx, ty + h
        else:
            return cx, ty

for tname, t in Base.metadata.tables.items():
    if tname not in positions:
        continue
    for col in t.columns:
        for fk in col.foreign_keys:
            target_t = fk.column.table.name
            if target_t not in positions:
                continue
            x1, y1 = positions[tname]
            h1 = HEAD_H + len(t.columns) * COL_H + 8
            x2, y2 = positions[target_t]
            h2 = HEAD_H + len(Base.metadata.tables[target_t].columns) * COL_H + 8
            cx1, cy1 = x1 + TABLE_W / 2, y1 + h1 / 2
            cx2, cy2 = x2 + TABLE_W / 2, y2 + h2 / 2

            p1 = punto_anclaje(x1, y1, TABLE_W, h1, cx2, cy2)
            p2 = punto_anclaje(x2, y2, TABLE_W, h2, cx1, cy1)

            svg.append(
                f'<line x1="{p1[0]:.0f}" y1="{p1[1]:.0f}" '
                f'x2="{p2[0]:.0f}" y2="{p2[1]:.0f}" '
                f'stroke="#5a6a70" stroke-width="1.2" '
                f'stroke-dasharray="0" opacity="0.55" '
                f'marker-end="url(#fk)"/>'
            )

# Leyenda de dominios
ly = CANVAS_H - 80
svg.append(
    f'<text x="{MARGIN}" y="{ly}" font-size="12" font-weight="700" '
    f'fill="#243239">Dominios funcionales</text>'
)
lx = MARGIN
for nombre, bg, border, tablas in DOMAINS:
    svg.append(
        f'<rect x="{lx}" y="{ly + 12}" width="14" height="14" rx="3" '
        f'fill="{bg}" stroke="{border}" stroke-width="1.5"/>'
    )
    svg.append(
        f'<text x="{lx + 22}" y="{ly + 23}" font-size="11" fill="#33424a">'
        f'{nombre} ({len(tablas)})</text>'
    )
    lx += 220

svg.append("</svg>")

svg_str = "\n".join(svg)
(OUT_DIR / "db_erd.svg").write_text(svg_str, encoding="utf-8")

# HTML envoltorio para visualización
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>ERD · Sami</title>
  <style>
    body {{ margin: 0; padding: 20px; background: #e8eced; font-family: Inter, Arial, sans-serif; }}
    .frame {{ max-width: {CANVAS_W + 40}px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); }}
    svg {{ display: block; max-width: 100%; height: auto; }}
  </style>
</head>
<body>
  <div class="frame">
    {svg_str}
  </div>
</body>
</html>
"""
(OUT_DIR / "db_erd.html").write_text(html, encoding="utf-8")

print(f"✓ Diagrama generado:")
print(f"  • {OUT_DIR / 'db_erd.svg'}  ({len(svg_str)//1024} KB)")
print(f"  • {OUT_DIR / 'db_erd.html'} (para abrir en navegador)")
print(f"\n  Lienzo: {CANVAS_W}×{CANVAS_H}px · {len(positions)} tablas")
