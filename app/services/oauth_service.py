"""
OAuth con Google y Microsoft (Hotmail / Outlook).

Flujo client-side: el frontend abre un popup hacia el provider, recibe un
`id_token` (Google) o `access_token` (Microsoft) en el callback, y los manda
al backend para que los valide y emita el JWT propio.

Verificación:
- Google: endpoint público `tokeninfo` que valida la firma + claims.
- Microsoft: consulta MS Graph `/me` con el access_token. Si responde 200,
  el token es válido y nos devuelve email/nombre.

Si las credenciales OAuth no están configuradas en .env, los endpoints
devuelven 503 con un mensaje claro — el resto del login sigue funcionando.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class OAuthError(Exception):
    """Error verificando un token OAuth (token inválido, expirado, etc.)."""


class OAuthNotConfigured(Exception):
    """Las credenciales OAuth del provider no están configuradas en .env."""


async def verificar_google(id_token: str) -> dict:
    """
    Verifica un id_token de Google. Devuelve {email, nombre, apellido}.
    Lanza OAuthError si el token no es válido o el email no está verificado.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise OAuthNotConfigured(
            "GOOGLE_CLIENT_ID no está configurado en el backend."
        )

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )
    if resp.status_code != 200:
        raise OAuthError("Token de Google inválido o expirado.")

    payload = resp.json()

    if payload.get("aud") != settings.GOOGLE_CLIENT_ID:
        raise OAuthError("El token no corresponde a esta aplicación.")

    if payload.get("email_verified") not in ("true", True):
        raise OAuthError("Tu correo de Google no está verificado.")

    email = payload.get("email", "").lower().strip()
    if not email:
        raise OAuthError("Google no devolvió un correo asociado.")

    nombre_completo = (payload.get("name") or "").strip()
    given_name = (payload.get("given_name") or "").strip()
    family_name = (payload.get("family_name") or "").strip()

    if given_name or family_name:
        nombre = given_name or nombre_completo or email.split("@")[0]
        apellido = family_name or "—"
    elif nombre_completo:
        partes = nombre_completo.split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else "—"
    else:
        nombre = email.split("@")[0]
        apellido = "—"

    return {"email": email, "nombre": nombre, "apellido": apellido}


async def verificar_microsoft(access_token: str) -> dict:
    """
    Verifica un access_token de Microsoft contra MS Graph.
    Devuelve {email, nombre, apellido}.
    """
    if not settings.MICROSOFT_CLIENT_ID:
        raise OAuthNotConfigured(
            "MICROSOFT_CLIENT_ID no está configurado en el backend."
        )

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise OAuthError("Token de Microsoft inválido o expirado.")

    me = resp.json()

    email = (
        me.get("mail")
        or me.get("userPrincipalName")
        or ""
    ).lower().strip()
    if not email:
        raise OAuthError("Microsoft no devolvió un correo asociado.")

    nombre = (me.get("givenName") or "").strip()
    apellido = (me.get("surname") or "").strip()
    if not nombre and not apellido:
        display = (me.get("displayName") or email.split("@")[0]).strip()
        partes = display.split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else "—"
    elif not nombre:
        nombre = apellido
        apellido = "—"
    elif not apellido:
        apellido = "—"

    return {"email": email, "nombre": nombre, "apellido": apellido}


def config_publica() -> dict:
    """
    Configuración pública que el frontend necesita para armar los popups OAuth.
    El client_secret no se expone — el flujo es implicit/PKCE.
    """
    return {
        "google": {
            "configurado": bool(settings.GOOGLE_CLIENT_ID),
            "client_id": settings.GOOGLE_CLIENT_ID,
        },
        "microsoft": {
            "configurado": bool(settings.MICROSOFT_CLIENT_ID),
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "tenant": settings.MICROSOFT_TENANT,
        },
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
    }
