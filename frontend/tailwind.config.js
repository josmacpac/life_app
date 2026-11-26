/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#00C2CB',
        secondary: '#7FE0D4',
        accent: {
          yellow: '#FFE38A',
          orange: '#FF9A76',
          pink: '#FF5D8F',
        },
      },
    },
  },
  plugins: [],
}
