"""
Extrae respuestas de fotos de cuestionarios de papel (Pack A, B, C) del
piloto Sami usando Claude Vision, y genera un CSV listo para pegar en la
Google Sheet vinculada al form.

Uso:
    venv/bin/python scripts/procesar_fotos_piloto.py --pack B \
        --carpeta fotos/pack_B/ --salida respuestas_B.csv

    # Prueba rápida con 2 fotos
    venv/bin/python scripts/procesar_fotos_piloto.py --pack B \
        --carpeta fotos/pack_B/ --salida test.csv --limite 2

Requisitos:
    export ANTHROPIC_API_KEY=sk-ant-...        # Obtener en console.anthropic.com

Notas:
    - Usa Claude Opus 4.7 (mejor Vision + JSON estructurado).
    - Prompt caching baja ~90% el input tokens desde la 2da foto de cada pack.
    - Costo estimado: ~US$ 2–3 por 96 fotos.
    - Redimensiona a 1600px max lado antes de mandar (ahorra tokens y evita
      rechazos por tamaño).
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import sys
from pathlib import Path
from typing import List, Optional

import anthropic
from PIL import Image


# ── Ítems clínicos (idénticos a scripts/generar_forms_google.gs) ───────
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


# ── Prompts + tool schemas por pack ────────────────────────────────────
LABELS_03_TEXT = (
    "0 = Nunca / En blanco no marcado en la primera columna\n"
    "1 = Algunos días (segunda columna)\n"
    "2 = Más de la mitad (tercera columna)\n"
    "3 = Casi todos los días (cuarta columna)"
)
LABELS_DASS_TEXT = (
    "0 = No me aplicó\n"
    "1 = Un poco\n"
    "2 = Bastante\n"
    "3 = Mucho"
)


def _tool_schema_pack(pack: str) -> dict:
    """Schema del tool que Claude va a completar con los datos extraídos."""
    common = {
        "edad": {
            "type": ["integer", "null"],
            "description": "Edad del alumno. null si el campo está en blanco o ilegible.",
        },
        "genero": {
            "type": ["string", "null"],
            "description": "M, F, u Otro (si el alumno marcó una opción). null si ilegible.",
        },
        "codigo_papel": {
            "type": ["string", "null"],
            "description": "El número/código escrito en el campo 'Código de participante' del papel, si el alumno lo escribió. null si está en blanco.",
        },
    }

    if pack == "A":
        props = {
            **common,
            "phqa": {
                "type": "array",
                "description": "Los 9 ítems del PHQ-A en orden. Para cada uno, 0-3 según la columna marcada. Usá -1 si está en blanco o ilegible.",
                "items": {"type": "integer", "minimum": -1, "maximum": 3},
                "minItems": 9,
                "maxItems": 9,
            },
            "gad7": {
                "type": "array",
                "description": "Los 7 ítems del GAD-7 en orden. Para cada uno, 0-3 según la columna marcada. Usá -1 si está en blanco.",
                "items": {"type": "integer", "minimum": -1, "maximum": 3},
                "minItems": 7,
                "maxItems": 7,
            },
        }
    elif pack == "B":
        props = {
            **common,
            "dass21": {
                "type": "array",
                "description": "Los 21 ítems del DASS-21 en orden. Para cada uno, 0-3 según la columna marcada. Usá -1 si está en blanco.",
                "items": {"type": "integer", "minimum": -1, "maximum": 3},
                "minItems": 21,
                "maxItems": 21,
            },
        }
    else:  # C
        props = {
            **common,
            "frases": {
                "type": "array",
                "description": "Las 20 respuestas de texto libre en orden. Usá string vacío '' si el alumno dejó la frase en blanco.",
                "items": {"type": "string"},
                "minItems": 20,
                "maxItems": 20,
            },
        }

    return {
        "type": "object",
        "properties": props,
        "required": list(props.keys()),
        "additionalProperties": False,
    }


def _system_prompt(pack: str) -> str:
    """System prompt específico por pack. Se cachea entre fotos del mismo pack."""
    base = (
        "Sos un asistente que extrae respuestas de cuestionarios de papel del "
        "piloto Sami — un estudio de salud mental con adolescentes de "
        "secundaria de un colegio privado. Los cuestionarios los llenaron "
        "los alumnos a mano; te llegan fotos escaneadas.\n\n"
        "Tu trabajo:\n"
        "1. Ubicar los campos demográficos: código de participante, edad, género.\n"
        "2. Para cada ítem numerado, identificar cuál de los círculos está "
        "marcado (rellenado, tachado, con X, o con un tick). Si dudás entre "
        "dos, elegí el más marcado.\n"
        "3. Si un ítem está sin marcar o no lo podés determinar con "
        "seguridad razonable, usá -1 (no adivines).\n"
        "4. Los items van numerados del 1 al N. Respetá el orden.\n"
    )

    if pack == "A":
        items_txt = "PHQ-A (9 ítems):\n" + "\n".join(
            f"  {i+1}. {t}" for i, t in enumerate(PHQA)
        ) + "\n\nGAD-7 (7 ítems):\n" + "\n".join(
            f"  {i+1}. {t}" for i, t in enumerate(GAD7)
        )
        escala = LABELS_03_TEXT
    elif pack == "B":
        items_txt = "DASS-21 (21 ítems):\n" + "\n".join(
            f"  {i+1}. {t}" for i, t in enumerate(DASS21)
        )
        escala = LABELS_DASS_TEXT
    else:  # C
        items_txt = "Frases incompletas (20 estímulos):\n" + "\n".join(
            f"  {i+1}. {t}" for i, t in enumerate(FRASES_SSCT)
        )
        escala = (
            "Cada frase tiene una línea debajo donde el alumno escribió a "
            "mano su continuación. Transcribí LITERALMENTE lo que escribió, "
            "sin corregir ni interpretar. Si dejó en blanco, devolvé string "
            "vacío ''. Si la letra es totalmente ilegible, devolvé '[ilegible]'."
        )

    return (
        f"{base}\n"
        f"ESCALA DE RESPUESTA:\n{escala}\n\n"
        f"ÍTEMS DE ESTE PACK:\n{items_txt}\n\n"
        f"Devolvé todos los datos llamando al tool guardar_respuestas."
    )


# ── Utilidades ────────────────────────────────────────────────────────
def preparar_imagen(path: Path, max_lado: int = 1600) -> tuple[str, str]:
    """Redimensiona (si hace falta) y devuelve (base64_data, media_type)."""
    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_lado:
        ratio = max_lado / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode(), "image/jpeg"


def cabecera_csv(pack: str) -> list[str]:
    common = ["foto", "codigo_papel", "edad", "genero"]
    if pack == "A":
        return common + [f"phqa_{i+1}" for i in range(9)] + [f"gad7_{i+1}" for i in range(7)]
    if pack == "B":
        return common + [f"dass_{i+1:02d}" for i in range(21)]
    return common + [f"frase_{i+1:02d}" for i in range(20)]


def fila_csv(pack: str, nombre: str, datos: dict) -> list:
    common = [nombre, datos.get("codigo_papel") or "", datos.get("edad") or "", datos.get("genero") or ""]
    if pack == "A":
        return common + list(datos["phqa"]) + list(datos["gad7"])
    if pack == "B":
        return common + list(datos["dass21"])
    return common + list(datos["frases"])


# ── Extractor ─────────────────────────────────────────────────────────
def extraer(client: anthropic.Anthropic, path: Path, pack: str) -> tuple[dict, object]:
    """Llama a Claude Vision con la foto. Devuelve (dict con datos, usage)."""
    img_b64, media_type = preparar_imagen(path)

    tool = {
        "name": "guardar_respuestas",
        "description": "Guarda las respuestas extraídas de la foto del cuestionario.",
        "input_schema": _tool_schema_pack(pack),
    }

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        system=[
            {
                "type": "text",
                "text": _system_prompt(pack),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        tools=[tool],
        tool_choice={"type": "tool", "name": "guardar_respuestas"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            f"Extraé todos los datos de esta foto (Pack {pack}) "
                            f"llamando al tool guardar_respuestas."
                        ),
                    },
                ],
            }
        ],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        raise RuntimeError(f"Claude no llamó al tool. Respuesta: {response.content}")

    return tool_use.input, response.usage


# ── Main ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Extrae respuestas de fotos de cuestionarios del piloto Sami."
    )
    parser.add_argument("--pack", choices=["A", "B", "C"], required=True)
    parser.add_argument("--carpeta", type=Path, required=True,
                        help="Carpeta con las fotos (jpg/png/webp) del pack.")
    parser.add_argument("--salida", type=Path, required=True,
                        help="Archivo CSV donde escribir las respuestas.")
    parser.add_argument("--limite", type=int, default=None,
                        help="Procesar solo las primeras N fotos (útil para probar).")
    args = parser.parse_args()

    if not args.carpeta.is_dir():
        sys.exit(f"❌ No existe la carpeta: {args.carpeta}")

    extensiones = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    fotos = sorted(
        p for p in args.carpeta.iterdir()
        if p.is_file() and p.suffix.lower() in extensiones
    )
    if not fotos:
        sys.exit(f"❌ No hay fotos en {args.carpeta}")
    if args.limite:
        fotos = fotos[: args.limite]

    print(f"Procesando {len(fotos)} fotos del Pack {args.pack} → {args.salida}")

    client = anthropic.Anthropic()
    total_in = total_out = cache_read = cache_write = 0
    errores = []

    with args.salida.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cabecera_csv(args.pack))
        f.flush()

        for i, path in enumerate(fotos, 1):
            print(f"  [{i:>3}/{len(fotos)}] {path.name} ... ", end="", flush=True)
            try:
                datos, usage = extraer(client, path, args.pack)
                writer.writerow(fila_csv(args.pack, path.name, datos))
                f.flush()
                total_in += usage.input_tokens
                total_out += usage.output_tokens
                cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0
                cache_write += getattr(usage, "cache_creation_input_tokens", 0) or 0
                print("OK")
            except anthropic.APIError as e:
                print(f"ERROR API: {e}")
                errores.append((path.name, str(e)))
            except Exception as e:
                print(f"ERROR: {e}")
                errores.append((path.name, str(e)))

    # Resumen
    print()
    print("=" * 60)
    print(f"CSV listo: {args.salida}")
    print(f"OK: {len(fotos) - len(errores)}  |  Errores: {len(errores)}")
    if errores:
        print("\nFotos con error:")
        for nombre, err in errores:
            print(f"  - {nombre}: {err}")
    print(
        f"\nTokens — input: {total_in:,}  output: {total_out:,}"
        f"  |  cache hits: {cache_read:,}  writes: {cache_write:,}"
    )
    # Estimado costo Opus 4.7: $5/M input, $25/M output, cache read $0.5/M, cache write $6.25/M
    costo = (
        (total_in - cache_read - cache_write) * 5 / 1_000_000
        + cache_read * 0.5 / 1_000_000
        + cache_write * 6.25 / 1_000_000
        + total_out * 25 / 1_000_000
    )
    print(f"Costo estimado: US$ {costo:.2f}")


if __name__ == "__main__":
    main()
