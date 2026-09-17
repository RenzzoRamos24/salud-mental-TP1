import { reactive } from "vue";

/**
 * Estado de interfaz compartido entre el shell y el sidebar.
 *
 * `menuAbierto` solo tiene efecto en pantallas ≤760px, donde el sidebar deja
 * de ser una columna fija y pasa a mostrarse como panel deslizante sobre el
 * contenido. En escritorio el sidebar siempre está visible.
 */
export const uiStore = reactive({
  menuAbierto: false,
  abrirMenu() {
    this.menuAbierto = true;
  },
  cerrarMenu() {
    this.menuAbierto = false;
  },
  alternarMenu() {
    this.menuAbierto = !this.menuAbierto;
  },
});
