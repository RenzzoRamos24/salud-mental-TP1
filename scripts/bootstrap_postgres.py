"""Bootstrap del banco fijo en PostgreSQL (idempotente).

Para SQLite usamos `seeds/banco_instrumentos.sql` directamente. Para Postgres
ese SQL tiene casi todo compatible pero hay diferencias menores; en lugar de
adaptar el SQL, sembramos los datos vía ORM, que es portable.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.bank import (
    BankInstrumento,
    BankItem,
    BankFraseIncompleta,
)


# ── 6 escalas validadas + 40 frases incompletas ─────────────────────────
INSTRUMENTOS = [
    {
        "codigo": "PHQ-A",
        "nombre": "Patient Health Questionnaire — Adolescent",
        "autor": "Johnson, Harris, Spitzer & Williams",
        "anio": 2002,
        "dominio": "depresion",
        "tipo_escala": "likert",
        "likert_min": 0,
        "likert_max": 3,
        "n_items": 9,
        "tiempo_min": 4,
        "instruccion": "Durante las últimas dos semanas, ¿con qué frecuencia te ha molestado alguno de los siguientes problemas?",
        "citacion": "Johnson JG, Harris ES, Spitzer RL, Williams JBW. The Patient Health Questionnaire for Adolescents. J Adolesc Health. 2002;30(3):196-204.",
        "items": [
            (1, "Poco interés o placer en hacer cosas.", "Anhedonia", 0, 0),
            (2, "Sentirte triste, decaído/a o sin esperanza.", "Estado de ánimo deprimido", 0, 0),
            (3, "Problemas para dormir, dormir demasiado, o despertarte mucho durante la noche.", "Insomnio/hipersomnia", 0, 0),
            (4, "Sentirte cansado/a o con poca energía.", "Fatiga", 0, 0),
            (5, "Falta de apetito o comer en exceso.", "Cambios de apetito/peso", 0, 0),
            (6, "Sentirte mal contigo mismo/a, sentir que eres un/a fracasado/a, o que has fallado a tu familia.", "Culpa/inutilidad", 0, 0),
            (7, "Dificultad para concentrarte en cosas como tareas escolares, leer o ver televisión.", "Concentración disminuida", 0, 0),
            (8, "Moverte o hablar tan lento que otras personas lo notan, o estar tan inquieto/a que te mueves mucho más de lo habitual.", "Agitación/retardo psicomotor", 0, 0),
            (9, "Pensar que estarías mejor muerto/a o tener pensamientos de hacerte daño de alguna manera.", "Ideación suicida", 0, 1),
        ],
    },
    {
        "codigo": "GAD-7",
        "nombre": "Generalized Anxiety Disorder — 7 item",
        "autor": "Spitzer, Kroenke, Williams & Löwe",
        "anio": 2006,
        "dominio": "ansiedad",
        "tipo_escala": "likert",
        "likert_min": 0,
        "likert_max": 3,
        "n_items": 7,
        "tiempo_min": 3,
        "instruccion": "Durante las últimas dos semanas, ¿con qué frecuencia te has sentido afectado/a por los siguientes problemas?",
        "citacion": "Spitzer RL, Kroenke K, Williams JBW, Löwe B. A brief measure for assessing generalized anxiety disorder: the GAD-7. Arch Intern Med. 2006;166(10):1092-1097.",
        "items": [
            (1, "Sentirte nervioso/a, ansioso/a o con los nervios de punta.", "Ansiedad/preocupación excesiva", 0, 0),
            (2, "No poder dejar de preocuparte o no poder controlar tus preocupaciones.", "Dificultad para controlar la preocupación", 0, 0),
            (3, "Preocuparte demasiado por diferentes cosas.", "Preocupación excesiva", 0, 0),
            (4, "Tener dificultad para relajarte.", "Tensión muscular", 0, 0),
            (5, "Estar tan inquieto/a que te resulta difícil quedarte quieto/a.", "Inquietud", 0, 0),
            (6, "Irritarte o enojarte con facilidad.", "Irritabilidad", 0, 0),
            (7, "Sentir miedo como si algo terrible fuera a pasar.", "Aprensión", 0, 0),
        ],
    },
    {
        "codigo": "SRQ-20",
        "nombre": "Self-Reporting Questionnaire 20 (OMS)",
        "autor": "Harding, de Arango, Baltazar, Climent et al.",
        "anio": 1980,
        "dominio": "tamizaje_general",
        "tipo_escala": "binaria",
        "likert_min": 0,
        "likert_max": 1,
        "n_items": 20,
        "tiempo_min": 7,
        "instruccion": "Las siguientes preguntas se refieren a cómo te has sentido durante los últimos 30 días. Responde 'sí' si el problema te ha ocurrido y 'no' si no te ha ocurrido.",
        "citacion": "Harding TW et al. Mental disorders in primary health care. Psychol Med. 1980;10(2):231-241.",
        "items": [
            (1, "¿Tienes frecuentemente dolores de cabeza?", None, 0, 0),
            (2, "¿Tienes mal apetito?", None, 0, 0),
            (3, "¿Duermes mal?", None, 0, 0),
            (4, "¿Te asustas con facilidad?", None, 0, 0),
            (5, "¿Sufres de temblor de manos?", None, 0, 0),
            (6, "¿Te sientes nervioso/a, tenso/a o aburrido/a?", None, 0, 0),
            (7, "¿Tienes mala digestión?", None, 0, 0),
            (8, "¿No puedes pensar con claridad?", None, 0, 0),
            (9, "¿Te sientes triste?", None, 0, 0),
            (10, "¿Lloras con mucha frecuencia?", None, 0, 0),
            (11, "¿Tienes dificultad para disfrutar tus actividades diarias?", None, 0, 0),
            (12, "¿Tienes dificultad para tomar decisiones?", None, 0, 0),
            (13, "¿Tienes dificultad en hacer tu trabajo o estudios (te causa sufrimiento)?", None, 0, 0),
            (14, "¿Eres incapaz de desempeñar un papel útil en tu vida?", None, 0, 0),
            (15, "¿Has perdido interés en las cosas?", None, 0, 0),
            (16, "¿Sientes que eres una persona inútil?", None, 0, 0),
            (17, "¿Has tenido la idea de acabar con tu vida?", None, 0, 1),
            (18, "¿Te sientes cansado/a todo el tiempo?", None, 0, 0),
            (19, "¿Tienes sensaciones desagradables en el estómago?", None, 0, 0),
            (20, "¿Te cansas con facilidad?", None, 0, 0),
        ],
    },
    {
        "codigo": "RSES",
        "nombre": "Rosenberg Self-Esteem Scale",
        "autor": "Rosenberg",
        "anio": 1965,
        "dominio": "autoestima",
        "tipo_escala": "likert",
        "likert_min": 1,
        "likert_max": 4,
        "n_items": 10,
        "tiempo_min": 3,
        "instruccion": "Indica cuán de acuerdo estás con cada afirmación.",
        "citacion": "Rosenberg M. Society and the Adolescent Self-Image. Princeton University Press; 1965.",
        "items": [
            (1, "Siento que soy una persona digna de aprecio, al menos en igual medida que los demás.", None, 0, 0),
            (2, "Estoy convencido/a de que tengo cualidades buenas.", None, 0, 0),
            (3, "Soy capaz de hacer las cosas tan bien como la mayoría de la gente.", None, 0, 0),
            (4, "Tengo una actitud positiva hacia mí mismo/a.", None, 0, 0),
            (5, "En general estoy satisfecho/a conmigo mismo/a.", None, 0, 0),
            (6, "Siento que no tengo mucho de lo que estar orgulloso/a.", None, 1, 0),
            (7, "En general, me inclino a pensar que soy un/a fracasado/a.", None, 1, 0),
            (8, "Me gustaría poder sentir más respeto por mí mismo/a.", None, 1, 0),
            (9, "Hay veces que realmente pienso que soy un/a inútil.", None, 1, 0),
            (10, "A veces creo que no soy buena persona.", None, 1, 0),
        ],
    },
    {
        "codigo": "WHO-5",
        "nombre": "WHO-5 Well-Being Index",
        "autor": "WHO Regional Office for Europe",
        "anio": 1998,
        "dominio": "bienestar",
        "tipo_escala": "likert",
        "likert_min": 0,
        "likert_max": 5,
        "n_items": 5,
        "tiempo_min": 2,
        "instruccion": "Indica cómo te has sentido durante las últimas dos semanas.",
        "citacion": "Topp CW et al. The WHO-5 Well-Being Index. Psychother Psychosom. 2015;84(3):167-176.",
        "items": [
            (1, "Me he sentido alegre y de buen humor.", None, 0, 0),
            (2, "Me he sentido tranquilo/a y relajado/a.", None, 0, 0),
            (3, "Me he sentido activo/a y con energía.", None, 0, 0),
            (4, "Me he despertado sintiéndome descansado/a.", None, 0, 0),
            (5, "Mi vida diaria ha estado llena de cosas que me interesan.", None, 0, 0),
        ],
    },
    {
        "codigo": "UCLA-3",
        "nombre": "UCLA Loneliness Scale — versión de 3 ítems",
        "autor": "Hughes, Waite, Hawkley & Cacioppo",
        "anio": 2004,
        "dominio": "soledad",
        "tipo_escala": "likert",
        "likert_min": 1,
        "likert_max": 3,
        "n_items": 3,
        "tiempo_min": 1,
        "instruccion": "Indica con qué frecuencia te sientes de la siguiente manera.",
        "citacion": "Hughes ME, Waite LJ, Hawkley LC, Cacioppo JT. A short scale for measuring loneliness. Res Aging. 2004;26(6):655-672.",
        "items": [
            (1, "¿Con qué frecuencia sientes que te falta compañía?", None, 0, 0),
            (2, "¿Con qué frecuencia te sientes excluido/a o dejado/a de lado?", None, 0, 0),
            (3, "¿Con qué frecuencia te sientes aislado/a de los demás?", None, 0, 0),
        ],
    },
]


FRASES = [
    # familia (1-5)
    (1, "familia", "En mi casa yo…"),
    (2, "familia", "Mi mamá siempre…"),
    (3, "familia", "Mi papá siempre…"),
    (4, "familia", "Cuando estoy con mi familia…"),
    (5, "familia", "Mis hermanos…"),
    # autoconcepto (6-10)
    (6, "autoconcepto", "Yo soy…"),
    (7, "autoconcepto", "Lo que más me gusta de mí es…"),
    (8, "autoconcepto", "Cuando me miro al espejo…"),
    (9, "autoconcepto", "Las personas piensan que yo…"),
    (10, "autoconcepto", "Lo que me cuesta aceptar de mí es…"),
    # escuela (11-15)
    (11, "escuela", "El colegio para mí…"),
    (12, "escuela", "Mis profesores…"),
    (13, "escuela", "Cuando tengo un examen…"),
    (14, "escuela", "Las tareas escolares…"),
    (15, "escuela", "Estudiar es…"),
    # pares (16-20)
    (16, "pares", "Mis amigos…"),
    (17, "pares", "Cuando estoy con otros chicos/as…"),
    (18, "pares", "Hablar con alguien nuevo…"),
    (19, "pares", "Cuando me invitan a una fiesta…"),
    (20, "pares", "La gente de mi edad…"),
    # emociones (21-25)
    (21, "emociones", "Cuando me enojo…"),
    (22, "emociones", "Cuando estoy triste yo…"),
    (23, "emociones", "Cuando algo me hace feliz…"),
    (24, "emociones", "Llorar es…"),
    (25, "emociones", "Cuando algo me preocupa…"),
    # miedos (26-30)
    (26, "miedos", "Lo que más me da miedo es…"),
    (27, "miedos", "Por las noches a veces…"),
    (28, "miedos", "Cuando estoy solo/a…"),
    (29, "miedos", "Lo que no quisiera que me pase es…"),
    (30, "miedos", "Si pudiera evitar algo, sería…"),
    # futuro (31-35)
    (31, "futuro", "Dentro de 5 años…"),
    (32, "futuro", "Cuando sea grande quiero…"),
    (33, "futuro", "Mi mayor sueño es…"),
    (34, "futuro", "El futuro me…"),
    (35, "futuro", "Lo que más espero de la vida es…"),
    # identidad (36-40)
    (36, "identidad", "Si pudiera cambiar algo de mí…"),
    (37, "identidad", "Lo que me hace diferente es…"),
    (38, "identidad", "Mis valores más importantes…"),
    (39, "identidad", "Cuando pienso en quién soy…"),
    (40, "identidad", "Lo que define quién soy es…"),
]


def main() -> None:
    db = SessionLocal()
    try:
        if db.query(BankInstrumento).count() > 0:
            print("Banco ya sembrado, salteando.")
            return

        for instr in INSTRUMENTOS:
            items = instr.pop("items")
            i = BankInstrumento(**instr)
            db.add(i)
            db.flush()
            for numero, texto, criterio, inverso, crisis in items:
                db.add(
                    BankItem(
                        instrumento_id=i.id,
                        numero=numero,
                        texto=texto,
                        criterio_dsm5=criterio,
                        inverso=inverso,
                        bandera_crisis=crisis,
                    )
                )

        for numero, area, texto in FRASES:
            db.add(
                BankFraseIncompleta(numero=numero, area=area, texto=texto)
            )

        db.commit()
        print(
            f"Sembrado: {db.query(BankInstrumento).count()} instrumentos, "
            f"{db.query(BankItem).count()} items, "
            f"{db.query(BankFraseIncompleta).count()} frases."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
