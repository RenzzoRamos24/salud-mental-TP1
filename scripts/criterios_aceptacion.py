# -*- coding: utf-8 -*-
"""
Criterios de aceptación en formato Gherkin para todas las HU del backlog.

Cada HU mapea a una lista de escenarios. Cada escenario es
    {"titulo": str, "pasos": [str, ...]}
donde los pasos empiezan con Dado / Cuando / Entonces / Y.

Los criterios están redactados contra el código real (endpoint + servicio +
vista), no contra la documentación. La clave `ESTADO` registra la verificación.
"""

# ── Estado verificado en código (auditoría) ──────────────────────────────
OK = "Implementado"
PARCIAL = "Parcial"
NO = "No implementado"

ESTADO = {}

CRITERIOS = {}


def _hu(hu_id, estado, *escenarios):
    ESTADO[hu_id] = estado
    CRITERIOS[hu_id] = [{"titulo": t, "pasos": list(p)} for t, p in escenarios]


# ═══════════════════════════════════════════════════════════════════════
# SPRINT 1 — Autenticación y consentimiento
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-01", OK,
    ("Registro exitoso de un estudiante", [
        "Dado que soy un visitante no autenticado en la pantalla /register",
        "Y elijo el rol \"estudiante\"",
        "Cuando envío nombre, apellido, correo institucional y una contraseña válida",
        "Entonces el sistema responde 201 y crea el usuario con rol \"estudiante\"",
        "Y recibo un token JWT que me deja autenticado",
        "Y soy redirigido a la pantalla de consentimiento informado",
    ]),
    ("Correo ya registrado", [
        "Dado que ya existe una cuenta con el correo \"ana@colegio.edu.pe\"",
        "Cuando intento registrarme con ese mismo correo",
        "Entonces el sistema responde 400 con el mensaje de correo ya registrado",
        "Y no se crea un segundo usuario",
    ]),
    ("Contraseña que no cumple la política", [
        "Dado que estoy en el formulario de registro",
        "Cuando envío una contraseña de menos de 8 caracteres",
        "Entonces el sistema responde 422 con el detalle de validación",
        "Y no se crea la cuenta",
    ]),
    ("Rol restringido: el administrador no se registra por la UI", [
        "Dado que el selector de rol solo ofrece estudiante, psicólogo y padre",
        "Cuando envío una petición de registro con role=\"admin\"",
        "Entonces el sistema responde 422 y rechaza el alta",
        "Y el administrador solo puede crearse con el script seed_admin",
    ]),
)

_hu("HU-02", OK,
    ("Inicio de sesión válido con enrutamiento por rol", [
        "Dado que tengo una cuenta activa con rol \"psicologo\"",
        "Cuando inicio sesión con mi correo y contraseña correctos",
        "Entonces el sistema responde 200 con un token JWT que contiene mi rol",
        "Y soy redirigido al panel de psicóloga (/psicologo)",
    ]),
    ("Credenciales incorrectas", [
        "Dado que estoy en la pantalla de login",
        "Cuando envío una contraseña incorrecta",
        "Entonces el sistema responde 401 con \"credenciales inválidas\"",
        "Y no se emite ningún token",
    ]),
    ("Acceso a una ruta de otro rol", [
        "Dado que estoy autenticado como estudiante",
        "Cuando intento entrar a /admin",
        "Entonces el guard del router me redirige a mi panel de inicio",
        "Y el backend responde 403 si llamo directamente al endpoint",
    ]),
)

_hu("HU-03", OK,
    ("Aceptación del consentimiento informado", [
        "Dado que acabo de registrarme y no he aceptado el consentimiento",
        "Cuando leo el documento y pulso \"Acepto\"",
        "Entonces el sistema registra el consentimiento con su versión y fecha",
        "Y a partir de ese momento puedo navegar al resto del sistema",
    ]),
    ("Bloqueo mientras no se acepta", [
        "Dado que estoy autenticado pero no he aceptado el consentimiento",
        "Cuando intento entrar a cualquier ruta protegida",
        "Entonces el router me redirige siempre a /consent",
    ]),
    ("Consulta del estado del consentimiento", [
        "Dado que ya acepté el consentimiento",
        "Cuando el frontend consulta GET /consent/estado",
        "Entonces recibe aceptado=true con la versión aceptada",
    ]),
)

_hu("HU-26", OK,
    ("Cierre de sesión", [
        "Dado que tengo una sesión activa",
        "Cuando pulso \"Cerrar sesión\"",
        "Entonces el token se elimina del almacenamiento local del navegador",
        "Y soy redirigido a la pantalla de login",
    ]),
    ("Token inválido tras expirar", [
        "Dado que mi token JWT ha expirado",
        "Cuando realizo cualquier petición autenticada",
        "Entonces el interceptor recibe un 401 y me devuelve al login automáticamente",
    ]),
)

_hu("HU-27", OK,
    ("Solicitud de recuperación de contraseña", [
        "Dado que olvidé mi contraseña",
        "Cuando ingreso mi correo en /forgot-password",
        "Entonces el sistema genera un token de recuperación de un solo uso",
        "Y responde siempre con el mismo mensaje neutro para no revelar si el correo existe",
    ]),
    ("Restablecimiento con token válido", [
        "Dado que tengo un token de recuperación vigente",
        "Cuando envío el token junto con la nueva contraseña",
        "Entonces el sistema actualiza el hash de mi contraseña",
        "Y el token queda marcado como usado",
        "Y puedo iniciar sesión con la nueva contraseña",
    ]),
    ("Token vencido o ya utilizado", [
        "Dado que mi token de recuperación ya fue usado o caducó",
        "Cuando intento restablecer la contraseña con él",
        "Entonces el sistema responde 400 y no modifica la contraseña",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 2 — Onboarding y gestión de usuarios
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-06", OK,
    ("Menú principal según el rol", [
        "Dado que inicié sesión y acepté el consentimiento",
        "Cuando entro a mi pantalla de inicio",
        "Entonces veo únicamente las secciones habilitadas para mi rol",
        "Y el estudiante ve Inicio, Cuestionario, Reuniones, Recursos, Mi bienestar y Mi Perfil",
    ]),
    ("Acceso directo a la acción pendiente", [
        "Dado que tengo un cuestionario asignado sin responder",
        "Cuando abro el menú principal",
        "Entonces veo una tarjeta destacada que me lleva directo a responderlo",
    ]),
)

_hu("HU-20", OK,
    ("Listado de usuarios del sistema", [
        "Dado que estoy autenticado como administrador",
        "Cuando abro la gestión de usuarios",
        "Entonces veo el listado con nombre, correo, rol y fecha de alta",
        "Y puedo filtrar por rol (estudiante, psicólogo, padre, admin)",
    ]),
    ("Estadísticas de la base de usuarios", [
        "Dado que estoy en el panel de administración",
        "Cuando se carga el dashboard",
        "Entonces veo el total de usuarios agregado por rol",
    ]),
    ("Acceso restringido al rol administrador", [
        "Dado que estoy autenticado como psicóloga",
        "Cuando llamo a GET /admin/users",
        "Entonces el sistema responde 403",
    ]),
)

_hu("HU-04", OK,
    ("Actualización de los datos personales", [
        "Dado que estoy autenticado y en Mi Perfil",
        "Cuando modifico mi nombre y apellido y guardo",
        "Entonces el sistema responde 200 con los datos actualizados",
        "Y el nuevo nombre aparece de inmediato en la barra superior",
    ]),
    ("El correo y el rol no son editables", [
        "Dado que estoy editando mi perfil",
        "Cuando intento cambiar mi correo o mi rol",
        "Entonces el sistema ignora esos campos y conserva los valores originales",
    ]),
)

_hu("HU-05", OK,
    ("Eliminación de la propia cuenta", [
        "Dado que estoy autenticado y quiero ejercer mi derecho de supresión",
        "Cuando confirmo la eliminación con mi contraseña y el texto de confirmación",
        "Entonces el sistema elimina mi cuenta y mis datos asociados",
        "Y mi sesión se cierra y quedo en la pantalla de login",
    ]),
    ("Confirmación incorrecta", [
        "Dado que estoy en el diálogo de eliminación de cuenta",
        "Cuando escribo mal la contraseña o el texto de confirmación",
        "Entonces el sistema responde 400 y la cuenta se mantiene intacta",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 3 — Cuestionarios validados y NLP
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-08", OK,
    ("Respuesta a un cuestionario con escalas validadas", [
        "Dado que mi psicóloga me asignó un cuestionario que incluye PHQ-A y GAD-7",
        "Cuando abro la aplicación asignada",
        "Entonces veo los ítems con la redacción literal publicada de cada instrumento",
        "Y cada ítem muestra las opciones de su escala oficial",
    ]),
    ("Cierre del cuestionario con todos los ítems respondidos", [
        "Dado que respondí todos los ítems obligatorios",
        "Cuando pulso \"Enviar\"",
        "Entonces el estado de la aplicación pasa a \"completado\"",
        "Y el sistema calcula el resultado y lo deja disponible para la psicóloga",
        "Y yo solo veo una confirmación de cierre, nunca el resultado clínico",
    ]),
    ("Intento de cierre con ítems sin responder", [
        "Dado que dejé ítems obligatorios en blanco",
        "Cuando intento enviar el cuestionario",
        "Entonces el sistema me indica cuántos ítems faltan y no cierra la aplicación",
    ]),
    ("Puntaje calculado con los cortes publicados", [
        "Dado un bloque PHQ-A respondido con un puntaje total de 12",
        "Cuando el sistema evalúa el bloque",
        "Entonces la severidad se determina con los cortes de Johnson (2002) y no con umbrales inventados",
    ]),
)

_hu("HU-09", OK,
    ("Clasificación de una frase incompleta con BETO", [
        "Dado que el estudiante completó la frase \"Mi familia... me hace sentir solo\"",
        "Cuando el sistema procesa la respuesta abierta",
        "Entonces BETO zero-shot devuelve puntajes para las 8 categorías emocionales",
        "Y la clasificación es multietiqueta, no una única categoría excluyente",
    ]),
    ("Frase sin contenido evaluable", [
        "Dado que el estudiante dejó la frase vacía o escribió menos de 3 caracteres",
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

_hu("HU-12", OK,
    ("Consulta del historial propio de cuestionarios", [
        "Dado que soy estudiante y he completado tres cuestionarios",
        "Cuando abro \"Mis cuestionarios\"",
        "Entonces veo cada aplicación con su nombre, fecha y estado",
        "Y no se muestra ningún puntaje, severidad ni bandera de riesgo",
    ]),
    ("Historial vacío", [
        "Dado que aún no tengo cuestionarios asignados",
        "Cuando abro \"Mis cuestionarios\"",
        "Entonces veo un estado vacío explicativo y ningún error",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 4 — Contenido psicoeducativo, SOS y satisfacción
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-11", OK,
    ("Acceso al catálogo de recursos", [
        "Dado que soy un usuario autenticado con consentimiento aceptado",
        "Cuando abro la sección Recursos",
        "Entonces veo los contenidos publicados por el colegio",
        "Y puedo filtrar por categoría",
    ]),
)

_hu("HU-29", OK,
    ("Lectura de un contenido psicoeducativo", [
        "Dado que estoy en el listado de recursos",
        "Cuando abro un artículo, video o infografía",
        "Entonces veo su contenido completo con su categoría y fecha",
    ]),
    ("Contenido inexistente o despublicado", [
        "Dado que abro el enlace de un contenido eliminado",
        "Cuando el sistema intenta cargarlo",
        "Entonces responde 404 y la vista muestra un mensaje claro",
    ]),
)

_hu("HU-31", OK,
    ("Activación del botón SOS", [
        "Dado que estoy en una situación de crisis emocional",
        "Cuando pulso el botón SOS y confirmo",
        "Entonces el sistema registra un evento SOS con mi identificador, origen y fecha",
        "Y me muestra de inmediato la Línea 113 del MINSA y los contactos de ayuda",
    ]),
    ("Disponibilidad permanente del botón", [
        "Dado que soy un estudiante autenticado",
        "Cuando navego por cualquier pantalla de mi panel",
        "Entonces el botón SOS está visible y accesible sin pasos intermedios",
    ]),
    ("El evento queda visible para la psicóloga", [
        "Dado que activé el SOS",
        "Cuando la psicóloga abre su bandeja de alertas SOS",
        "Entonces mi evento aparece como abierto y pendiente de atención",
    ]),
)

_hu("HU-25", OK,
    ("Envío de la encuesta de satisfacción", [
        "Dado que soy un usuario autenticado",
        "Cuando completo y envío la encuesta de satisfacción",
        "Entonces el sistema responde 201 y guarda mis respuestas",
        "Y puedo consultar después la encuesta que envié",
    ]),
    ("Respuestas fuera de rango", [
        "Dado que la escala de cada ítem es de 1 a 5",
        "Cuando envío un valor fuera de ese rango",
        "Entonces el sistema responde 422 y no guarda la encuesta",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 5 — Panel del psicólogo
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-14", OK,
    ("Ingreso al panel profesional", [
        "Dado que tengo una cuenta con rol \"psicologo\"",
        "Cuando inicio sesión correctamente",
        "Entonces soy dirigida al dashboard de psicóloga y no al panel de estudiante",
    ]),
)

_hu("HU-15", OK,
    ("Dashboard con métricas generales", [
        "Dado que soy la psicóloga y tengo estudiantes a cargo",
        "Cuando abro el dashboard",
        "Entonces veo el total de estudiantes, los cuestionarios pendientes y completados",
        "Y veo la distribución de estudiantes por nivel de riesgo",
    ]),
    ("Sin datos todavía", [
        "Dado que ningún estudiante ha completado un cuestionario",
        "Cuando abro el dashboard",
        "Entonces las métricas muestran cero y se explica que aún no hay datos",
    ]),
)

_hu("HU-16", OK,
    ("Bandera de crisis por ideación en PHQ-A", [
        "Dado que un estudiante respondió el ítem 9 del PHQ-A con un valor mayor o igual a 1",
        "Cuando el sistema evalúa su cuestionario",
        "Entonces se levanta una bandera de crisis para ese estudiante",
        "Y aparece en la bandeja de alertas de la psicóloga",
    ]),
    ("Bandera de crisis por SRQ-20", [
        "Dado que un estudiante respondió afirmativamente el ítem 17 del SRQ-20",
        "Cuando el sistema evalúa su cuestionario",
        "Entonces se levanta la bandera de crisis correspondiente",
    ]),
    ("Bandera por ideación detectada en texto libre", [
        "Dado que BETO asigna a una frase la categoría de ideación con puntaje mayor o igual a 0.40",
        "Cuando el sistema evalúa la aplicación",
        "Entonces se levanta una bandera de crisis basada en la señal textual",
        "Y el reporte indica la frase y el puntaje que la originaron",
    ]),
    ("Ausencia de banderas", [
        "Dado que ningún criterio de crisis se cumple",
        "Cuando el sistema evalúa la aplicación",
        "Entonces no se genera ninguna alerta y el caso sigue el flujo normal",
    ]),
)

_hu("HU-17", OK,
    ("Consulta del historial clínico de un estudiante", [
        "Dado que soy la psicóloga a cargo de un estudiante",
        "Cuando abro su ficha",
        "Entonces veo todas sus aplicaciones con puntajes, severidades y banderas",
        "Y veo sus citas, notas clínicas y eventos SOS",
    ]),
    ("Acceso denegado a otro rol", [
        "Dado que soy un estudiante autenticado",
        "Cuando llamo al endpoint de historial de otro estudiante",
        "Entonces el sistema responde 403",
    ]),
)

_hu("HU-19", OK,
    ("Agendamiento de una cita", [
        "Dado que soy la psicóloga y quiero atender a un estudiante",
        "Cuando creo una cita con estudiante, fecha, hora y modalidad",
        "Entonces el sistema responde 201 y la cita queda registrada",
        "Y el estudiante ve la cita en su panel de Reuniones",
    ]),
    ("Fecha en el pasado", [
        "Dado que estoy creando una cita",
        "Cuando indico una fecha y hora anteriores al momento actual",
        "Entonces el sistema rechaza la creación y explica el motivo",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 6 — Administración
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-22", OK,
    ("Auditoría de accesos", [
        "Dado que soy administrador",
        "Cuando abro la auditoría de accesos",
        "Entonces veo cada request con fecha, usuario, rol, IP, endpoint y código de estado",
        "Y puedo paginar y filtrar por rol y por endpoint",
    ]),
    ("Registro automático de cada request", [
        "Dado que cualquier usuario realiza una petición al API",
        "Cuando el middleware de auditoría la procesa",
        "Entonces queda un registro en access_logs sin intervención manual",
    ]),
)

_hu("HU-21", NO,
    ("Edición de un parámetro general del sistema", [
        "Dado que soy administrador en la pantalla de configuración",
        "Cuando modifico un parámetro (por ejemplo, la ventana de ciclo en días) y guardo",
        "Entonces el sistema persiste el nuevo valor en la tabla de configuraciones",
        "Y el valor pasa a usarse sin necesidad de tocar código ni reiniciar",
    ]),
    ("Validación del valor ingresado", [
        "Dado que edito un parámetro numérico",
        "Cuando ingreso un valor fuera del rango permitido",
        "Entonces el sistema lo rechaza y conserva el valor anterior",
    ]),
    ("Trazabilidad del cambio", [
        "Dado que cambié un parámetro del sistema",
        "Cuando reviso la auditoría",
        "Entonces el cambio queda registrado con el usuario y la fecha",
    ]),
)

_hu("HU-23", OK,
    ("Respaldo automático diario", [
        "Dado que el planificador está activo",
        "Cuando llegan las 02:00 de cada día",
        "Entonces el sistema genera un respaldo de la base de datos",
        "Y el archivo queda disponible en el listado de respaldos",
    ]),
    ("Purga por política de retención", [
        "Dado que existen respaldos más antiguos que la ventana de retención",
        "Cuando se ejecuta el job de respaldo",
        "Entonces los respaldos vencidos se eliminan automáticamente",
    ]),
)

_hu("HU-37", OK,
    ("Visualización de los logs del sistema", [
        "Dado que soy administrador",
        "Cuando abro la vista de logs",
        "Entonces veo los registros más recientes ordenados de forma descendente por fecha",
        "Y puedo ajustar el límite de registros a mostrar",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 7 — Proceso del alumno
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-28", OK,
    ("Línea de tiempo del proceso del estudiante", [
        "Dado que soy estudiante con citas y cuestionarios completados",
        "Cuando abro \"Mi bienestar\"",
        "Entonces veo una línea de tiempo cronológica con mis hitos",
        "Y cada hito indica su tipo (cuestionario, cita o mensaje) y su fecha",
        "Y no se muestra ningún puntaje ni severidad clínica",
    ]),
    ("Proceso recién iniciado", [
        "Dado que acabo de registrarme y no tengo hitos",
        "Cuando abro \"Mi bienestar\"",
        "Entonces veo un hito de bienvenida y un estado vacío explicativo",
    ]),
)

_hu("HU-30", OK,
    ("Solicitud de cita por el estudiante", [
        "Dado que soy estudiante y quiero apoyo profesional",
        "Cuando solicito una cita indicando fecha, hora y motivo",
        "Entonces el sistema responde 201 y crea la cita en estado solicitado",
        "Y la cita aparece en la agenda de la psicóloga",
    ]),
    ("Estudiante sin psicóloga asignada", [
        "Dado que no tengo una psicóloga asignada",
        "Cuando solicito una cita",
        "Entonces el sistema deriva la solicitud a la psicóloga de guardia",
        "Y la solicitud no se pierde",
    ]),
)

_hu("HU-41", PARCIAL,
    ("Cierre automático del ciclo a los 14 días", [
        "Dado que existe una aplicación pendiente o en progreso con más de 14 días de antigüedad",
        "Cuando el planificador ejecuta el job de cierre de ciclos a las 03:00",
        "Entonces la aplicación pasa a estado \"expirada\"",
        "Y el estudiante puede iniciar un ciclo nuevo",
    ]),
    ("Disparo de la encuesta de cierre", [
        "Dado que se cerró el ciclo de un estudiante",
        "Cuando el job termina de procesar el cierre",
        "Entonces el sistema genera la encuesta de cierre para ese estudiante",
        "Y el estudiante la ve pendiente en su panel",
    ]),
    ("Aplicación dentro de la ventana", [
        "Dado que una aplicación tiene menos de 14 días",
        "Cuando corre el job de cierre",
        "Entonces la aplicación conserva su estado actual",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 8 — Reportes y gestión de casos
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-18", OK,
    ("Generación del reporte mensual institucional", [
        "Dado que soy la psicóloga y quiero reportar a las autoridades del colegio",
        "Cuando solicito el reporte de un mes y año determinados",
        "Entonces el sistema devuelve un PDF con indicadores agregados del periodo",
        "Y el reporte no contiene nombres ni datos identificables de estudiantes",
    ]),
    ("Periodo sin actividad", [
        "Dado que en el mes solicitado no hubo cuestionarios completados",
        "Cuando genero el reporte",
        "Entonces el PDF se genera igualmente e indica explícitamente que no hubo actividad",
    ]),
)

_hu("HU-32", OK,
    ("Filtrado de estudiantes por nivel de riesgo", [
        "Dado que soy la psicóloga en el listado de estudiantes",
        "Cuando aplico el filtro de riesgo \"alto\"",
        "Entonces la tabla muestra únicamente los estudiantes en ese nivel",
        "Y el contador de resultados se actualiza",
    ]),
    ("Filtro sin coincidencias", [
        "Dado que ningún estudiante está en el nivel filtrado",
        "Cuando aplico ese filtro",
        "Entonces la tabla queda vacía con un mensaje explicativo y sin error",
    ]),
)

_hu("HU-33", OK,
    ("Registro de una nota clínica privada", [
        "Dado que soy la psicóloga en la ficha de un estudiante",
        "Cuando escribo una nota y la guardo",
        "Entonces el sistema responde 201 y la nota queda asociada al estudiante",
        "Y la nota es visible únicamente para el personal clínico",
    ]),
    ("La nota nunca llega al estudiante", [
        "Dado que existe una nota clínica sobre mí",
        "Cuando consulto cualquier endpoint disponible para mi rol de estudiante",
        "Entonces la nota no aparece en ninguna respuesta",
    ]),
    ("Eliminación de una nota", [
        "Dado que registré una nota por error",
        "Cuando la elimino desde la ficha",
        "Entonces el sistema responde 204 y la nota deja de listarse",
    ]),
)

_hu("HU-34", OK,
    ("Exportación del reporte individual en PDF", [
        "Dado que soy la psicóloga en la ficha de un estudiante evaluado",
        "Cuando solicito el reporte individual en PDF",
        "Entonces el sistema devuelve un archivo PDF descargable",
        "Y el PDF incluye puntajes, severidades, banderas y señales de las frases",
        "Y lleva la firma de la psicóloga si está cargada",
    ]),
    ("Estudiante sin evaluaciones", [
        "Dado que el estudiante no tiene ninguna aplicación completada",
        "Cuando solicito su reporte individual",
        "Entonces el sistema informa que no hay datos suficientes y no genera un PDF vacío",
    ]),
)

_hu("HU-35", OK,
    ("Cambio del estado del caso", [
        "Dado que soy la psicóloga en la ficha de un estudiante",
        "Cuando marco el caso como \"en seguimiento\"",
        "Entonces el sistema persiste el nuevo estado",
        "Y el estado se refleja en el listado de estudiantes",
    ]),
    ("Estado no permitido", [
        "Dado que envío un estado fuera del conjunto permitido",
        "Cuando el sistema procesa la petición",
        "Entonces responde 422 y conserva el estado anterior",
    ]),
)

_hu("HU-38", OK,
    ("Asignación de un estudiante a una psicóloga", [
        "Dado que soy administrador",
        "Cuando asigno un estudiante a una psicóloga específica",
        "Entonces el estudiante queda vinculado a esa profesional",
        "Y aparece en el listado de estudiantes de esa psicóloga",
    ]),
    ("Reasignación a otra profesional", [
        "Dado que el estudiante ya tenía una psicóloga asignada",
        "Cuando lo asigno a otra",
        "Entonces la asignación anterior se reemplaza sin duplicar el vínculo",
    ]),
)

_hu("HU-40", OK,
    ("Creación de un contenido psicoeducativo", [
        "Dado que soy administrador",
        "Cuando creo un contenido con título, categoría y cuerpo",
        "Entonces el sistema responde 201 y el contenido queda publicado",
        "Y los estudiantes lo ven en la sección Recursos",
    ]),
    ("Edición y eliminación", [
        "Dado que existe un contenido publicado",
        "Cuando lo edito o lo elimino desde el panel de administración",
        "Entonces el cambio se refleja de inmediato en el listado público",
    ]),
    ("Acceso restringido a la gestión", [
        "Dado que soy estudiante o psicóloga",
        "Cuando llamo a los endpoints de administración de contenidos",
        "Entonces el sistema responde 403",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 9 — Sistema de cuestionarios
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-42", OK,
    ("Consulta del banco de instrumentos validados", [
        "Dado que soy la psicóloga",
        "Cuando abro el banco clínico",
        "Entonces veo los instrumentos validados con su código, nombre, escala y cortes",
        "Y veo también las 40 frases incompletas agrupadas en sus 8 áreas",
    ]),
    ("Los instrumentos validados no son editables", [
        "Dado que la validez de las escalas depende de su redacción literal publicada",
        "Cuando abro un instrumento del banco fijo",
        "Entonces la interfaz lo muestra en modo solo lectura",
        "Y no existe ningún endpoint que permita modificar sus ítems",
    ]),
    ("Detalle de un instrumento", [
        "Dado que quiero revisar el contenido de una escala antes de usarla",
        "Cuando abro el instrumento por su código",
        "Entonces veo todos sus ítems en orden con su criterio DSM-5 y sus banderas de crisis",
    ]),
)

_hu("HU-43", OK,
    ("Creación de un bloque personalizado", [
        "Dado que soy la psicóloga y necesito preguntas propias",
        "Cuando creo un bloque con nombre, escala (likert o binaria), ítems y cortes",
        "Entonces el sistema responde 201 y el bloque queda disponible para mis plantillas",
    ]),
    ("Sugerencia automática de cortes", [
        "Dado que estoy definiendo un bloque personalizado",
        "Cuando solicito la sugerencia de cortes para el rango máximo del bloque",
        "Entonces el sistema propone cortes por tercios sobre ese rango",
        "Y puedo aceptarlos o reemplazarlos por los míos",
    ]),
    ("Edición y borrado del bloque propio", [
        "Dado que creé un bloque personalizado",
        "Cuando lo edito o lo elimino",
        "Entonces el cambio se aplica sin afectar a los instrumentos del banco fijo",
    ]),
)

_hu("HU-44", OK,
    ("Armado de una plantilla combinando bloques", [
        "Dado que soy la psicóloga",
        "Cuando creo una plantilla combinando instrumentos del banco fijo, bloques personalizados y áreas de frases",
        "Entonces el sistema responde 201 y guarda la plantilla con el orden de bloques definido",
        "Y la plantilla queda disponible para reutilizarse en futuras asignaciones",
    ]),
    ("Plantilla sin bloques", [
        "Dado que intento guardar una plantilla vacía",
        "Cuando envío el formulario",
        "Entonces el sistema la rechaza e indica que debe tener al menos un bloque",
    ]),
    ("Edición y borrado de una plantilla", [
        "Dado que una plantilla ya existe",
        "Cuando la edito o la elimino",
        "Entonces el cambio se guarda y las aplicaciones ya respondidas no se alteran",
    ]),
)

_hu("HU-45", OK,
    ("Asignación de una plantilla a un estudiante", [
        "Dado que soy la psicóloga con una plantilla guardada",
        "Cuando la asigno a un estudiante",
        "Entonces el sistema responde 201 y crea la aplicación en estado \"pendiente\"",
        "Y el estudiante ve el cuestionario como pendiente en su panel",
    ]),
    ("Asignación a un estudiante inexistente", [
        "Dado que envío un identificador de estudiante que no existe",
        "Cuando intento asignar la plantilla",
        "Entonces el sistema responde 404 y no crea la aplicación",
    ]),
)

_hu("HU-46", OK,
    ("Capa 1 — puntaje por bloque con cortes científicos", [
        "Dado un cuestionario completado con bloques de escalas validadas",
        "Cuando el evaluador procesa la aplicación",
        "Entonces calcula el puntaje total de cada bloque",
        "Y le asigna una severidad usando los cortes publicados del instrumento",
    ]),
    ("Capa 2 — banderas de crisis", [
        "Dado que se cumple alguno de los criterios de crisis definidos",
        "Cuando el evaluador procesa la aplicación",
        "Entonces registra la bandera con el ítem exacto que la originó",
    ]),
    ("Capa 3 — riesgo compuesto", [
        "Dado que varios bloques quedaron en zona de alerta",
        "Cuando el evaluador calcula el riesgo compuesto",
        "Entonces el nivel resultante depende de cuántos bloques están en alerta",
        "Y el resultado se guarda en el resultado_json de la aplicación",
    ]),
    ("Capa 4 — clasificación de las frases", [
        "Dado que la aplicación incluye frases incompletas respondidas",
        "Cuando el evaluador ejecuta la capa de NLP",
        "Entonces cada frase queda clasificada por BETO en las 8 categorías emocionales",
    ]),
    ("El resultado nunca es un diagnóstico", [
        "Dado cualquier resultado generado por el evaluador",
        "Cuando la psicóloga lo abre",
        "Entonces el reporte presenta señales, puntajes y banderas",
        "Y declara explícitamente que la interpretación clínica corresponde a la profesional",
    ]),
)

_hu("HU-47", OK,
    ("Pantalla de respuesta tipo hoja A4", [
        "Dado que tengo un cuestionario asignado",
        "Cuando lo abro para responder",
        "Entonces veo todos los bloques en una sola página continua tipo A4",
        "Y cada tipo de ítem se renderiza con su control adecuado (likert, binario o texto abierto)",
    ]),
    ("Indicador de avance", [
        "Dado que estoy respondiendo el cuestionario",
        "Cuando marco respuestas",
        "Entonces el indicador de progreso refleja cuántos ítems llevo respondidos",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 10 — SVM, OAuth, rediseño y despliegue
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-48", OK,
    ("Segunda opinión del SVM sobre DASS-21", [
        "Dado que la plantilla respondida incluye el instrumento DASS-21",
        "Cuando el evaluador ejecuta la capa 5",
        "Entonces el SVM recibe las 21 respuestas en el orden con el que fue entrenado",
        "Y devuelve una clase de riesgo con su probabilidad asociada",
    ]),
    ("Aplicación sin DASS-21", [
        "Dado que la plantilla no incluye DASS-21",
        "Cuando el evaluador procesa la aplicación",
        "Entonces la capa 5 se omite y el resultado no contiene segunda opinión",
        "Y las cuatro capas por reglas se calculan normalmente",
    ]),
    ("Modelo no disponible", [
        "Dado que el archivo del modelo entrenado no puede cargarse",
        "Cuando el evaluador intenta la segunda opinión",
        "Entonces el sistema continúa sin el SVM y no interrumpe la evaluación",
    ]),
)

_hu("HU-49", OK,
    ("Concordancia entre reglas y SVM", [
        "Dado que las reglas y el SVM coinciden en marcar o no marcar riesgo",
        "Cuando la psicóloga abre el reporte clínico",
        "Entonces la tarjeta de segunda opinión muestra concordancia",
    ]),
    ("Discrepancia señalada", [
        "Dado que las reglas marcan riesgo y el SVM no, o viceversa",
        "Cuando la psicóloga abre el reporte clínico",
        "Entonces el sistema muestra una bandera de discrepancia visible",
        "Y explica que el SVM complementa y no reemplaza el criterio por reglas",
    ]),
)

_hu("HU-50", OK,
    ("Inicio de sesión con Google", [
        "Dado que el proveedor Google está configurado",
        "Cuando inicio sesión con mi cuenta Google desde la pantalla de login",
        "Entonces el sistema valida el id_token contra Google",
        "Y emite un JWT propio del sistema con mi rol",
    ]),
    ("Primera vez con OAuth", [
        "Dado que mi correo de Google no tiene cuenta en el sistema",
        "Cuando inicio sesión con Google por primera vez",
        "Entonces el sistema crea mi cuenta y me lleva al consentimiento informado",
    ]),
    ("Proveedor no configurado", [
        "Dado que las credenciales OAuth no están configuradas en el entorno",
        "Cuando se carga la pantalla de login",
        "Entonces el botón de Google no se ofrece y el login con contraseña sigue disponible",
    ]),
)

_hu("HU-51", OK,
    ("Panel del estudiante con las seis vistas", [
        "Dado que soy estudiante autenticado",
        "Cuando abro mi panel",
        "Entonces puedo navegar entre Inicio, Cuestionario, Reuniones, Recursos, Mi bienestar y Mi Perfil",
        "Y el cambio de vista ocurre sin recargar la página",
    ]),
    ("Comportamiento responsive", [
        "Dado que abro el panel en una pantalla angosta",
        "Cuando el ancho baja de los puntos de quiebre definidos",
        "Entonces la barra lateral colapsa y el contenido se reordena sin scroll horizontal",
    ]),
)

_hu("HU-52", OK,
    ("Lectura del mensaje de la psicóloga", [
        "Dado que mi psicóloga escribió un resumen para mí después de una sesión",
        "Cuando abro mi panel de inicio",
        "Entonces leo ese mensaje asociado a la sesión correspondiente",
    ]),
    ("Separación entre mensaje y nota interna", [
        "Dado que la psicóloga registró tanto una nota interna como un resumen para el estudiante",
        "Cuando consulto mis citas como estudiante",
        "Entonces solo recibo el resumen dirigido a mí",
        "Y la nota interna no se incluye en ninguna respuesta que yo pueda leer",
    ]),
)

_hu("HU-53", OK,
    ("Disponibilidad del sistema desplegado", [
        "Dado que el sistema está desplegado en Azure App Service",
        "Cuando un usuario accede a la URL pública",
        "Entonces la aplicación responde sobre HTTPS con TLS 1.2 o superior",
        "Y toda petición HTTP se redirige a HTTPS",
    ]),
    ("Persistencia y respaldo gestionado", [
        "Dado que la base de datos es PostgreSQL Flexible Server",
        "Cuando ocurre un incidente que exige restauración",
        "Entonces existen respaldos gestionados con al menos 7 días de retención",
    ]),
)

_hu("HU-54", OK,
    ("Registro de cada request HTTP", [
        "Dado que el middleware de auditoría está activo",
        "Cuando se procesa cualquier petición al API",
        "Entonces se registra la IP, el usuario, la ruta, el método y el código de estado",
    ]),
    ("Peticiones anónimas", [
        "Dado que la petición no lleva token de autenticación",
        "Cuando el middleware la registra",
        "Entonces el registro se guarda igualmente sin identificador de usuario",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# SPRINT 11 — Padres y firma
# ═══════════════════════════════════════════════════════════════════════

_hu("HU-55", OK,
    ("Listado de los hijos vinculados", [
        "Dado que soy padre o tutor con hijos vinculados",
        "Cuando abro mi panel",
        "Entonces veo cada hijo con su grado, su estado y el número de cuestionarios completados",
        "Y veo el nombre de la psicóloga que lo acompaña",
    ]),
    ("Ningún dato clínico expuesto al padre", [
        "Dado que mi hijo tiene puntajes, banderas y notas clínicas registradas",
        "Cuando consulto el listado de hijos",
        "Entonces la respuesta no incluye puntajes, severidades, banderas ni notas internas",
    ]),
    ("Padre sin hijos vinculados", [
        "Dado que aún no me vincularon ningún hijo",
        "Cuando abro mi panel",
        "Entonces veo un estado vacío que me indica contactar al colegio",
    ]),
)

_hu("HU-56", OK,
    ("Carga de la firma manuscrita", [
        "Dado que soy la psicóloga en la sección de firma",
        "Cuando subo una imagen PNG o JPG de hasta 2 MB",
        "Entonces el sistema la almacena y la asocia a mi usuario",
        "Y la vista previa muestra la firma cargada",
    ]),
    ("Formato o tamaño no permitido", [
        "Dado que intento subir un archivo que no es PNG ni JPG, o que supera los 2 MB",
        "Cuando envío el archivo",
        "Entonces el sistema lo rechaza con un mensaje claro y conserva la firma anterior",
    ]),
    ("Inserción automática en los informes", [
        "Dado que tengo mi firma cargada",
        "Cuando se genera un reporte clínico en PDF o Word, o un informe para el padre",
        "Entonces la firma se inserta automáticamente al final del documento",
    ]),
    ("Eliminación de la firma", [
        "Dado que quiero reemplazar mi firma",
        "Cuando la elimino",
        "Entonces el sistema responde 204 y los informes se generan sin firma hasta que cargue una nueva",
    ]),
)

_hu("HU-57", OK,
    ("Descarga del reporte clínico en Word", [
        "Dado que soy la psicóloga en la ficha de un estudiante evaluado",
        "Cuando solicito el reporte individual en formato Word",
        "Entonces el sistema devuelve un archivo .docx editable",
        "Y su estructura y contenido corresponden a los del reporte en PDF",
    ]),
)

_hu("HU-58", OK,
    ("Descarga del informe oficial por el padre", [
        "Dado que soy padre de un estudiante evaluado",
        "Cuando descargo su informe en PDF o en Word",
        "Entonces el sistema entrega el documento con la firma de la psicóloga",
        "Y el informe no contiene puntajes ni notas clínicas reservadas",
    ]),
    ("Intento de acceso a un hijo no vinculado", [
        "Dado que soy padre y solicito el informe de un estudiante que no es mi hijo",
        "Cuando llamo al endpoint con ese identificador",
        "Entonces el sistema responde 403 y no entrega ningún documento",
    ]),
)

_hu("HU-59", OK,
    ("Vinculación de un padre con un estudiante", [
        "Dado que soy administrador",
        "Cuando vinculo una cuenta de padre con un estudiante",
        "Entonces el vínculo queda registrado",
        "Y el padre ve a ese estudiante en su panel",
    ]),
    ("Un padre puede tutelar varios estudiantes", [
        "Dado que un padre ya tiene un hijo vinculado",
        "Cuando le vinculo un segundo estudiante",
        "Entonces ambos aparecen en su listado sin reemplazar al anterior",
    ]),
    ("Desvinculación", [
        "Dado que un padre está vinculado a un estudiante",
        "Cuando lo desvinculo",
        "Entonces el padre deja de ver a ese estudiante y de poder descargar su informe",
    ]),
)

# ═══════════════════════════════════════════════════════════════════════
# HU FALTANTES — funcionalidad hallada en el código sin historia asociada
# (auditoría inversa código → backlog, ver docs/AUDITORIA_REQUISITOS.md)
# ═══════════════════════════════════════════════════════════════════════

NUEVAS_HU = [
    dict(id="HU-60", rol="Usuario", epica="EPICA0001", sp=3, prio="Media", sprint="Sprint 10",
         historia=("Como Usuario quiero iniciar sesión con mi cuenta Microsoft (OAuth) "
                   "para entrar con la cuenta institucional del colegio"),
         notas=("Regularización: POST /auth/oauth/microsoft + api.oauthMicrosoft ya "
                "implementados. HU-50 solo cubría Google.")),
    dict(id="HU-61", rol="Usuario", epica="EPICA0001", sp=2, prio="Media", sprint="Sprint 2",
         historia=("Como Usuario quiero cambiar mi contraseña desde mi perfil estando "
                   "autenticado para mantener segura mi cuenta sin depender del correo"),
         notas=("Regularización: PUT /users/me/password. Distinto de HU-27, que es "
                "recuperación por correo con token.")),
    dict(id="HU-62", rol="Padre", epica="EPICA0009", sp=3, prio="Alta", sprint="Sprint 11",
         historia=("Como Padre/Tutor quiero registrarme en el sistema y ser dirigido a mi "
                   "panel para acceder al seguimiento de mis hijos"),
         notas=("Regularización: el rol 'padre' es seleccionable en /register y el router "
                "enruta a /padre. HU-01 solo contemplaba al estudiante.")),
    dict(id="HU-63", rol="Estudiante", epica="EPICA0002", sp=2, prio="Media", sprint="Sprint 7",
         historia=("Como Estudiante quiero saber qué psicóloga tengo asignada para saber a "
                   "quién acudo y con quién me estoy reuniendo"),
         notas="Regularización: GET /users/me/psicologo + api.miPsicologo."),
    dict(id="HU-64", rol="Estudiante", epica="EPICA0002", sp=3, prio="Media", sprint="Sprint 7",
         historia=("Como Estudiante quiero que el sistema me proponga horarios disponibles "
                   "al solicitar una cita para elegir sin escribir la fecha a mano"),
         notas=("Regularización: GET /users/me/slots-sugeridos + api.slotsSugeridos. "
                "Complementa HU-30.")),
    dict(id="HU-65", rol="Psicólogo", epica="EPICA0003", sp=5, prio="Alta", sprint="Sprint 5",
         historia=("Como Psicólogo quiero ver la bandeja de alertas SOS abiertas y marcarlas "
                   "como atendidas para no perder de vista ninguna crisis"),
         notas=("Regularización: GET /sos/abiertos, PATCH /sos/{id}/atender y "
                "PsychologistSOSView.vue. HU-31 solo cubría el botón del alumno.")),
    dict(id="HU-66", rol="Estudiante", epica="EPICA0002", sp=3, prio="Alta", sprint="Sprint 9",
         historia=("Como Estudiante quiero guardar mis respuestas parciales y retomar el "
                   "cuestionario después para no perder lo avanzado"),
         notas=("Regularización: POST /cuestionarios/responder/{id}/guardar, separado de "
                "/cerrar. Estado 'en_progreso'.")),
    dict(id="HU-67", rol="Psicólogo", epica="EPICA0003", sp=3, prio="Media", sprint="Sprint 11",
         historia=("Como Psicólogo quiero vincular o desvincular al padre de un estudiante "
                   "desde su ficha para gestionar el acompañamiento familiar sin depender del admin"),
         notas=("Regularización: GET /psychologist/padres, POST/DELETE "
                "/psychologist/students/{id}/assign-padre. HU-59 es la vía del administrador.")),
    dict(id="HU-68", rol="Administrador", epica="EPICA0004", sp=3, prio="Media", sprint="Sprint 6",
         historia=("Como Administrador quiero consultar el estado del modelo de NLP y "
                   "recargarlo para diagnosticar y resolver fallas del clasificador"),
         notas="Regularización: GET /admin/nlp/modelo, POST /admin/nlp/recargar + AdminSystemView."),
    dict(id="HU-69", rol="Administrador", epica="EPICA0004", sp=5, prio="Media", sprint="Sprint 8",
         historia=("Como Administrador quiero un tablero de reportes con estadísticas "
                   "agregadas de los cuestionarios para monitorear el uso del sistema en el colegio"),
         notas=("Regularización: GET /admin/cuestionarios/stats + AdminReportsView.vue. "
                "Distinto de HU-18 (reporte clínico mensual de la psicóloga).")),
    dict(id="HU-70", rol="Administrador", epica="EPICA0004", sp=3, prio="Baja", sprint="Sprint 6",
         historia=("Como Administrador quiero ver el resumen consolidado de la encuesta de "
                   "satisfacción para evaluar la aceptación del sistema"),
         notas=("Regularización: GET /survey/admin/satisfaction/summary + "
                "api.adminResumenSatisfaccion. HU-25 es el lado del alumno.")),
    dict(id="HU-71", rol="Padre", epica="EPICA0009", sp=3, prio="Alta", sprint="Sprint 11",
         historia=("Como Padre/Tutor quiero abrir el detalle de un hijo para revisar su "
                   "avance y descargar su informe desde un solo lugar"),
         notas=("Regularización: GET /padre/hijos/{id} + PadreHijoView.vue. HU-55 solo "
                "cubría el listado.")),
    dict(id="HU-72", rol="Psicólogo", epica="EPICA0006", sp=2, prio="Media", sprint="Sprint 9",
         historia=("Como Psicólogo quiero marcar una aplicación de cuestionario como revisada "
                   "para llevar el control de qué resultados ya analicé"),
         notas=("Regularización: POST /cuestionarios/aplicacion/{id}/marcar-revisado. "
                "Cierra el estado 'revisado' del flujo. Distinto de HU-35 (estado del caso).")),
    dict(id="HU-73", rol="Administrador", epica="EPICA0004", sp=3, prio="Media", sprint="Sprint 6",
         historia=("Como Administrador quiero ejecutar un respaldo manual y consultar el "
                   "estado del planificador para verificar que las tareas automáticas funcionan"),
         notas=("Regularización: POST /admin/backup, GET /admin/backups, GET "
                "/admin/scheduler/info, POST /admin/scheduler/backup-ahora. Complementa HU-23.")),
    dict(id="HU-74", rol="Psicólogo", epica="EPICA0003", sp=3, prio="Media", sprint="Sprint 5",
         historia=("Como Psicólogo quiero reprogramar o cancelar una cita ya agendada para "
                   "ajustar mi agenda ante imprevistos"),
         notas=("Regularización: PUT /psychologist/citas/{id}, DELETE "
                "/psychologist/citas/{id}. HU-19 solo cubría la creación.")),
    dict(id="HU-75", rol="Psicólogo", epica="EPICA0003", sp=5, prio="Media", sprint="Sprint 10",
         historia=("Como Psicólogo quiero un panel rediseñado con barra lateral y navegación "
                   "unificada para moverme entre estudiantes, alertas, banco y plantillas sin perderme"),
         notas=("Regularización: AppShellPsico.vue + AppSidebar.vue montados en App.vue. "
                "HU-51 solo cubría el rediseño del alumno.")),
]

_hu("HU-60", OK,
    ("Inicio de sesión con Microsoft", [
        "Dado que el proveedor Microsoft está configurado en el entorno",
        "Cuando inicio sesión con mi cuenta Microsoft desde la pantalla de login",
        "Entonces el sistema valida el token contra Microsoft y emite un JWT propio",
        "Y quedo autenticado con el rol que corresponde a mi cuenta",
    ]),
    ("Token de proveedor inválido", [
        "Dado que el token recibido del proveedor no es válido o expiró",
        "Cuando el backend intenta verificarlo",
        "Entonces responde 401 y no emite ningún JWT del sistema",
    ]),
)

_hu("HU-61", OK,
    ("Cambio de contraseña desde el perfil", [
        "Dado que estoy autenticado en Mi Perfil",
        "Cuando ingreso mi contraseña actual y una nueva contraseña válida",
        "Entonces el sistema actualiza mi contraseña y confirma el cambio",
        "Y puedo iniciar sesión con la nueva contraseña",
    ]),
    ("Contraseña actual incorrecta", [
        "Dado que estoy cambiando mi contraseña",
        "Cuando ingreso mal la contraseña actual",
        "Entonces el sistema responde 400 y no modifica nada",
    ]),
)

_hu("HU-62", OK,
    ("Registro de un padre o tutor", [
        "Dado que soy un padre de familia del colegio",
        "Cuando me registro seleccionando el rol \"padre\"",
        "Entonces el sistema crea mi cuenta con ese rol",
        "Y tras aceptar el consentimiento soy dirigido al panel /padre",
    ]),
    ("El padre no accede a paneles de otros roles", [
        "Dado que estoy autenticado como padre",
        "Cuando intento entrar a /psicologo o a /admin",
        "Entonces el guard me devuelve a mi panel y el backend responde 403",
    ]),
)

_hu("HU-63", OK,
    ("Consulta de la psicóloga asignada", [
        "Dado que soy estudiante con una psicóloga asignada",
        "Cuando abro mi panel",
        "Entonces veo su nombre como profesional a cargo de mi acompañamiento",
    ]),
    ("Estudiante sin psicóloga asignada", [
        "Dado que todavía no tengo una psicóloga asignada",
        "Cuando abro mi panel",
        "Entonces el sistema lo indica sin mostrar un error",
    ]),
)

_hu("HU-64", OK,
    ("Horarios sugeridos para la cita", [
        "Dado que quiero solicitar una cita",
        "Cuando abro el formulario de solicitud",
        "Entonces el sistema me propone un conjunto de horarios disponibles",
        "Y al elegir uno se completa la fecha y hora de la solicitud",
    ]),
    ("Sin horarios disponibles", [
        "Dado que no hay horarios sugeridos disponibles",
        "Cuando abro el formulario",
        "Entonces puedo igualmente proponer una fecha y hora manualmente",
    ]),
)

_hu("HU-65", OK,
    ("Bandeja de alertas SOS abiertas", [
        "Dado que soy la psicóloga y hay eventos SOS sin atender",
        "Cuando abro la bandeja de SOS",
        "Entonces veo cada evento con el estudiante, la fecha, el origen y el mensaje",
        "Y los eventos se ordenan del más reciente al más antiguo",
    ]),
    ("Marcado de un SOS como atendido", [
        "Dado que ya contacté al estudiante que activó el SOS",
        "Cuando marco el evento como atendido",
        "Entonces el sistema registra quién lo atendió y cuándo",
        "Y el evento deja de aparecer en la bandeja de abiertos",
    ]),
    ("Sin alertas pendientes", [
        "Dado que no hay eventos SOS abiertos",
        "Cuando abro la bandeja",
        "Entonces veo un estado vacío que confirma que no hay crisis pendientes",
    ]),
)

_hu("HU-66", OK,
    ("Guardado parcial de respuestas", [
        "Dado que estoy respondiendo un cuestionario largo",
        "Cuando guardo mis respuestas sin cerrarlo",
        "Entonces el sistema las persiste y la aplicación queda en estado \"en_progreso\"",
        "Y el cuestionario no se evalúa todavía",
    ]),
    ("Retomar el cuestionario", [
        "Dado que guardé respuestas parciales y cerré el navegador",
        "Cuando vuelvo a abrir el mismo cuestionario",
        "Entonces mis respuestas anteriores aparecen ya marcadas",
        "Y puedo continuar desde donde me quedé",
    ]),
    ("No se puede modificar tras el cierre", [
        "Dado que ya cerré y envié el cuestionario",
        "Cuando intento guardar nuevas respuestas sobre esa aplicación",
        "Entonces el sistema lo rechaza y conserva las respuestas originales",
    ]),
)

_hu("HU-67", OK,
    ("Vinculación del padre desde la ficha del estudiante", [
        "Dado que soy la psicóloga en la ficha de un estudiante",
        "Cuando selecciono una cuenta de padre disponible y la vinculo",
        "Entonces el vínculo queda registrado y el padre ve al estudiante en su panel",
    ]),
    ("Consulta y desvinculación", [
        "Dado que el estudiante ya tiene un padre vinculado",
        "Cuando abro su ficha veo qué cuenta está vinculada",
        "Y al desvincularla el sistema responde 204 y el padre pierde el acceso",
    ]),
)

_hu("HU-68", OK,
    ("Consulta del estado del modelo de NLP", [
        "Dado que soy administrador en la vista de sistema",
        "Cuando se carga la pantalla",
        "Entonces veo el identificador del modelo cargado y su estado",
    ]),
    ("Recarga del modelo", [
        "Dado que el clasificador presenta fallas",
        "Cuando ejecuto la recarga del modelo",
        "Entonces el sistema lo vuelve a cargar y refresca la información mostrada",
    ]),
)

_hu("HU-69", OK,
    ("Tablero de reportes del administrador", [
        "Dado que soy administrador",
        "Cuando abro la vista de reportes",
        "Entonces veo estadísticas agregadas de cuestionarios asignados, completados y pendientes",
        "Y los datos son agregados, sin identificar a ningún estudiante",
    ]),
    ("Descarga del reporte del periodo", [
        "Dado que estoy en el tablero de reportes",
        "Cuando elijo un mes y un año y solicito la descarga",
        "Entonces el sistema entrega el reporte en PDF",
    ]),
)

_hu("HU-70", OK,
    ("Resumen de la encuesta de satisfacción", [
        "Dado que soy administrador y existen encuestas respondidas",
        "Cuando abro el resumen de satisfacción",
        "Entonces veo el número de respuestas y el promedio por ítem",
        "Y los resultados se muestran de forma agregada y anónima",
    ]),
    ("Sin respuestas registradas", [
        "Dado que ningún usuario ha respondido la encuesta",
        "Cuando abro el resumen",
        "Entonces la vista lo indica y no muestra promedios inventados",
    ]),
)

_hu("HU-71", OK,
    ("Detalle del hijo para el padre", [
        "Dado que soy padre con un hijo vinculado",
        "Cuando abro su detalle",
        "Entonces veo su información de seguimiento no clínica y el acceso a su informe",
    ]),
    ("Detalle de un hijo ajeno", [
        "Dado que solicito el detalle de un estudiante que no está vinculado a mí",
        "Cuando llamo al endpoint",
        "Entonces el sistema responde 403 y no revela ninguna información",
    ]),
)

_hu("HU-72", OK,
    ("Marcado de la aplicación como revisada", [
        "Dado que soy la psicóloga y abrí el resultado de una aplicación completada",
        "Cuando la marco como revisada",
        "Entonces el estado de la aplicación pasa a \"revisado\"",
        "Y deja de figurar como pendiente de revisión en mi panel",
    ]),
    ("Aplicación aún no completada", [
        "Dado que la aplicación sigue pendiente o en progreso",
        "Cuando intento marcarla como revisada",
        "Entonces el sistema lo rechaza porque no hay resultado que revisar",
    ]),
)

_hu("HU-73", OK,
    ("Ejecución de un respaldo manual", [
        "Dado que soy administrador",
        "Cuando ejecuto un respaldo manual",
        "Entonces el sistema genera el archivo y lo agrega al listado de respaldos",
    ]),
    ("Consulta del estado del planificador", [
        "Dado que quiero verificar las tareas automáticas",
        "Cuando consulto el estado del planificador",
        "Entonces veo los jobs registrados y su próxima ejecución programada",
    ]),
)

_hu("HU-74", OK,
    ("Reprogramación de una cita", [
        "Dado que soy la psicóloga con una cita agendada",
        "Cuando modifico su fecha, hora o modalidad",
        "Entonces el sistema guarda los cambios y responde con la cita actualizada",
        "Y el estudiante ve la nueva fecha en su panel",
    ]),
    ("Cancelación de una cita", [
        "Dado que una cita ya no se realizará",
        "Cuando la cancelo",
        "Entonces el sistema responde 204 y la cita deja de figurar como próxima",
    ]),
)

_hu("HU-75", OK,
    ("Navegación unificada del panel clínico", [
        "Dado que soy la psicóloga autenticada",
        "Cuando entro a cualquier vista de mi panel",
        "Entonces la barra lateral muestra las secciones disponibles y resalta la vista activa",
        "Y puedo moverme entre ellas sin volver a un menú intermedio",
    ]),
    ("El shell no se aplica a otros roles", [
        "Dado que soy estudiante o padre",
        "Cuando navego por mi panel",
        "Entonces se aplica el shell correspondiente a mi rol y no el clínico",
    ]),
)
