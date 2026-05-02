"""
Crea o actualiza el usuario admin del sistema.

Uso:
    python -m scripts.seed_admin

Variables opcionales:
    ADMIN_EMAIL    (default: admin@admin.com)
    ADMIN_PASSWORD (default: Admin12345)
    ADMIN_NOMBRE   (default: Admin)
    ADMIN_APELLIDO (default: Sistema)
"""
import os
import sys
from pathlib import Path

# Permite ejecutar el script desde la raíz del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.core.security import hash_password


def main():
    Base.metadata.create_all(bind=engine)

    email = os.getenv("ADMIN_EMAIL", "admin@admin.com").lower()
    password = os.getenv("ADMIN_PASSWORD", "Admin12345")
    nombre = os.getenv("ADMIN_NOMBRE", "Admin")
    apellido = os.getenv("ADMIN_APELLIDO", "Sistema")

    db = SessionLocal()
    try:
        existente = db.query(User).filter(User.email == email).first()
        if existente:
            existente.hashed_password = hash_password(password)
            existente.role = "admin"
            existente.activo = True
            db.commit()
            print(f"✅ Admin actualizado: {email}")
        else:
            admin = User(
                email=email,
                hashed_password=hash_password(password),
                nombre=nombre,
                apellido=apellido,
                role="admin",
                activo=True,
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin creado: {email}")

        print(f"   Password: {password}")
        print("   Cambia la contraseña después del primer login.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
