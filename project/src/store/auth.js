import { reactive, computed, readonly } from "vue";

const STORAGE_KEY = "sm_upc_auth";

function leerStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function escribirStorage(data) {
  if (data) localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  else localStorage.removeItem(STORAGE_KEY);
}

const state = reactive({
  token: null,
  user: null,
});

const inicial = leerStorage();
if (inicial) {
  state.token = inicial.token;
  state.user = inicial.user;
}

// Si la cuenta es de evaluador, el panel clínico queda cerrado hasta que
// termina de evaluar. Se guarda acá para que el sidebar, el topbar y el guard
// del router lean lo mismo y no se contradigan entre sí.
const evaluacion = reactive({ panelDesbloqueado: false, faltan: null });

// Lee `exp` (segundos) del payload del JWT. No verifica la firma: eso es del
// backend. Sirve solo para saber, del lado del cliente, si la sesión ya venció.
function expiraEn(token) {
  try {
    const b64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    const exp = JSON.parse(atob(b64)).exp;
    return typeof exp === "number" ? exp * 1000 : null;
  } catch {
    return null;
  }
}

export const authStore = {
  state: readonly(state),
  evaluacion: readonly(evaluacion),

  setEvaluacion({ panel_desbloqueado, casos_para_desbloquear }) {
    evaluacion.panelDesbloqueado = !!panel_desbloqueado;
    evaluacion.faltan = casos_para_desbloquear ?? null;
  },

  isAuthenticated: computed(() => !!state.token && !!state.user),
  consentimientoAceptado: computed(() => !!state.user?.consentimiento_aceptado),
  rol: computed(() => state.user?.role || null),

  setSession(token, user) {
    state.token = token;
    state.user = user;
    escribirStorage({ token, user });
  },

  setUser(user) {
    state.user = { ...state.user, ...user };
    escribirStorage({ token: state.token, user: state.user });
  },

  /** QA CP012: true si hay token y ya venció (sin esperar a una petición 401). */
  sesionVencida() {
    if (!state.token) return false;
    const ms = expiraEn(state.token);
    return ms !== null && ms <= Date.now();
  },

  clear() {
    state.token = null;
    state.user = null;
    escribirStorage(null);
  },
};
