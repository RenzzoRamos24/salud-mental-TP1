import axios from 'axios'
import { authStore } from './store/auth'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1'

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 300000, // 5 min (primera llamada carga BERT)
})

// Inyecta token en cada request
client.interceptors.request.use((config) => {
  const token = authStore.state.token
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Maneja 401 globalmente
client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 401) {
      authStore.clear()
      // El router redirigirá a /login en el siguiente render
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export const api = {
  // ─── AUTH ───
  async register(payload) {
    const { data } = await client.post('/auth/register', payload)
    return data
  },
  async login(email, password) {
    const { data } = await client.post('/auth/login', { email, password })
    return data
  },
  async logout() {
    try { await client.post('/auth/logout') } catch (_) {}
  },
  async forgotPassword(email) {
    const { data } = await client.post('/auth/forgot-password', { email })
    return data
  },
  async resetPassword(email, token, nueva_password) {
    const { data } = await client.post('/auth/reset-password', { email, token, nueva_password })
    return data
  },
  async me() {
    const { data } = await client.get('/auth/me')
    return data
  },

  // ─── PERFIL / GESTIÓN DE CUENTA ───
  async actualizarPerfil(nombre, apellido) {
    const { data } = await client.put('/users/me', { nombre, apellido })
    return data
  },
  async cambiarPassword(password_actual, nueva_password) {
    const { data } = await client.put('/users/me/password', { password_actual, nueva_password })
    return data
  },
  async eliminarCuenta(password, confirmacion) {
    const { data } = await client.delete('/users/me', { data: { password, confirmacion } })
    return data
  },

  // ─── ADMIN ───
  async listarUsuarios(role = null) {
    const { data } = await client.get('/admin/users', { params: role ? { role } : {} })
    return data
  },
  async statsUsuarios() {
    const { data } = await client.get('/admin/stats')
    return data
  },

  // ─── PSICÓLOGO (HU-20) ───
  async listarEstudiantes() {
    const { data } = await client.get('/psychologist/students')
    return data
  },
  async historialEstudiante(student_id) {
    const { data } = await client.get(`/psychologist/students/${student_id}/history`)
    return data
  },

  // ─── CONSENTIMIENTO ───
  async aceptarConsentimiento(version) {
    const { data } = await client.post('/consent/aceptar', { version })
    return data
  },
  async estadoConsentimiento() {
    const { data } = await client.get('/consent/estado')
    return data
  },

  // ─── CHATBOT ───
  async iniciarSesion() {
    const { data } = await client.post('/chatbot/start')
    return data
  },
  async responder(session_id, respuesta) {
    const { data } = await client.post('/chatbot/answer', { session_id, respuesta })
    return data
  },
  async analizar(session_id) {
    const { data } = await client.post('/chatbot/analizar', null, { params: { session_id } })
    return data
  },
  async historial(session_id) {
    const { data } = await client.get(`/chatbot/conversacion/${session_id}`)
    return data
  },
  async health() {
    const { data } = await client.get('/chatbot/health')
    return data
  },
}
