module.exports = {
  darkMode: "class",   // 👈 ADD THIS LINE

  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}'
  ],

  theme: {
    extend: {
      colors: {
        brand: {
          500: '#10b981',
          600: '#059669',
          700: '#047857'
        }
      }
    }
  },

  plugins: []
}
