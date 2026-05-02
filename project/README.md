# Frontend — Salud Mental UPC (Vue 3)

Prototipo de chat conversacional estilo ChatGPT para evaluación de bienestar emocional basada en BERT.

## Stack

- **Vue 3** (composition API + `<script setup>`)
- **Vite** (build tool)
- **Tailwind CSS** (estilo)
- **Chart.js** (gráfico de barras horizontales)
- **Axios** (cliente HTTP)

## Estructura

```
project/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.js
    ├── App.vue                    → orquestador de vistas
    ├── api.js                     → cliente axios
    ├── style.css                  → tailwind + animaciones
    └── components/
        ├── StartScreen.vue        → formulario de entrada
        ├── ChatScreen.vue         → chat tipo ChatGPT con 10 preguntas
        └── ResultsScreen.vue      → perfil + gráfico + métodos + conclusión
```

## Cómo ejecutar

### 1. Arrancar el backend (FastAPI, en otra terminal)

```bash
cd /home/renzo/salud-mental-TP1
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Instalar y correr el frontend

```bash
cd /home/renzo/salud-mental-TP1/project
npm install
npm run dev
```

Abrir: http://localhost:5173

> **Nota:** La primera petición a `/analizar` tarda 1–3 minutos (descarga del modelo BERT ~400 MB). Las siguientes son instantáneas.

## Flujo

1. **StartScreen** — el usuario ingresa su nombre.
2. **ChatScreen** — 10 preguntas conversacionales (alineadas a PHQ-9, GAD-7, ASRS, UCLA-3, C-SSRS).
3. **ResultsScreen** — tras la respuesta 10, se llama a `/analizar` y se muestra:
   - **Perfil** con nivel de riesgo global (CRÍTICO / ALTO / MEDIO / BAJO)
   - **Gráfico** de barras con scores de cada condición
   - **Condiciones detectadas** (depresión, ansiedad, TDAH, estrés, soledad, riesgo suicida)
   - **Indicaciones** generadas por el modelo
   - **Métodos** (modelo, técnica, escalas de referencia, umbrales)
   - **Conclusión para revisión profesional** (resumen para el psicólogo)
   - Botón "Imprimir / PDF" para exportar

## Variables de entorno (opcional)

Crea `.env` en `project/` si el backend está en otro host:

```
VITE_API_BASE=http://localhost:8000/api/v1
```
