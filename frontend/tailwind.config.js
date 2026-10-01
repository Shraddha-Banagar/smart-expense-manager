/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Single restrained accent color, used consistently across the app.
        accent: {
          DEFAULT: "#2563eb", // blue-600
          hover: "#1d4ed8",
          // For accent-coloured TEXT on light surfaces (blue-700: >=6:1 on white and on
          // the tinted active-nav background). The base accent (#2563eb) is fine for
          // fills and rings but only 4.5:1 or worse as text.
          fg: "#1d4ed8",
        },
      },
    },
  },
  plugins: [],
};
