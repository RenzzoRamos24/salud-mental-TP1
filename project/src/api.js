import axios from "axios";
import { authStore } from "./store/auth";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 300000, // 5 min (primera llamada carga BERT)
});

// Inyecta token en cada request
client.interceptors.request.use((config) => {
  const token = authStore.state.token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Maneja 401 globalmente
client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 401) {
      authStore.clear();
      // El router redirigirá a /login en el siguiente render
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export const api = {
  // ─── AUTH ───
  async register(payload) {
    const { data } = await client.post("/auth/register", payload);
    return data;
  },
  async login(email, password) {
    const { data } = await client.post("/auth/login", { email, password });
    return data;
  },
  async logout() {
    try {
      await client.post("/auth/logout");
    } catch (_) {}
  },
  async forgotPassword(email) {
    const { data } = await client.post("/auth/forgot-password", { email });
    return data;
  },
  async resetPassword(email, token, nueva_password) {
    const { data } = await client.post("/auth/reset-password", {
      email,
      token,
      nueva_password,
    });
    return data;
  },
  async me() {
    const { data } = await client.get("/auth/me");
    return data;
  },

  // ─── OAUTH (Google / Microsoft) ───
  async oauthConfig() {
    const { data } = await client.get("/auth/oauth/config");
    return data;
  },
  async oauthGoogle(id_token) {
    const { data } = await client.post("/auth/oauth/google", { id_token });
    return data;
  },
  async oauthMicrosoft(access_token) {
    const { data } = await client.post("/auth/oauth/microsoft", {
      access_token,
    });
    return data;
  },

  // ─── PERFIL / GESTIÓN DE CUENTA ───
  async actualizarPerfil(nombre, apellido) {
    const { data } = await client.put("/users/me", { nombre, apellido });
    return data;
  },
  async cambiarPassword(password_actual, nueva_password) {
    const { data } = await client.put("/users/me/password", {
      password_actual,
      nueva_password,
    });
    return data;
  },
  async eliminarCuenta(password, confirmacion) {
    const { data } = await client.delete("/users/me", {
      data: { password, confirmacion },
    });
    return data;
  },

  // ─── ADMIN: usuarios ───
  async listarUsuarios(role = null) {
    const { data } = await client.get("/admin/users", {
      params: role ? { role } : {},
    });
    return data;
  },
  async statsUsuarios() {
    const { data } = await client.get("/admin/stats");
    return data;
  },

  // ─── ADMIN: Sprint 6 ───
  async adminGetEncuesta() {
    const { data } = await client.get("/admin/config/encuesta");
    return data;
  },
  async adminUpdateEncuesta(preguntas, frecuencia_dias) {
    const { data } = await client.put("/admin/config/encuesta", {
      preguntas,
      frecuencia_dias,
    });
    return data;
  },
  async adminGetAuditLogs({ limit = 100, offset = 0, role, endpoint } = {}) {
    const { data } = await client.get("/admin/audit-logs", {
      params: {
        limit,
        offset,
        ...(role && { role }),
        ...(endpoint && { endpoint }),
      },
    });
    return data;
  },
  async adminCrearBackup() {
    const { data } = await client.post("/admin/backup");
    return data;
  },
  async adminListarBackups() {
    const { data } = await client.get("/admin/backups");
    return data;
  },
  async adminGetUmbrales() {
    const { data } = await client.get("/admin/bert/umbrales");
    return data;
  },
  async adminUpdateUmbrales(payload) {
    const { data } = await client.put("/admin/bert/umbrales", payload);
    return data;
  },
  async adminGetModeloInfo() {
    const { data } = await client.get("/admin/bert/modelo");
    return data;
  },
  async adminRecargarModelo() {
    const { data } = await client.post("/admin/bert/recargar");
    return data;
  },

  // ─── ESTUDIANTE: historial propio (HU-12) ───
  async miHistorial() {
    const { data } = await client.get("/chatbot/mi-historial");
    return data;
  },

  // ─── PSICÓLOGO (Sprint 5: HU-15, HU-16, HU-17, HU-19) ───
  async dashboardStats() {
    const { data } = await client.get("/psychologist/dashboard-stats");
    return data;
  },
  async listarEstudiantes() {
    const { data } = await client.get("/psychologist/students");
    return data;
  },
  async resumenEstudiantes() {
    const { data } = await client.get("/psychologist/students-overview");
    return data;
  },
  async historialEstudiante(student_id) {
    const { data } = await client.get(
      `/psychologist/students/${student_id}/history`,
    );
    return data;
  },
  async resumenDiarioEstudiante(student_id) {
    const { data } = await client.get(
      `/psychologist/students/${student_id}/diario-resumen`,
    );
    return data;
  },
  async reporteCicloEstudiante(student_id, ciclo = null) {
    const params = ciclo != null ? { ciclo } : {};
    const { data } = await client.get(
      `/psychologist/students/${student_id}/reporte-ciclo`,
      { params },
    );
    return data;
  },
  async crearCita(payload) {
    const { data } = await client.post("/psychologist/citas", payload);
    return data;
  },
  async listarCitas(estudiante_id = null) {
    const params = estudiante_id ? { estudiante_id } : {};
    const { data } = await client.get("/psychologist/citas", { params });
    return data;
  },
  async actualizarCita(cita_id, payload) {
    const { data } = await client.put(
      `/psychologist/citas/${cita_id}`,
      payload,
    );
    return data;
  },
  async cancelarCita(cita_id) {
    await client.delete(`/psychologist/citas/${cita_id}`);
  },

  // ─── CONSENTIMIENTO ───
  async aceptarConsentimiento(version) {
    const { data } = await client.post("/consent/aceptar", { version });
    return data;
  },
  async estadoConsentimiento() {
    const { data } = await client.get("/consent/estado");
    return data;
  },

  // ─── CHATBOT ───
  async iniciarSesion() {
    const { data } = await client.post("/chatbot/start");
    return data;
  },
  async responder(session_id, respuesta, score_likert = null) {
    const payload = { session_id, respuesta };
    if (score_likert !== null && score_likert !== undefined) {
      payload.score_likert = score_likert;
    }
    const { data } = await client.post("/chatbot/answer", payload);
    return data;
  },
  async analizar(session_id) {
    const { data } = await client.post("/chatbot/analizar", null, {
      params: { session_id },
    });
    return data;
  },
  async historial(session_id) {
    const { data } = await client.get(`/chatbot/conversacion/${session_id}`);
    return data;
  },
  async health() {
    const { data } = await client.get("/chatbot/health");
    return data;
  },

  // ─── HU-30: Cita iniciada por el estudiante ───
  async solicitarCita({
    fecha,
    hora,
    modalidad = "presencial",
    motivo = null,
  }) {
    const { data } = await client.post("/chatbot/cita", {
      fecha,
      hora,
      modalidad,
      motivo,
    });
    return data;
  },
  async misCitas() {
    const { data } = await client.get("/chatbot/citas/mias");
    return data;
  },

  // ─── HU-31: SOS ───
  async activarSOS({ origen = null, mensaje = null } = {}) {
    const { data } = await client.post("/sos/", { origen, mensaje });
    return data;
  },
  async listarSOSAbiertos() {
    const { data } = await client.get("/sos/abiertos");
    return data;
  },
  async marcarSOSAtendido(event_id) {
    const { data } = await client.patch(`/sos/${event_id}/atender`);
    return data;
  },

  // ─── HU-25: Encuesta de satisfacción ───
  async miSatisfaccion() {
    const { data } = await client.get("/survey/satisfaction/me");
    return data;
  },
  async enviarSatisfaccion(payload) {
    const { data } = await client.post("/survey/satisfaction", payload);
    return data;
  },
  async adminResumenSatisfaccion() {
    const { data } = await client.get("/survey/admin/satisfaction/summary");
    return data;
  },

  // ─── HU-29 + HU-40: Contenido psicoeducativo ───
  async listarContenidos(categoria = null) {
    const { data } = await client.get("/content/", {
      params: categoria ? { categoria } : {},
    });
    return data;
  },
  async obtenerContenido(id) {
    const { data } = await client.get(`/content/${id}`);
    return data;
  },
  async adminListarTodosContenidos() {
    const { data } = await client.get("/content/admin/all");
    return data;
  },
  async adminCrearContenido(payload) {
    const { data } = await client.post("/content/admin", payload);
    return data;
  },
  async adminActualizarContenido(id, payload) {
    const { data } = await client.put(`/content/admin/${id}`, payload);
    return data;
  },
  async adminEliminarContenido(id) {
    await client.delete(`/content/admin/${id}`);
  },

  // ─── HU-33: Notas clínicas privadas ───
  async listarNotas(student_id) {
    const { data } = await client.get(
      `/psychologist/students/${student_id}/notes`,
    );
    return data;
  },
  async crearNota(student_id, { texto, etiqueta = null }) {
    const { data } = await client.post(
      `/psychologist/students/${student_id}/notes`,
      { texto, etiqueta },
    );
    return data;
  },
  async borrarNota(student_id, nota_id) {
    await client.delete(
      `/psychologist/students/${student_id}/notes/${nota_id}`,
    );
  },

  // ─── HU-35: Estado del caso ───
  async cambiarEstadoCaso(student_id, estado) {
    const { data } = await client.patch(
      `/psychologist/students/${student_id}/case-status`,
      { estado },
    );
    return data;
  },

  // ─── HU-18: Reportes mensuales ───
  async reporteMensual(year, month) {
    const { data } = await client.get("/psychologist/reports/monthly", {
      params: { year, month },
    });
    return data;
  },
  async reporteMensualAdmin(year, month) {
    const { data } = await client.get("/admin/reports/monthly", {
      params: { year, month },
    });
    return data;
  },

  // ─── HU-38: Asignar psicólogo ───
  async asignarPsicologo(student_id, psicologo_id) {
    const { data } = await client.post(
      `/admin/students/${student_id}/assign-psychologist`,
      { psicologo_id },
    );
    return data;
  },

  // ─── HU-39: Mensajes del chatbot ───
  async getChatbotMessages() {
    const { data } = await client.get("/admin/chatbot-messages");
    return data;
  },
  async updateChatbotMessages(mensajes) {
    const { data } = await client.put("/admin/chatbot-messages", { mensajes });
    return data;
  },

  // ─── DIARIO digital del estudiante ───
  async crearEntradaDiario({
    texto,
    estado_animo = null,
    prompt_del_dia = null,
  }) {
    const { data } = await client.post("/diario/entrada", {
      texto,
      estado_animo,
      prompt_del_dia,
    });
    return data;
  },
  async listarMisEntradasDiario() {
    const { data } = await client.get("/diario/mis-entradas");
    return data;
  },
  async obtenerEntradaDiario(id) {
    const { data } = await client.get(`/diario/entrada/${id}`);
    return data;
  },
  async actualizarEntradaDiario(id, { texto, estado_animo = null, prompt_del_dia = null }) {
    const { data } = await client.put(`/diario/entrada/${id}`, {
      texto,
      estado_animo,
      prompt_del_dia,
    });
    return data;
  },

  // ─── Panel de apoyo del estudiante ───
  async misRecomendaciones() {
    const { data } = await client.get("/diario/recomendaciones");
    return data;
  },
  async misMensajesPsicologo() {
    const { data } = await client.get("/diario/mensajes-psicologo");
    return data;
  },
  // ─── ENCUESTA CLÍNICA (cierre de ciclo) ───
  async encuestaPendiente() {
    const { data } = await client.get("/diario/encuesta-clinica/pendiente");
    return data;
  },
  async encuestaResponder(item_id, valor) {
    const { data } = await client.post("/diario/encuesta-clinica/respuesta", {
      item_id,
      valor,
    });
    return data;
  },
  async encuestaCerrar() {
    const { data } = await client.post("/diario/encuesta-clinica/cerrar");
    return data;
  },

  async marcarMensajePsicologoLeido(id) {
    const { data } = await client.post(
      `/diario/mensajes-psicologo/${id}/leido`,
    );
    return data;
  },
  async misCitas() {
    const { data } = await client.get("/diario/mis-citas");
    return data;
  },
  async miCiclo() {
    const { data } = await client.get("/diario/mi-ciclo");
    return data;
  },
  async consejoDelDia() {
    const { data } = await client.get("/diario/consejo-del-dia");
    return data;
  },

  // ─── Mensajes del psicólogo al estudiante (lado psicólogo) ───
  async listarMensajesEstudiante(student_id) {
    const { data } = await client.get(
      `/psychologist/students/${student_id}/mensajes`,
    );
    return data;
  },
  async crearMensajeEstudiante(student_id, mensaje) {
    const { data } = await client.post(
      `/psychologist/students/${student_id}/mensajes`,
      { mensaje },
    );
    return data;
  },
  async borrarMensajeEstudiante(student_id, mensaje_id) {
    const { data } = await client.delete(
      `/psychologist/students/${student_id}/mensajes/${mensaje_id}`,
    );
    return data;
  },
};
