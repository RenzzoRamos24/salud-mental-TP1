import { ref } from "vue";
import { api } from "../api";

// Estado compartido — se carga una sola vez por sesión.
const config = ref(null);
let cargando = null;

async function cargarConfig() {
  if (config.value) return config.value;
  if (cargando) return cargando;
  cargando = api
    .oauthConfig()
    .then((c) => {
      config.value = c;
      return c;
    })
    .catch(() => {
      config.value = {
        google: { configurado: false },
        microsoft: { configurado: false },
      };
      return config.value;
    })
    .finally(() => {
      cargando = null;
    });
  return cargando;
}

function abrirPopup(url, w = 480, h = 640) {
  const left = window.screenX + (window.outerWidth - w) / 2;
  const top = window.screenY + (window.outerHeight - h) / 2;
  return window.open(
    url,
    "sami-oauth",
    `width=${w},height=${h},left=${left},top=${top}`,
  );
}

function generarState() {
  const a = new Uint8Array(8);
  crypto.getRandomValues(a);
  return Array.from(a, (b) => b.toString(16).padStart(2, "0")).join("");
}

// ─── Google ─────────────────────────────────────────────────────────
// Implicit flow id_token: ideal para web SPA, devuelve el JWT directamente.
async function loginGoogle() {
  const c = await cargarConfig();
  if (!c.google?.configurado) {
    throw new Error(
      "Inicio con Google aún no está activado. Pídele al administrador que configure GOOGLE_CLIENT_ID.",
    );
  }

  const state = generarState();
  const nonce = generarState();
  const url =
    "https://accounts.google.com/o/oauth2/v2/auth" +
    "?response_type=id_token" +
    `&client_id=${encodeURIComponent(c.google.client_id)}` +
    `&redirect_uri=${encodeURIComponent(c.redirect_uri)}` +
    "&scope=" +
    encodeURIComponent("openid email profile") +
    `&state=${state}` +
    `&nonce=${nonce}` +
    "&prompt=select_account";

  const id_token = await esperarToken(url, state, "id_token");
  return api.oauthGoogle(id_token);
}

// ─── Microsoft (Outlook / Hotmail) ──────────────────────────────────
// Implicit flow access_token contra MS Graph (scope User.Read).
async function loginMicrosoft() {
  const c = await cargarConfig();
  if (!c.microsoft?.configurado) {
    throw new Error(
      "Inicio con Outlook aún no está activado. Pídele al administrador que configure MICROSOFT_CLIENT_ID.",
    );
  }

  const state = generarState();
  const nonce = generarState();
  const tenant = c.microsoft.tenant || "common";
  const url =
    `https://login.microsoftonline.com/${encodeURIComponent(tenant)}/oauth2/v2.0/authorize` +
    "?response_type=token" +
    `&client_id=${encodeURIComponent(c.microsoft.client_id)}` +
    `&redirect_uri=${encodeURIComponent(c.redirect_uri)}` +
    "&scope=" +
    encodeURIComponent("openid profile email User.Read") +
    "&response_mode=fragment" +
    `&state=${state}` +
    `&nonce=${nonce}` +
    "&prompt=select_account";

  const access_token = await esperarToken(url, state, "access_token");
  return api.oauthMicrosoft(access_token);
}

function esperarToken(authUrl, state, key) {
  return new Promise((resolve, reject) => {
    const popup = abrirPopup(authUrl);
    if (!popup) {
      reject(new Error("El navegador bloqueó la ventana emergente."));
      return;
    }

    const onMessage = (ev) => {
      if (ev.origin !== window.location.origin) return;
      const data = ev.data;
      if (!data || data.source !== "sami-oauth") return;
      if (data.error) {
        cleanup();
        reject(new Error(data.error));
        return;
      }
      if (data.state && data.state !== state) {
        cleanup();
        reject(new Error("Estado OAuth inválido."));
        return;
      }
      const token = data[key];
      if (!token) {
        cleanup();
        reject(new Error("No recibimos el token del proveedor."));
        return;
      }
      cleanup();
      resolve(token);
    };

    const interval = setInterval(() => {
      if (popup.closed) {
        cleanup();
        reject(new Error("Cancelaste el inicio de sesión."));
      }
    }, 600);

    function cleanup() {
      window.removeEventListener("message", onMessage);
      clearInterval(interval);
      try {
        if (!popup.closed) popup.close();
      } catch (_) {}
    }

    window.addEventListener("message", onMessage);
  });
}

export function useOAuth() {
  cargarConfig();
  return {
    config,
    loginGoogle,
    loginMicrosoft,
  };
}
