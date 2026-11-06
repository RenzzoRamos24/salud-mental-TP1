"""Regresión de los tickets del QA de la semana 10 (Mantis P20261028).

Cubre lo que se arregló en backend: CP126, CP114, CP093, CP094, CP119 (texto
compartido), CP102, CP104/CP106, CP061-063, CP013, CP139. No toca producción:
usa una SQLite temporal.

Uso:  PYTHONPATH=. venv/bin/python tests/test_qa_semana10.py
"""
import asyncio
import io
import json
import os
import sqlite3
import tempfile
import uuid
from datetime import datetime

DB = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"

import httpx
import app.models  # noqa  (registra las tablas)
from app.config import settings
from app.core.security import hash_password
from app.database import engine, Base, SessionLocal
from app.main import app as fastapi_app
from app.models.bank import AplicacionCuestionario, PlantillaCuestionario
from app.models.password_reset import PasswordResetToken
from app.models.user import User

Base.metadata.create_all(bind=engine)
_c = sqlite3.connect(DB)
_c.executescript(open("seeds/banco_instrumentos.sql", encoding="utf-8").read())
_c.commit()
_c.close()

# El PDF de reportlab va comprimido; sin compresión se puede buscar texto en bytes.
import reportlab.rl_config as _rl
_rl.pageCompression = 0

suf = uuid.uuid4().hex[:6]
SECRETO = "TEXTO-LIBRE-DEL-ALUMNO-QUE-NO-DEBE-SALIR"
RESULTADO = {
    "riesgo_global": "ALTO", "crisis_activada": True, "n_senales": 2,
    "bloques": [{
        "tipo": "instrumento", "codigo": "PHQ-A", "nombre": "PHQ-A", "puntaje": 15,
        "rango_max": 27, "severidad": "moderadamente severa",
        "severidad_alerta": True, "bandera_crisis": True,
    }],
    "frases": [{
        "numero": 22, "area": "x", "pregunta": "Cuando estoy triste yo…",
        "respuesta": SECRETO, "dominante": "depresion", "detectadas": ["depresion"],
        "scores": {}, "crisis": True,
    }],
}


def ok(n, txt):
    print(f"{n:>2}. {txt:<62} OK")


async def main():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=fastapi_app),
                                 base_url="http://test") as c:
        async def reg(role, email):
            r = await c.post("/api/v1/auth/register", json={
                "nombre": "T", "apellido": "T", "email": email,
                "password": "Password123", "role": role})
            assert r.status_code in (200, 201), (r.status_code, r.text)
            d = r.json()
            return d["access_token"], d["user"]["id"]

        tok_psi, id_psi = await reg("psicologo", f"psi{suf}@colegio.edu.pe")
        tok_alu, id_alu = await reg("estudiante", f"alu{suf}@colegio.edu.pe")
        tok_alu2, id_alu2 = await reg("estudiante", f"alu2{suf}@colegio.edu.pe")
        H = lambda t: {"Authorization": f"Bearer {t}"}

        db = SessionLocal()
        for uid in (id_alu, id_alu2):
            db.query(User).filter(User.id == uid).update({"psicologo_id": id_psi})
        db.add(User(email=f"adm{suf}@colegio.edu.pe", hashed_password=hash_password("Password123"),
                    nombre="A", apellido="A", role="admin", activo=True))
        pl = PlantillaCuestionario(psicologo_id=id_psi, nombre="Plantilla QA")
        db.add(pl); db.commit(); db.refresh(pl)
        pend = AplicacionCuestionario(plantilla_id=pl.id, estudiante_id=id_alu,
                                      psicologo_id=id_psi, estado="pendiente")
        comp = AplicacionCuestionario(
            plantilla_id=pl.id, estudiante_id=id_alu, psicologo_id=id_psi,
            estado="completado", completada_at=datetime.utcnow(),
            riesgo_global="ALTO", crisis_activada=True,
            resultado_json=json.dumps(RESULTADO))
        db.add_all([pend, comp]); db.commit()
        id_pend, id_comp, id_pl = pend.id, comp.id, pl.id
        db.close()
        r = await c.post("/api/v1/auth/login", json={
            "email": f"adm{suf}@colegio.edu.pe", "password": "Password123"})
        tok_adm = r.json()["access_token"]

        # ── CP126 ───────────────────────────────────────────────────────
        r = await c.post(f"/api/v1/cuestionarios/aplicacion/{id_pend}/marcar-revisado",
                         headers=H(tok_psi))
        assert r.status_code == 400, (r.status_code, r.text)
        db = SessionLocal()
        assert db.query(AplicacionCuestionario).get(id_pend).estado == "pendiente"
        db.close()
        ok(1, "CP126 pendiente NO se puede marcar revisada (400, sigue pendiente)")
        r = await c.post(f"/api/v1/cuestionarios/aplicacion/{id_comp}/marcar-revisado",
                         headers=H(tok_psi))
        assert r.status_code == 200 and r.json()["estado"] == "revisado", r.text
        ok(2, "CP126 completada SÍ se marca revisada")

        # ── CP114 ───────────────────────────────────────────────────────
        db = SessionLocal(); antes = db.query(AplicacionCuestionario).count(); db.close()
        r = await c.post("/api/v1/cuestionarios/asignar", headers=H(tok_psi), json={
            "plantilla_id": id_pl, "estudiante_id": str(uuid.uuid4())})
        assert r.status_code == 404, (r.status_code, r.text)
        db = SessionLocal(); assert db.query(AplicacionCuestionario).count() == antes; db.close()
        ok(3, "CP114 estudiante inexistente → 404 y no crea la aplicación")
        r = await c.post("/api/v1/cuestionarios/asignar", headers=H(tok_psi), json={
            "plantilla_id": 99999, "estudiante_id": id_alu})
        assert r.status_code == 404, r.status_code
        r = await c.post("/api/v1/cuestionarios/asignar", headers=H(tok_psi), json={
            "plantilla_id": id_pl, "estudiante_id": id_alu2})
        assert r.status_code == 201, r.text
        ok(4, "CP114 plantilla inexistente → 404; caso válido → 201")

        # ── CP094 ───────────────────────────────────────────────────────
        # id_alu2 solo tiene una aplicación PENDIENTE (la recién asignada): sin resultado.
        for ext in ("pdf", "docx"):
            r = await c.get(f"/api/v1/psychologist/students/{id_alu2}/report.{ext}",
                            headers=H(tok_psi))
            assert r.status_code == 409, (ext, r.status_code)
            assert "datos suficientes" in r.json()["detail"].lower()
            assert not r.content.startswith(b"%PDF")
        ok(5, "CP094 sin resultados → 409 'sin datos suficientes' (PDF y Word)")

        # ── CP093 ───────────────────────────────────────────────────────
        r = await c.get(f"/api/v1/psychologist/students/{id_alu}/report.pdf", headers=H(tok_psi))
        assert r.status_code == 200 and r.content.startswith(b"%PDF"), r.status_code
        for esperado in (b"15/27", b"moderadamente severa", b"CRISIS ACTIVADA"):
            assert esperado in r.content, esperado
        assert SECRETO.encode() not in r.content, "el texto libre del alumno salió en el PDF"
        ok(6, "CP093 PDF trae puntaje 15/27, severidad y crisis; sin texto libre")
        r = await c.get(f"/api/v1/psychologist/students/{id_alu}/report.docx", headers=H(tok_psi))
        assert r.status_code == 200, r.status_code
        from docx import Document
        d = Document(io.BytesIO(r.content))
        texto = "\n".join(p.text for p in d.paragraphs) + "\n".join(
            cel.text for t in d.tables for row in t.rows for cel in row.cells)
        assert "15/27" in texto and "moderadamente severa" in texto
        assert "no es un diagnóstico" in texto and SECRETO not in texto
        ok(7, "CP093/CP119 Word trae puntajes y la declaración de no-diagnóstico")

        # ── CP102 ───────────────────────────────────────────────────────
        r = await c.get("/api/v1/admin/cuestionarios/stats", headers=H(tok_adm))
        s = r.json()
        assert s["total_pendientes"] == s["total_asignados"] - s["total_completados"] >= 1, s
        ok(8, f"CP102 stats: asignados {s['total_asignados']}, completados "
              f"{s['total_completados']}, pendientes {s['total_pendientes']}")

        # ── CP104 / CP106 ───────────────────────────────────────────────
        r = await c.get("/api/v1/banco/instrumentos", headers=H(tok_psi))
        phq = next(i for i in r.json() if i["codigo"] == "PHQ-A")
        assert phq["escala"] == "0–3" and len(phq["cortes"]) == 5, phq
        assert phq["cortes"][0]["severidad"] == "mínima"
        r = await c.get("/api/v1/banco/instrumentos/PHQ-A", headers=H(tok_psi))
        items = r.json()["items"]
        assert all(it["criterio_dsm5"] for it in items), "falta criterio DSM-5 en algún ítem"
        ok(9, "CP104/106 el banco expone escala, cortes y criterio DSM-5 por ítem")

        # ── CP061 / CP062 / CP063 ───────────────────────────────────────
        r = await c.get("/api/v1/admin/configuracion", headers=H(tok_adm))
        assert r.status_code == 200, (r.status_code, r.text[:300])
        assert {p["clave"] for p in r.json()} == {
            "PASSWORD_RESET_TOKEN_MINUTOS", "JWT_EXPIRE_MINUTES", "BACKUP_RETENCION_DIAS"}
        r = await c.get("/api/v1/admin/configuracion", headers=H(tok_psi))
        assert r.status_code == 403
        orig = settings.PASSWORD_RESET_TOKEN_MINUTOS
        r = await c.put("/api/v1/admin/configuracion/PASSWORD_RESET_TOKEN_MINUTOS",
                        headers=H(tok_adm), json={"valor": 999})
        assert r.status_code == 422 and settings.PASSWORD_RESET_TOKEN_MINUTOS == orig, r.text
        r = await c.put("/api/v1/admin/configuracion/NO_EXISTE", headers=H(tok_adm),
                        json={"valor": 5})
        assert r.status_code == 404
        ok(10, "CP061/062 lista de parámetros, 403 a no-admin, 422 fuera de rango, 404 clave ajena")
        r = await c.put("/api/v1/admin/configuracion/PASSWORD_RESET_TOKEN_MINUTOS",
                        headers=H(tok_adm), json={"valor": 20})
        assert r.status_code == 200 and r.json()["cambio"] and settings.PASSWORD_RESET_TOKEN_MINUTOS == 20
        r = await c.put("/api/v1/admin/configuracion/PASSWORD_RESET_TOKEN_MINUTOS",
                        headers=H(tok_adm), json={"valor": 20})
        assert r.json()["cambio"] is False
        aud = (await c.get("/api/v1/admin/configuracion/auditoria", headers=H(tok_adm))).json()
        assert len(aud) == 1 and aud[0]["valor_anterior"] == str(orig) and aud[0]["valor_nuevo"] == "20"
        assert aud[0]["usuario"] == f"adm{suf}@colegio.edu.pe"
        ok(11, "CP063 el cambio queda auditado (antes/después/quién); sin cambio no audita")
        from app.services import config_service
        settings.PASSWORD_RESET_TOKEN_MINUTOS = 5
        db = SessionLocal(); config_service.cargar_en_settings(db); db.close()
        assert settings.PASSWORD_RESET_TOKEN_MINUTOS == 20
        ok(12, "CP061 el valor guardado se re-aplica al arrancar")
        settings.PASSWORD_RESET_TOKEN_MINUTOS = orig

        # ── CP013: el código sale por correo, no por el log ─────────────
        import logging
        enviados = []

        class FakeSMTP:
            def __init__(self, *a, **k): pass
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def starttls(self, **k): pass
            def login(self, *a): pass
            def send_message(self, msg): enviados.append(msg)

        from app.services import mail_service
        settings.SMTP_HOST, settings.SMTP_FROM = "smtp.fake", "no-responder@fake"
        mail_service.smtplib.SMTP = FakeSMTP

        class Captura(logging.Handler):
            def __init__(self): super().__init__(); self.msgs = []
            def emit(self, rec):
                # El eco de SQLAlchemy (solo con DEBUG=True, local) imprime parámetros;
                # lo que se mide acá es el log de la aplicación.
                if not rec.name.startswith("sqlalchemy"):
                    self.msgs.append(rec.getMessage())
        cap = Captura(); logging.getLogger().addHandler(cap)
        settings.DEBUG = False

        r = await c.post("/api/v1/auth/forgot-password", json={"email": f"alu{suf}@colegio.edu.pe"})
        assert r.status_code == 200 and "consola" not in r.json()["mensaje"].lower(), r.text
        assert len(enviados) == 1, f"se enviaron {len(enviados)} correos"
        cuerpo = enviados[0].get_content()
        db = SessionLocal()
        tok = db.query(PasswordResetToken).order_by(PasswordResetToken.id.desc()).first().token
        db.close()
        assert tok in cuerpo and enviados[0]["To"] == f"alu{suf}@colegio.edu.pe"
        assert not any(tok in m for m in cap.msgs), "el código quedó en el log"
        ok(13, "CP013 el código llega por correo y NO queda en el log")
        msg_ok = r.json()["mensaje"]
        r = await c.post("/api/v1/auth/forgot-password", json={"email": "nadie@colegio.edu.pe"})
        assert r.status_code == 200 and r.json()["mensaje"] == msg_ok and len(enviados) == 1
        ok(14, "CP013 correo no registrado: misma respuesta y no se envía nada")
        settings.SMTP_HOST = ""
        r = await c.post("/api/v1/auth/forgot-password", json={"email": f"alu{suf}@colegio.edu.pe"})
        assert r.status_code == 200 and len(enviados) == 1
        assert not any("código de recuperación para" in m for m in cap.msgs)
        ok(15, "Sin SMTP configurado: responde 200, no envía, avisa sin imprimir el código")
        logging.getLogger().removeHandler(cap)

        # ── CP139 ───────────────────────────────────────────────────────
        r = await c.post("/api/v1/auth/oauth/microsoft", json={"access_token": "invalido"})
        assert r.status_code == 503, r.status_code           # proveedor sin configurar
        settings.MICROSOFT_CLIENT_ID = "client-id-de-prueba"
        from app.services import oauth_service

        class R401:
            status_code = 401
            def json(self): return {}

        class FakeClient:
            def __init__(self, *a, **k): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *a): return False
            async def get(self, *a, **k): return R401()

        oauth_service.httpx.AsyncClient = FakeClient
        r = await c.post("/api/v1/auth/oauth/microsoft", json={"access_token": "invalido"})
        assert r.status_code == 401 and "access_token" not in r.text, (r.status_code, r.text)
        settings.MICROSOFT_CLIENT_ID = ""
        ok(16, "CP139 sin configurar → 503; configurado + token inválido → 401, sin JWT")

        # ── CP066 / CP067 / CP073: el respaldo debe funcionar también con PostgreSQL ──
        import gzip, stat
        from app.services import admin_service
        tmp = tempfile.mkdtemp()
        admin_service.BACKUPS_DIR = tmp
        admin_service._es_postgres = lambda: True      # producción usa PostgreSQL
        r = await c.post("/api/v1/admin/backup", headers=H(tok_adm))
        assert r.status_code in (200, 201), (r.status_code, r.text[:200])
        nombre = r.json()["archivo"]
        assert nombre.endswith(".json.gz") and r.json()["tamanio_bytes"] > 0
        ruta = os.path.join(tmp, nombre)
        assert stat.S_IMODE(os.stat(ruta).st_mode) == 0o600, "el respaldo debe ser 0600"
        vol = json.loads(gzip.open(ruta, "rt", encoding="utf-8").read())
        assert "users" in vol["tablas"] and len(vol["tablas"]["users"]) >= 3
        assert any(f["archivo"] == nombre for f in (await c.get(
            "/api/v1/admin/backups", headers=H(tok_adm))).json())
        ok(17, "CP066/073 respaldo con PostgreSQL: volcado .json.gz, 0600, aparece en la lista")
        # purga: un respaldo viejo .json.gz se elimina por retención
        from app.services import scheduler_service
        scheduler_service.BACKUPS_DIR = tmp
        viejo = os.path.join(tmp, "backup_19990101_000000.json.gz")
        open(viejo, "wb").write(b"x")
        os.utime(viejo, (0, 0))
        scheduler_service._purgar_viejos()
        assert not os.path.exists(viejo) and os.path.exists(ruta)
        ok(18, "CP067 la purga por retención alcanza a los respaldos .json.gz")

    print("\nQA semana 10: APROBADO")


asyncio.run(main())
os.unlink(DB)
