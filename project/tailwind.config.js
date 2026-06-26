/** @type {import('tailwindcss').Config} */
// Paleta TEAL del handoff design (Sami 2026-06).
// Primario teal #45988C; rojo solo riesgo/crisis.
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Teal — paleta Apollo del handoff hospital_dashboard.
        teal: {
          50: "#e3f3ef",
          100: "#d3e8e3",
          200: "#a8d6cc",
          300: "#74b8ae",
          400: "#22b8a6",
          500: "#1aa896",
          600: "#0e8d7e",
          700: "#0c8475",
          800: "#0a7066",
          900: "#075a53",
        },
        // Aliases para compatibilidad.
        green: {
          50: "#EDF5F3",
          100: "#C5E1DC",
          200: "#9ECFC6",
          300: "#74B8AE",
          400: "#5BA89E",
          500: "#45988C",
          600: "#347F74",
          700: "#2F7D72",
          800: "#236058",
          900: "#1B4A45",
        },
        brand: {
          50: "#EDF5F3",
          100: "#C5E1DC",
          200: "#9ECFC6",
          300: "#74B8AE",
          400: "#5BA89E",
          500: "#45988C",
          600: "#347F74",
          700: "#2F7D72",
          800: "#236058",
          900: "#1B4A45",
        },
        mint: {
          50: "#EDF5F3",
          100: "#C5E1DC",
          200: "#9ECFC6",
          300: "#74B8AE",
          400: "#5BA89E",
          500: "#45988C",
          600: "#347F74",
        },
        // Coral solo para SOS.
        coral: {
          50: "#FEF2F2",
          100: "#FEE2E2",
          200: "#FECACA",
          300: "#FCA5A5",
          400: "#F87171",
          500: "#F87171",
          600: "#DC2626",
        },
        // Peach neutralizado.
        peach: {
          50: "#F4F5F6",
          100: "#E5E7EB",
          200: "#D1D5DB",
          300: "#9CA3AF",
          400: "#6B7280",
          500: "#4B5563",
          600: "#374151",
        },
        sky2: {
          50: "#F4F5F6",
          100: "#E5E7EB",
          200: "#D1D5DB",
          300: "#9CA3AF",
          400: "#6B7280",
          500: "#4B5563",
        },
        // Escala de riesgo — semántica, NO tocar.
        risk: {
          critico: "#DC2626",
          alto: "#F97316",
          medio: "#F59E0B",
          bajo: "#0EA5E9",
          sin: "#45988C",
          eval: "#9CA3AF",
        },
        cream: {
          50: "#F9FAFB",
          100: "#F4F5F6",
          200: "#ECECEE",
        },
        ink: {
          900: "#0A0A0A",
          800: "#1F2937",
          700: "#344054",
          600: "#475467",
          500: "#667085",
          400: "#98A2B3",
          300: "#B0B7BF",
          200: "#E5E7EB",
          100: "#F4F5F6",
        },
      },
      fontFamily: {
        sans: ['"Work Sans"', "system-ui", "sans-serif"],
        display: ['"Newsreader"', "Georgia", "serif"],
        serif: ['"Newsreader"', "Georgia", "serif"],
      },
      borderRadius: {
        xl2: "1rem",
        "2xl2": "1.25rem",
        card: "18px",
      },
      boxShadow: {
        subtle: "0 1px 2px rgba(16,24,40,.04)",
        soft: "0 1px 2px rgba(16,24,40,.04)",
        card: "0 1px 2px rgba(16,24,40,.04)",
        "card-hover": "0 4px 14px -6px rgba(16,24,40,.12)",
        hero: "0 1px 2px rgba(16,24,40,.04), 0 14px 34px -16px rgba(16,24,40,.18)",
        lift: "0 8px 18px -8px rgba(16,24,40,.2)",
        green: "0 8px 18px -6px rgba(69,152,140,.5)",
        teal: "0 8px 18px -6px rgba(69,152,140,.5)",
        pastel: "0 1px 2px rgba(16,24,40,.04), 0 6px 20px -10px rgba(16,24,40,.16)",
      },
      letterSpacing: {
        tightish: "-0.012em",
        title: "-0.025em",
      },
      keyframes: {
        pop: {
          "0%": { transform: "scale(.96)", opacity: 0 },
          "100%": { transform: "scale(1)", opacity: 1 },
        },
        slidedown: {
          from: { opacity: 0, transform: "translateY(-6px)" },
          to: { opacity: 1, transform: "none" },
        },
        ckpop: {
          "0%": { transform: "scale(.3)", opacity: 0 },
          "55%": { transform: "scale(1.25)" },
          "100%": { transform: "scale(1)", opacity: 1 },
        },
      },
      animation: {
        pop: "pop .18s ease-out",
        slidedown: "slidedown .2s ease-out",
        ckpop: "ckpop .25s ease-out",
      },
    },
  },
  plugins: [],
};
