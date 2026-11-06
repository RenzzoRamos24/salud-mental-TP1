"""Parámetros generales del sistema editables por el administrador (HU0021).

Solo se exponen parámetros que el código REALMENTE lee de `settings` en tiempo
de ejecución; no hay parámetros decorativos. Cada uno tiene tipo, rango y valor
por defecto. Un valor fuera de rango se rechaza (QA CP062) y cada cambio efectivo
queda en `configuracion_cambios` (QA CP063).

Cómo se aplica: se guarda en `configuraciones` (persistente) y se copia al objeto
`settings` del proceso. Al arrancar, `cargar_en_settings` vuelve a aplicar lo
guardado. El servidor corre con un solo worker (ver `startup.sh`), así que el
valor en memoria es el único y no puede divergir.
"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.configuracion import Configuracion, ConfiguracionCambio

# clave -> (etiqueta, minimo, maximo, unidad, descripcion)
PARAMETROS: dict[str, dict] = {
    "PASSWORD_RESET_TOKEN_MINUTOS": {
        "etiqueta": "Vigencia del código de recuperación",
        "min": 5, "max": 60, "unidad": "minutos",
        "descripcion": "Cuánto tiempo sirve el código que se envía por correo.",
    },
    "JWT_EXPIRE_MINUTES": {
        "etiqueta": "Duración de la sesión",
        "min": 15, "max": 10080, "unidad": "minutos",
        "descripcion": "Tiempo hasta que la sesión vence y pide volver a entrar. "
                       "Aplica a las sesiones que se inicien desde el cambio.",
    },
    "BACKUP_RETENCION_DIAS": {
        "etiqueta": "Retención de respaldos",
        "min": 1, "max": 365, "unidad": "días",
        "descripcion": "Los respaldos más antiguos que esto se purgan.",
    },
}

# Valores de fábrica, tomados de `settings` al importar (antes de cualquier override)
_DEFAULTS = {k: int(getattr(settings, k)) for k in PARAMETROS}


class ParametroInvalido(ValueError):
    """Clave desconocida o valor fuera de rango (los endpoints devuelven 422)."""


class ParametroDesconocido(ValueError):
    """La clave no es un parámetro editable (404)."""


def _validar(clave: str, valor) -> int:
    if clave not in PARAMETROS:
        raise ParametroDesconocido(f"'{clave}' no es un parámetro editable.")
    p = PARAMETROS[clave]
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ParametroInvalido(f"{p['etiqueta']}: debe ser un número entero.")
    if not (p["min"] <= valor <= p["max"]):
        raise ParametroInvalido(
            f"{p['etiqueta']}: el valor debe estar entre {p['min']} y {p['max']} "
            f"{p['unidad']} (recibido {valor})."
        )
    return valor


def _guardado(db: Session, clave: str) -> Optional[int]:
    row = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if row is None:
        return None
    try:
        return int(json.loads(row.valor))
    except (TypeError, ValueError):
        return None


def listar(db: Session) -> list[dict]:
    salida = []
    for clave, p in PARAMETROS.items():
        salida.append({
            "clave": clave, "etiqueta": p["etiqueta"], "descripcion": p["descripcion"],
            "unidad": p["unidad"], "min": p["min"], "max": p["max"],
            "valor": int(getattr(settings, clave)),
            "por_defecto": _DEFAULTS[clave],
        })
    return salida


def actualizar(db: Session, clave: str, valor, admin) -> dict:
    nuevo = _validar(clave, valor)
    anterior = int(getattr(settings, clave))
    if nuevo == anterior:
        return {"clave": clave, "valor": nuevo, "cambio": False}

    row = db.query(Configuracion).filter(Configuracion.clave == clave).first()
    if row is None:
        db.add(Configuracion(clave=clave, valor=json.dumps(nuevo)))
    else:
        row.valor = json.dumps(nuevo)
    db.add(ConfiguracionCambio(
        clave=clave, valor_anterior=str(anterior), valor_nuevo=str(nuevo),
        usuario_id=getattr(admin, "id", None), usuario_email=getattr(admin, "email", None),
    ))
    db.commit()
    setattr(settings, clave, nuevo)
    return {"clave": clave, "valor": nuevo, "cambio": True, "anterior": anterior}


def auditoria(db: Session, limite: int = 50) -> list[dict]:
    filas = (
        db.query(ConfiguracionCambio)
        .order_by(ConfiguracionCambio.timestamp.desc(), ConfiguracionCambio.id.desc())
        .limit(max(1, min(limite, 500)))
        .all()
    )
    return [{
        "id": f.id, "clave": f.clave,
        "etiqueta": PARAMETROS.get(f.clave, {}).get("etiqueta", f.clave),
        "valor_anterior": f.valor_anterior, "valor_nuevo": f.valor_nuevo,
        "usuario": f.usuario_email, "timestamp": f.timestamp.isoformat(),
    } for f in filas]


def cargar_en_settings(db: Session) -> int:
    """Hook de arranque: re-aplica lo guardado. Ignora valores que hoy no validan."""
    n = 0
    for clave in PARAMETROS:
        v = _guardado(db, clave)
        if v is None:
            continue
        try:
            setattr(settings, clave, _validar(clave, v))
            n += 1
        except ParametroInvalido:
            continue
    return n
