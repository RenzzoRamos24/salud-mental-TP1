"""
Diagnostica (y opcionalmente repara) la asignación del piloto en Azure.

Problema que resuelve
---------------------
`PsychologistService.listar_estudiantes` filtra por `User.psicologo_id`.
Si los alumnos del piloto quedaron sin psicóloga o asignados a otra cuenta,
el panel clínico aparece vacío aunque las 102 aplicaciones estén cargadas.

Uso
---
    # Solo mirar, no toca nada
    venv/bin/python scripts/diagnostico_piloto_azure.py

    # Mirar y reparar (reasigna el piloto a la psicóloga indicada)
    venv/bin/python scripts/diagnostico_piloto_azure.py --reparar

    # Contra otra instancia / con otras credenciales
    venv/bin/python scripts/diagnostico_piloto_azure.py \
        --api http://127.0.0.1:8000/api/v1 \
        --admin-email admin@admin.com --admin-password '...' \
        --psicologa psicologa@demo.pe
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_DEFAULT = "https://sami-app-9921877.azurewebsites.net/api/v1"


def _pedir(url, token=None, metodo="GET", cuerpo=None, timeout=120):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        detalle = e.read().decode()[:300]
        raise SystemExit(f"HTTP {e.code} en {url}\n  {detalle}")
    except urllib.error.URLError as e:
        raise SystemExit(f"No se pudo conectar a {url}\n  {e.reason}")


def _login(api, email, password):
    r = _pedir(f"{api}/auth/login", metodo="POST",
               cuerpo={"email": email, "password": password})
    tok = (r or {}).get("access_token")
    if not tok:
        raise SystemExit(f"Login falló para {email} (sin access_token).")
    return tok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--api", default=os.getenv("SAMI_API", API_DEFAULT))
    ap.add_argument("--admin-email", default=os.getenv("SAMI_ADMIN_EMAIL", "admin@admin.com"))
    ap.add_argument("--admin-password", default=os.getenv("SAMI_ADMIN_PASSWORD", "Admin12345"))
    ap.add_argument("--psicologa", default=os.getenv("SAMI_PSICOLOGA", "psicologa@demo.pe"),
                    help="Email de la psicóloga que debe quedar como responsable.")
    ap.add_argument("--reparar", action="store_true",
                    help="Ejecuta la reasignación. Sin este flag solo diagnostica.")
    args = ap.parse_args()

    print(f"API: {args.api}\n")

    # ── 1. Login admin ───────────────────────────────────────────────────
    print("[1] Autenticando como admin…")
    token = _login(args.api, args.admin_email, args.admin_password)
    print("    OK\n")

    # ── 2. Inventario de usuarios ────────────────────────────────────────
    print("[2] Usuarios en el sistema")
    usuarios = _pedir(f"{args.api}/admin/users", token) or []
    por_rol = {}
    for u in usuarios:
        por_rol.setdefault(u.get("role", "?"), []).append(u)
    for rol, lista in sorted(por_rol.items()):
        print(f"    {rol:12} {len(lista)}")

    psicologas = por_rol.get("psicologo", [])
    if not psicologas:
        raise SystemExit("\n  No hay ninguna psicóloga registrada en esta instancia.\n"
                         "  Registrá una en /register con rol Psicólogo/a y reintentá.")
    print("\n    Psicólogas registradas:")
    for p in psicologas:
        print(f"      - {p.get('email')}  ({p.get('nombre','')} {p.get('apellido','')})")

    objetivo = next((p for p in psicologas
                     if (p.get("email") or "").lower() == args.psicologa.lower()), None)
    if not objetivo:
        raise SystemExit(f"\n  No existe la psicóloga '{args.psicologa}' en esta instancia.\n"
                         f"  Usá --psicologa con uno de los emails de arriba.")

    # ── 3. Reparto de alumnos por psicóloga ──────────────────────────────
    print("\n[3] Alumnos por psicóloga responsable")
    estudiantes = [u for u in usuarios if u.get("role") == "estudiante"]
    email_por_id = {p.get("id"): p.get("email") for p in psicologas}
    reparto = {}
    for e in estudiantes:
        pid = e.get("psicologo_id")
        clave = email_por_id.get(pid, "(SIN ASIGNAR)" if not pid else f"(id {pid})")
        reparto[clave] = reparto.get(clave, 0) + 1
    if not reparto:
        print("    No hay estudiantes cargados en esta instancia.")
    for clave, n in sorted(reparto.items(), key=lambda x: -x[1]):
        print(f"    {clave:32} {n}")

    asignados_objetivo = reparto.get(args.psicologa, 0)

    # ── 4. Aplicaciones de cuestionario ──────────────────────────────────
    print("\n[4] Cuestionarios")
    try:
        stats = _pedir(f"{args.api}/admin/cuestionarios/stats", token) or {}
        for k, v in stats.items():
            if not isinstance(v, (dict, list)):
                print(f"    {k}: {v}")
    except SystemExit as e:
        print(f"    (no disponible: {e})")

    # ── 5. Veredicto ─────────────────────────────────────────────────────
    print("\n" + "=" * 62)
    if not estudiantes:
        print("DIAGNÓSTICO: no hay alumnos cargados en esta instancia.")
        print("El piloto nunca se cargó acá. Hay que correr:")
        print("  venv/bin/python scripts/cargar_piloto_colegio.py")
        print("apuntando DATABASE_URL a esta base.")
        return

    if asignados_objetivo > 0:
        print(f"DIAGNÓSTICO: {args.psicologa} ya tiene {asignados_objetivo} alumnos.")
        print("Si aun así ves el panel vacío, el problema es otro")
        print("(sesión vieja, caché del navegador o alumnos inactivos).")
        return

    print(f"DIAGNÓSTICO: hay {len(estudiantes)} alumnos, pero NINGUNO")
    print(f"tiene a {args.psicologa} como responsable.")
    print("Por eso el panel sale vacío: listar_estudiantes filtra por psicologo_id.")

    if not args.reparar:
        print("\nPara repararlo, volvé a correr con --reparar")
        return

    # ── 6. Reparación ────────────────────────────────────────────────────
    print("\n[6] Reasignando el piloto…")
    r = _pedir(f"{args.api}/admin/piloto/reasignar-a-psicologo", token, metodo="POST",
               cuerpo={"psicologo_email": args.psicologa, "solo_piloto": True})
    print(f"    estudiantes reasignados : {r.get('estudiantes_reasignados')}")
    print(f"    aplicaciones reasignadas: {r.get('aplicaciones_reasignadas')}")

    if not r.get("estudiantes_reasignados"):
        print("\n    0 reasignados — no se encontraron aplicaciones con plantilla")
        print("    'Piloto Colegio%'. Puede que las plantillas tengan otro nombre")
        print("    en esta base. Revisá el listado de plantillas.")
        return

    print("\n    Listo. Cerrá sesión y volvé a entrar como la psicóloga.")


if __name__ == "__main__":
    sys.exit(main())
