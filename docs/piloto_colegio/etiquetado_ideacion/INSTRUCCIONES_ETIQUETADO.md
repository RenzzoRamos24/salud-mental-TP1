# Etiquetado de ideación suicida — instrucciones

Gracias por ayudarnos con esto. El objetivo es tener un criterio clínico
independiente contra el cual medir el clasificador automático de Sami.

## Qué hay en el archivo

`frases_para_etiquetar.csv` — 100 frases incompletas del piloto, completadas
por estudiantes de 4to y 5to de secundaria. Cada fila tiene:

| Columna | Qué hacer |
|---|---|
| `id` | No tocar. Es el código interno de la frase. |
| `texto` | La frase completa: el estímulo y lo que escribió el estudiante. |
| `ideacion_presente` | **Completar.** `1` si la frase expresa ideación suicida según criterio clínico, `0` si no. |
| `confianza` | **Opcional.** `alta`, `media` o `baja`, según qué tan clara le parezca la frase. |

Se puede abrir en Excel o Google Sheets. Al guardar, mantener el formato CSV
y no cambiar el orden ni los nombres de las columnas.

## Criterio

Marcar `1` cuando la frase exprese, de forma explícita o razonablemente
inequívoca, alguna de estas:

- Deseo de morir, de no existir o de desaparecer.
- Pensamientos sobre la propia muerte o sobre quitarse la vida.
- Intención, plan o método de autolesión con fin suicida.
- Autolesión con intención de morir.

Marcar `0` en todo lo demás, incluyendo tristeza, desesperanza, ansiedad,
cansancio, autolesión sin intención suicida, o expresiones intensas que no
apunten a la muerte. **Tristeza severa sin referencia a morir es `0`.**

Si duda, marque su mejor juicio y ponga `confianza = baja`. Preferimos una
etiqueta con confianza baja a una fila vacía.

## Cosas importantes

- **Etiquete cada frase por sí sola.** No intente reconstruir de qué
  estudiante viene ni relacionarla con otras: el orden está deliberadamente
  mezclado y las frases del mismo alumno no están juntas.
- **No verá ninguna predicción del sistema**, y es a propósito. Si el
  etiquetado se hiciera viendo lo que el modelo predijo, la comparación
  posterior no valdría como validación independiente.
- Las frases vienen de estudiantes reales del piloto. Si alguna le parece
  clínicamente urgente, avísenos aparte del archivo — el `id` permite
  identificar al estudiante desde el sistema.

## Cuando termine

Devolver el CSV con las columnas completas. Con eso se calcula la matriz de
confusión y el recall del clasificador (`scripts/eval_ideacion_recall.py`).
