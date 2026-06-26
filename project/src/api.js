import axios from "axios";
import { authStore } from "./store/auth";

// En producción la SPA se sirve desde el mismo origen que la API → usamos
// path relativo. En dev (vite en :5173) usamos http://localhost:8000.
const API_BASE =
  import.meta.env.VITE_API_BASE ||
  (import.meta.env.PROD ? "/api/v1" : "http://localhost:8000/api/v1");

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 300000,
});

client.interceptors.request.use((config) => {
  const token = authStore.state.token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 401) {
      authStore.clear();
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

  // ─── OAUTH ───
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

  // ─── PERFIL ───
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

  // ─── ALUMNO: citas + psicólogo asignado ───
  async misCitas() {
    const { data } = await client.get("/users/me/citas");
    return data;
  },
  async solicitarCita(payload) {
    const { data } = await client.post("/users/me/citas", payload);
    return data;
  },
  async miPsicologo() {
    const { data } = await client.get("/users/me/psicologo");
    return data;
  },
  async slotsSugeridos(cantidad = 4) {
    const { data } = await client.get("/users/me/slots-sugeridos", {
      params: { cantidad },
    });
    return data;
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

  // ─── BANCO (psicóloga / admin) ───
  async listarInstrumentos() {
    const { data } = await client.get("/banco/instrumentos");
    return data;
  },
  async obtenerInstrumento(codigo) {
    const { data } = await client.get(`/banco/instrumentos/${codigo}`);
    return data;
  },
  async listarFrases() {
    const { data } = await client.get("/banco/frases");
    return data;
  },
  async listarAreasFrases() {
    const { data } = await client.get("/banco/frases/areas");
    return data;
  },
  async listarBloquesCustom() {
    const { data } = await client.get("/banco/bloques-custom");
    return data;
  },
  async crearBloqueCustom(payload) {
    const { data } = await client.post("/banco/bloques-custom", payload);
    return data;
  },
  async obtenerBloqueCustom(id) {
    const { data } = await client.get(`/banco/bloques-custom/${id}`);
    return data;
  },
  async actualizarBloqueCustom(id, payload) {
    const { data } = await client.put(`/banco/bloques-custom/${id}`, payload);
    return data;
  },
  async borrarBloqueCustom(id) {
    await client.delete(`/banco/bloques-custom/${id}`);
  },
  async sugerirCortes(rango_max) {
    const { data } = await client.get("/banco/sugerir-cortes", {
      params: { rango_max },
    });
    return data;
  },

  // ─── PLANTILLAS ───
  async listarPlantillas() {
    const { data } = await client.get("/plantillas");
    return data;
  },
  async crearPlantilla(payload) {
    const { data } = await client.post("/plantillas", payload);
    return data;
  },
  async obtenerPlantilla(id) {
    const { data } = await client.get(`/plantillas/${id}`);
    return data;
  },
  async actualizarPlantilla(id, payload) {
    const { data } = await client.put(`/plantillas/${id}`, payload);
    return data;
  },
  async borrarPlantilla(id) {
    await client.delete(`/plantillas/${id}`);
  },

  // ─── CUESTIONARIOS (asignación + respuesta) ───
  async asignarCuestionario(plantilla_id, estudiante_id) {
    const { data } = await client.post("/cuestionarios/asignar", {
      plantilla_id,
      estudiante_id,
    });
    return data;
  },
  async misCuestionarios() {
    const { data } = await client.get("/cuestionarios/mis-cuestionarios");
    return data;
  },
  async detalleParaResponder(aplicacion_id) {
    const { data } = await client.get(
      `/cuestionarios/responder/${aplicacion_id}`,
    );
    return data;
  },
  async guardarRespuestas(aplicacion_id, respuestas) {
    const { data } = await client.post(
      `/cuestionarios/responder/${aplicacion_id}/guardar`,
      { respuestas },
    );
    return data;
  },
  async cerrarCuestionario(aplicacion_id) {
    const { data } = await client.post(
      `/cuestionarios/responder/${aplicacion_id}/cerrar`,
    );
    return data;
  },
  async obtenerResultado(aplicacion_id) {
    const { data } = await client.get(
      `/cuestionarios/aplicacion/${aplicacion_id}/resultado`,
    );
    return data;
  },
  async marcarRevisado(aplicacion_id) {
    const { data } = await client.post(
      `/cuestionarios/aplicacion/${aplicacion_id}/marcar-revisado`,
    );
    return data;
  },

  // ─── PSICÓLOGA: dashboard y estudiantes ───
  async dashboardStats() {
    const { data } = await client.get("/psychologist/dashboard-stats");
    return data;
  },
  async listarEstudiantes() {
    const { data } = await client.get("/psychologist/students");
    return data;
  },
  async historialEstudiante(student_id) {
    const { data } = await client.get(
      `/psychologist/students/${student_id}/history`,
    );
    return data;
  },
  async cambiarEstadoCaso(student_id, estado) {
    const { data } = await client.patch(
      `/psychologist/students/${student_id}/case-status`,
      { estado },
    );
    return data;
  },

  // ─── CITAS ───
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

  // ─── NOTAS CLÍNICAS ───
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

  // ─── ADMIN ───
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
  async adminGetModeloInfo() {
    const { data } = await client.get("/admin/nlp/modelo");
    return data;
  },
  async adminRecargarModelo() {
    const { data } = await client.post("/admin/nlp/recargar");
    return data;
  },
  async asignarPsicologo(student_id, psicologo_id) {
    const { data } = await client.post(
      `/admin/students/${student_id}/assign-psychologist`,
      { psicologo_id },
    );
    return data;
  },
  async adminStatsCuestionarios() {
    const { data } = await client.get("/admin/cuestionarios/stats");
    return data;
  },

  // ─── SOS ───
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

  // ─── SATISFACCIÓN ───
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

  // ─── CONTENIDO ───
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
};
