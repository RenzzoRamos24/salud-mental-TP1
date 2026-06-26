-- ============================================================================
-- Seed: Banco de instrumentos clínicos para Sami
-- ============================================================================
-- Carga 6 escalas validadas + 40 frases incompletas adaptadas de Sacks SSCT.
-- Referencia científica completa en BANCO_INSTRUMENTOS.md (raíz del repo).
--
-- Crea 3 tablas (idempotente):
--   bank_instrumento     -- catálogo de escalas/cuestionarios
--   bank_item            -- ítems de cada escala
--   bank_frase_incompleta -- banco proyectivo
--
-- Re-ejecutable: hace DELETE de las filas con código conocido antes de insertar.
-- Compatible con SQLite (motor del proyecto).
-- ============================================================================


-- ────────────────────────────────────────────────────────────────────────────
-- 1. DDL
-- ────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS bank_instrumento (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo         VARCHAR(20)  NOT NULL UNIQUE,    -- 'PHQ-A', 'GAD-7', etc.
    nombre         VARCHAR(200) NOT NULL,
    autor          VARCHAR(200) NOT NULL,
    anio           INTEGER      NOT NULL,
    dominio        VARCHAR(80)  NOT NULL,           -- depresion / ansiedad / autoestima / etc.
    tipo_escala    VARCHAR(20)  NOT NULL,           -- 'likert' | 'binaria' | 'texto_libre'
    likert_min     INTEGER,
    likert_max     INTEGER,
    n_items        INTEGER      NOT NULL,
    tiempo_min     INTEGER,                          -- minutos estimados
    instruccion    TEXT,
    citacion       TEXT         NOT NULL,            -- cita APA original
    validacion_es  TEXT,                             -- cita validación española
    activo         INTEGER      NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS bank_item (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    instrumento_id  INTEGER NOT NULL,
    numero          INTEGER NOT NULL,                -- orden dentro del instrumento
    texto           TEXT    NOT NULL,
    inverso         INTEGER NOT NULL DEFAULT 0,      -- 1 si la puntuación se invierte
    criterio_dsm5   TEXT,
    bandera_crisis  INTEGER NOT NULL DEFAULT 0,     -- 1 si dispara protocolo de crisis
    FOREIGN KEY (instrumento_id) REFERENCES bank_instrumento(id),
    UNIQUE (instrumento_id, numero)
);

CREATE TABLE IF NOT EXISTS bank_frase_incompleta (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    area   VARCHAR(40)  NOT NULL,                    -- familia, autoconcepto, escuela, etc.
    numero INTEGER      NOT NULL,                    -- orden global
    texto  TEXT         NOT NULL,
    activo INTEGER      NOT NULL DEFAULT 1,
    UNIQUE (numero)
);

CREATE INDEX IF NOT EXISTS idx_bank_item_instr ON bank_item(instrumento_id);
CREATE INDEX IF NOT EXISTS idx_bank_frase_area ON bank_frase_incompleta(area);


-- ────────────────────────────────────────────────────────────────────────────
-- 2. Limpieza idempotente
-- ────────────────────────────────────────────────────────────────────────────

DELETE FROM bank_item
WHERE instrumento_id IN (
    SELECT id FROM bank_instrumento
    WHERE codigo IN ('PHQ-A','GAD-7','SRQ-20','RSES','WHO-5','UCLA-3')
);

DELETE FROM bank_instrumento
WHERE codigo IN ('PHQ-A','GAD-7','SRQ-20','RSES','WHO-5','UCLA-3');

DELETE FROM bank_frase_incompleta WHERE numero BETWEEN 1 AND 40;


-- ────────────────────────────────────────────────────────────────────────────
-- 3. PHQ-A — Depresión adolescente
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO bank_instrumento
    (codigo, nombre, autor, anio, dominio, tipo_escala,
     likert_min, likert_max, n_items, tiempo_min, instruccion,
     citacion, validacion_es)
VALUES (
    'PHQ-A',
    'Patient Health Questionnaire — Adolescent',
    'Johnson, Harris, Spitzer & Williams',
    2002,
    'depresion',
    'likert',
    0, 3, 9, 4,
    'Durante las últimas dos semanas, ¿con qué frecuencia te ha molestado alguno de los siguientes problemas?',
    'Johnson JG, Harris ES, Spitzer RL, Williams JBW. The Patient Health Questionnaire for Adolescents. J Adolesc Health. 2002;30(3):196-204.',
    'Diez-Quevedo C, Rangil T, Sanchez-Planell L, Kroenke K, Spitzer RL. Validation and utility of the Patient Health Questionnaire in diagnosing mental disorders in 1003 general hospital Spanish inpatients. Psychosom Med. 2001;63(4):679-686.'
);

INSERT INTO bank_item (instrumento_id, numero, texto, criterio_dsm5, bandera_crisis) VALUES
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 1, 'Poco interés o placer en hacer cosas.', 'Anhedonia', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 2, 'Sentirte triste, decaído/a o sin esperanza.', 'Estado de ánimo deprimido', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 3, 'Problemas para dormir, dormir demasiado, o despertarte mucho durante la noche.', 'Insomnio/hipersomnia', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 4, 'Sentirte cansado/a o con poca energía.', 'Fatiga', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 5, 'Falta de apetito o comer en exceso.', 'Cambios de apetito/peso', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 6, 'Sentirte mal contigo mismo/a, sentir que eres un/a fracasado/a, o que has fallado a tu familia.', 'Culpa/inutilidad', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 7, 'Dificultad para concentrarte en cosas como tareas escolares, leer o ver televisión.', 'Concentración disminuida', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 8, 'Moverte o hablar tan lento que otras personas lo notan, o estar tan inquieto/a que te mueves mucho más de lo habitual.', 'Agitación/retardo psicomotor', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='PHQ-A'), 9, 'Pensar que estarías mejor muerto/a o tener pensamientos de hacerte daño de alguna manera.', 'Ideación suicida', 1);


-- ────────────────────────────────────────────────────────────────────────────
-- 4. GAD-7 — Ansiedad generalizada
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO bank_instrumento
    (codigo, nombre, autor, anio, dominio, tipo_escala,
     likert_min, likert_max, n_items, tiempo_min, instruccion,
     citacion, validacion_es)
VALUES (
    'GAD-7',
    'Generalized Anxiety Disorder — 7 item',
    'Spitzer, Kroenke, Williams & Löwe',
    2006,
    'ansiedad',
    'likert',
    0, 3, 7, 3,
    'Durante las últimas dos semanas, ¿con qué frecuencia te has sentido afectado/a por los siguientes problemas?',
    'Spitzer RL, Kroenke K, Williams JBW, Löwe B. A brief measure for assessing generalized anxiety disorder: the GAD-7. Arch Intern Med. 2006;166(10):1092-1097.',
    'García-Campayo J, Zamorano E, Ruiz MA, Pardo A, Pérez-Páramo M, López-Gómez V, Freire O, Rejas J. Cultural adaptation into Spanish of the Generalized Anxiety Disorder-7 (GAD-7) scale as a screening tool. Health Qual Life Outcomes. 2010;8:8.'
);

INSERT INTO bank_item (instrumento_id, numero, texto, criterio_dsm5) VALUES
    ((SELECT id FROM bank_instrumento WHERE codigo='GAD-7'), 1, 'Sentirte nervioso/a, ansioso/a o con los nervios de punta.', 'Ansiedad/preocupación excesiva'),
    ((SELECT id FROM bank_instrumento WHERE codigo='GAD-7'), 2, 'No poder dejar de preocuparte o no poder controlar tus preocupaciones.', 'Dificultad para controlar la preocupación'),
    ((SELECT id FROM bank_instrumento WHERE codigo='GAD-7'), 3, 'Preocuparte demasiado por diferentes cosas.', 'Preocupación excesiva'),
    ((SELECT id FROM bank_instrumento WHERE codigo='GAD-7'), 4, 'Tener dificultad para relajarte.', 'Tensión muscular'),
    ((SELECT id FROM bank_instrumento WHERE codigo='GAD-7'), 5, 'Estar tan inquieto/a que te resulta difícil quedarte quieto/a.', 'Inquietud'),
    ((SELECT id FROM bank_instrumento WHERE codigo='GAD-7'), 6, 'Irritarte o enojarte con facilidad.', 'Irritabilidad'),
    ((SELECT id FROM bank_instrumento WHERE codigo='GAD-7'), 7, 'Sentir miedo como si algo terrible fuera a pasar.', 'Aprensión');


-- ────────────────────────────────────────────────────────────────────────────
-- 5. SRQ-20 — Tamizaje general OMS
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO bank_instrumento
    (codigo, nombre, autor, anio, dominio, tipo_escala,
     likert_min, likert_max, n_items, tiempo_min, instruccion,
     citacion, validacion_es)
VALUES (
    'SRQ-20',
    'Self-Reporting Questionnaire 20 (OMS)',
    'Harding, de Arango, Baltazar, Climent et al.',
    1980,
    'tamizaje_general',
    'binaria',
    0, 1, 20, 7,
    'Las siguientes preguntas se refieren a cómo te has sentido durante los últimos 30 días. Responde "sí" si el problema te ha ocurrido y "no" si no te ha ocurrido.',
    'Harding TW, de Arango MV, Baltazar J, Climent CE, Ibrahim HH, Ladrido-Ignacio L, Murthy RS, Wig NN. Mental disorders in primary health care: a study of their frequency and diagnosis in four developing countries. Psychol Med. 1980;10(2):231-241.',
    'Beusenberg M, Orley J. A user''s guide to the Self-Reporting Questionnaire (SRQ). Geneva: WHO; 1994. WHO/MNH/PSF/94.8. Adaptaciones latinoamericanas vigentes.'
);

INSERT INTO bank_item (instrumento_id, numero, texto, bandera_crisis) VALUES
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  1, '¿Tienes frecuentemente dolores de cabeza?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  2, '¿Tienes mal apetito?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  3, '¿Duermes mal?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  4, '¿Te asustas con facilidad?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  5, '¿Sufres de temblor de manos?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  6, '¿Te sientes nervioso/a, tenso/a o aburrido/a?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  7, '¿Tienes mala digestión?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  8, '¿No puedes pensar con claridad?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'),  9, '¿Te sientes triste?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 10, '¿Lloras con mucha frecuencia?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 11, '¿Tienes dificultad para disfrutar tus actividades diarias?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 12, '¿Tienes dificultad para tomar decisiones?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 13, '¿Tienes dificultad en hacer tu trabajo o estudios (te causa sufrimiento)?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 14, '¿Eres incapaz de desempeñar un papel útil en tu vida?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 15, '¿Has perdido interés en las cosas?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 16, '¿Sientes que eres una persona inútil?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 17, '¿Has tenido la idea de acabar con tu vida?', 1),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 18, '¿Te sientes cansado/a todo el tiempo?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 19, '¿Tienes sensaciones desagradables en el estómago?', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='SRQ-20'), 20, '¿Te cansas con facilidad?', 0);


-- ────────────────────────────────────────────────────────────────────────────
-- 6. RSES — Autoestima de Rosenberg
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO bank_instrumento
    (codigo, nombre, autor, anio, dominio, tipo_escala,
     likert_min, likert_max, n_items, tiempo_min, instruccion,
     citacion, validacion_es)
VALUES (
    'RSES',
    'Rosenberg Self-Esteem Scale',
    'Rosenberg',
    1965,
    'autoestima',
    'likert',
    1, 4, 10, 3,
    'A continuación encontrarás una lista de afirmaciones sobre los sentimientos generales que tienes respecto a ti mismo/a. Indica cuán de acuerdo estás con cada una.',
    'Rosenberg M. Society and the Adolescent Self-Image. Princeton: Princeton University Press; 1965.',
    'Atienza FL, Moreno Y, Balaguer I. Análisis de la dimensionalidad de la Escala de Autoestima de Rosenberg en una muestra de adolescentes valencianos. Revista de Psicología Universitas Tarraconensis. 2000;22(1):29-42.'
);

INSERT INTO bank_item (instrumento_id, numero, texto, inverso) VALUES
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  1, 'Siento que soy una persona digna de aprecio, al menos en igual medida que los demás.', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  2, 'Estoy convencido/a de que tengo cualidades buenas.', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  3, 'Soy capaz de hacer las cosas tan bien como la mayoría de la gente.', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  4, 'Tengo una actitud positiva hacia mí mismo/a.', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  5, 'En general estoy satisfecho/a conmigo mismo/a.', 0),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  6, 'Siento que no tengo mucho de lo que estar orgulloso/a.', 1),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  7, 'En general, me inclino a pensar que soy un/a fracasado/a.', 1),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  8, 'Me gustaría poder sentir más respeto por mí mismo/a.', 1),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'),  9, 'Hay veces que realmente pienso que soy un/a inútil.', 1),
    ((SELECT id FROM bank_instrumento WHERE codigo='RSES'), 10, 'A veces creo que no soy buena persona.', 1);


-- ────────────────────────────────────────────────────────────────────────────
-- 7. WHO-5 — Bienestar
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO bank_instrumento
    (codigo, nombre, autor, anio, dominio, tipo_escala,
     likert_min, likert_max, n_items, tiempo_min, instruccion,
     citacion, validacion_es)
VALUES (
    'WHO-5',
    'WHO-5 Well-Being Index',
    'WHO Regional Office for Europe (orig. Bech)',
    1998,
    'bienestar',
    'likert',
    0, 5, 5, 2,
    'Por favor, indica cómo te has sentido durante las últimas dos semanas.',
    'Topp CW, Østergaard SD, Søndergaard S, Bech P. The WHO-5 Well-Being Index: a systematic review of the literature. Psychother Psychosom. 2015;84(3):167-176.',
    'Versión oficial OMS disponible en español; uso libre con atribución.'
);

INSERT INTO bank_item (instrumento_id, numero, texto) VALUES
    ((SELECT id FROM bank_instrumento WHERE codigo='WHO-5'), 1, 'Me he sentido alegre y de buen humor.'),
    ((SELECT id FROM bank_instrumento WHERE codigo='WHO-5'), 2, 'Me he sentido tranquilo/a y relajado/a.'),
    ((SELECT id FROM bank_instrumento WHERE codigo='WHO-5'), 3, 'Me he sentido activo/a y con energía.'),
    ((SELECT id FROM bank_instrumento WHERE codigo='WHO-5'), 4, 'Me he despertado sintiéndome descansado/a.'),
    ((SELECT id FROM bank_instrumento WHERE codigo='WHO-5'), 5, 'Mi vida diaria ha estado llena de cosas que me interesan.');


-- ────────────────────────────────────────────────────────────────────────────
-- 8. UCLA-3 — Soledad
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO bank_instrumento
    (codigo, nombre, autor, anio, dominio, tipo_escala,
     likert_min, likert_max, n_items, tiempo_min, instruccion,
     citacion, validacion_es)
VALUES (
    'UCLA-3',
    'UCLA Loneliness Scale — versión de 3 ítems',
    'Hughes, Waite, Hawkley & Cacioppo',
    2004,
    'soledad',
    'likert',
    1, 3, 3, 1,
    'Indica con qué frecuencia te sientes de la siguiente manera.',
    'Hughes ME, Waite LJ, Hawkley LC, Cacioppo JT. A short scale for measuring loneliness in large surveys: results from two population-based studies. Res Aging. 2004;26(6):655-672.',
    'Adaptaciones latinoamericanas vigentes desde la versión completa (Russell 1996).'
);

INSERT INTO bank_item (instrumento_id, numero, texto) VALUES
    ((SELECT id FROM bank_instrumento WHERE codigo='UCLA-3'), 1, '¿Con qué frecuencia sientes que te falta compañía?'),
    ((SELECT id FROM bank_instrumento WHERE codigo='UCLA-3'), 2, '¿Con qué frecuencia te sientes excluido/a o dejado/a de lado?'),
    ((SELECT id FROM bank_instrumento WHERE codigo='UCLA-3'), 3, '¿Con qué frecuencia te sientes aislado/a de los demás?');


-- ────────────────────────────────────────────────────────────────────────────
-- 9. Frases incompletas — adaptación SSCT (Sacks & Levy 1950) para adolescentes
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO bank_frase_incompleta (numero, area, texto) VALUES
    -- Familia
    ( 1, 'familia',      'En mi casa yo…'),
    ( 2, 'familia',      'Mi mamá siempre…'),
    ( 3, 'familia',      'Mi papá siempre…'),
    ( 4, 'familia',      'Cuando estoy con mi familia…'),
    ( 5, 'familia',      'Mis hermanos…'),
    -- Autoconcepto
    ( 6, 'autoconcepto', 'Yo soy…'),
    ( 7, 'autoconcepto', 'Lo que más me gusta de mí es…'),
    ( 8, 'autoconcepto', 'Cuando me miro al espejo…'),
    ( 9, 'autoconcepto', 'Las personas piensan que yo…'),
    (10, 'autoconcepto', 'Lo que me cuesta aceptar de mí es…'),
    -- Escuela
    (11, 'escuela',      'El colegio para mí…'),
    (12, 'escuela',      'Mis profesores…'),
    (13, 'escuela',      'Cuando tengo un examen…'),
    (14, 'escuela',      'Las tareas escolares…'),
    (15, 'escuela',      'Estudiar es…'),
    -- Pares
    (16, 'pares',        'Mis amigos…'),
    (17, 'pares',        'Cuando estoy con otros chicos/as…'),
    (18, 'pares',        'Hablar con alguien nuevo…'),
    (19, 'pares',        'Cuando me invitan a una fiesta…'),
    (20, 'pares',        'La gente de mi edad…'),
    -- Emociones
    (21, 'emociones',    'Cuando me enojo…'),
    (22, 'emociones',    'Cuando estoy triste yo…'),
    (23, 'emociones',    'Cuando algo me hace feliz…'),
    (24, 'emociones',    'Llorar es…'),
    (25, 'emociones',    'Cuando algo me preocupa…'),
    -- Miedos
    (26, 'miedos',       'Lo que más me da miedo es…'),
    (27, 'miedos',       'Por las noches a veces…'),
    (28, 'miedos',       'Cuando estoy solo/a…'),
    (29, 'miedos',       'Lo que no quisiera que me pase es…'),
    (30, 'miedos',       'Si pudiera evitar algo, sería…'),
    -- Futuro
    (31, 'futuro',       'Dentro de 5 años…'),
    (32, 'futuro',       'Cuando sea grande quiero…'),
    (33, 'futuro',       'Mi mayor sueño es…'),
    (34, 'futuro',       'El futuro me…'),
    (35, 'futuro',       'Lo que más espero de la vida es…'),
    -- Identidad
    (36, 'identidad',    'Si pudiera cambiar algo de mí…'),
    (37, 'identidad',    'Lo que me hace diferente es…'),
    (38, 'identidad',    'Mis valores más importantes…'),
    (39, 'identidad',    'Cuando pienso en quién soy…'),
    (40, 'identidad',    'Lo que define quién soy es…');


-- ============================================================================
-- Verificación rápida (opcional):
--   SELECT codigo, n_items FROM bank_instrumento ORDER BY id;
--   SELECT COUNT(*) FROM bank_item;             -- esperado: 54
--   SELECT COUNT(*) FROM bank_frase_incompleta; -- esperado: 40
-- ============================================================================
