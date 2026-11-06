# Inicio de sesión con Microsoft (Outlook / Hotmail) — registro de la app

Hoy el botón «Continuar con Outlook» **no se muestra** porque `MICROSOFT_CLIENT_ID` no
está configurado (QA CP129/CP138). Cuando se registre la app, aparece solo.

## 1. Registrar la aplicación (Microsoft Entra ID)

1. <https://entra.microsoft.com> → **Identidad** → **Aplicaciones** → **Registros de aplicaciones** → **Nuevo registro**.
2. **Nombre:** `Sami`.
3. **Tipos de cuenta compatibles:** *Cuentas en cualquier directorio organizativo y cuentas personales de Microsoft*.
   Los alumnos usan cuentas personales (Outlook/Hotmail); con una opción solo-organización no podrían entrar.
4. **URI de redirección:** plataforma *Aplicación de página única (SPA)*, y agregar **las tres**:
   - `https://samipsicologos.com/oauth-callback`
   - `https://sami-app-9921877.azurewebsites.net/oauth-callback`
   - `http://localhost:5173/oauth-callback` (solo desarrollo)
5. **Autenticación** → activar **Tokens de acceso (usados para flujos implícitos)**. El front usa
   `response_type=token`; sin esto Microsoft rechaza el inicio.
6. **Permisos de API:** `Microsoft Graph` → delegado → `User.Read` (viene por defecto) y `openid`, `profile`, `email`.
7. Copiar el **Id. de aplicación (cliente)**. No se necesita *client secret* con este flujo.

## 2. Configurar el backend (app settings de Azure)

| Setting | Valor |
|---|---|
| `MICROSOFT_CLIENT_ID` | el Id. de aplicación (cliente) del paso 7 |
| `MICROSOFT_TENANT` | `common` |
| `OAUTH_REDIRECT_URI` | `https://samipsicologos.com/oauth-callback` |

Cambiar app settings **reinicia la app** (≈1 min). Conviene juntarlo con otro reinicio.

## 3. Comprobar

- `GET /api/v1/auth/oauth/config` → `microsoft.configurado: true`.
- La pantalla de login muestra «Continuar con Outlook» y entra con una cuenta personal y una institucional.
- Con un token inválido el backend responde **401** (CP139); sin configurar responde **503** por diseño.

## Limitación conocida (no es de QA, conviene resolver después)

El backend valida el `access_token` llamando a Microsoft Graph (`/me`). Un access token de Graph
tiene como audiencia a Graph y no a Sami, así que **no se puede comprobar que haya sido emitido para
esta aplicación**: un token válido obtenido por otra aplicación serviría para entrar como ese
usuario. La corrección es pasar a `response_type=id_token` y validar firma, `aud == MICROSOFT_CLIENT_ID`
e `iss` en el backend. Hasta entonces, el riesgo es acotado (hay que engañar al usuario para que
autorice una app maliciosa) pero real.
