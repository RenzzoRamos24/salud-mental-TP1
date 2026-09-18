"""Feedback de la psicologa sobre el analisis de BETO.

El veredicto es por cuestionario completo, no por frase. Cubre el ciclo
por HTTP: aceptar, descartar, cambiar de opinion, deshacer, y que los
conteos y las metricas globales cuadren. Tambien que una psicologa ajena
no pueda votar sobre una aplicacion que no es suya.

Uso:  PYTHONPATH=. venv/bin/python tests/test_feedback_clasificador.py
"""
import os, tempfile, uuid, asyncio, json

DB = tempfile.mktemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{DB}"

import httpx
import app.models  # noqa  (registra las tablas antes de rebindear el nombre)
from app.database import engine, Base, SessionLocal
from app.main import app as fastapi_app
from app.models.bank import AplicacionCuestionario, PlantillaCuestionario

Base.metadata.create_all(bind=engine)
suf = uuid.uuid4().hex[:6]

# Resultado ya evaluado que se inyecta a mano: el test valida el feedback,
# no al evaluator ni a BETO (que tardaria minutos en cargar el modelo).
RESULTADO = {
    "riesgo_global": "CRITICO", "crisis_activada": True,
    "n_senales": 0, "n_bloques": 0, "bloques": [],
    "frases": [
        {"area": "familia", "numero": 1, "pregunta": "En mi casa yo...",
         "respuesta": "duermo", "dominante": "depresion",
         "detectadas": ["depresion"], "scores": {}, "crisis": True},
        {"area": "familia", "numero": 5, "pregunta": "Mis hermanos...",
         "respuesta": "son muy cheveres", "dominante": "neutral",
         "detectadas": ["neutral"], "scores": {}, "crisis": False},
        {"area": "futuro", "numero": 21, "pregunta": "Dentro de 5 anios...",
         "respuesta": "no se", "dominante": "ansiedad",
         "detectadas": ["ansiedad"], "scores": {}, "crisis": False},
    ],
    "svm_segunda_opinion": None,
}


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

        tok_psi, id_psi = await reg("psicologo", f"psi{suf}@colegio.edu.pe")
        tok_otra, _ = await reg("psicologo", f"otra{suf}@colegio.edu.pe")
        _, id_alu = await reg("estudiante", f"alu{suf}@colegio.edu.pe")
        H = lambda t: {"Authorization": f"Bearer {t}"}

        # Aplicacion ya completada y evaluada, en la BD directamente.
        db = SessionLocal()
        pl = PlantillaCuestionario(nombre=f"Test {suf}", psicologo_id=id_psi)
        db.add(pl); db.commit(); db.refresh(pl)
        pl_id = pl.id
        apl = AplicacionCuestionario(
            plantilla_id=pl.id, estudiante_id=id_alu, psicologo_id=id_psi,
            estado="completado", resultado_json=json.dumps(RESULTADO),
            riesgo_global="CRITICO", crisis_activada=True)
        db.add(apl); db.commit(); db.refresh(apl)
        aid = apl.id
        db.close()

        base = f"/api/v1/cuestionarios/aplicacion/{aid}"

        # Segunda aplicacion, para que el acumulado tenga mas de un caso.
        db = SessionLocal()
        apl2 = AplicacionCuestionario(
            plantilla_id=pl_id, estudiante_id=id_alu, psicologo_id=id_psi,
            estado="completado", resultado_json=json.dumps(
                {**RESULTADO, "riesgo_global": "BAJO", "crisis_activada": False}),
            riesgo_global="BAJO", crisis_activada=False)
        db.add(apl2); db.commit(); db.refresh(apl2)
        aid2 = apl2.id
        db.close()
        base2 = f"/api/v1/cuestionarios/aplicacion/{aid2}"

        # 1. Al principio el resultado no tiene veredicto.
        r = await c.get(f"{base}/resultado", headers=H(tok_psi))
        assert r.status_code == 200, (r.status_code, r.text)
        assert r.json()["feedback"] is None, r.json()["feedback"]
        print("1. Sin veredicto, el resultado sale sin juzgar ........ OK")

        # 2. Descartar el analisis de este cuestionario.
        r = await c.post(f"{base}/feedback", headers=H(tok_psi),
                         json={"veredicto": "rechazado",
                               "comentario": "marca ideacion donde no la hay"})
        assert r.status_code == 200, (r.status_code, r.text)
        m = r.json()["metricas"]
        assert (m["rechazados"], m["aceptados"]) == (1, 0), m
        print("2. Descartar el analisis completo .................... OK")

        # 3. Aceptar el analisis del segundo cuestionario.
        r = await c.post(f"{base2}/feedback", headers=H(tok_psi),
                         json={"veredicto": "aceptado"})
        assert r.status_code == 200, (r.status_code, r.text)
        m = r.json()["metricas"]
        assert (m["aceptados"], m["rechazados"], m["revisados"]) == (1, 1, 2), m
        assert m["tasa_acierto"] == 0.5, m["tasa_acierto"]
        print("3. Conteo: 1 aceptado / 1 descartado / 50% ........... OK")

        # 4. Cambiar de opinion reemplaza, no suma otro registro.
        r = await c.post(f"{base}/feedback", headers=H(tok_psi),
                         json={"veredicto": "aceptado"})
        m = r.json()["metricas"]
        assert (m["aceptados"], m["rechazados"]) == (2, 0), m
        assert m["revisados"] == 2, m
        print("4. Cambiar de opinion reemplaza, no suma ............. OK")

        # 5. Deshacer devuelve el resultado a sin juzgar.
        r = await c.delete(f"{base}/feedback", headers=H(tok_psi))
        assert r.status_code == 200, (r.status_code, r.text)
        m = r.json()["metricas"]
        assert m["revisados"] == 1 and m["sin_revisar"] == 1, m
        print("5. Deshacer el veredicto ............................. OK")

        # 6. El veredicto persiste al recargar el resultado.
        d = (await c.get(f"{base2}/resultado", headers=H(tok_psi))).json()
        assert d["feedback"]["veredicto"] == "aceptado", d["feedback"]
        d = (await c.get(f"{base}/resultado", headers=H(tok_psi))).json()
        assert d["feedback"] is None, d["feedback"]
        print("6. El veredicto persiste al recargar ................. OK")

        # 7. Metricas globales con desglose por nivel de riesgo.
        m = (await c.get("/api/v1/psychologist/metricas-clasificador",
                         headers=H(tok_psi))).json()
        assert m["aceptados"] == 1 and m["rechazados"] == 0, m
        assert m["total_evaluados"] == 2, m
        riesgos = {x["riesgo"] for x in m["por_riesgo"]}
        assert riesgos == {"BAJO"}, riesgos
        print("7. Metricas globales y desglose por riesgo ........... OK")

        # 8. Una psicologa ajena no puede votar sobre esta aplicacion.
        r = await c.post(f"{base}/feedback", headers=H(tok_otra),
                         json={"veredicto": "rechazado"})
        assert r.status_code == 400, (r.status_code, r.text)
        assert "acceso" in r.text.lower(), r.text
        print("8. Una psicologa ajena no puede votar ................ OK")

        # 9. Veredicto invalido y aplicacion inexistente se rechazan.
        r = await c.post(f"{base}/feedback", headers=H(tok_psi),
                         json={"veredicto": "quiza"})
        assert r.status_code == 400, (r.status_code, r.text)
        r = await c.post("/api/v1/cuestionarios/aplicacion/99999/feedback",
                         headers=H(tok_psi), json={"veredicto": "aceptado"})
        assert r.status_code == 400, (r.status_code, r.text)
        print("9. Veredicto invalido y aplicacion inexistente ....... OK")

        print("\nTODO OK - el feedback del clasificador funciona.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        if os.path.exists(DB):
            os.remove(DB)
