import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuración de la aplicación"""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./mental_health.db"
    )

    # NLP — BERT multilingüe fine-tuned en XNLI para zero-shot en español
    # BETO (BERT en español) + XNLI permite clasificación multi-etiqueta sin traducción.
    MODEL_NAME: str = os.getenv(
        "MODEL_NAME",
        "Recognai/bert-base-spanish-wwm-cased-xnli"
    )
    MAX_QUESTIONS: int = 16  # 9 PHQ-9 + 7 GAD-7
    DEVICE: int = -1  # -1 = CPU, 0 = GPU

    # AI Provider activo para el chatbot conversacional.
    # Valores: "bert" (default, local) | "claude" (futuro) | "openai" (futuro).
    # La capa AIProvider (app/services/ai_provider.py) abstrae el motor para
    # poder enchufar APIs externas sin tocar el ChatService.
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "bert")

    # Plantilla de hipótesis en español (crítica para precisión del zero-shot)
    HYPOTHESIS_TEMPLATE: str = "Este texto expresa {}."

    # Condiciones clínicas a detectar.
    # Cada clave interna tiene (a) la hipótesis para el modelo y (b) un umbral calibrado.
    # Umbrales más bajos = mayor sensibilidad (importante en riesgo suicida).
    CONDICIONES: dict = {
        "depresion": {
            "hipotesis": "síntomas de depresión, tristeza profunda y desesperanza",
            "umbral": 0.55,
            "etiqueta": "Depresión",
        },
        "ansiedad": {
            "hipotesis": "síntomas de ansiedad, preocupación excesiva y nerviosismo",
            "umbral": 0.55,
            "etiqueta": "Ansiedad",
        },
        "tdah": {
            "hipotesis": "dificultad de atención, concentración, impulsividad o hiperactividad propia del TDAH",
            "umbral": 0.50,
            "etiqueta": "TDAH (déficit de atención / hiperactividad)",
        },
        "estres_academico": {
            "hipotesis": "estrés escolar, sobrecarga de tareas, exámenes y agotamiento por el colegio",
            "umbral": 0.55,
            "etiqueta": "Estrés escolar",
        },
        "soledad": {
            "hipotesis": "sentimientos de soledad, aislamiento social y falta de apoyo",
            "umbral": 0.55,
            "etiqueta": "Soledad / aislamiento",
        },
        "riesgo_suicida": {
            "hipotesis": "ideación suicida, pensamientos de autolesión o de no querer seguir viviendo",
            "umbral": 0.40,  # sensibilidad alta por seguridad clínica
            "etiqueta": "Riesgo suicida / autolesión",
        },
        "estabilidad": {
            "hipotesis": "bienestar emocional, estabilidad psicológica y equilibrio mental",
            "umbral": 0.60,
            "etiqueta": "Estabilidad emocional",
        },
    }

    # Keywords clínicos en español (booster de precisión).
    # Refuerzan el score del modelo cuando aparecen términos diagnósticos explícitos.
    KEYWORDS: dict = {
        "depresion": [
            "triste", "vacío", "vacia", "deprim", "sin ganas", "desesperanza",
            "no disfruto", "sin sentido", "llor", "inútil", "cansad", "agotad",
            "nada me importa", "no tengo ánimo", "sin motivación",
        ],
        "ansiedad": [
            "ansi", "nervios", "preocup", "miedo", "pánico", "panico",
            "taquicardia", "agobi", "respirar", "tenso", "tensa", "inquiet",
            "no puedo parar de pensar", "sobrepensar",
        ],
        "tdah": [
            "concentr", "distra", "impulsiv", "inquiet", "disper",
            "me olvido", "no termino", "me aburro rápido", "mente acelerada",
            "no puedo quedarme quiet", "hiperactiv", "postergar",
        ],
        "estres_academico": [
            "estres", "estrés", "carga", "exámen", "examen", "agobiad",
            "saturad", "no me alcanza el tiempo", "presión", "presion",
            "tareas", "trabajos", "entregas", "bimestral", "promedio",
            "notas", "profe", "colegio",
        ],
        "soledad": [
            "solo", "sola", "aislad", "nadie", "extraño a", "lejos de",
            "sin amigos", "no tengo con quien", "me dejaron de lado",
            "no encajo", "no tengo amigos",
        ],
        "riesgo_suicida": [
            "morir", "no estar", "hacerme daño", "suicid", "no quiero vivir",
            "terminar con todo", "desaparecer", "no despertar",
            "mejor no estar", "cortar", "autolesion", "autolesión",
        ],
    }

    # Boost de keywords: cada match suma este valor (capeado en MAX_BOOST)
    KEYWORD_BOOST_PER_MATCH: float = 0.05
    KEYWORD_BOOST_MAX: float = 0.25

    # ─────────────────────────────────────────────────────────────────
    # PHQ-9 + GAD-7 — Escalas clínicas estructuradas
    # ─────────────────────────────────────────────────────────────────
    #
    # Cada ítem mide un criterio DSM-5 específico y se puntúa en escala
    # Likert 0-3 (frecuencia en las últimas 2 semanas):
    #   0 = Nunca
    #   1 = Algunos días
    #   2 = Más de la mitad de los días
    #   3 = Casi todos los días
    #
    # El sistema acepta texto libre del usuario y BERT propone un score 0-3.
    # Si la confianza es baja (< UMBRAL_CONFIANZA_LIKERT) el frontend muestra
    # los 4 botones para que el usuario seleccione manualmente.

    OPCIONES_LIKERT: list = [
        {"valor": 0, "etiqueta": "Nunca", "descripcion": "Ningún día"},
        {"valor": 1, "etiqueta": "Algunos días", "descripcion": "Varios días"},
        {"valor": 2, "etiqueta": "Más de la mitad de los días", "descripcion": "Mayoría de días"},
        {"valor": 3, "etiqueta": "Casi todos los días", "descripcion": "Casi a diario"},
    ]

    # Plantilla zero-shot para clasificar la frecuencia descrita en el texto.
    # Las hipótesis se reescriben por ítem para apuntar al criterio DSM-5.
    HYPOTHESIS_TEMPLATE_LIKERT: str = "Este texto describe que esto ocurre {}."

    # Confianza mínima del modelo para aceptar el score sin pedir confirmación.
    # Con 4 etiquetas mutuamente excluyentes el baseline es ~25%, por eso el
    # umbral se mantiene en 0.40 (suficientemente sobre baseline pero no
    # demasiado alto como para pedir confirmación a cada respuesta).
    UMBRAL_CONFIANZA_LIKERT: float = 0.40
    # Si la diferencia entre la frecuencia más probable y la segunda es ≥ esta
    # cifra, también aceptamos automáticamente aunque el top no llegue al umbral.
    MARGEN_MINIMO_LIKERT: float = 0.10

    # Mensajes empáticos para variar el tono del bot.
    # ACKS_CONTINUAR: se anteponen como bubble antes de la siguiente pregunta
    # cuando BERT aceptó el score automáticamente.
    ACKS_CONTINUAR: list = [
        "Gracias por contarme.",
        "Te entiendo.",
        "Vale, te escucho.",
        "Aprecio que me lo cuentes.",
        "Entiendo lo que me dices.",
        "Eso es importante, gracias por compartirlo.",
        "Te sigo.",
        "Ok, te entiendo.",
    ]
    # ACKS_PEDIR_FRECUENCIA: se usan cuando la confianza es baja y hay que
    # mostrar los 4 botones. Reflejan empatía + transición a la pregunta de
    # frecuencia, en lenguaje natural y variado.
    ACKS_PEDIR_FRECUENCIA: list = [
        "Entiendo. Cuéntame, ¿qué tan seguido te pasa esto?",
        "Gracias por contarme. Para entenderte mejor, ¿con qué frecuencia te ocurre?",
        "Te escucho. ¿Es algo que te pasa todos los días, o solo a veces?",
        "Vale, te sigo. ¿Cómo describirías la frecuencia con la que te ocurre?",
        "Eso suena importante. ¿Cada cuánto sientes esto?",
        "Aprecio que me lo cuentes. ¿Qué tan frecuente dirías que es?",
        "Te entiendo. Para tenerlo más claro, ¿qué tan seguido te pasa?",
        "Ok, gracias por abrirte. ¿Esto te ocurre algunos días, casi siempre, o todo el tiempo?",
    ]

    # Banco de ítems PHQ-9 (depresión, 9 ítems, total 0-27)
    PHQ9_ITEMS: list = [
        {
            "id": "phq9_1",
            "modulo": "PHQ-9",
            "numero_oficial": 1,
            "criterio_dsm5": "Pérdida de interés o placer (anhedonia)",
            "texto": (
                "Cuéntame, en estas últimas semanas ¿cómo has estado con las "
                "cosas que antes te gustaban —música, salir, hobbies, estudiar—? "
                "¿Sigues disfrutándolas como antes?"
            ),
            "hipotesis_likert": "pérdida de interés o falta de placer al hacer cosas",
            "keywords_signal": [
                "no disfruto", "nada me da alegría", "no me gusta nada",
                "perdí el interés", "ya nada me importa", "sin ganas",
            ],
        },
        {
            "id": "phq9_2",
            "modulo": "PHQ-9",
            "numero_oficial": 2,
            "criterio_dsm5": "Estado de ánimo deprimido",
            "texto": (
                "¿Y tu ánimo cómo ha estado? Quiero saber si te has sentido "
                "decaído/a, triste o sin esperanza estos días."
            ),
            "hipotesis_likert": "sentirse decaído, deprimido, vacío o sin esperanza",
            "keywords_signal": [
                "triste", "deprim", "vacío", "vacia", "sin esperanza",
                "desesperanza", "decaíd", "decaid",
            ],
        },
        {
            "id": "phq9_3",
            "modulo": "PHQ-9",
            "numero_oficial": 3,
            "criterio_dsm5": "Alteración del sueño",
            "texto": (
                "Hablemos un poco de tu sueño. ¿Has estado durmiendo bien, te "
                "cuesta conciliarlo, o quizás duermes más de la cuenta?"
            ),
            "hipotesis_likert": "problemas para dormir o dormir en exceso",
            "keywords_signal": [
                "no puedo dormir", "insomnio", "duermo mucho", "duermo todo el día",
                "me despierto", "no concilio", "trasnoch",
            ],
        },
        {
            "id": "phq9_4",
            "modulo": "PHQ-9",
            "numero_oficial": 4,
            "criterio_dsm5": "Fatiga o pérdida de energía",
            "texto": (
                "¿Y la energía? ¿Sientes que tienes fuerzas para tu día a día, "
                "o has estado más cansado/a de lo normal, incluso después de descansar?"
            ),
            "hipotesis_likert": "sentirse cansado, agotado o con poca energía",
            "keywords_signal": [
                "cansad", "agotad", "sin energía", "sin energia", "fatiga",
                "no tengo fuerzas", "exhaust",
            ],
        },
        {
            "id": "phq9_5",
            "modulo": "PHQ-9",
            "numero_oficial": 5,
            "criterio_dsm5": "Cambio en el apetito o peso",
            "texto": (
                "Cuéntame, ¿cómo va tu apetito? ¿Comes parecido a siempre, o "
                "has notado que comes menos —o más— de lo normal?"
            ),
            "hipotesis_likert": "tener poco apetito o comer en exceso",
            "keywords_signal": [
                "no tengo hambre", "como mucho", "atracon", "atracón",
                "perdí el apetito", "comer de más", "sin apetito",
            ],
        },
        {
            "id": "phq9_6",
            "modulo": "PHQ-9",
            "numero_oficial": 6,
            "criterio_dsm5": "Sentimientos de inutilidad o culpa",
            "texto": (
                "A veces uno se siente mal consigo mismo —como si no fuera "
                "suficiente, o como si le hubiera fallado a alguien importante. "
                "¿Te ha pasado algo así estas semanas?"
            ),
            "hipotesis_likert": "sentirse inútil, fracasado o culpable",
            "keywords_signal": [
                "inútil", "inutil", "fracasad", "soy un fracaso", "no sirvo",
                "le fallé", "culpa", "no valgo nada", "decepción",
            ],
        },
        {
            "id": "phq9_7",
            "modulo": "PHQ-9",
            "numero_oficial": 7,
            "criterio_dsm5": "Dificultad para concentrarse",
            "texto": (
                "¿Cómo va tu concentración? Por ejemplo, cuando lees algo, "
                "ves una serie o estás en clase, ¿logras mantenerte enfocado/a?"
            ),
            "hipotesis_likert": "tener dificultad para concentrarse",
            "keywords_signal": [
                "no me concentro", "me distra", "no puedo concentrarme",
                "se me va la cabeza", "no retengo", "leer y no entiendo",
            ],
        },
        {
            "id": "phq9_8",
            "modulo": "PHQ-9",
            "numero_oficial": 8,
            "criterio_dsm5": "Enlentecimiento o agitación psicomotora",
            "texto": (
                "Cuéntame si has notado algo distinto en cómo te mueves o "
                "hablas: ¿alguien te ha dicho que estás más lento/a de lo "
                "usual, o tú sientes que no puedes parar de moverte?"
            ),
            "hipotesis_likert": "moverse o hablar muy lento, o estar muy inquieto",
            "keywords_signal": [
                "muy lento", "me muevo lento", "no puedo quedarme quieto",
                "inquiet", "agitad", "acelerad",
            ],
        },
        {
            "id": "phq9_9",
            "modulo": "PHQ-9",
            "numero_oficial": 9,
            "criterio_dsm5": "Ideación suicida o de autolesión",
            "texto": (
                "Esta pregunta la hago con cuidado, porque me importa cómo "
                "estás. ¿En estas semanas has tenido pensamientos de hacerte "
                "daño, de no estar, o de que sería mejor desaparecer? "
                "Puedes responder con confianza, esto es para cuidarte."
            ),
            "hipotesis_likert": (
                "pensamientos de hacerse daño o de estar mejor muerto"
            ),
            "keywords_signal": [
                "hacerme daño", "mejor muerto", "no quiero vivir", "suicid",
                "desaparecer", "no despertar", "terminar con todo", "autolesion",
                "autolesión", "cortar",
            ],
            "es_critica": True,  # cualquier score ≥ 1 dispara protocolo de emergencia
        },
    ]

    # Banco de ítems GAD-7 (ansiedad generalizada, 7 ítems, total 0-21)
    GAD7_ITEMS: list = [
        {
            "id": "gad7_1",
            "modulo": "GAD-7",
            "numero_oficial": 1,
            "criterio_dsm5": "Ansiedad o nerviosismo excesivo",
            "texto": (
                "Cuéntame cómo has estado con los nervios. ¿Te has sentido más "
                "ansioso/a o con los nervios de punta últimamente?"
            ),
            "hipotesis_likert": "sentirse nervioso, ansioso o con los nervios de punta",
            "keywords_signal": [
                "nervios", "ansi", "tens", "con los nervios", "nerviosa",
                "nerviosismo",
            ],
        },
        {
            "id": "gad7_2",
            "modulo": "GAD-7",
            "numero_oficial": 2,
            "criterio_dsm5": "Dificultad para controlar la preocupación",
            "texto": (
                "Y cuando empiezas a preocuparte, ¿logras parar de pensar en "
                "eso, o sientes que la preocupación se te escapa de las manos?"
            ),
            "hipotesis_likert": "no poder dejar de preocuparse o controlar la preocupación",
            "keywords_signal": [
                "no puedo dejar de preocuparme", "no controlo", "no paro de pensar",
                "sobrepensar", "rumiar", "le doy vueltas",
            ],
        },
        {
            "id": "gad7_3",
            "modulo": "GAD-7",
            "numero_oficial": 3,
            "criterio_dsm5": "Preocupación excesiva sobre múltiples temas",
            "texto": (
                "¿Te ha pasado que te preocupas por muchas cosas a la vez "
                "—los estudios, la familia, el futuro, la salud— y todo se "
                "junta en tu cabeza?"
            ),
            "hipotesis_likert": "preocuparse demasiado por muchas cosas diferentes",
            "keywords_signal": [
                "me preocupo por todo", "todo me preocupa", "preocupación constante",
                "preocup",
            ],
        },
        {
            "id": "gad7_4",
            "modulo": "GAD-7",
            "numero_oficial": 4,
            "criterio_dsm5": "Tensión muscular o dificultad para relajarse",
            "texto": (
                "Hablemos del cuerpo: ¿logras relajarte, o sientes que estás "
                "todo el tiempo tenso/a, con el cuerpo rígido o sin poder desconectar?"
            ),
            "hipotesis_likert": "tener dificultad para relajarse",
            "keywords_signal": [
                "no me puedo relajar", "no logro relajarme", "tens", "rígido",
                "rigida", "contracturad",
            ],
        },
        {
            "id": "gad7_5",
            "modulo": "GAD-7",
            "numero_oficial": 5,
            "criterio_dsm5": "Inquietud o sensación de estar al límite",
            "texto": (
                "¿Has sentido como una inquietud por dentro, como si no "
                "pudieras quedarte quieto/a, ni siquiera cuando intentas descansar?"
            ),
            "hipotesis_likert": "estar tan inquieto que es difícil quedarse quieto",
            "keywords_signal": [
                "inquiet", "no me quedo quiet", "tengo que moverme",
                "al límite", "al limite",
            ],
        },
        {
            "id": "gad7_6",
            "modulo": "GAD-7",
            "numero_oficial": 6,
            "criterio_dsm5": "Irritabilidad",
            "texto": (
                "Cuéntame, ¿has estado más irritable o de mal humor estos "
                "días? Como si las cosas pequeñas te fastidiaran más de lo normal."
            ),
            "hipotesis_likert": "irritarse o molestarse fácilmente",
            "keywords_signal": [
                "irrit", "me molesto", "me enojo rápido", "todo me molesta",
                "explot", "malhumorad",
            ],
        },
        {
            "id": "gad7_7",
            "modulo": "GAD-7",
            "numero_oficial": 7,
            "criterio_dsm5": "Sensación de peligro o catástrofe inminente",
            "texto": (
                "A veces uno tiene la sensación de que algo malo va a pasar, "
                "sin saber muy bien qué. ¿Te ha pasado algo así últimamente?"
            ),
            "hipotesis_likert": (
                "sentir miedo como si algo terrible fuera a pasar"
            ),
            "keywords_signal": [
                "algo malo va a pasar", "siento que va a pasar algo",
                "miedo", "pánico", "panico", "catástrofe", "catastrofe",
                "presentimiento",
            ],
        },
    ]

    # Severidad PHQ-9 (puntaje total 0-27) — ver Kroenke & Spitzer (2001)
    PHQ9_SEVERIDAD: list = [
        {"min": 0, "max": 4, "nivel": "Mínima", "accion": "Solo monitoreo"},
        {"min": 5, "max": 9, "nivel": "Leve", "accion": "Recomendaciones de autocuidado"},
        {"min": 10, "max": 14, "nivel": "Moderada", "accion": "Alerta al psicólogo"},
        {"min": 15, "max": 19, "nivel": "Moderada-severa", "accion": "Alerta urgente"},
        {"min": 20, "max": 27, "nivel": "Severa", "accion": "Protocolo de emergencia"},
    ]

    # Severidad GAD-7 (puntaje total 0-21) — ver Spitzer & Löwe (2006)
    GAD7_SEVERIDAD: list = [
        {"min": 0, "max": 4, "nivel": "Mínima", "accion": "Solo monitoreo"},
        {"min": 5, "max": 9, "nivel": "Leve", "accion": "Recomendaciones de autocuidado"},
        {"min": 10, "max": 14, "nivel": "Moderada", "accion": "Alerta al psicólogo"},
        {"min": 15, "max": 21, "nivel": "Severa", "accion": "Alerta urgente"},
    ]

    # App
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Mental Health Chatbot"

    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # ─────────────────────────────────────────────────────────────────
    # AUTENTICACIÓN
    # ─────────────────────────────────────────────────────────────────
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-production-please")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h

    # Recuperación de contraseña
    PASSWORD_RESET_TOKEN_MINUTOS: int = 15

    # Consentimiento informado
    CONSENT_VERSION_ACTUAL: str = "1.0"

    # ─────────────────────────────────────────────────────────────────
    # HU-23: Backups automáticos
    # ─────────────────────────────────────────────────────────────────
    BACKUP_HORA_DIARIA: int = int(os.getenv("BACKUP_HORA_DIARIA", "2"))      # 02:00 AM
    BACKUP_RETENCION_DIAS: int = int(os.getenv("BACKUP_RETENCION_DIAS", "14"))

settings = Settings()
