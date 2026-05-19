/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        riesgo: {
          alto: '#ef4444',
          medio: '#f59e0b',
          bajo: '#22c55e',
        },
      },
      fontSize: {
        base: ['1rem', { lineHeight: '1.6' }],
      },
    },
  },
  plugins: [],
}
