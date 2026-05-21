/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Pastel Empático — paleta principal lavanda (salud mental / calma / confianza)
        brand: {
          50:  '#F6F3FF',
          100: '#EDE7FE',
          200: '#DDD3FD',
          300: '#C5B3FB',
          400: '#A78BFA',
          500: '#8B6CF0',
          600: '#7551E0',
          700: '#5E3FC1',
          800: '#4A3299',
          900: '#3A2876',
        },
        // Melocotón cálido — empatía / acción suave
        peach: {
          50:  '#FFF6F2',
          100: '#FFE9DF',
          200: '#FFD2BD',
          300: '#FFB597',
          400: '#FB9573',
          500: '#F2754F',
          600: '#D85B36',
        },
        // Menta — calma / éxito
        mint: {
          50:  '#EFFBF4',
          100: '#D4F5E2',
          200: '#A8EBC4',
          300: '#74DBA1',
          400: '#3DC57E',
          500: '#1FA862',
          600: '#138A4E',
        },
        // Cielo — info
        sky2: {
          50:  '#EFF8FE',
          100: '#D9EEFC',
          200: '#B0DBF8',
          300: '#7DC1F1',
          400: '#4BA5E6',
          500: '#2486CC',
        },
        // Niveles de riesgo (alineado con backend)
        risk: {
          bajo:    '#3DC57E',
          medio:   '#F2A93B',
          alto:    '#F2754F',
          critico: '#E0413A',
          sin:     '#9A93A4',
        },
        // Fondos
        cream: {
          50:  '#FBF7F2',
          100: '#F5EFE6',
          200: '#ECE3D4',
        },
        // Texto / tinta cálida (no negro puro)
        ink: {
          900: '#1F1B24',
          800: '#2E2735',
          700: '#3F3A45',
          600: '#55505C',
          500: '#6B6471',
          400: '#928B98',
          300: '#B7B0BD',
          200: '#DCD7E0',
          100: '#EDEAF0',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', 'sans-serif'],
        serif: ['Fraunces', 'Georgia', 'serif'],
      },
      borderRadius: {
        'xl2': '1.25rem',
        '2xl2': '1.75rem',
      },
      boxShadow: {
        'soft':   '0 2px 8px -2px rgba(94, 63, 193, 0.08), 0 1px 3px -1px rgba(94, 63, 193, 0.06)',
        'pastel': '0 8px 24px -8px rgba(139, 108, 240, 0.18), 0 2px 6px -2px rgba(139, 108, 240, 0.10)',
        'lift':   '0 20px 50px -20px rgba(94, 63, 193, 0.30)',
      },
      backgroundImage: {
        'pastel-hero': 'radial-gradient(at 0% 0%, #EDE7FE 0%, transparent 50%), radial-gradient(at 100% 0%, #FFE9DF 0%, transparent 50%), radial-gradient(at 50% 100%, #D4F5E2 0%, transparent 55%)',
      },
    },
  },
  plugins: [],
}
