"""Desglose por subescala DASS-21 sobre el Pack B del piloto (datos reales de la BD)."""
import sqlite3
import statistics as st

SUB = {
    "Depresion": [3, 5, 10, 13, 16, 17, 21],
    "Ansiedad":  [2, 4, 7, 9, 15, 19, 20],
    "Estres":    [1, 6, 8, 11, 12, 14, 18],
}
# Cortes Lovibond & Lovibond (1995) sobre puntaje x2
BANDAS = {
    "Depresion": [(9, "Normal"), (13, "Leve"), (20, "Moderado"), (27, "Severo"), (99, "Ext. severo")],
    "Ansiedad":  [(7, "Normal"), (9, "Leve"), (14, "Moderado"), (19, "Severo"), (99, "Ext. severo")],
    "Estres":    [(14, "Normal"), (18, "Leve"), (25, "Moderado"), (33, "Severo"), (99, "Ext. severo")],
}
ORDEN = ["Normal", "Leve", "Moderado", "Severo", "Ext. severo"]


def banda(sub, x):
    for techo, nombre in BANDAS[sub]:
        if x <= techo:
            return nombre


def alpha_cronbach(matriz):
    """matriz: lista de filas (sujetos), cada una lista de items."""
    k = len(matriz[0])
    cols = list(zip(*matriz))
    var_items = sum(st.variance(c) for c in cols)
    var_total = st.variance([sum(f) for f in matriz])
    return (k / (k - 1)) * (1 - var_items / var_total)


c = sqlite3.connect("mental_health.db")
apps = [r[0] for r in c.execute(
    "SELECT id FROM aplicacion_cuestionario WHERE plantilla_id=5 AND estado='completado'")]

sujetos = []
for aid in apps:
    resp = {}
    for origen, val in c.execute(
            "SELECT origen, valor_num FROM respuesta_aplicacion "
            "WHERE aplicacion_id=? AND origen LIKE 'INSTR:DASS-21:%'", (aid,)):
        if val is not None:
            resp[int(origen.rsplit(":", 1)[1])] = val
    if len(resp) == 21:
        sujetos.append(resp)

n = len(sujetos)
print(f"Aplicaciones Pack B completadas: {len(apps)}")
print(f"Con las 21 respuestas completas: {n}\n")

print(f"{'Subescala':<12}{'M':>7}{'DE':>7}{'Mdn':>6}{'Min':>5}{'Max':>5}{'alpha':>8}{'>=Mod':>9}")
print("-" * 60)
resumen = {}
for sub, items in SUB.items():
    matriz = [[s[i] for i in items] for s in sujetos]
    puntajes = [sum(f) * 2 for f in matriz]
    bandas = [banda(sub, p) for p in puntajes]
    mod = sum(1 for b in bandas if b in ("Moderado", "Severo", "Ext. severo"))
    a = alpha_cronbach(matriz)
    resumen[sub] = (puntajes, bandas, a)
    print(f"{sub:<12}{st.mean(puntajes):>7.2f}{st.stdev(puntajes):>7.2f}"
          f"{st.median(puntajes):>6.1f}{min(puntajes):>5}{max(puntajes):>5}"
          f"{a:>8.3f}{mod:>5} ({mod/n*100:>4.1f}%)")

print("\nDistribucion por banda de severidad (n = %d)" % n)
print(f"{'Subescala':<12}" + "".join(f"{b:>14}" for b in ORDEN))
print("-" * 82)
for sub in SUB:
    _, bandas, _ = resumen[sub]
    fila = f"{sub:<12}"
    for b in ORDEN:
        k = bandas.count(b)
        fila += f"{k:>7} ({k/n*100:>4.1f}%)"
    print(fila)

# escala total (21 items) para alpha global
matriz_tot = [[s[i] for i in range(1, 22)] for s in sujetos]
print(f"\nAlpha de Cronbach escala total (21 items): {alpha_cronbach(matriz_tot):.3f}")

# item critico #21
crit = sum(1 for s in sujetos if s[21] >= 1)
print(f"Item 21 ('la vida no tenia ningun sentido') >= 1: {crit}/{n} ({crit/n*100:.1f}%)")

# cuantos en riesgo por cualquier subescala
riesgo = sum(1 for i in range(n)
             if any(resumen[s][1][i] in ("Moderado", "Severo", "Ext. severo") for s in SUB))
print(f"En riesgo por al menos una subescala (>= Moderado): {riesgo}/{n} ({riesgo/n*100:.1f}%)")

# solapamiento entre subescalas
combo = {}
for i in range(n):
    key = tuple(sorted(s for s in SUB if resumen[s][1][i] in ("Moderado", "Severo", "Ext. severo")))
    combo[key] = combo.get(key, 0) + 1
print("\nCombinaciones de subescalas en zona de alerta:")
for k, v in sorted(combo.items(), key=lambda x: -x[1]):
    print(f"  {' + '.join(k) if k else '(ninguna)':<40} {v:>3} ({v/n*100:.1f}%)")
