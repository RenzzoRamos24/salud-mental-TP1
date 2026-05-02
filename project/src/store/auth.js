import { reactive, computed, readonly } from 'vue'

const STORAGE_KEY = 'sm_upc_auth'

function leerStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function escribirStorage(data) {
  if (data) localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  else localStorage.removeItem(STORAGE_KEY)
}

const state = reactive({
  token: null,
  user: null,
})

const inicial = leerStorage()
if (inicial) {
  state.token = inicial.token
  state.user = inicial.user
}

export const authStore = {
  state: readonly(state),

  isAuthenticated: computed(() => !!state.token && !!state.user),
  consentimientoAceptado: computed(() => !!state.user?.consentimiento_aceptado),
  rol: computed(() => state.user?.role || null),

  setSession(token, user) {
    state.token = token
    state.user = user
    escribirStorage({ token, user })
  },

  setUser(user) {
    state.user = { ...state.user, ...user }
    escribirStorage({ token: state.token, user: state.user })
  },

  clear() {
    state.token = null
    state.user = null
    escribirStorage(null)
  },
}
