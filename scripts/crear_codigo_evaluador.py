"""
Emite un código de acceso para un psicólogo evaluador.

Por qué un script y no un curl
------------------------------
El endpoint pide un JWT de admin, así que un curl a mano son tres pasos y es
fácil equivocarse en el medio. Acá se pasa la clave por entorno, nunca se
imprime, y la salida dice exactamente qué hacer con el código.

Sobre `--hereda-de`: NO hace falta para etiquetar. Las colas de etiquetado
leen todas las aplicaciones evaluadas sin filtrar por psicólogo, así que un
evaluador ve los casos sin que nadie le transfiera alumnos. Y heredar NO
copia: **reasigna** — les cambia el `psicologo_id` a los alumnos, que
desaparecen del panel de la psicóloga titular. Por eso está apagado por
defecto y hay que pedirlo explícito. Úsalo solo si querés que el evaluador
vea además la bandeja de evaluaciones, que sí filtra por psicólogo.

Uso
---
    # Código de prueba, para recorrer el flujo sin ensuciar las métricas
    SAMI_ADMIN_PASSWORD='...' venv/bin/python scripts/crear_codigo_evaluador.py --prueba

    # Los dos códigos reales
    SAMI_ADMIN_PASSWORD='...' venv/bin/python scripts/crear_codigo_evaluador.py \
        --nombre Lucia --apellido Ramirez

    # Ver qué códigos ya se emitieron
    SAMI_ADMIN_PASSWORD='...' venv/bin/python scripts/crear_codigo_evaluador.py --listar
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_DEFAULT = "https://sami-app-9921877.azurewebsites.net/api/v1"


def pedir(url, token=None, cuerpo=None, metodo=None, timeout=180):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(
        url, data=datos,
        method=metodo or ("POST" if cuerpo is not None else "GET"),
    )
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        detalle = e.read().decode()[:400]
        if e.code in (401, 403):
            raise SystemExit(f"HTTP {e.code}: credenciales rechazadas.\n  {detalle}")
        raise SystemExit(f"HTTP {e.code} en {url}\n  {detalle}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Sin conexión a {url}\n  {e.reason}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=API_DEFAULT)
    ap.add_argument("--admin-email", default="admin@admin.com")
    ap.add_argument("--admin-password", default=os.environ.get("SAMI_ADMIN_PASSWORD"))
    ap.add_argument("--nombre", default="Evaluador")
    ap.add_argument("--apellido", default="de prueba")
    ap.add_argument("--prueba", action="store_true",
                    help="cuenta de ensayo: etiqueta igual, pero sus etiquetas "
                         "quedan fuera de todas las métricas")
    ap.add_argument("--hereda-de", metavar="EMAIL",
                    help="REASIGNA los alumnos de ese psicólogo al evaluador. "
                         "No hace falta para etiquetar; leé el docstring.")
    ap.add_argument("--listar", action="store_true",
                    help="solo mostrar los códigos ya emitidos")
    args = ap.parse_args()

    if not args.admin_password:
        raise SystemExit(
            "Falta la clave de admin. Pasala en SAMI_ADMIN_PASSWORD o con "
            "--admin-password."
        )

    tok = pedir(f"{args.api}/auth/login",
                cuerpo={"email": args.admin_email, "password": args.admin_password})
    T = tok["access_token"]

    if args.listar:
        d = pedir(f"{args.api}/admin/psicologo/codigos", T)
        print(f"Códigos de evaluador emitidos: {d['total']}\n")
        if not d["codigos"]:
            print("  (ninguno todavía)")
        for f in d["codigos"]:
            marca = "  [PRUEBA]" if f.get("es_prueba") else ""
            print(f"  {f['codigo_acceso']:24s} {f['nombre']:28s}"
                  f" alumnos={f['alumnos']:4d}{marca}")
        return

    cuerpo = {
        "nombre": args.nombre,
        "apellido": args.apellido,
        "es_prueba": bool(args.prueba),
    }
    if args.hereda_de:
        cuerpo["hereda_alumnos_de_email"] = args.hereda_de

    d = pedir(f"{args.api}/admin/psicologo/generar-codigo", T, cuerpo=cuerpo)

    base = args.api.replace("/api/v1", "")
    print("=" * 58)
    print(f"  CÓDIGO: {d['codigo_acceso']}")
    print("=" * 58)
    print(f"  Nombre   : {d['nombre']}")
    print(f"  Prueba   : {'sí — sus etiquetas NO entran en las métricas' if d.get('es_prueba') else 'no, es una cuenta real'}")
    if d.get("alumnos_heredados"):
        print(f"  Heredó   : {d['alumnos_heredados']} alumnos, "
              f"{d['aplicaciones_heredadas']} aplicaciones")
    print()
    print("  Cómo entra:")
    print(f"    1. {base}/codigo")
    print(f"    2. escribe {d['codigo_acceso']}")
    print("    3. acepta el acuerdo de confidencialidad (primera vez)")
    print("    4. en el menú de arriba: Etiquetar")
    print()
    print("  Qué va a ver:")
    print("    · Frases incompletas — una por pantalla, dos preguntas")
    print("      (atajos: 1-4 categoría, S/N ideación, Enter guarda)")
    print(f"    · Casos completos — {base}/etiquetado/casos")
    print("    · Nada de lo que predijo el modelo, a propósito")

    # Chequeo del corte: si no está puesto, el evaluador vería el piloto viejo.
    try:
        corte = pedir(f"{args.api}/etiquetado/corte", T)
        print()
        if corte.get("desde"):
            print(f"  Corte de cohorte vigente: solo evaluaciones desde "
                  f"{corte['desde']}")
        else:
            print("  ATENCIÓN: no hay corte de cohorte. El evaluador va a ver")
            print("  también el piloto viejo. Ponelo en /etiquetado/metricas.")
    except SystemExit:
        print()
        print("  (no pude leer el corte de cohorte — ¿versión vieja desplegada?)")


if __name__ == "__main__":
    main()
