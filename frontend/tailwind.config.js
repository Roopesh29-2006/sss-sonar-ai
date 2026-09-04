/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sonar: {
          950: '#060B18',
          900: '#0B132B',
          800: '#1C2541',
          700: '#2A365C',
          600: '#3A4B7C',
          accent: '#00F5D4',
          cyan: '#00BBF9',
          amber: '#FFB703',
          emerald: '#10B981',
          rose: '#F43F5E'
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif']
      }
    },
  },
  plugins: [],
}
