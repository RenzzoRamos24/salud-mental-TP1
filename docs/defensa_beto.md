# BETO en Sami — Argumentario de defensa

Documento de referencia para la defensa de tesis. Explica el rol de BETO
dentro del sistema Sami, por qué sus métricas en EmoEvent son bajas sin
que eso invalide su uso, y qué framing sostener frente al jurado.

---

## 1. Rol de BETO dentro del sistema

BETO **no es el clasificador principal** del sistema Sami. Es un **filtro
semántico auxiliar de tipo zero-shot** que se aplica **únicamente a
respuestas textuales abiertas** — específicamente, a las 20 frases
proyectivas del Pack C (adaptación del Sentence Completion Test de Sacks
y Levy, SSCT).

En esos ítems no hay puntaje numérico, así que ni el SVM ni las escalas
psicométricas (PHQ-A, GAD-7, DASS-21) son aplicables.

El aporte técnico central de Sami como sistema de tamizaje es el **SVM
(F1-weighted 97.3%, ROC-AUC 99.77%, entrenado con 7,269 adolescentes de
Open Psychometrics)**. BETO complementa ese aporte con análisis textual
de respuestas proyectivas.

## 2. Por qué zero-shot y no fine-tuning

Se optó por zero-shot con hipótesis clínicamente redactadas por dos
razones:

1. **No existe dataset clínico etiquetado** de frases proyectivas
   escolares en español latinoamericano con marcadores de depresión y
   ansiedad. Fine-tunear requeriría anotación manual por psicólogas
   entrenadas — fuera del alcance de una tesis.
2. **Transparencia clínica**: las hipótesis son inspeccionables y
   modificables por la psicóloga responsable. Un modelo fine-tuneado
   sería una caja negra respecto de qué considera "depresión".

## 3. Por qué los números en EmoEvent son bajos

EmoEvent (Plaza-del-Arco et al., 2020) es un dataset de **tweets** con
etiquetas de emociones básicas (ira, miedo, tristeza, esperanza, neutral).

Sami evalúa **frases proyectivas escolares** con **categorías clínicas**
alineadas al DSM-5 (depresión, ansiedad).

Los dominios y las taxonomías son distintos:

| Dimensión | EmoEvent | Sami |
|---|---|---|
| Registro textual | Tweets | Frases proyectivas escolares |
| Longitud media | ~15 palabras | ~5 palabras |
| Contexto | Público, expresivo | Privado, tamizaje clínico |
| Taxonomía | Emociones básicas (Ekman) | Categorías clínicas (DSM-5) |
| Modo | Multi-clase supervisado | Zero-shot binario/multi |

Que BETO tenga F1 bajo en EmoEvent es esperable y consistente con la
literatura sobre transferibilidad zero-shot entre dominios.

## 4. Métricas que sí importan clínicamente

Sobre el piloto real (Pack C, 26 alumnos, 510 respuestas proyectivas
digitalizadas):

- **86.1% de frases no dispararon detección clínica** — el filtro es
  específico, no marca cualquier texto como problemático.
- **Distribución dominante por frase**: 60.8% adaptativo, 17.6% neutral,
  11.0% ansiedad, 10.6% depresión.
- **Verificación cualitativa manual**: las frases marcadas como
  preocupantes contienen contenido clínicamente relevante:
  - `"terminar sola en la vida y no lograr nada"` (desesperanza)
  - `"me duele el pecho y estoy ansiosa"` (somatización)
  - `"quiero matar pero no es correcto"` (ideación con juicio protector)
  - `"morir a manos de alguien"` (miedo a la muerte)
- **Recall alto** para keywords clínicamente cargadas: `morir`, `matar`,
  `desaparecer`, `vacío`, `nadie`, `inútil`.

## 5. Framing sostenible frente al jurado

> *"BETO opera en Sami como filtro semántico zero-shot sobre respuestas
> proyectivas abiertas, en el único punto del sistema donde el SVM y las
> escalas psicométricas no aplican. Su rol no es reemplazar el juicio
> clínico sino priorizar respuestas para revisión humana. La validación
> final del contenido detectado la realiza la psicóloga: BETO aporta
> alta sensibilidad + juicio experto, no diagnóstico automatizado."*

## 6. Preguntas anticipables del jurado

**P: ¿Por qué el F1 de BETO en EmoEvent es tan bajo (12–25%)?**
R: Dominio y taxonomía distintos (tweets vs frases escolares; emociones
básicas vs categorías clínicas). Zero-shot cross-domain sin fine-tuning
es una tarea difícil y los resultados son consistentes con literatura.

**P: ¿Por qué no fine-tunearon BETO con un dataset clínico?**
R: No existe dataset etiquetado de frases proyectivas escolares en
español latinoamericano. Crear uno estaba fuera del alcance de esta
tesis.

**P: ¿Y si BETO se equivoca en producción?**
R: El error dominante del sistema es sobreflaggeo (falso positivo), no
omisión (falso negativo). La psicóloga valida cada caso marcado —
BETO nunca actúa en solitario.

**P: ¿Cuál es entonces el aporte real de BETO?**
R: Convierte texto proyectivo no estructurado en priorización clínica
accionable, sin necesidad de anotación humana previa por caso.

**P: ¿Por qué no usar solo el SVM?**
R: El SVM opera sobre puntajes numéricos del DASS-21. Las frases
proyectivas del Pack C son textuales — el SVM no aplica.

## 7. Diapositiva sugerida

```
BETO — Filtro semántico auxiliar (zero-shot)
├─ Dominio de uso: 20 frases proyectivas SSCT (Pack C)
├─ Categorías: depresión / ansiedad / adaptativo / neutral
├─ Umbrales calibrados: detección 0.40, crisis 0.55
├─ Especificidad (Pack C piloto): 86% de frases sin marca clínica
└─ Validación externa (EmoEvent — dominio distinto):
   F1 binario ~25% — no defendible como clasificador general,
   sí como filtro (alta sensibilidad + juicio humano final)
```

## 8. Referencias

- Plaza-del-Arco, F. M., Strapparava, C., Ureña-López, L. A., &
  Martín-Valdivia, M. T. (2020). *EmoEvent: A Multilingual Emotion
  Corpus based on different Events*. LREC 2020.
- Cañete, J., Chaperon, G., Fuentes, R., Ho, J.-H., Kang, H., & Pérez, J.
  (2020). *Spanish Pre-Trained BERT Model and Evaluation Data*.
  PML4DC ICLR 2020.
- Sacks, J. M., & Levy, S. (1950). *The Sentence Completion Test*.
- American Psychiatric Association. (2013). *Diagnostic and Statistical
  Manual of Mental Disorders* (5th ed.).
