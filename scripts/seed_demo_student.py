"""
Crea un estudiante demo con datos clínicamente realistas:
  - Ciclo 1 CERRADO: 13 entradas en 14 días, PHQ-A=17, GAD-7=11
    → Posible depresión moderada-severa + posible TAG según DSM-5
  - Ciclo 2 EN CURSO: 5 entradas (ciclo activo)

Uso:
    python -m scripts.seed_demo_student

Credenciales creadas:
    Estudiante : maria.torres@demo.upc.edu.pe / Demo12345
    Psicólogo  : psicologa@demo.upc.edu.pe   / Demo12345
"""

import json
import sys
from datetime import date, timedelta, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.consent import Consent
from app.models.diario_entrada import DiarioEntrada
from app.models.diario_analisis import DiarioAnalisis
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

# ──────────────────────────────────────────────────────────────────────────────
# Configuración de items por día (Ciclo 1, 14 días)
# Resultado esperado: PHQ-A = 17, GAD-7 = 11
# ──────────────────────────────────────────────────────────────────────────────
# Conteos por ítem:
#   p1(anhedonia):     días 1-12  → 12 días → 3 pts
#   p2(ánimo dep.):    días 1-13  → 13 días → 3 pts
#   p3(sueño):         días 1-3,5-11 → 10 días → 2 pts
#   p4(fatiga):        días 1-12  → 12 días → 3 pts
#   p5(apetito):       días 2,3,5,9,11 → 5 días → 1 pt
#   p6(culpa):         días 2,4,5,6,7,8,9,11 → 8 días → 2 pts
#   p7(concentración): días 1,3,5,6,7,8,9,11 → 8 días → 2 pts
#   p8(psicomotor):    días 7,10,13 → 3 días → 1 pt
#   p9(ideación):      ninguno     → 0 días → 0 pts  ← sin crisis
#   g1(nervios):       días 1-9    → 9 días → 2 pts
#   g2(control):       días 1-9    → 9 días → 2 pts
#   g3(preocupación):  días 1-12   → 12 días → 3 pts
#   g4(tensión):       días 1,3,5,7,9,11 → 6 días → 1 pt
#   g5(inquietud):     días 2,4,6,8,10 → 5 días → 1 pt
#   g6(irritabilidad): días 3,5,7,9,11 → 5 días → 1 pt
#   g7(miedo):         días 4,8,10 → 3 días → 1 pt
# PHQ-A = 3+3+2+3+1+2+2+1+0 = 17  |  GAD-7 = 2+2+3+1+1+1+1 = 11

DIAS_CICLO1 = {
    1:  {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_7",
                   "gad7_1","gad7_2","gad7_3","gad7_4"],
         "emoji": "lluvioso",
         "texto": (
             "Hoy fue un día muy difícil. No tengo ganas de hacer nada, "
             "ni siquiera de hablar con mis amigos. Me costó mucho levantarme "
             "de la cama. Llevo semanas sintiéndome así y no sé cuánto más "
             "puedo aguantar. Los exámenes se acercan y siento que no soy capaz "
             "de concentrarme ni un minuto. La cabeza me da vueltas con todo "
             "lo que tengo que hacer y no sé por dónde empezar."
         ),
         "beto": {"depresion": 82, "ansiedad": 68, "estres_academico": 74,
                  "soledad": 55, "tdah": 28, "riesgo_suicida": 8}},
    2:  {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_5","phq9_6",
                   "gad7_1","gad7_2","gad7_3","gad7_5"],
         "emoji": "lluvioso",
         "texto": (
             "Otra vez no pude dormir bien. Me desperté a las 3 de la mañana "
             "pensando en el parcial de estadística y ya no pude volver a dormir. "
             "No tenía hambre en el desayuno, me comí solo una tostada. "
             "Me siento inútil, como si no sirviera para la universidad. "
             "No puedo dejar de preocuparme por todo."
         ),
         "beto": {"depresion": 78, "ansiedad": 72, "estres_academico": 70,
                  "soledad": 52, "tdah": 25, "riesgo_suicida": 7}},
    3:  {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_5","phq9_7",
                   "gad7_1","gad7_2","gad7_3","gad7_4","gad7_6"],
         "emoji": "lluvioso",
         "texto": (
             "Hoy intenté estudiar pero no pude retener nada. Leía los mismos "
             "párrafos una y otra vez. Sin ganas de nada. Me siento tan cansada "
             "que hasta respirar parece un esfuerzo. No tengo apetito. "
             "Encima mis compañeros del grupo de trabajo me escribieron y no "
             "tuve fuerzas de responder. Me molesta todo últimamente, "
             "cualquier cosa pequeña me desespera."
         ),
         "beto": {"depresion": 80, "ansiedad": 65, "estres_academico": 78,
                  "soledad": 60, "tdah": 32, "riesgo_suicida": 9}},
    4:  {"items": ["phq9_1","phq9_2","phq9_4","phq9_6",
                   "gad7_1","gad7_2","gad7_3","gad7_5","gad7_7"],
         "emoji": "lluvioso",
         "texto": (
             "Le fallé a mi mamá otra vez. Prometí ayudarla con algo y se me "
             "olvidó porque estaba metida en mi propia angustia. Me siento tan "
             "culpable. No disfruto nada, ni la música que antes me gustaba. "
             "Tengo miedo de que algo malo vaya a pasar, no sé qué, pero lo "
             "siento. No puedo controlar los pensamientos."
         ),
         "beto": {"depresion": 75, "ansiedad": 70, "estres_academico": 60,
                  "soledad": 58, "tdah": 22, "riesgo_suicida": 6}},
    5:  {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_5","phq9_6","phq9_7",
                   "gad7_1","gad7_2","gad7_3","gad7_4","gad7_6"],
         "emoji": "lluvioso",
         "texto": (
             "Cinco días seguidos sintiéndome igual. Hoy fue el peor. "
             "No pude comer casi nada. El insomnio sigue, me despierto en "
             "la madrugada y me quedo mirando el techo. Me preocupo por todo: "
             "los exámenes, mi familia, el futuro, todo junto. Me siento sin "
             "energía, sin interés, sin ganas. Como si hubiera una niebla que "
             "no me deja ver nada claro. No sirvo para esto."
         ),
         "beto": {"depresion": 85, "ansiedad": 74, "estres_academico": 76,
                  "soledad": 62, "tdah": 30, "riesgo_suicida": 10}},
    6:  {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_6","phq9_7",
                   "gad7_1","gad7_2","gad7_3","gad7_5"],
         "emoji": "nublado",
         "texto": (
             "Hoy salí un poco, fui a la universidad. Igual me costó mucho. "
             "Estaba en clase pero mi mente estaba en otro lado. No puedo "
             "concentrarme. Me fui antes de que terminara la clase porque "
             "no podía más. Sigo sin dormir bien y sigo sin sentir ganas de "
             "nada. La preocupación constante no me suelta."
         ),
         "beto": {"depresion": 79, "ansiedad": 66, "estres_academico": 72,
                  "soledad": 55, "tdah": 27, "riesgo_suicida": 8}},
    7:  {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_6","phq9_7","phq9_8",
                   "gad7_1","gad7_2","gad7_3","gad7_4","gad7_6"],
         "emoji": "nublado",
         "texto": (
             "Me muevo muy lento hoy, como si el cuerpo no me respondiera. "
             "Hasta hablar me cuesta. Me siento agotada por dentro y por fuera. "
             "No disfruto nada de lo que hago. Mis amigas me invitaron a salir "
             "y dije que no, no tenía fuerzas. Me irritan hasta los ruidos "
             "pequeños. Sigo tenso con todo."
         ),
         "beto": {"depresion": 81, "ansiedad": 67, "estres_academico": 65,
                  "soledad": 64, "tdah": 29, "riesgo_suicida": 7}},
    8:  {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_6","phq9_7",
                   "gad7_1","gad7_2","gad7_3","gad7_5","gad7_7"],
         "emoji": "nublado",
         "texto": (
             "Otro día difícil. Siento que algo malo va a pasar y no sé qué. "
             "No puedo relajarme. Dormí 4 horas esta noche. En el trabajo "
             "grupal no pude aportar casi nada, me fui sintiendo culpable "
             "otra vez. La concentración sigue sin aparecer. "
             "¿Cuándo va a terminar esto?"
         ),
         "beto": {"depresion": 77, "ansiedad": 71, "estres_academico": 68,
                  "soledad": 56, "tdah": 26, "riesgo_suicida": 9}},
    9:  {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_5","phq9_6","phq9_7",
                   "gad7_1","gad7_2","gad7_3","gad7_4","gad7_6"],
         "emoji": "nublado",
         "texto": (
             "Semana y media así y ya me cansé de cansarme. No tengo hambre "
             "desde hace días. El insomnio es constante. Me preocupo por todo "
             "a la vez: los exámenes finales, mi mamá que está enferma, "
             "no saber qué quiero hacer con mi vida. Me molesta todo. "
             "No me veo capaz de terminar el semestre."
         ),
         "beto": {"depresion": 83, "ansiedad": 73, "estres_academico": 80,
                  "soledad": 60, "tdah": 31, "riesgo_suicida": 8}},
    10: {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_8",
                   "gad7_3","gad7_5","gad7_7"],
         "emoji": "nublado",
         "texto": (
             "Hoy me levanté muy tarde. El cuerpo no me obedece, me siento "
             "pesada, lenta. Fui a la biblioteca pero no pude estudiar, "
             "solo miraba la pantalla. Sigo preocupada por todo aunque "
             "hoy los nervios están un poco más bajos. Aún así no logro "
             "estar tranquila. Sigo sin sentir nada especial por las cosas."
         ),
         "beto": {"depresion": 74, "ansiedad": 58, "estres_academico": 65,
                  "soledad": 50, "tdah": 24, "riesgo_suicida": 6}},
    11: {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","phq9_5","phq9_6","phq9_7",
                   "gad7_3","gad7_4","gad7_6"],
         "emoji": "nublado",
         "texto": (
             "Hablé con mi mamá hoy. Le dije que estaba mal pero no le dije "
             "todo. No sé cómo explicarlo. Sigo sin apetito, sin dormir bien, "
             "sin concentración. Me siento culpable por no rendir en la "
             "universidad. No disfruto nada. La fatiga no se va. "
             "Todavía me preocupo mucho y me molesto fácil."
         ),
         "beto": {"depresion": 78, "ansiedad": 62, "estres_academico": 70,
                  "soledad": 54, "tdah": 28, "riesgo_suicida": 7}},
    12: {"items": ["phq9_1","phq9_2","phq9_4",
                   "gad7_3"],
         "emoji": "mixto",
         "texto": (
             "Hoy fue un poco mejor. Igual me cuesta, pero pude comer algo "
             "más. El cansancio sigue ahí. Sigo sin tener muchas ganas de "
             "hacer cosas, pero al menos no me sentí tan mal como los días "
             "anteriores. La preocupación sigue dando vueltas."
         ),
         "beto": {"depresion": 65, "ansiedad": 52, "estres_academico": 58,
                  "soledad": 44, "tdah": 20, "riesgo_suicida": 5}},
    13: {"items": ["phq9_2","phq9_8"],
         "emoji": "mixto",
         "texto": (
             "Dos semanas así. Entregué el trabajo grupal aunque no quedé "
             "contenta con lo que aporté. El cuerpo sigue pesado. "
             "El ánimo sigue bajo pero ya no me siento tan desesperada. "
             "Ojalá la próxima semana sea distinta."
         ),
         "beto": {"depresion": 60, "ansiedad": 48, "estres_academico": 55,
                  "soledad": 40, "tdah": 18, "riesgo_suicida": 4}},
}

# Ciclo 2: 5 entradas (mejora leve pero aún elevada)
DIAS_CICLO2 = {
    1: {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","gad7_1","gad7_2","gad7_3"],
        "emoji": "nublado",
        "texto": (
            "Empieza otra semana. Todavía me siento cansada pero un poco "
            "menos que antes. Fui a clase y pude quedarme toda la hora. "
            "Dormí mejor anoche, aunque me desperté una vez. "
            "Sigo preocupada por los finales."
        ),
        "beto": {"depresion": 68, "ansiedad": 60, "estres_academico": 70,
                 "soledad": 45, "tdah": 22, "riesgo_suicida": 5}},
    2: {"items": ["phq9_1","phq9_2","phq9_4","gad7_2","gad7_3"],
        "emoji": "nublado",
        "texto": (
            "Hoy estudié un par de horas. Me costó pero lo hice. "
            "Sigo sin tener muchas ganas de socializar. "
            "El ánimo sigue bajo pero ya no me paraliza tanto. "
            "La preocupación sigue ahí aunque un poco menos intensa."
        ),
        "beto": {"depresion": 65, "ansiedad": 55, "estres_academico": 65,
                 "soledad": 42, "tdah": 20, "riesgo_suicida": 4}},
    3: {"items": ["phq9_1","phq9_2","phq9_3","phq9_4","gad7_3","gad7_4"],
        "emoji": "nublado",
        "texto": (
            "Dormí mal otra vez. Me puse a pensar en todo lo que falta del "
            "semestre. No logro relajarme del todo. Sigo sin sentir alegría "
            "por las cosas. Voy día a día."
        ),
        "beto": {"depresion": 70, "ansiedad": 62, "estres_academico": 68,
                 "soledad": 46, "tdah": 21, "riesgo_suicida": 5}},
    4: {"items": ["phq9_2","phq9_4","gad7_3"],
        "emoji": "mixto",
        "texto": (
            "Hoy fue un día más tranquilo. Fui al comedor con una amiga y "
            "eso me ayudó. Sigo cansada pero el ánimo estuvo algo mejor. "
            "Todavía me preocupo mucho pero pude estudiar un rato."
        ),
        "beto": {"depresion": 58, "ansiedad": 50, "estres_academico": 60,
                 "soledad": 35, "tdah": 18, "riesgo_suicida": 3}},
    5: {"items": ["phq9_1","phq9_2","phq9_4","gad7_2","gad7_3"],
        "emoji": "nublado",
        "texto": (
            "Hoy tuve un bajón otra vez. No sé si mejoro o empeoro. "
            "Nada me da mucha alegría todavía. El cansancio es constante. "
            "Seguiré escribiendo para ver si esto ayuda."
        ),
        "beto": {"depresion": 66, "ansiedad": 57, "estres_academico": 64,
                 "soledad": 44, "tdah": 20, "riesgo_suicida": 5}},
}


def _crear_analisis(db, entrada, beto_scores, items_keys):
    """Crea y persiste un DiarioAnalisis para una entrada."""
    condiciones = {
        k: {"etiqueta": k.replace("_", " ").title(), "confianza": v}
        for k, v in beto_scores.items()
        if k != "riesgo_suicida" and v >= 50
    }
    items_detectados = [
        {"item": key, "score": 2, "confianza": 0.72, "keywords": []}
        for key in items_keys
    ]
    # Nivel de riesgo
    dep = beto_scores.get("depresion", 0)
    ans = beto_scores.get("ansiedad", 0)
    sui = beto_scores.get("riesgo_suicida", 0)
    if sui >= 40:
        nivel = "CRÍTICO"
    elif dep >= 75 or ans >= 70:
        nivel = "ALTO"
    elif dep >= 55 or ans >= 55:
        nivel = "MEDIO"
    else:
        nivel = "BAJO"

    analisis = DiarioAnalisis(
        entrada_id=entrada.id,
        user_id=entrada.user_id,
        nivel_riesgo=nivel,
        score=max(beto_scores.values()),
        explicacion="Análisis BETO (seed demo)",
        phq9_total=None,
        gad7_total=None,
        crisis_protocolo=False,
        condiciones_detectadas_json=json.dumps(condiciones, ensure_ascii=False),
        scores_completos_json=json.dumps(beto_scores, ensure_ascii=False),
        items_detectados_json=json.dumps(items_detectados, ensure_ascii=False),
        modelo="seed-demo",
        tiempo_inferencia=0.0,
    )
    db.add(analisis)
    db.flush()
    return analisis


def main():
    db = SessionLocal()
    try:
        hoy = date.today()

        # ── Psicólogo demo ────────────────────────────────────────────
        psi_email = "psicologa@demo.upc.edu.pe"
        psi = db.query(User).filter(User.email == psi_email).first()
        if not psi:
            psi = User(
                email=psi_email,
                hashed_password=hash_password("Demo12345"),
                nombre="Carla",
                apellido="Mendoza",
                role="psicologo",
                activo=True,
            )
            db.add(psi)
            db.flush()
            db.add(Consent(user_id=psi.id, version="1.0"))
            db.commit()
            print(f"✅ Psicóloga creada: {psi_email}")
        else:
            print(f"ℹ️  Psicóloga ya existe: {psi_email}")

        # ── Estudiante demo ────────────────────────────────────────────
        est_email = "maria.torres@demo.upc.edu.pe"
        est = db.query(User).filter(User.email == est_email).first()
        if est:
            # Limpiar datos previos del ciclo
            entradas_ids = [
                e.id for e in db.query(DiarioEntrada.id)
                .filter(DiarioEntrada.user_id == est.id).all()
            ]
            if entradas_ids:
                db.query(DiarioAnalisis).filter(
                    DiarioAnalisis.entrada_id.in_(entradas_ids)
                ).delete(synchronize_session=False)
                db.query(DiarioEntrada).filter(
                    DiarioEntrada.user_id == est.id
                ).delete(synchronize_session=False)
            db.commit()
            print(f"ℹ️  Estudiante ya existe, limpiando entradas previas: {est_email}")
        else:
            est = User(
                email=est_email,
                hashed_password=hash_password("Demo12345"),
                nombre="María Alejandra",
                apellido="Torres Huanca",
                role="estudiante",
                activo=True,
            )
            db.add(est)
            db.flush()
            db.add(Consent(user_id=est.id, version="1.0"))
            db.commit()
            print(f"✅ Estudiante creada: {est_email}")

        # ── Ciclo 1: empieza 30 días atrás, cierra hace 17 días ──────
        inicio_c1 = hoy - timedelta(days=29)

        for dia_num, datos in DIAS_CICLO1.items():
            fecha_entrada = inicio_c1 + timedelta(days=dia_num - 1)
            ts = datetime.combine(fecha_entrada, datetime.min.time()).replace(hour=20)

            entrada = DiarioEntrada(
                user_id=est.id,
                texto=datos["texto"],
                estado_animo=datos["emoji"],
                prompt_del_dia="¿Cómo te sentiste hoy?",
                fecha=fecha_entrada,
                timestamp=ts,
            )
            db.add(entrada)
            db.flush()

            analisis = _crear_analisis(db, entrada, datos["beto"], datos["items"])
            entrada.analisis_id = analisis.id

        db.commit()
        print(f"✅ Ciclo 1: {len(DIAS_CICLO1)} entradas creadas (PHQ-A≈17, GAD-7≈11)")

        # ── Ciclo 2: empieza hace 16 días, en curso ───────────────────
        inicio_c2 = inicio_c1 + timedelta(days=14)

        for dia_num, datos in DIAS_CICLO2.items():
            fecha_entrada = inicio_c2 + timedelta(days=dia_num - 1)
            ts = datetime.combine(fecha_entrada, datetime.min.time()).replace(hour=20)

            entrada = DiarioEntrada(
                user_id=est.id,
                texto=datos["texto"],
                estado_animo=datos["emoji"],
                prompt_del_dia="¿Cómo te sentiste hoy?",
                fecha=fecha_entrada,
                timestamp=ts,
            )
            db.add(entrada)
            db.flush()

            analisis = _crear_analisis(db, entrada, datos["beto"], datos["items"])
            entrada.analisis_id = analisis.id

        db.commit()
        print(f"✅ Ciclo 2: {len(DIAS_CICLO2)} entradas creadas (en curso, leve mejoría)")

        print("\n── Credenciales ────────────────────────────────────────")
        print(f"   Estudiante : {est_email} / Demo12345")
        print(f"   Psicóloga  : {psi_email} / Demo12345")
        print("────────────────────────────────────────────────────────")
        print("Ciclo 1 → PHQ-A esperado: 17 (moderada-severa)")
        print("          GAD-7 esperado: 11 (moderada)")
        print("          DSM-5: posible EDM + posible TAG")

    finally:
        db.close()


if __name__ == "__main__":
    main()
