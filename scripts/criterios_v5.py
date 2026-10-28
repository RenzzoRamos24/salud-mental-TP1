# -*- coding: utf-8 -*-
"""
Criterios de aceptación de la versión 5 del backlog (octubre 2026).

Extiende `criterios_aceptacion.py` (la v4) sin modificarlo, para que
`generar_backlog_v4.py` siga reproduciendo exactamente la v4 de septiembre.

Cambios respecto de la v4, todos verificados contra el código desplegado:

  1. Seis HU nuevas (HU-76 … HU-81): funciones que el sistema ganó en octubre
     y que no tenían historia. Cinco salieron de la prueba de usabilidad
     OBS-SW-23 de la psicóloga y la sexta es el módulo de evaluación clínica
     ciega, que es la base de la validación de la tesis.
  2. HU-09 corregida: BETO corre con 4 categorías y softmax (una sola
     categoría dominante), no con 8 categorías multietiqueta.
  3. HU-48 y HU-49 descartadas: el SVM de DASS-21 nunca emitió predicciones
     en producción y la tarjeta de segunda opinión se retiró de la interfaz.
"""
import copy

from scripts.criterios_aceptacion import (
    CRITERIOS as _CRITERIOS_V4,
    ESTADO as _ESTADO_V4,
    OK,
    PARCIAL,  # noqa: F401  (se reexporta para los generadores)
    NO,  # noqa: F401
)

DESCARTADA = "Descartada"

CRITERIOS = copy.deepcopy(_CRITERIOS_V4)
ESTADO = dict(_ESTADO_V4)


def _hu(hu_id, estado, *escenarios):
    ESTADO[hu_id] = estado
    CRITERIOS[hu_id] = [{"titulo": t, "pasos": list(p)} for t, p in escenarios]


SPRINT_12 = "Sprint 12"
OBJETIVO_SPRINT_12 = (
    "Validación clínica ciega y ajustes de la prueba de usabilidad\n\n"
    "Módulo de evaluación clínica ciega (evaluadoras que entran por código, "
    "panel bloqueado hasta terminar la cohorte), asignación de cuestionarios "
    "por salón, tope de 26 preguntas por cuestionario, selección de frases "
    "puntuales, equipo psicopedagógico y restablecimiento de contraseñas por "
    "el administrador."
)
FOCO_SPRINT_12 = "Validación clínica ciega + ajustes de la prueba de usabilidad (octubre 2026)"

# Épicas: una nueva para la validación y el nombre de la del SVM actualizado.
EPICAS_V5 = {
    "EPICA0007": ("SVM como segunda opinión sobre DASS-21 — descartada en producción "
                  "(su validación contra criterio clínico se reporta offline en el paper)"),
    "EPICA0010": "Validación clínica ciega del sistema (patrón de oro de la psicóloga)",
}


# ═══════════════════════════════════════════════════════════════════════
# Ajustes a HU existentes
# ═══════════════════════════════════════════════════════════════════════

AJUSTES_V5 = {
    "HU-09": dict(
        historia=("Como Sistema quiero clasificar las respuestas abiertas (frases "
                  "incompletas SSCT) con BETO zero-shot en 4 categorías (depresión, "
                  "ansiedad, adaptativo y neutral) para detectar señales sin diagnosticar"),
        notas=("Corregida en v5. BETO zero-shot (Recognai/bert-base-spanish-wwm-cased-xnli) "
               "con softmax entre 4 categorías (multi_label=False). Una categoría clínica "
               "se detecta solo si domina y supera 0.40; la bandera de crisis exige "
               "depresión dominante ≥ 0.55. La taxonomía de 8 categorías se retiró en "
               "el commit 6850641."),
    ),
    "HU-48": dict(
        notas=("DESCARTADA en v5. El SVM de DASS-21 nunca emitió predicciones en "
               "producción: la plantilla del colegio aplica PHQ-A + GAD-7, no DASS-21. "
               "Además su F1 de 0.92 era circular (la etiqueta salía de las propias "
               "features). El SVM contra el criterio clínico de la psicóloga se reporta "
               "como validación offline en el paper, no como función del sistema."),
    ),
    "HU-49": dict(
        notas=("DESCARTADA en v5. La tarjeta de segunda opinión se retiró de la vista "
               "de resultado (prueba de usabilidad T-P7): sin SVM desplegado aparecía "
               "siempre vacía."),
    ),
}

ESTADO["HU-48"] = DESCARTADA
ESTADO["HU-49"] = DESCARTADA

# HU-67, escenario 2: en la v4 el «Cuando» mezclaba acción y resultado y el
# resultado quedaba en un «Y» sin «Entonces». Mismo contenido, Gherkin válido.
CRITERIOS["HU-67"][1] = {
    "titulo": "Consulta y desvinculación",
    "pasos": [
        "Dado que el estudiante ya tiene un padre vinculado",
        "Y abro su ficha y veo qué cuenta de padre está vinculada",
        "Cuando desvinculo al padre",
        "Entonces el sistema responde 204",
        "Y el padre pierde el acceso al seguimiento del estudiante",
    ],
}

_hu("HU-09", OK,
    ("Clasificación de una frase incompleta con BETO", [
        "Dado que el estudiante completó una frase incompleta",
        "Cuando el sistema procesa la respuesta abierta",
        "Entonces BETO zero-shot devuelve un puntaje para cada una de las 4 "
        "categorías: depresión, ansiedad, adaptativo y neutral",
        "Y los puntajes compiten entre sí y suman 1 (softmax), no son multietiqueta",
    ]),
    ("Detección por categoría dominante", [
        "Dado los puntajes de una frase",
        "Cuando una categoría clínica (depresión o ansiedad) es la de mayor puntaje "
        "y supera 0.40",
        "Entonces esa categoría se marca como detectada",
        "Y si la categoría dominante es adaptativo o neutral no se marca ninguna "
        "señal clínica, aunque otra categoría supere 0.40",
    ]),
    ("Frase sin contenido", [
        "Dado que el estudiante dejó la frase vacía o solo con espacios",
        "Cuando el sistema procesa la respuesta",
        "Entonces la frase se omite de la clasificación y no genera señal",
    ]),
    ("El clasificador no emite diagnóstico", [
        "Dado cualquier conjunto de frases clasificadas",
        "Cuando se genera el reporte clínico",
        "Entonces el sistema muestra categorías y puntajes como señales",
        "Y en ningún caso emite un nombre de trastorno ni un diagnóstico",
    ]),
)


# ═══════════════════════════════════════════════════════════════════════
# HU nuevas (Sprint 12)
# ═══════════════════════════════════════════════════════════════════════

NUEVAS_HU_V5 = [
    dict(id="HU-76", rol="Psicólogo", epica="EPICA0006", sp=5, prio="Alta", sprint=SPRINT_12,
         historia=("Como Psicólogo quiero asignar un cuestionario a todo un salón de una "
                   "sola vez para aplicarlo en grupo durante la hora de tutoría"),
         notas=("POST /cuestionarios/asignar-grado (CuestionarioService.asignar_por_grado) "
                "y modo «Por salón» en la vista de asignar. Alcance: alumnos activos del "
                "grado a cargo de la psicóloga o de su equipo (HU-80). Una sola "
                "transacción; no duplica. Prueba de usabilidad T-P11.")),
    dict(id="HU-77", rol="Psicólogo", epica="EPICA0006", sp=3, prio="Alta", sprint=SPRINT_12,
         historia=("Como Psicólogo quiero que el sistema impida crear o asignar "
                   "cuestionarios de más de 26 preguntas para respetar el límite de "
                   "extensión definido para la aplicación en aula"),
         notas=("MAX_PREGUNTAS = 26 en plantilla_service: ítems de instrumentos + ítems "
                "custom + frases. Se valida en el backend al crear, editar y asignar, "
                "también para plantillas anteriores a la regla. El cuestionario del "
                "piloto (PHQ-A 9 + GAD-7 7 + 10 frases) suma exactamente 26. Pruebas "
                "de usabilidad T-P12 y T-P13.")),
    dict(id="HU-78", rol="Psicólogo", epica="EPICA0006", sp=3, prio="Media", sprint=SPRINT_12,
         historia=("Como Psicólogo quiero elegir frases incompletas puntuales del banco "
                   "cruzando áreas para armar el set validado de 10 frases sin traer "
                   "áreas completas"),
         notas=("PlantillaBloque.frases_numeros (números del banco de 40), con prioridad "
                "sobre frases_areas. Botón «Usar las 10 del piloto»: 1, 6, 11, 13, 17, "
                "22, 23, 25, 28 y 31. Prueba de usabilidad T-P2.")),
    dict(id="HU-79", rol="Administrador", epica="EPICA0004", sp=3, prio="Media", sprint=SPRINT_12,
         historia=("Como Administrador quiero fijar una contraseña nueva a cualquier cuenta "
                   "para restablecer el acceso de quien la olvidó sin conocer la anterior"),
         notas=("POST /admin/users/{id}/reset-password (hash bcrypt nuevo). Nunca muestra "
                "ni recupera la contraseña anterior. Las cuentas por código muestran "
                "«entra con código» en lugar del botón. Limitación conocida: la "
                "contraseña del propio admin vuelve al valor de ADMIN_PASSWORD en cada "
                "reinicio (seed_admin).")),
    dict(id="HU-80", rol="Administrador", epica="EPICA0004", sp=8, prio="Alta", sprint=SPRINT_12,
         historia=("Como Administrador quiero crear cuentas de psicóloga y sumarlas al "
                   "equipo psicopedagógico de una titular para que compartan el "
                   "seguimiento de los mismos alumnos"),
         notas=("POST /admin/psicologas + User.equipo_titular_id + equipo_service."
                "ids_equipo, aplicado en lista de alumnos, dashboard, alertas, ficha, "
                "resultado, revisado, asignar por salón, veredicto, reportes y "
                "satisfacción. Ningún alumno cambia de responsable. Plantillas, bloques "
                "custom, notas clínicas y agenda siguen siendo individuales.")),
    dict(id="HU-81", rol="Psicólogo", epica="EPICA0010", sp=8, prio="Alta", sprint=SPRINT_12,
         historia=("Como Psicólogo evaluador quiero evaluar a ciegas los casos de la "
                   "cohorte sin ver lo que calculó el sistema para que mi criterio "
                   "clínico sirva como patrón de oro de la validación"),
         notas=("Módulo de etiquetado (commit 5192e9d, 02-oct): cuentas SAMI-PSI-NN que "
                "entran por código, acuerdo de confidencialidad (Ley 29733), colas de "
                "casos y de frases, panel clínico bloqueado hasta terminar la cohorte. "
                "Las cuentas SAMI-PSI-PRUEBA guardan etiquetas pero quedan fuera de las "
                "métricas. Binarización de la etiqueta en riesgo ≥ MEDIO.")),
]

_hu("HU-76", OK,
    ("Asignación a todo el salón", [
        "Dado que tengo a mi cargo, o en mi equipo, alumnos activos de \"5to secundaria\"",
        "Y elijo una plantilla de 26 preguntas o menos",
        "Cuando selecciono el modo \"Por salón\", elijo \"5to secundaria\" y pulso "
        "\"Asignar a todo el salón\"",
        "Entonces el sistema crea una aplicación en estado \"pendiente\" para cada "
        "alumno activo de ese salón, en una sola operación",
        "Y me informa cuántos alumnos quedaron asignados",
        "Y cada alumno ve el cuestionario en su panel",
    ]),
    ("No se duplica a quien ya lo tiene", [
        "Dado que algunos alumnos del salón ya tienen esa plantilla pendiente o en curso",
        "Cuando asigno la plantilla al salón",
        "Entonces esos alumnos se omiten",
        "Y el sistema informa cuántos no se duplicaron",
    ]),
    ("Solo alumnos propios o del equipo", [
        "Dado que en el mismo grado hay alumnos a cargo de una psicóloga ajena a mi equipo",
        "Cuando asigno la plantilla al salón",
        "Entonces esos alumnos no reciben la asignación",
    ]),
    ("Salón sin alumnos a cargo", [
        "Dado que no tengo alumnos de ese grado a mi cargo ni en mi equipo",
        "Cuando intento asignar la plantilla al salón",
        "Entonces el sistema rechaza la operación indicando que no tengo alumnos de "
        "ese grado a mi cargo ni en mi equipo",
        "Y no se crea ninguna aplicación",
    ]),
    ("Asignación individual desde la ficha", [
        "Dado que entro a asignar un cuestionario desde la ficha de un estudiante",
        "Cuando se abre la pantalla de asignación",
        "Entonces aparece en modo \"Por alumno\" con ese estudiante preseleccionado",
    ]),
)

_hu("HU-77", OK,
    ("Conteo visible al armar la plantilla", [
        "Dado que estoy armando una plantilla",
        "Cuando agrego instrumentos, bloques custom o frases",
        "Entonces veo el total como \"N / 26 preguntas\"",
        "Y el total suma los ítems de los instrumentos, los ítems de los bloques "
        "custom y las frases",
    ]),
    ("Plantilla que supera el máximo", [
        "Dado que la plantilla suma más de 26 preguntas",
        "Cuando intento guardarla",
        "Entonces el contador se marca en rojo y aparece el aviso de que superé el máximo",
        "Y el botón \"Guardar\" queda deshabilitado",
        "Y si la solicitud llega igual al servidor, este la rechaza indicando cuántas "
        "preguntas tiene y el máximo permitido",
    ]),
    ("Plantilla en el límite", [
        "Dado una plantilla con PHQ-A, GAD-7 y las 10 frases del piloto (26 preguntas)",
        "Cuando la guardo",
        "Entonces se guarda sin advertencias",
        "Y se puede asignar a un alumno o a un salón",
    ]),
    ("Asignación de una plantilla que supera el máximo", [
        "Dado que existe una plantilla de más de 26 preguntas, incluso creada antes de "
        "esta regla",
        "Cuando intento asignarla a un alumno o a un salón",
        "Entonces en la lista aparece marcada como \"supera el máximo\"",
        "Y el sistema no permite asignarla y explica que hay que editarla",
    ]),
)

_hu("HU-78", OK,
    ("Selección de frases puntuales", [
        "Dado que estoy armando una plantilla",
        "Cuando marco frases por su número en el banco, agrupadas por área",
        "Entonces la plantilla guarda exactamente esas frases",
        "Y el estudiante responde solo esas frases, ordenadas por número",
    ]),
    ("Set del piloto en un clic", [
        "Dado que estoy armando una plantilla",
        "Cuando pulso \"Usar las 10 del piloto\"",
        "Entonces quedan seleccionadas las frases 1, 6, 11, 13, 17, 22, 23, 25, 28 y 31",
    ]),
    ("Las frases puntuales tienen prioridad sobre las áreas", [
        "Dado que elegí áreas de frases y además frases puntuales",
        "Cuando guardo la plantilla",
        "Entonces se usan solo las frases puntuales",
        "Y la pantalla avisa que las áreas se ignoran",
    ]),
    ("La edición conserva la selección", [
        "Dado una plantilla guardada con frases puntuales",
        "Cuando la abro para editarla",
        "Entonces veo seleccionadas las mismas frases",
    ]),
)

_hu("HU-79", OK,
    ("Restablecimiento exitoso", [
        "Dado que soy administrador y una psicóloga olvidó su contraseña",
        "Cuando pulso \"Restablecer contraseña\" en su fila, escribo la contraseña "
        "nueva dos veces y confirmo",
        "Entonces el sistema guarda un hash nuevo",
        "Y la psicóloga entra con la contraseña nueva",
        "Y la contraseña anterior deja de funcionar",
    ]),
    ("La contraseña anterior nunca se muestra", [
        "Dado cualquier cuenta con correo y contraseña",
        "Cuando abro el restablecimiento",
        "Entonces el sistema no muestra ni permite recuperar la contraseña anterior",
    ]),
    ("Validación de la contraseña nueva", [
        "Dado que escribo menos de 8 caracteres o las dos contraseñas no coinciden",
        "Cuando confirmo el restablecimiento",
        "Entonces el sistema no la guarda e indica el error",
    ]),
    ("Cuentas que entran por código", [
        "Dado una cuenta de alumno del piloto o de evaluadora, que entra solo con su código",
        "Cuando la veo en el panel de administración",
        "Entonces aparece la etiqueta \"entra con código\" en lugar del botón de "
        "restablecer",
    ]),
    ("Solo el administrador", [
        "Dado que soy psicóloga o estudiante",
        "Cuando intento usar el restablecimiento de contraseñas",
        "Entonces el sistema responde 403",
    ]),
)

_hu("HU-80", OK,
    ("Alta de una psicóloga en un equipo", [
        "Dado que soy administrador",
        "Cuando completo nombre, apellido, correo y contraseña, elijo el equipo de una "
        "titular y pulso \"Crear cuenta\"",
        "Entonces se crea la cuenta con rol psicóloga vinculada a ese equipo",
        "Y la psicóloga puede entrar con su correo y la contraseña elegida",
    ]),
    ("La integrante ve a los alumnos del equipo", [
        "Dado una psicóloga integrante del equipo de una titular",
        "Cuando entra a su panel",
        "Entonces ve los mismos alumnos, resultados, alertas y fichas que la titular",
        "Y ningún alumno cambia de psicóloga responsable",
    ]),
    ("Trabajo compartido", [
        "Dado que una integrante asigna un cuestionario a un alumno del equipo",
        "Cuando el alumno lo responde",
        "Entonces la titular y el resto del equipo también ven ese resultado",
    ]),
    ("Fuera del equipo no se ve nada", [
        "Dado una psicóloga que no pertenece al equipo",
        "Cuando intenta abrir la ficha o el resultado de un alumno del equipo",
        "Entonces el sistema le niega el acceso",
    ]),
    ("Datos que siguen siendo individuales", [
        "Dado dos integrantes del mismo equipo",
        "Cuando una escribe una nota clínica o agenda una cita",
        "Entonces la otra no ve esa nota ni esa cita en su agenda",
    ]),
    ("Validaciones del alta", [
        "Dado que el correo ya existe, la contraseña tiene menos de 8 caracteres, o la "
        "titular elegida no es psicóloga o es una evaluadora",
        "Cuando intento crear la cuenta",
        "Entonces el sistema la rechaza e indica el motivo",
    ]),
)

_hu("HU-81", OK,
    ("Ingreso con código y acuerdo de confidencialidad", [
        "Dado que el administrador me emitió un código de evaluadora",
        "Cuando lo escribo en la pantalla de ingreso por código por primera vez",
        "Entonces debo aceptar el acuerdo de confidencialidad antes de entrar",
        "Y la aceptación queda registrada con mi usuario y la fecha",
    ]),
    ("Evaluación de un caso sin las salidas del modelo", [
        "Dado que abro un caso de la cola \"Evaluar alumnos\"",
        "Cuando reviso sus respuestas",
        "Entonces veo el valor de cada ítem y las frases tal como el estudiante las escribió",
        "Y no veo ningún puntaje, nivel de riesgo, bandera de crisis ni clasificación "
        "del modelo",
    ]),
    ("Registro del juicio clínico", [
        "Dado que terminé de revisar un caso",
        "Cuando emito mi evaluación",
        "Entonces registro el nivel de riesgo en 5 niveles, si requiere atención ahora, "
        "si hay ideación suicida (sí, no o no evaluable) y qué predomina",
        "Y el sistema guarda, sin mostrármelo, lo que había calculado en ese momento",
    ]),
    ("Panel clínico bloqueado hasta terminar", [
        "Dado que todavía me faltan casos de la cohorte por evaluar",
        "Cuando intento entrar al panel clínico",
        "Entonces el sistema me devuelve a la cola de evaluación",
        "Y al terminar todos los casos el panel completo se abre",
    ]),
    ("Cuentas de prueba fuera de las métricas", [
        "Dado una cuenta de evaluadora de prueba",
        "Cuando etiqueta casos",
        "Entonces sus etiquetas se guardan pero no entran en las métricas de concordancia",
    ]),
)
