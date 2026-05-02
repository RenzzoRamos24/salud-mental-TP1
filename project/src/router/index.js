import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../store/auth'

import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ForgotPasswordView from '../views/ForgotPasswordView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import ConsentView from '../views/ConsentView.vue'
import MainMenuView from '../views/MainMenuView.vue'
import ProfileView from '../views/ProfileView.vue'
import ChatView from '../views/ChatView.vue'
import ResultsView from '../views/ResultsView.vue'
import PsychologistDashboardView from '../views/PsychologistDashboardView.vue'
import StudentHistoryView from '../views/StudentHistoryView.vue'
import AdminDashboardView from '../views/AdminDashboardView.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: LoginView, meta: { publica: true } },
  { path: '/register', name: 'register', component: RegisterView, meta: { publica: true } },
  { path: '/forgot-password', name: 'forgot', component: ForgotPasswordView, meta: { publica: true } },
  { path: '/reset-password', name: 'reset', component: ResetPasswordView, meta: { publica: true } },
  { path: '/consent', name: 'consent', component: ConsentView, meta: { requiereAuth: true } },
  { path: '/menu', name: 'menu', component: MainMenuView, meta: { requiereAuth: true, requiereConsent: true } },
  { path: '/perfil', name: 'perfil', component: ProfileView, meta: { requiereAuth: true, requiereConsent: true } },
  { path: '/chat', name: 'chat', component: ChatView, meta: { requiereAuth: true, requiereConsent: true, roles: ['estudiante'] } },
  { path: '/resultados', name: 'resultados', component: ResultsView, meta: { requiereAuth: true, requiereConsent: true, roles: ['estudiante'] } },
  { path: '/psicologo', name: 'psicologo', component: PsychologistDashboardView, meta: { requiereAuth: true, requiereConsent: true, roles: ['psicologo', 'admin'] } },
  { path: '/psicologo/estudiante/:id', name: 'psicologo-estudiante', component: StudentHistoryView, meta: { requiereAuth: true, requiereConsent: true, roles: ['psicologo', 'admin'] } },
  { path: '/admin', name: 'admin', component: AdminDashboardView, meta: { requiereAuth: true, requiereConsent: true, roles: ['admin'] } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = authStore.isAuthenticated.value
  const consent = authStore.consentimientoAceptado.value
  const rol = authStore.rol.value

  // No autenticado y la ruta requiere auth → /login
  if (to.meta.requiereAuth && !auth) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // Autenticado yendo a una ruta pública → /menu o /consent
  if (to.meta.publica && auth) {
    return consent ? { name: 'menu' } : { name: 'consent' }
  }

  // Autenticado, no aceptó consentimiento y va a algo que lo requiere → /consent
  if (to.meta.requiereConsent && !consent) {
    return { name: 'consent' }
  }

  // Restricción por rol
  if (to.meta.roles && !to.meta.roles.includes(rol)) {
    return { name: 'menu' }
  }

  return true
})

export default router
