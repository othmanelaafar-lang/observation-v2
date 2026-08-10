/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        morocco: {
          red: '#C41E3A',
          'red-light': '#D4385A',
          green: '#006233',
          'green-light': '#0A8550',
          gold: '#C9A227',
          'gold-light': '#E5C158',
          cream: '#FAF7F2',
          sand: '#F5EFE6',
          dark: '#1A1A2E',
          medium: '#4A4A68',
          light: '#8B8BA7',
        }
      },
      fontFamily: {
        display: ['Outfit', 'sans-serif'],
        body: ['Nunito', 'sans-serif'],
      },
      backgroundImage: {
        'zellige': "repeating-conic-gradient(from 45deg at 50% 50%, rgba(0,98,51,0.04) 0deg 11.25deg, transparent 11.25deg 22.5deg, rgba(196,30,58,0.03) 22.5deg 33.75deg, transparent 33.75deg 45deg)",
      }
    },
  },
  plugins: [],
}