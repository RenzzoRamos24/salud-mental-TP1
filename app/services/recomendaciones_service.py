"""
Servicio de recomendaciones para el estudiante.

Toma las últimas N entradas del diario, agrega las condiciones que BERT
detectó + detecta temas extra por keywords (bullying, familia, sueño, etc.)
y devuelve un set ordenado de bloques de consejos.

Los consejos están hardcoded en este módulo: son textos cortos, en tono
conversacional, no clínicos. NO sustituyen a la atención profesional —
siempre incluyen un cierre que invita a contactar al psicólogo si la
persona lo necesita.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Iterable

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.diario_entrada import DiarioEntrada
from app.models.diario_analisis import DiarioAnalisis

logger = logging.getLogger(__name__)

# Cuántas entradas mirar hacia atrás para armar el perfil.
VENTANA_ENTRADAS = 10


# ─────────────────────────────────────────────────────────────────────────
# CATÁLOGO DE CONSEJOS
# ─────────────────────────────────────────────────────────────────────────
# Cada bloque cubre un tema. Las claves de `disparadores` se cruzan con:
#   - condiciones BERT (depresion, ansiedad, tdah, estres_academico,
#     soledad, riesgo_suicida)
#   - temas extra detectados por keywords (bullying, familia, sueño, etc.)

CATALOGO: dict[str, dict] = {
    "depresion": {
        "titulo": "Cuando todo se siente apagado",
        "tono": "calma",
        "consejos": [
            "Empezá el día con UNA tarea pequeña y celebrala — lavarte la cara cuenta.",
            "Salí 10 minutos al aire libre, aunque sea hasta la esquina.",
            "Hablá con una persona de confianza esta semana. No tenés que contar todo, basta con escribir 'hola, ¿cómo estás?'.",
            "Si llevás varios días así, pedí una cita en psicología UPC. No tiene que ser grave para pedir ayuda.",
        ],
    },
    "ansiedad": {
        "titulo": "Cuando la cabeza no para",
        "tono": "tecnica",
        "consejos": [
            "Probá 4-7-8: inhalá 4 segundos, retené 7, exhalá 8. Tres rondas alcanzan.",
            "Escribí lo que te preocupa en una hoja aparte, fuera del diario. Sacarlo de la cabeza ayuda.",
            "Identificá UNA sola cosa que sí podés controlar hoy y enfocate ahí.",
            "Si la ansiedad te aparece muchos días seguidos, contale a tu psicólogo en la próxima cita.",
        ],
    },
    "estres_academico": {
        "titulo": "Cuando la UPC te pasa por encima",
        "tono": "practica",
        "consejos": [
            "Listá TODO lo que tenés pendiente. Tachá las 2 cosas más urgentes y olvidate del resto por hoy.",
            "Estudiá en bloques de 25 min con pausas de 5 (Pomodoro). El cerebro no rinde 4 horas seguidas.",
            "Hablá con tu coordinador académico si vas atrasado/a — hay opciones (rezagados, tutorías).",
            "Dormir 6 horas rinde más que estudiar hasta las 3 a.m. En serio.",
        ],
    },
    "soledad": {
        "titulo": "Cuando te sentís solo/a",
        "tono": "calidez",
        "consejos": [
            "Mandale un mensaje a alguien que hace tiempo no ves. Un meme cuenta.",
            "Sumate a una actividad de la UPC: deporte, club, grupo de estudio. La rutina nueva conecta gente.",
            "La soledad no es un defecto tuyo, es una señal. Como hambre o sueño: hay que atenderla.",
            "Si la sensación dura semanas, pedí una cita. Vale la pena hablarlo.",
        ],
    },
    "tdah": {
        "titulo": "Cuando no podés concentrarte",
        "tono": "practica",
        "consejos": [
            "Sacá el celular del escritorio cuando vayas a estudiar. La tentación cuesta más que la voluntad.",
            "Una sola tarea por vez, no muchas pestañas abiertas.",
            "Anotá las ideas que se cruzan en una libreta aparte y volvé a lo que estabas haciendo.",
        ],
    },
    "riesgo_suicida": {
        "titulo": "Si estás pensando en hacerte daño",
        "tono": "urgente",
        "consejos": [
            "Lo que sentís ahora no va a durar para siempre, aunque ahora parezca eterno.",
            "Llamá a la Línea 113 opción 5 (gratis, 24h). Hablan en serio, no juzgan.",
            "Avisale a alguien hoy: familiar, amigo, profesor, psicólogo UPC. No tiene que ser perfecto, solo decí 'no estoy bien'.",
            "Si estás en peligro inmediato, andá a emergencias del centro de salud más cercano.",
        ],
    },
    "bullying": {
        "titulo": "Si alguien te está lastimando",
        "tono": "validacion",
        "consejos": [
            "Lo que te están haciendo no es culpa tuya. Repetí esto cada vez que dudes.",
            "Guardá evidencia: capturas, mensajes, fechas. Si decidís reportar, lo vas a necesitar.",
            "Contale a un adulto que confíes — tutor, profesor, psicólogo. No es 'acusar', es protegerte.",
            "En la UPC podés escribir al canal de convivencia o pedir una cita con bienestar. No estás solo/a en esto.",
        ],
    },
    "familia": {
        "titulo": "Cuando lo de tu casa pesa",
        "tono": "validacion",
        "consejos": [
            "Los conflictos familiares son agotadores. Tenés derecho a sentirte mal por eso.",
            "Si podés, armate un espacio físico tuyo aunque sea por unas horas (biblioteca UPC, casa de amigo/a).",
            "No tenés que resolver vos solo/a los problemas de los adultos.",
            "Si la situación se vuelve violenta o peligrosa, pedí ayuda externa — Línea 100 (violencia familiar, 24h).",
        ],
    },
    "sueño": {
        "titulo": "Si no estás durmiendo bien",
        "tono": "practica",
        "consejos": [
            "Apagá pantallas 30 min antes de dormir. La luz azul retrasa el sueño.",
            "Misma hora para acostarte y levantarte, incluso fines de semana. El cuerpo necesita ritmo.",
            "Si te despertás a las 3 a.m. dando vueltas, levantate, leé 10 min algo aburrido y volvé.",
            "Si llevás más de 2 semanas sin dormir bien, comentalo en tu próxima cita.",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────
# DETECCIÓN DE TEMAS EXTRA POR KEYWORDS
# ─────────────────────────────────────────────────────────────────────────
# Las condiciones BERT cubren depresión/ansiedad/TDAH/estrés/soledad/
# riesgo_suicida. Bullying / familia / sueño los detectamos acá para no
# tocar el modelo.

TEMAS_EXTRA_KEYWORDS: dict[str, list[str]] = {
    "bullying": [
        "bullying", "acoso", "me molestan", "se burlan", "me hostigan",
        "matonea", "me joden", "me hacen bullying", "me discriminan",
    ],
    "familia": [
        "mi mamá", "mi papá", "mis padres", "en casa", "discutimos en casa",
        "mi familia", "pelea en casa", "violencia en casa", "mi hermano",
        "mi hermana",
    ],
    "sueño": [
        "no duermo", "no puedo dormir", "insomnio", "pesadillas",
        "me despierto", "duermo poco", "duermo mal",
    ],
}


def _detectar_temas_extra(textos: Iterable[str]) -> set[str]:
    blob = " ".join((t or "").lower() for t in textos)
    detectados: set[str] = set()
    for tema, kws in TEMAS_EXTRA_KEYWORDS.items():
        if any(kw in blob for kw in kws):
            detectados.add(tema)
    return detectados


# ─────────────────────────────────────────────────────────────────────────
# FORTALEZAS / CONDUCTAS PROTECTORAS
# ─────────────────────────────────────────────────────────────────────────
# Conductas saludables que el alumno menciona y conviene reforzar.
# El sistema valida específicamente lo que escribió (ej: "mencionaste que
# bailaste") en vez de dar consejos genéricos.

FORTALEZAS_KEYWORDS: dict[str, list[str]] = {
    "ejercicio": [
        "bail", "correr", "salí a correr", "gimnasio", "gym", "ejercicio",
        "hacer deporte", "jugué fútbol", "jugué vóley", "yoga", "caminar",
        "salí a caminar", "trotar", "pesas", "entrenar", "entrené",
        "estiramientos", "natación", "nadar",
    ],
    "sueño_bueno": [
        "dormí bien", "descansé", "buen sueño", "dormí 8 horas",
        "me sentí descansado", "me sentí descansada",
    ],
    "social": [
        "salí con amigos", "salí con mis amigos", "salí con mi amigo",
        "salí con mi amiga", "hablé con", "tomé un café con",
        "almorzamos juntos", "vi a mi amigo", "vi a mi amiga",
        "vi a mis amigos", "pasé tiempo con", "me reuní con",
    ],
    "hobby": [
        "pinté", "leí un libro", "toqué guitarra", "toqué piano",
        "cocin", "escribí una canción", "vi una película", "jugué videojuego",
        "armé un puzzle", "dibujé",
    ],
    "naturaleza": [
        "fui al parque", "vi el atardecer", "paseé", "salí al sol",
        "tomé aire", "playa", "miré el cielo",
    ],
    "logro_academico": [
        "aprobé", "saqué buena nota", "terminé el trabajo", "me felicitaron",
        "presenté el proyecto", "expuse y me fue bien", "entregué a tiempo",
    ],
    "autocuidado": [
        "medité", "respiré profundo", "tomé un baño", "me cuidé",
        "comí saludable", "me organicé", "armé mi rutina",
    ],
    "recuperacion": [
        "me siento mejor", "me estoy recuperando", "ya pasó", "estoy mejor",
        "me siento bien", "tuve un mejor día", "se me pasó",
        "estoy mucho mejor",
    ],
}


REFUERZOS: dict[str, dict] = {
    "ejercicio": {
        "titulo": "Moverte te está ayudando",
        "validacion": (
            "Mencionaste que hiciste ejercicio. Eso libera endorfinas y "
            "regula el ánimo — es una de las cosas con más evidencia clínica."
        ),
        "consejos": [
            "Seguí incluyéndolo aunque sean 20 minutos.",
            "Notar que algo te hizo bien y volver a hacerlo es exactamente el camino.",
            "Si podés, anotá cómo te sentís antes y después — vas a ver el patrón.",
        ],
    },
    "sueño_bueno": {
        "titulo": "Dormiste bien — eso pesa mucho",
        "validacion": (
            "Cuando descansás, tu cerebro procesa emociones y regula el "
            "estrés. Lo notaste vos mismo/a."
        ),
        "consejos": [
            "Si funcionó algo (horario, no usar celular antes de dormir), repetilo.",
            "El sueño es la base — cuidalo como una rutina, no como suerte.",
        ],
    },
    "social": {
        "titulo": "Hablar con alguien cambia el día",
        "validacion": (
            "Mencionaste que pasaste tiempo con alguien. Las conexiones "
            "humanas son uno de los amortiguadores más fuertes contra el malestar."
        ),
        "consejos": [
            "No tiene que ser una conversación profunda — la compañía sola alcanza.",
            "Probá agendar algo así una vez por semana, aunque sea un café corto.",
        ],
    },
    "hobby": {
        "titulo": "Hacer algo que te gusta importa",
        "validacion": (
            "Lo que escribiste sobre lo que hiciste suena a actividad que te "
            "conecta con vos mismo/a. Eso baja el ruido mental."
        ),
        "consejos": [
            "Reservá un rato a la semana para esto, como si fuera una clase.",
            "No tiene que ser productivo. Disfrutarlo ya es suficiente.",
        ],
    },
    "naturaleza": {
        "titulo": "Salir al aire libre te hizo bien",
        "validacion": (
            "Estar afuera baja cortisol (la hormona del estrés) y mejora el "
            "ánimo. Lo notaste, eso es importante."
        ),
        "consejos": [
            "Si podés, repetilo 2–3 veces por semana, aunque sean 15 minutos.",
            "El sol de la mañana también ayuda a dormir mejor a la noche.",
        ],
    },
    "logro_academico": {
        "titulo": "Lograste algo — celebralo",
        "validacion": (
            "Escribiste sobre algo que te salió bien. Es fácil saltar al "
            "siguiente problema sin registrar las victorias. Vos lo registraste."
        ),
        "consejos": [
            "Date un momento para reconocerlo, aunque sea contártelo a alguien.",
            "Acordate de este momento cuando otra cosa te frustre.",
        ],
    },
    "autocuidado": {
        "titulo": "Te estás cuidando",
        "validacion": (
            "Lo que describiste es autocuidado activo. No es egoísmo, es lo "
            "que te permite estar disponible para vos y para los demás."
        ),
        "consejos": [
            "Si una práctica te funcionó, hacela parte de la rutina, no de la excepción.",
        ],
    },
    "recuperacion": {
        "titulo": "Estás notando que estás mejor",
        "validacion": (
            "Que reconozcas vos mismo/a que estás mejor es importante. "
            "Significa que algo de lo que estás haciendo está funcionando."
        ),
        "consejos": [
            "Tratá de identificar qué cambió: ¿algo que hiciste, dejaste de hacer, alguien con quien hablaste?",
            "Las mejorías no son lineales — si volvés a sentirte mal, no significa que retrocediste.",
            "Anotar lo que te ayudó hoy puede servirte la próxima vez que el ánimo baje.",
        ],
    },
}


def _detectar_fortalezas(textos: Iterable[str]) -> list[str]:
    """
    Devuelve las fortalezas detectadas en orden de aparición frecuente.
    Aplica sobre los textos completos (todas las entradas de la ventana).
    """
    blob = " ".join((t or "").lower() for t in textos)
    detectadas: list[str] = []
    for clave, kws in FORTALEZAS_KEYWORDS.items():
        if any(kw in blob for kw in kws):
            detectadas.append(clave)
    return detectadas


# ─────────────────────────────────────────────────────────────────────────
# API PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────

def recomendaciones_para_estudiante(db: Session, user_id: str) -> dict:
    """
    Construye un set de recomendaciones a partir de las últimas
    `VENTANA_ENTRADAS` entradas del diario del estudiante.

    Estrategia:
      1. Detecta condiciones BERT, fortalezas y crisis en la ventana.
      2. Intenta generar consejos DINÁMICOS con Claude API.
      3. Si la API no está configurada o falla, usa el catálogo estático.

    Devuelve:
      {
        "tiene_datos": bool,
        "mensaje": str (texto contextual),
        "temas_detectados": [str, ...],
        "fortalezas_detectadas": [str, ...],
        "fuente": "ia" | "estatico" | "vacio",
        "recomendaciones": [
          { "clave", "titulo", "tono", "validacion"?, "consejos": [str, ...] }, ...
        ]
      }
    """
    entradas = (
        db.query(DiarioEntrada)
        .filter(DiarioEntrada.user_id == user_id)
        .order_by(desc(DiarioEntrada.timestamp))
        .limit(VENTANA_ENTRADAS)
        .all()
    )

    if not entradas:
        return {
            "tiene_datos": False,
            "mensaje": (
                "Todavía no escribiste nada en tu diario. Cuando lo hagas, "
                "acá vas a ver consejos pensados para lo que estás viviendo."
            ),
            "temas_detectados": [],
            "fortalezas_detectadas": [],
            "fuente": "vacio",
            "recomendaciones": [],
        }

    # ── 1) Condiciones BERT acumuladas en la ventana ──────────────────
    cond_counter: Counter[str] = Counter()
    crisis_detectada = False
    for e in entradas:
        if not e.analisis_id:
            continue
        a = (
            db.query(DiarioAnalisis)
            .filter(DiarioAnalisis.id == e.analisis_id)
            .first()
        )
        if not a:
            continue
        if a.crisis_protocolo:
            crisis_detectada = True
        try:
            condiciones = json.loads(a.condiciones_detectadas_json or "{}")
        except Exception:
            condiciones = {}
        for clave in condiciones:
            cond_counter[clave] += 1

    # ── 2) Temas extra por keywords ───────────────────────────────────
    textos_entradas = [e.texto for e in entradas]
    temas_extra = _detectar_temas_extra(textos_entradas)

    # ── 3) Fortalezas / conductas protectoras detectadas ──────────────
    fortalezas = _detectar_fortalezas(textos_entradas)

    # ── 3.5) Intentar generación DINÁMICA con Claude API ──────────────
    # Si hay API key configurada, esto reemplaza al catálogo estático.
    from app.services.consejos_dinamicos_service import generar_consejos_dinamicos

    entradas_para_ia = [
        {
            "fecha": (e.fecha.isoformat() if e.fecha else None),
            "texto": e.texto or "",
            "estado_animo": e.estado_animo,
        }
        # Orden cronológico ascendente para que la IA lea el progreso temporal.
        for e in reversed(entradas)
    ]

    resultado_ia = generar_consejos_dinamicos(
        entradas=entradas_para_ia,
        condiciones_bert=list(cond_counter.keys()),
        fortalezas=fortalezas,
        crisis=crisis_detectada,
    )

    if resultado_ia is not None:
        # La IA generó consejos personalizados. Devolvemos eso directo.
        return {
            "tiene_datos": True,
            "mensaje": resultado_ia.mensaje,
            "temas_detectados": [r.clave for r in resultado_ia.recomendaciones],
            "fortalezas_detectadas": fortalezas,
            "fuente": "ia",
            "recomendaciones": [
                {
                    "clave": r.clave,
                    "titulo": r.titulo,
                    "tono": r.tono,
                    "validacion": r.validacion,
                    "consejos": r.consejos,
                }
                for r in resultado_ia.recomendaciones
            ],
        }
    # Si no hubo IA (sin API key o falló), seguimos con catálogo estático.

    # ── 4) Construir paneles ──────────────────────────────────────────
    # Orden final:
    #   a) Crisis (si hay) → riesgo_suicida arriba de todo.
    #   b) Refuerzos positivos (validar lo que está haciendo bien).
    #   c) Consejos por condición BERT.
    #   d) Consejos por temas extra (bullying, familia, sueño).
    recomendaciones: list[dict] = []
    temas_listados: list[str] = []

    if crisis_detectada and "riesgo_suicida" in CATALOGO:
        recomendaciones.append({
            "clave": "riesgo_suicida",
            "titulo": CATALOGO["riesgo_suicida"]["titulo"],
            "tono": "urgente",
            "consejos": CATALOGO["riesgo_suicida"]["consejos"],
        })
        temas_listados.append("riesgo_suicida")

    # Refuerzos positivos — máximo 2 para no diluir el foco.
    for clave in fortalezas[:2]:
        if clave not in REFUERZOS:
            continue
        bloque = REFUERZOS[clave]
        recomendaciones.append({
            "clave": f"refuerzo_{clave}",
            "titulo": bloque["titulo"],
            "tono": "refuerzo",
            "validacion": bloque["validacion"],
            "consejos": bloque["consejos"],
        })
        temas_listados.append(f"refuerzo_{clave}")

    # Condiciones BERT por frecuencia (excluye estabilidad y riesgo_suicida
    # que ya entró por crisis si correspondía).
    for clave, _ in cond_counter.most_common():
        if clave in ("estabilidad",):
            continue
        if clave in temas_listados:
            continue
        if clave not in CATALOGO:
            continue
        recomendaciones.append({
            "clave": clave,
            "titulo": CATALOGO[clave]["titulo"],
            "tono": CATALOGO[clave].get("tono", "calma"),
            "consejos": CATALOGO[clave]["consejos"],
        })
        temas_listados.append(clave)

    for tema in temas_extra:
        if tema in temas_listados or tema not in CATALOGO:
            continue
        recomendaciones.append({
            "clave": tema,
            "titulo": CATALOGO[tema]["titulo"],
            "tono": CATALOGO[tema].get("tono", "calma"),
            "consejos": CATALOGO[tema]["consejos"],
        })
        temas_listados.append(tema)

    # Limitar total a 6 paneles para no abrumar (más cuando hay refuerzos +
    # condiciones para abordar el mismo día).
    recomendaciones = recomendaciones[:6]

    # ── 5) Mensaje contextual ─────────────────────────────────────────
    if not recomendaciones:
        mensaje = (
            "Buenas noticias: el sistema no está detectando señales fuertes "
            "en tu diario por ahora. Seguí escribiendo, ayuda mucho mantener "
            "el hábito."
        )
    elif crisis_detectada:
        mensaje = (
            "El sistema detectó señales serias en tu diario. Estos consejos "
            "son un primer paso, pero por favor también contactá a alguien "
            "hoy — psicología UPC o la Línea 113."
        )
    elif fortalezas and not cond_counter:
        mensaje = (
            "Lo que escribiste tiene cosas buenas. Vale la pena reconocer y "
            "reforzar lo que te está funcionando."
        )
    elif fortalezas:
        mensaje = (
            "Hay cosas buenas en lo que escribiste y también cosas que "
            "podrían cuidarse mejor. Primero lo que está sumando, después "
            "lo que conviene atender."
        )
    else:
        mensaje = (
            "Estos consejos están pensados para lo que escribiste en los "
            "últimos días. No reemplazan una conversación con tu psicólogo."
        )

    return {
        "tiene_datos": True,
        "mensaje": mensaje,
        "temas_detectados": temas_listados,
        "fortalezas_detectadas": fortalezas,
        "fuente": "estatico",
        "recomendaciones": recomendaciones,
    }
