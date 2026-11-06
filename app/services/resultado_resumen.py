"""Resumen clínico de un resultado, compartido por el PDF, el Word y la pantalla.

Qué entra: puntaje y severidad por bloque, banderas de crisis y recuento de
señales de las frases incompletas (por categoría, sin el texto del alumno).
Qué no entra: la respuesta literal del estudiante, que es texto libre y puede
identificar. La psicóloga lo ve en la pantalla de resultado.

El sistema no diagnostica: reporta señales y banderas (regla 5 del proyecto).
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Optional

# Misma declaración en la pantalla de resultado (QA CP119) y en los reportes.
DECLARACION_NO_DIAGNOSTICO = (
    "Este resultado no es un diagnóstico. Presenta señales, puntajes y banderas "
    "calculados a partir de las respuestas; la interpretación clínica "
    "corresponde a la profesional."
)

ESTADOS_CON_RESULTADO = ("completado", "revisado")


class SinDatosSuficientes(ValueError):
    """El estudiante no tiene ningún cuestionario con resultado (QA CP094)."""


def _cargar(resultado_json: Optional[str]) -> dict:
    if not resultado_json:
        return {}
    try:
        return json.loads(resultado_json)
    except (TypeError, ValueError):
        return {}


def resumen(resultado_json: Optional[str]) -> dict:
    r = _cargar(resultado_json)
    bloques = []
    for b in r.get("bloques", []):
        bloques.append({
            "nombre": b.get("nombre") or b.get("codigo") or "—",
            "codigo": b.get("codigo"),
            "puntaje": b.get("puntaje"),
            "rango_max": b.get("rango_max"),
            "severidad": b.get("severidad") or "—",
            "alerta": bool(b.get("severidad_alerta")),
            "bandera_crisis": bool(b.get("bandera_crisis")),
        })
    frases = r.get("frases", [])
    dominantes = Counter(f.get("dominante") for f in frases if f.get("dominante"))
    return {
        "riesgo_global": r.get("riesgo_global"),
        "crisis_activada": bool(r.get("crisis_activada")),
        "n_senales": r.get("n_senales"),
        "bloques": bloques,
        "frases": {
            "total": len(frases),
            "con_deteccion": sum(1 for f in frases if f.get("detectadas")),
            "con_crisis": sorted(int(f["numero"]) for f in frases
                                 if f.get("crisis") and f.get("numero") is not None),
            "por_categoria": dict(dominantes),
        },
    }


def texto_puntaje(b: dict) -> str:
    if b.get("puntaje") is None:
        return "—"
    return f"{b['puntaje']}/{b['rango_max']}" if b.get("rango_max") else str(b["puntaje"])


def con_resultado(aplicaciones) -> list:
    """Aplicaciones del estudiante que ya tienen resultado que reportar."""
    return [a for a in aplicaciones
            if a.estado in ESTADOS_CON_RESULTADO and a.completada_at is not None]
