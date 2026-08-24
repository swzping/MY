/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0F172A',
        primary: '#F59E0B',
        secondary: '#FBBF24',
        cta: '#8B5CF6',
        text: '#F8FAFC',
        'text-muted': '#94A3B8',
      },
      fontFamily: {
        'ibm-plex': ['IBM Plex Sans', 'sans-serif'],
      },
    },
  },
  plugins: [],
  darkMode: 'class',
}