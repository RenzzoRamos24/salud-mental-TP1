"""
Crea un administrador ADICIONAL de forma segura.

Por qué no usar seed_admin.py para esto
---------------------------------------
- seed_admin cae en la contraseña por defecto "Admin12345" si no se le pasa
  ADMIN_PASSWORD, y esa contraseña está publicada en el repo.
- seed_admin, si el correo ya existe, convierte esa cuenta en admin y le
  cambia la contraseña sin avisar.

Este script no tiene contraseña por defecto, se niega si el correo ya existe
y nunca imprime la contraseña. Además, seed_admin solo reescribe la cuenta de
ADMIN_EMAIL en cada arranque: este admin conserva su contraseña tras reinicios.

Uso (en tu propia terminal, no en el chat: pide la contraseña sin mostrarla)
---
    export DATABASE_URL="$(az webapp config appsettings list --name sami-app-9921877 \\
        --resource-group sami-rg --query "[?name=='DATABASE_URL'].value" -o tsv)"
    venv/bin/python -m scripts.crear_admin_adicional \\
        --email tu.correo@dominio --nombre Renzo --apellido Gutierrez
"""
from __future__ import annotations

import argparse
import getpass
import sys
import uuid

from app.core.security import hash_password
from app.database import SessionLocal
from app.models.user import User


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--nombre", required=True)
    ap.add_argument("--apellido", required=True)
    args = ap.parse_args()

    email = args.email.strip().lower()
    if "@" not in email or email.endswith(".sami.local"):
        sys.exit("Correo inválido (el dominio .sami.local es de las cuentas por código).")

    pwd = getpass.getpass("Contraseña del nuevo admin (mínimo 12 caracteres): ")
    if len(pwd) < 12:
        sys.exit("La contraseña debe tener al menos 12 caracteres. No se creó nada.")
    if len(pwd) > 72:
        sys.exit("Máximo 72 caracteres (límite de bcrypt). No se creó nada.")
    if getpass.getpass("Repetir contraseña: ") != pwd:
        sys.exit("Las contraseñas no coinciden. No se creó nada.")

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            sys.exit(f"Ya existe una cuenta con {email}. No se modificó nada.")
        db.add(User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=hash_password(pwd),
            nombre=args.nombre.strip(),
            apellido=args.apellido.strip(),
            role="admin",
            activo=True,
        ))
        db.commit()
        n = db.query(User).filter(User.role == "admin").count()
        print(f"✅ Admin creado: {email}  (administradores en el sistema: {n})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
