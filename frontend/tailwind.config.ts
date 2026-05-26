import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: "hsl(var(--card))",
        border: "hsl(var(--border))",
        primary: "#2563eb",
        success: "#059669",
        warning: "#d97706",
      },
      borderRadius: { lg: "8px", md: "6px", sm: "4px" },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;

