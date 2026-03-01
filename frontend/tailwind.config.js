/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['../backend/templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: '#060B18',
          surface: '#0C1425',
          card: '#111C32',
          border: '#1A2744',
          accent: '#06B6D4',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
