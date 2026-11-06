import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./style.css";
import "./sami.css";

import { authStore } from "./store/auth";

createApp(App).use(router).mount("#app");

// QA CP012: aunque el usuario no navegue ni dispare peticiones, la sesión
// vencida lo devuelve al login (el interceptor 401 solo actúa cuando hay una).
setInterval(() => {
  if (authStore.sesionVencida()) {
    authStore.clear();
    if (window.location.pathname !== "/login") {
      window.location.href = "/login?expirada=1";
    }
  }
}, 30000);
