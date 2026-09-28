"""
Genera códigos de acceso anónimos para la re-encuesta del colegio (4to y 5to
de secundaria) y deja a cada alumno con el cuestionario corto ya asignado.

Qué hace:
  1. Crea (si no existe) la plantilla "Re-encuesta colegio" con:
       - PHQ-A completo (9 ítems)
       - GAD-7 completo (7 ítems)
       - Frases incompletas de las áreas "emociones" + "futuro" (10 frases)
     Ese orden es el que se decidió en la sesión de diseño: PHQ-A y GAD-7
     primero (lo más importante, antes de que se cansen), frases al final.
  2. Genera N alumnos anónimos por sección (SAMI-4TO-01, SAMI-4TO-02, ...),
     sin nombre real — cada uno con un `codigo_acceso` único que reemplaza
     el login por email+contraseña (ver /auth/login-codigo).
  3. Les asigna una AplicacionCuestionario "pendiente" de esa plantilla,
     lista para responder apenas entren con el código.
  4. Exporta un CSV con los códigos para imprimir y repartir en papel.

Uso:
    venv/bin/python -m scripts.generar_codigos_encuesta \
        --psicologa-email psicologa@colegio.edu.pe \
        --n-4to 52 --n-5to 53

Re-correr es seguro: si el código ya existe, lo saltea (no duplica).
"""
from __future__ import annotations

import argparse
import csv
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.config import settings
from app.database import SessionLocal
from app.models.bank import (
    AplicacionCuestionario,
    BankInstrumento,
    PlantillaBloque,
    PlantillaCuestionario,
)
from app.models.consent import Consent
from app.models.user import User

ROOT = Path(__file__).resolve().parent.parent
SALIDA_CSV = ROOT / "docs" / "piloto_colegio" / "codigos_encuesta.csv"

PLANTILLA_NOMBRE = "Re-encuesta colegio · PHQ-A + GAD-7 + frases"
# Áreas de frases priorizadas para depresión/ansiedad (ver BANCO_INSTRUMENTOS.md
# y la justificación vía Cognitive Triad de Beck discutida para el diseño).
FRASES_AREAS = "emociones,futuro"


def _get_psicologa(db: Session, email: str) -> User:
    psi = db.query(User).filter_by(email=email.lower().strip()).first()
    if psi is None:
        sys.exit(
            f"❌ No existe una psicóloga con el email '{email}'. "
            "Registrala primero desde /register o pasá el email correcto con "
            "--psicologa-email."
        )
    if psi.role != "psicologo":
        sys.exit(f"❌ El usuario '{email}' no tiene rol 'psicologo'.")
    return psi


def _get_instrumento(db: Session, codigo: str) -> BankInstrumento:
    inst = db.query(BankInstrumento).filter_by(codigo=codigo).first()
    if inst is None:
        sys.exit(f"❌ Falta el instrumento '{codigo}' en el banco. Corré los seeds.")
    return inst


def _asegurar_plantilla(db: Session, psi_id: str) -> PlantillaCuestionario:
    pl = db.query(PlantillaCuestionario).filter_by(nombre=PLANTILLA_NOMBRE).first()
    if pl:
        return pl

    phqa = _get_instrumento(db, "PHQ-A")
    gad7 = _get_instrumento(db, "GAD-7")

    pl = PlantillaCuestionario(
        psicologo_id=psi_id,
        nombre=PLANTILLA_NOMBRE,
        descripcion=(
            "PHQ-A + GAD-7 completos, seguidos de frases incompletas de las "
            "áreas emociones y futuro. Usado para la re-encuesta de 4to/5to "
            "de secundaria — alimenta la selección de ítems (SVM) y el "
            "fine-tuning de BETO."
        ),
        activa=1,
    )
    db.add(pl)
    db.flush()

    db.add(PlantillaBloque(
        plantilla_id=pl.id, orden=1, tipo="instrumento", instrumento_id=phqa.id,
    ))
    db.add(PlantillaBloque(
        plantilla_id=pl.id, orden=2, tipo="instrumento", instrumento_id=gad7.id,
    ))
    db.add(PlantillaBloque(
        plantilla_id=pl.id, orden=3, tipo="frases", frases_areas=FRASES_AREAS,
    ))
    db.commit()
    print(f"✅ Plantilla creada: '{PLANTILLA_NOMBRE}' (id={pl.id})")
    return pl


def _generar_seccion(
    db: Session, plantilla: PlantillaCuestionario, psi_id: str,
    prefijo: str, grado: str, cantidad: int,
) -> list[dict]:
    """Genera `cantidad` alumnos anónimos SAMI-{prefijo}-NN con su código."""
    filas = []
    for i in range(1, cantidad + 1):
        codigo = f"SAMI-{prefijo}-{i:02d}"

        existente = db.query(User).filter_by(codigo_acceso=codigo).first()
        if existente:
            filas.append({"codigo": codigo, "grado": grado, "estado": "ya existía"})
            continue

        placeholder_email = f"{codigo.lower()}@piloto.sami.local"
        alumno = User(
            id=str(uuid.uuid4()),
            email=placeholder_email,
            hashed_password=hash_password(str(uuid.uuid4())),  # inaccesible por login normal
            nombre=f"Alumno {prefijo}",
            apellido=f"#{i:02d}",
            role="estudiante",
            activo=True,
            psicologo_id=psi_id,
            grado=grado,
            estado_caso="activo",
            codigo_acceso=codigo,
        )
        db.add(alumno)
        db.flush()

        db.add(Consent(
            user_id=alumno.id,
            version=settings.CONSENT_VERSION_ACTUAL,
            aceptado_en=datetime.utcnow(),
            ip_address="0.0.0.0",
        ))

        db.add(AplicacionCuestionario(
            plantilla_id=plantilla.id,
            estudiante_id=alumno.id,
            psicologo_id=psi_id,
            estado="pendiente",
            asignada_at=datetime.utcnow() - timedelta(minutes=1),
        ))

        filas.append({"codigo": codigo, "grado": grado, "estado": "nuevo"})
    db.commit()
    return filas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--psicologa-email", required=True)
    parser.add_argument("--n-4to", type=int, default=52)
    parser.add_argument("--n-5to", type=int, default=53)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        psi = _get_psicologa(db, args.psicologa_email)
        print(f"Psicóloga responsable: {psi.email} (id={psi.id})")

        plantilla = _asegurar_plantilla(db, psi.id)

        filas = []
        filas += _generar_seccion(
            db, plantilla, psi.id, prefijo="4TO", grado="4to secundaria",
            cantidad=args.n_4to,
        )
        filas += _generar_seccion(
            db, plantilla, psi.id, prefijo="5TO", grado="5to secundaria",
            cantidad=args.n_5to,
        )

        SALIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(SALIDA_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["codigo", "grado", "estado"])
            writer.writeheader()
            writer.writerows(filas)

        nuevos = sum(1 for r in filas if r["estado"] == "nuevo")
        print()
        print("=" * 60)
        print(f"Total códigos: {len(filas)}  (nuevos={nuevos})")
        print(f"CSV para imprimir: {SALIDA_CSV}")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()
