import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#0f131c",
        "surface-lowest": "#0a0e16",
        "surface-low": "#171c24",
        "surface-container": "#1b2028",
        "surface-high": "#262a33",
        "on-surface": "#dfe2ee",
        "on-surface-variant": "#b9cbbc",
        outline: "#849587",
        "outline-variant": "#3b4a3f",
        neon: "#00ff9d",
        "neon-dim": "#00e38b",
        "neon-ink": "#00391f",
        error: "#ffb4ab",
        "error-container": "#93000a",
      },
      fontFamily: {
        sans: ["Hanken Grotesk", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
