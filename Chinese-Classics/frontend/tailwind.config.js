/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#C41E3A", // Deep Red
        secondary: "#FFD700", // Gold
        background: "#2C2C2C", // Ink Black
        surface: "#F5F5DC", // Beige
      },
      fontFamily: {
        sans: ['"Noto Sans SC"', 'sans-serif'],
        serif: ['"Noto Serif SC"', 'serif'],
        mono: ['"Roboto Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}