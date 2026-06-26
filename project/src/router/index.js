import { createRouter, createWebHistory } from "vue-router";
import { authStore } from "../store/auth";

import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import ForgotPasswordView from "../views/ForgotPasswordView.vue";
import ResetPasswordView from "../views/ResetPasswordView.vue";
import ConsentView from "../views/ConsentView.vue";
import MainMenuView from "../views/MainMenuView.vue";
import StudentHomeView from "../views/StudentHomeView.vue";
import ProfileView from "../views/ProfileView.vue";
import RecursosView from "../views/RecursosView.vue";
import OAuthCallbackView from "../views/OAuthCallbackView.vue";

import StudentQuestionnairesView from "../views/StudentQuestionnairesView.vue";
import StudentAnswerView from "../views/StudentAnswerView.vue";

import PsychologistDashboardView from "../views/PsychologistDashboardView.vue";
import PsychologistStudentsView from "../views/PsychologistStudentsView.vue";
import PsychologistAlertsView from "../views/PsychologistAlertsView.vue";
import StudentHistoryView from "../views/StudentHistoryView.vue";
import PsychologistBankView from "../views/PsychologistBankView.vue";
import PsychologistTemplatesView from "../views/PsychologistTemplatesView.vue";
import PsychologistCustomBlockView from "../views/PsychologistCustomBlockView.vue";
import PsychologistAssignView from "../views/PsychologistAssignView.vue";
import PsychologistResultView from "../views/PsychologistResultView.vue";
import PsychologistSOSView from "../views/PsychologistSOSView.vue";
import PsychologistAppointmentsView from "../views/PsychologistAppointmentsView.vue";

import AdminDashboardView from "../views/AdminDashboardView.vue";
import AdminSystemView from "../views/AdminSystemView.vue";
import AdminContentView from "../views/AdminContentView.vue";
import AdminReportsView from "../views/AdminReportsView.vue";
import AdminLogsView from "../views/AdminLogsView.vue";

import SatisfactionSurveyView from "../views/SatisfactionSurveyView.vue";

const routes = [
  { path: "/", redirect: "/login" },
  { path: "/login", name: "login", component: LoginView, meta: { publica: true } },
  { path: "/register", name: "register", component: RegisterView, meta: { publica: true } },
  { path: "/forgot-password", name: "forgot", component: ForgotPasswordView, meta: { publica: true } },
  { path: "/reset-password", name: "reset", component: ResetPasswordView, meta: { publica: true } },
  { path: "/oauth-callback", name: "oauth-callback", component: OAuthCallbackView, meta: { publica: true } },
  { path: "/consent", name: "consent", component: ConsentView, meta: { requiereAuth: true } },

  { path: "/menu", name: "menu", component: StudentHomeView, meta: { requiereAuth: true, requiereConsent: true } },
  { path: "/menu-legacy", name: "menu-legacy", component: MainMenuView, meta: { requiereAuth: true, requiereConsent: true } },
  { path: "/perfil", name: "perfil", component: ProfileView, meta: { requiereAuth: true, requiereConsent: true } },
  { path: "/recursos", name: "recursos", component: RecursosView, meta: { requiereAuth: true, requiereConsent: true } },

  // ── Alumno ──
  {
    path: "/mis-cuestionarios",
    name: "mis-cuestionarios",
    component: StudentQuestionnairesView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["estudiante"] },
  },
  {
    path: "/responder/:id",
    name: "responder",
    component: StudentAnswerView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["estudiante"] },
  },

  // ── Psicóloga ──
  {
    path: "/psicologo",
    name: "psicologo",
    component: PsychologistDashboardView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/estudiantes",
    name: "psicologo-estudiantes",
    component: PsychologistStudentsView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/alertas",
    name: "psicologo-alertas",
    component: PsychologistAlertsView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/estudiante/:id",
    name: "psicologo-estudiante",
    component: StudentHistoryView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/banco",
    name: "psicologo-banco",
    component: PsychologistBankView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/bloque-custom",
    name: "psicologo-bloque-custom",
    component: PsychologistCustomBlockView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/plantillas",
    name: "psicologo-plantillas",
    component: PsychologistTemplatesView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/asignar",
    name: "asignar-cuestionario",
    component: PsychologistAssignView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/resultado/:id",
    name: "psicologo-resultado",
    component: PsychologistResultView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/sos",
    name: "psicologo-sos",
    component: PsychologistSOSView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },
  {
    path: "/psicologo/citas",
    name: "psicologo-citas",
    component: PsychologistAppointmentsView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["psicologo", "admin"] },
  },

  // ── Admin ──
  {
    path: "/admin",
    name: "admin",
    component: AdminDashboardView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["admin"] },
  },
  {
    path: "/admin/sistema",
    name: "admin-sistema",
    component: AdminSystemView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["admin"] },
  },
  {
    path: "/admin/contenidos",
    name: "admin-contenidos",
    component: AdminContentView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["admin"] },
  },
  {
    path: "/admin/reportes",
    name: "admin-reportes",
    component: AdminReportsView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["admin"] },
  },
  {
    path: "/admin/logs",
    name: "admin-logs",
    component: AdminLogsView,
    meta: { requiereAuth: true, requiereConsent: true, roles: ["admin"] },
  },

  // ── Satisfacción ──
  {
    path: "/encuesta",
    name: "encuesta",
    component: SatisfactionSurveyView,
    meta: { requiereAuth: true, requiereConsent: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

function inicioPorRol(rol) {
  if (rol === "psicologo") return { name: "psicologo" };
  if (rol === "admin") return { name: "admin" };
  return { name: "menu" };
}

router.beforeEach((to) => {
  const auth = authStore.isAuthenticated.value;
  const consent = authStore.consentimientoAceptado.value;
  const rol = authStore.rol.value;

  if (to.meta.requiereAuth && !auth) {
    return { name: "login", query: { redirect: to.fullPath } };
  }
  if (to.meta.publica && auth) {
    return consent ? inicioPorRol(rol) : { name: "consent" };
  }
  if (to.meta.requiereConsent && !consent) {
    return { name: "consent" };
  }
  if (auth && consent && to.name === "menu" && rol !== "estudiante") {
    return inicioPorRol(rol);
  }
  if (to.meta.roles && !to.meta.roles.includes(rol)) {
    return inicioPorRol(rol);
  }
  return true;
});

export default router;
