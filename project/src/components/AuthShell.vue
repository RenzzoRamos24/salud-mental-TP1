<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
});
</script>

<template>
  <div class="auth-shell">
    <div class="auth-col">
      <div class="auth-brand">
        <img src="/sentir-isotipo.svg" class="auth-logo" alt="SENTIR" />
        <span class="word">Sami</span>
      </div>
      <p class="auth-tag">Tu espacio para escribir.</p>

      <div class="auth-card">
        <div class="auth-head">
          <h1>{{ title }}</h1>
          <p v-if="subtitle">{{ subtitle }}</p>
        </div>

        <slot />

        <div v-if="$slots.footer" class="auth-foot">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.auth-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  background: #f5f5f6;
  color: #1d1d1f;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui,
    "Helvetica Neue", sans-serif;
  -webkit-font-smoothing: antialiased;
}
.auth-col {
  width: 100%;
  max-width: 420px;
}
.auth-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #1d1d1f;
}
.auth-logo {
  height: 30px;
  width: auto;
}
.auth-tag {
  text-align: center;
  margin: 6px 0 26px;
  font-size: 12.5px;
  color: #8e8e95;
}
.auth-card {
  background: #fff;
  border: 1px solid #e4e4e8;
  border-radius: 12px;
  padding: 32px 28px;
}
.auth-head {
  text-align: center;
  margin-bottom: 22px;
}
.auth-head h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #1d1d1f;
}
.auth-head p {
  margin: 6px 0 0;
  font-size: 13px;
  color: #56565c;
}
.auth-foot {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid #ececef;
  text-align: center;
  font-size: 13px;
  color: #56565c;
}
.auth-foot a {
  color: #0d9488;
  font-weight: 600;
  text-decoration: none;
}
.auth-foot a:hover {
  text-decoration: underline;
}
</style>
