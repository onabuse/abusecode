/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./static/js/**/*.js"],
  theme: {
    extend: {
      colors: {
        bg: "#171717",
        ink: "#141414",
        card: "#1c1c1c",
        raised: "#2f2f2f",
        line: "#252525",
        navline: "#242424",
        fg: "#ededed",
        muted: "#a9a9a9",
        dim: "#9a9a9a",
        accent: {
          DEFAULT: "#60a5fa",
          soft: "#5187c7",
          strong: "#1e6dd4",
          bg: "#1f2630",
          line: "#4a5b75",
        },
        danger: "#c96a6a",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "12px",
        ctrl: "8px",
      },
      boxShadow: {
        nav: "0 8px 24px rgba(0, 0, 0, 0.35)",
      },
    },
  },
  plugins: [],
};
