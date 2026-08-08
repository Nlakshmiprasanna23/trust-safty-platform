export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: { 900: "#070b18", 800: "#0c1225", 700: "#141c33", 600: "#1c2745" },
        accent: { DEFAULT: "#ff7a1a", soft: "#ffb066", dim: "#a1470b" },
      },
      boxShadow: { glass: "0 8px 32px rgba(0,0,0,0.35)" },
      fontFamily: { sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
