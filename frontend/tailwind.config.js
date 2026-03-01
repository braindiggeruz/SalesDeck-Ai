/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['../backend/templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#070707',
          surface: '#121212',
          card: '#16161D',
          border: '#2A2A2A',
          accent: '#C47C3C',
          'accent-light': '#E2A76F',
          'accent-dim': '#7A4D25',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
