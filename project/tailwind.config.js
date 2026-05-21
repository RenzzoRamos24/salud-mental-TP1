/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Verde agua — vivo, fresco, no militar.
        green: {
          50:  '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          300: '#6EE7B7',
          400: '#34D399',
          500: '#10B981',
          600: '#059669',
          700: '#047857',
          800: '#065F46',
          900: '#064E3B',
        },
        // Aliases mantenidos por compatibilidad — todos remapeados al verde nuevo.
        brand: {
          50: '#ECFDF5', 100: '#D1FAE5', 200: '#A7F3D0', 300: '#6EE7B7',
          400: '#34D399', 500: '#10B981', 600: '#059669', 700: '#047857',
          800: '#065F46', 900: '#064E3B',
        },
        mint: {
          50: '#ECFDF5', 100: '#D1FAE5', 200: '#A7F3D0', 300: '#6EE7B7',
          400: '#34D399', 500: '#10B981', 600: '#059669',
        },
        // Peach y sky neutralizados a grises FRÍOS (no cremosos) para no
        // ensuciar el fondo blanco con un tinte amarillento.
        peach: {
          50: '#FFFFFF', 100: '#F4F5F6', 200: '#E5E7EB', 300: '#CBD0D6',
          400: '#9CA3AF', 500: '#6B7280', 600: '#4B5563',
        },
        sky2: {
          50: '#FFFFFF', 100: '#F4F5F6', 200: '#E5E7EB',
          300: '#CBD0D6', 400: '#9CA3AF', 500: '#6B7280',
        },
        // Riesgo: dejamos el rojo de crisis para SOS y emergencia.
        risk: {
          bajo:    '#10B981',
          medio:   '#F59E0B',
          alto:    '#F97316',
          critico: '#DC2626',
          sin:     '#9CA3AF',
        },
        cream: {
          50:  '#FFFFFF',
          100: '#F8F9FA',
          200: '#EEF0F2',
        },
        ink: {
          900: '#0A0A0A',
          800: '#1A1A1A',
          700: '#262626',
          600: '#3D3D3D',
          500: '#5C5C5C',
          400: '#8A8A8A',
          300: '#B4B4B4',
          200: '#D6D6D6',
          100: '#EEF0F2',
        },
      },
      fontFamily: {
        sans:    ['"Work Sans"', 'system-ui', 'sans-serif'],
        display: ['"Work Sans"', 'system-ui', 'sans-serif'],
        serif:   ['"Work Sans"', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        'xl2': '1rem',
        '2xl2': '1.25rem',
      },
      boxShadow: {
        'soft':   '0 1px 2px rgba(10, 10, 10, 0.04), 0 2px 6px rgba(10, 10, 10, 0.04)',
        'pastel': '0 2px 6px rgba(10, 10, 10, 0.05), 0 8px 24px rgba(10, 10, 10, 0.06)',
        'lift':   '0 6px 16px rgba(10, 10, 10, 0.08), 0 24px 48px rgba(10, 10, 10, 0.12)',
        'card':   '0 1px 3px rgba(10, 10, 10, 0.05), 0 4px 12px rgba(10, 10, 10, 0.05)',
        'green':  '0 6px 20px rgba(16, 185, 129, 0.30)',
      },
      backgroundImage: {
        'pastel-hero': 'none',
      },
    },
  },
  plugins: [],
}
