# QA semana 10 — respuesta a los 29 tickets (Mantis P20261028)

Origen: `QA_Semana10.csv` (export del 2026-11-01). Rama: `fix/qa-semana10`.
Regresión automática: `PYTHONPATH=. venv/bin/python tests/test_qa_semana10.py` (18 pasos).

**Alcance de la verificación.** El backend se verificó con el test de arriba. El frontend se verificó
compilando (`vite build`); **las pantallas no se probaron en un navegador**. Nada de esto está
desplegado: los tickets pasan a «corregido en rama» y se cierran cuando se despliegue y QA los reverifique.

Leyenda: **C** corregido en la rama · **E** ya existía (ubicación indicada) · **D** diseño documentado ·
**A** requiere una acción del equipo · **N** no reproducible con el código actual (ninguno ya).

| Mantis | CP | Estado | Respuesta |
|---|---|---|---|
| 0005938 | CP102 | C | El tablero de reportes del admin muestra ahora **Completados** y **Pendientes** (la API ya traía `total_completados`; se agregó `total_pendientes`). |
| 0005930 | CP139 | C / A | Sin proveedor configurado el backend responde 503 (`MICROSOFT_CLIENT_ID` vacío): es el comportamiento documentado. Con el proveedor configurado y un token inválido responde **401** y no emite JWT (cubierto en el test). Queda resuelto al registrar la app: ver `docs/OAUTH_MICROSOFT.md`. |
| 0005929 | CP138 | A | La causa es que `MICROSOFT_CLIENT_ID` no está configurado en producción. Acción del equipo: registrar la app y cargar los app settings (`docs/OAUTH_MICROSOFT.md`). Mientras tanto el botón no se ofrece (CP129). |
| 0005928 | CP129 | C | El login oculta el botón de un proveedor OAuth que `/auth/oauth/config` informa como no configurado; el login con contraseña sigue disponible. |
| 0005927 | CP126 | C | «Marcar como revisada» rechaza (400) una aplicación sin resultado (pendiente o en progreso). Se mantiene permitido sobre `completado`/`revisado`. |
| 0005926 | CP119 | C | La pantalla de resultado y los reportes PDF y Word declaran que el resultado **no es un diagnóstico** y que la interpretación clínica corresponde a la profesional (texto único en `resultado_resumen.py`). |
| 0005925 | CP118 | D / C | **Diseño: el sistema clasifica en 4 categorías** (adaptativo, neutral, depresión, ansiedad). Los umbrales (detección 0.40, crisis 0.55) están calibrados para softmax de 4 categorías; pasar a 8 obligaría a recalibrar y revalidar. La documentación decía 8 y se **corrigió en `CLAUDE.md`**. Parte corregida: la pantalla de resultado ahora muestra, por frase, la categoría dominante y los 4 puntajes (antes solo las «detectadas»). Sobre el ejemplo clasificado como «adaptativo»: es una limitación del clasificador zero-shot, no un defecto de implementación; por eso el sistema no diagnostica y la psicóloga interpreta. Sigue abierto como hallazgo de validación clínica (no hay `etiqueta_frase` para medirlo). |
| 0005924 | CP114 | C | Asignar a un estudiante o plantilla inexistente responde **404** y no crea la aplicación. |
| 0005923 | CP106 | C | El detalle del instrumento muestra el **criterio DSM-5** de cada ítem junto a las banderas de crisis. |
| 0005922 | CP104 | C | El banco muestra la **escala** (p. ej. 0–3) y los **cortes** de cada instrumento; `/banco/instrumentos` los devuelve. Salen de la misma tabla que usa el evaluador, así no pueden divergir. |
| 0005921 | CP094 | C | Sin cuestionarios completados el reporte responde **409 «Sin datos suficientes»** y no genera archivo (PDF y Word). La pantalla muestra el motivo. |
| 0005919 | CP093 | C | El PDF (y el Word) incluyen puntaje por instrumento (p. ej. PHQ-A 15/27), severidad, bandera de crisis y el recuento de señales de las frases por categoría. **No** incluyen el texto libre del alumno. La firma ya se incluía si está cargada. |
| 0005916 | CP089 | C / N | En «Mis estudiantes» no existía filtro por nivel de riesgo; se agregó, con mensaje «Ningún estudiante coincide con el filtro». No pude reproducir un error en el código existente por lectura. **Si persiste, pasar pasos y captura.** |
| 0005913 | CP085 | D | Sin psicóloga asignada la solicitud va a la **psicóloga de guardia**: es el criterio de aceptación documentado de HU-30 («la solicitud no se pierde»). Un horario tomado por esa solicitud deja de ofrecerse a los demás alumnos de esa psicóloga, que es correcto (no puede atender dos a la vez). Se agregó un aviso al alumno. **Si el criterio vigente (HU0063/HU0064) es bloquear, hay que decidirlo y cambiar HU-30.** |
| 0005909 | CP084 | D | Igual que CP085. |
| 0005908 | CP083 | D | Igual que CP085. El panel del alumno ya indicaba «Sin psicólogo asignado»; ahora explica a quién llega la solicitud. |
| 0005906 | CP073 / CP074 | E / C | CP073: el respaldo manual existe en **Configuración del sistema → Crear respaldo manual**. CP074: la sección «Tareas programadas» era **texto fijo**; ahora muestra el estado real del planificador y la próxima ejecución de cada tarea. Además se corrigió un fallo mayor: el respaldo **no funcionaba con PostgreSQL** (producción) — ver nota 1. |
| 0005904 | CP071 / CP072 | E | Existe en **Reportes → Encuesta de satisfacción**: número de respuestas, promedio por ítem y estado vacío. Verificado leyendo el código; no ejecutado. |
| 0005902 | CP070 | E | Existe en **Configuración del sistema → Modelo NLP → Recargar**. |
| 0005901 | CP069 | E | Existe en **Configuración del sistema → Modelo NLP**: identificador y estado. |
| 0005900 | CP068 | E / C | Existe en **Auditoría y logs**, ordenado del más reciente al más antiguo. El **límite era fijo (200)**: se agregó el selector (50 / 100 / 200 / 500). |
| 0005899 | CP066 / CP067 | E / C | La pantalla de respaldos existe en **Configuración del sistema** (lista, crear, purga). Ni el respaldo ni la purga funcionaban en producción — ver nota 1. |
| 0005898 | CP064 / CP065 | E | Existe en **Auditoría y logs** (`access_logs`, con filtro por rol y endpoint). |
| 0005896 | CP063 | C | Se agregó la **auditoría de cambios de configuración** (`configuracion_cambios`: parámetro, antes, después, quién, cuándo), visible bajo los parámetros. |
| 0005895 | CP061 / CP062 / CP063 | C | Nueva sección **Parámetros generales** en Configuración del sistema: vigencia del código de recuperación, duración de la sesión y retención de respaldos, cada uno con rango; fuera de rango se rechaza (422) y se muestra el error. Solo hay parámetros que el código realmente lee. |
| 0005890 | CP022 | C | El listado ya se filtraba por rol y es una lista única; faltaba la opción **Padres**, que se agregó. |
| 0005889 | CP016 | C | **El tester tenía razón.** En la pestaña *Mi Perfil* del alumno los datos personales eran solo lectura y la única vía para editarlos era el enlace «Cambiar contraseña». Se agregó el botón **Editar mis datos** (en *Información personal* y en *Cuenta*), que lleva al formulario «Datos personales» con su botón Guardar. Mi primera revisión miró otra pantalla (`ProfileView`) y no la pestaña del alumno. |
| 0005888 | CP013 / CP014 / CP015 | C / A | **El correo nunca se había implementado**: el código se escribía en el log del servidor. Ahora se envía por SMTP y deja de registrarse. **Acción del equipo:** cargar `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` como app settings. Sin ellos el sistema no envía y lo avisa en el log. CP014 y CP015 se podrán ejecutar cuando llegue el correo. |
| 0005885 | CP012 | C | La sesión vencida se detecta en el cliente (al navegar y cada 30 s) y devuelve al login con el aviso «Tu sesión expiró». El 401 de la API también lleva al login. **El ticket está cortado en la descripción**; si faltaba otro detalle, indicarlo. |

## Notas

1. **El respaldo no funcionaba en producción.** `crear_backup` copiaba el archivo SQLite; con
   PostgreSQL eso falla, así que el respaldo manual y el diario fallaban (el diario solo dejaba un
   error en el log). Ahora, con PostgreSQL, genera un volcado lógico `backup_<fecha>.json.gz`
   (tabla → filas, permisos 0600). **No sustituye un `pg_dump` ni los respaldos administrados del servidor**,
   y contiene respuestas de menores. Pendiente del equipo: fijar el app setting `BACKUP_DIR=/home/backups`,
   porque el directorio de la app se reemplaza en cada despliegue.
2. **Correo de recuperación.** Además de enviar el código por correo, se dejó de escribirlo en el
   log, y se generó con un generador criptográfico (antes `random`). Siguen faltando límites de
   intentos sobre el código de 6 dígitos (no se hizo).
3. **No tocado:** el modelo de BETO y sus umbrales; la validación del SVM; las credenciales y su
   rotación (se trabajan aparte).
