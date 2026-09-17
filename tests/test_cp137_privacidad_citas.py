"""CP-137 — HU-52 esc. 2: la nota interna de la psicologa no llega al alumno.

Regresion del defecto de privacidad detectado en la auditoria de requisitos.
Uso:  PYTHONPATH=. venv/bin/python tests/test_cp137_privacidad_citas.py
"""
import os, tempfile, uuid, asyncio
DB = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"

import httpx
import app.models  # noqa  (registra las tablas antes de rebindear el nombre)
from app.database import engine, Base
from app.main import app as fastapi_app
Base.metadata.create_all(bind=engine)

NOTA = "SOSPECHA DE VIOLENCIA FAMILIAR - confirmar con tutoria"
suf = uuid.uuid4().hex[:6]


async def main():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=fastapi_app),
                                 base_url="http://test") as c:
        async def reg(role, email):
            r = await c.post("/api/v1/auth/register", json={
                "nombre": "T", "apellido": "T", "email": email,
                "password": "Password123", "role": role})
            assert r.status_code in (200, 201), (r.status_code, r.text)
            d = r.json()
            return d["access_token"], (d.get("user") or {}).get("id")

        tok_psi, _ = await reg("psicologo", f"psi{suf}@colegio.edu.pe")
        tok_alu, id_alu = await reg("estudiante", f"alu{suf}@colegio.edu.pe")
        H = lambda t: {"Authorization": f"Bearer {t}"}

        r = await c.post("/api/v1/psychologist/citas", headers=H(tok_psi), json={
            "estudiante_id": id_alu, "fecha": "2026-10-01", "hora": "10:00",
            "modalidad": "presencial", "notas": NOTA})
        assert r.status_code in (200, 201), (r.status_code, r.text)
        print("1. La psicologa crea la cita con nota interna ..... OK")
        assert r.json().get("notas") == NOTA
        print("2. La psicologa SI ve su nota ..................... OK")

        r = await c.get("/api/v1/users/me/citas", headers=H(tok_alu))
        assert r.status_code == 200, r.text
        citas = r.json()
        assert len(citas) == 1, citas
        print("3. El alumno ve la cita ........................... OK")
        assert "notas" not in citas[0], citas[0]
        assert NOTA not in r.text and "VIOLENCIA" not in r.text.upper()
        print("4. La nota interna NO aparece en la respuesta ..... OK")
        print("   campos recibidos:", sorted(citas[0].keys()))

        r = await c.post("/api/v1/users/me/citas", headers=H(tok_alu), json={
            "fecha": "2026-10-05", "hora": "11:00", "modalidad": "online",
            "motivo": "quiero conversar"})
        assert r.status_code in (200, 201), (r.status_code, r.text)
        assert "notas" not in r.json(), r.json()
        print("5. Al solicitar cita tampoco se filtra ............ OK")

        r = await c.get("/api/v1/psychologist/citas", headers=H(tok_psi))
        assert any(x.get("notas") == NOTA for x in r.json())
        print("6. La psicologa conserva acceso a sus notas ....... OK")
    print("\nCP-137: APROBADO")

asyncio.run(main())
os.unlink(DB)
