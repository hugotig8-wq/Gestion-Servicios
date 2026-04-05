/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./app/**/*.{js,jsx,ts,tsx,mdx}",
    "./components/**/*.{js,jsx,ts,tsx,mdx}",
    "./pages/**/*.{js,jsx,ts,tsx,mdx}",
    "./src/**/*.{js,jsx,ts,tsx,mdx}",
    "./*.{js,jsx,ts,tsx,mdx}"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
//Ahora ECM, EcmaScript Modules
//Sólo necesario para el tailwindcss.exe que es v3.1.6
//Antes module.export para CommonJs (require).
