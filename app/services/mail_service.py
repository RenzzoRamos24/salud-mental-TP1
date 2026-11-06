"""Envío de correo por SMTP (código de recuperación de contraseña).

Las credenciales SOLO se leen de variables de entorno / app settings de Azure
(`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`). Nunca van
en el código ni en el repositorio.

Si el SMTP no está configurado, `enviar` devuelve False y avisa en el log SIN
imprimir el código: el log de producción no debe contener secretos de un solo uso.
Nunca lanza: un fallo de correo no debe romper la solicitud ni revelar si el
correo existe (la API responde siempre lo mismo).
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


def configurado() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def enviar(destino: str, asunto: str, texto: str) -> bool:
    if not configurado():
        logger.warning(
            "SMTP sin configurar (SMTP_HOST / SMTP_FROM): no se envió el correo."
        )
        return False

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM
    msg["To"] = destino
    msg["Subject"] = asunto
    msg.set_content(texto)

    try:
        if settings.SMTP_SSL:
            servidor = smtplib.SMTP_SSL(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=10,
                context=ssl.create_default_context(),
            )
        else:
            servidor = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        with servidor as s:
            if not settings.SMTP_SSL and settings.SMTP_STARTTLS:
                s.starttls(context=ssl.create_default_context())
            if settings.SMTP_USER:
                s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.send_message(msg)
        return True
    except Exception as e:  # noqa: BLE001 — se registra el tipo, nunca el contenido
        logger.error("Falló el envío de correo SMTP (%s).", type(e).__name__)
        return False


def enviar_codigo_recuperacion(destino: str, codigo: str, minutos: int) -> bool:
    return enviar(
        destino,
        "Sami — código para recuperar tu contraseña",
        (
            f"Tu código de recuperación es: {codigo}\n\n"
            f"Vence en {minutos} minutos y solo sirve una vez.\n"
            "Si no lo pediste tú, ignora este mensaje: tu contraseña no cambia.\n"
        ),
    )
