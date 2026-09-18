"""Feedback de la psicologa sobre las clasificaciones de BETO.

Cubre el ciclo completo por HTTP: aceptar, descartar, cambiar de opinion,
deshacer, y que los conteos y las metricas globales cuadren. Tambien que
una psicologa ajena no pueda votar sobre una aplicacion que no es suya.

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
        apl = AplicacionCuestionario(
            plantilla_id=pl.id, estudiante_id=id_alu, psicologo_id=id_psi,
            estado="completado", resultado_json=json.dumps(RESULTADO),
            riesgo_global="CRITICO", crisis_activada=True)
        db.add(apl); db.commit(); db.refresh(apl)
        aid = apl.id
        db.close()

        base = f"/api/v1/cuestionarios/aplicacion/{aid}"

        # 1. Al principio no hay ningun veredicto.
        r = await c.get(f"{base}/resultado", headers=H(tok_psi))
        assert r.status_code == 200, (r.status_code, r.text)
        d = r.json()
        assert d["frases_feedback"] == {}, d["frases_feedback"]
        assert d["frases_resumen"]["sin_revisar"] == 3, d["frases_resumen"]
        print("1. Sin veredictos, las 3 frases salen sin revisar ..... OK")

        # 2. Descartar la clasificacion incorrecta ("duermo" -> depresion).
        r = await c.post(f"{base}/frases/1/feedback", headers=H(tok_psi),
                         json={"veredicto": "rechazado",
                               "comentario": "responde literal, no hay malestar"})
        assert r.status_code == 200, (r.status_code, r.text)
        res = r.json()["resumen"]
        assert (res["rechazados"], res["aceptados"]) == (1, 0), res
        print("2. Descartar una clasificacion incorrecta ............ OK")

        # 3. Aceptar las otras dos.
        for n in (5, 21):
            r = await c.post(f"{base}/frases/{n}/feedback", headers=H(tok_psi),
                             json={"veredicto": "aceptado"})
            assert r.status_code == 200, (r.status_code, r.text)
        res = r.json()["resumen"]
        assert (res["aceptados"], res["rechazados"], res["sin_revisar"]) == (2, 1, 0), res
        assert res["tasa_acierto"] == 0.6667, res["tasa_acierto"]
        print("3. Conteo: 2 aceptadas / 1 descartada / 66.67% ....... OK")

        # 4. Cambiar de opinion no duplica el registro.
        r = await c.post(f"{base}/frases/1/feedback", headers=H(tok_psi),
                         json={"veredicto": "aceptado"})
        res = r.json()["resumen"]
        assert (res["aceptados"], res["rechazados"]) == (3, 0), res
        assert res["revisadas"] == 3, res
        print("4. Cambiar de opinion reemplaza, no suma ............. OK")

        # 5. Deshacer devuelve la frase a sin revisar.
        r = await c.delete(f"{base}/frases/1/feedback", headers=H(tok_psi))
        assert r.status_code == 200, (r.status_code, r.text)
        res = r.json()["resumen"]
        assert res["sin_revisar"] == 1 and res["revisadas"] == 2, res
        print("5. Deshacer el veredicto ............................. OK")

        # 6. El estado persiste al recargar el resultado.
        d = (await c.get(f"{base}/resultado", headers=H(tok_psi))).json()
        assert set(d["frases_feedback"].keys()) == {"5", "21"}, d["frases_feedback"]
        print("6. El estado persiste al recargar .................... OK")

        # 7. Metricas globales de la psicologa.
        m = (await c.get("/api/v1/psychologist/metricas-clasificador",
                         headers=H(tok_psi))).json()
        assert m["aceptados"] == 2 and m["rechazados"] == 0, m
        assert m["tasa_acierto"] == 1.0, m
        cats = {x["categoria"] for x in m["por_categoria"]}
        assert cats == {"neutral", "ansiedad"}, cats
        print("7. Metricas globales y desglose por categoria ........ OK")

        # 8. Una psicologa ajena no puede votar sobre esta aplicacion.
        r = await c.post(f"{base}/frases/5/feedback", headers=H(tok_otra),
                         json={"veredicto": "rechazado"})
        assert r.status_code == 400, (r.status_code, r.text)
        assert "acceso" in r.text.lower(), r.text
        print("8. Una psicologa ajena no puede votar ................ OK")

        # 9. Veredicto invalido y frase inexistente se rechazan.
        r = await c.post(f"{base}/frases/5/feedback", headers=H(tok_psi),
                         json={"veredicto": "quiza"})
        assert r.status_code == 400, (r.status_code, r.text)
        r = await c.post(f"{base}/frases/999/feedback", headers=H(tok_psi),
                         json={"veredicto": "aceptado"})
        assert r.status_code == 400, (r.status_code, r.text)
        print("9. Veredicto invalido y frase inexistente rechazados .. OK")

        print("\nTODO OK - el feedback del clasificador funciona.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        if os.path.exists(DB):
            os.remove(DB)
