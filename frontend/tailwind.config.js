/** @type {import('tailwindcss').Config} */

// Los colores son variables CSS (src/index.css) con valores para el modo claro
// y el oscuro; así cada clase sirve en ambos modos y admite opacidad (bg-marca/10).
const token = (nombre) => `rgb(var(--${nombre}) / <alpha-value>)`

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  // El modo oscuro lo activa la clase "dark" en <html> (ver context/TemaContext.tsx).
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Figtree', 'system-ui', 'sans-serif'],
      },
      colors: {
        fondo: token('fondo'),
        superficie: {
          DEFAULT: token('superficie'),
          2: token('superficie-2'),
        },
        texto: {
          DEFAULT: token('texto'),
          2: token('texto-2'),
          3: token('texto-3'),
        },
        borde: {
          DEFAULT: token('borde'),
          fuerte: token('borde-fuerte'),
        },
        marca: {
          DEFAULT: token('marca'),
          hover: token('marca-hover'),
          texto: token('marca-texto'),
          suave: token('marca-suave'),
          'suave-texto': token('marca-suave-texto'),
          borde: token('marca-borde'),
        },
        riesgo: {
          alto: token('riesgo-alto'),
          medio: token('riesgo-medio'),
          bajo: token('riesgo-bajo'),
          'alto-solido': token('riesgo-alto-solido'),
          'medio-solido': token('riesgo-medio-solido'),
          'bajo-solido': token('riesgo-bajo-solido'),
        },
        juri: {
          fondo: token('juri-fondo'),
          texto: token('juri-texto'),
        },
      },
      fontSize: {
        base: ['1rem', { lineHeight: '1.6' }],
      },
    },
  },
  plugins: [],
}
