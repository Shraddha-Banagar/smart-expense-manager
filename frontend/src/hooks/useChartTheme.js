import { useTheme } from "../context/ThemeContext";

/** Chart colours that follow the app theme (Recharts ignores Tailwind classes for most of these). */
export default function useChartTheme() {
  const { theme } = useTheme();
  const dark = theme === "dark";
  return {
    axis: dark ? "#9ca3af" : "#4b5563",
    grid: dark ? "#374151" : "#e5e7eb",
    text: dark ? "#e5e7eb" : "#1f2937",
    bar: dark ? "#3b82f6" : "#2563eb",
    tooltip: {
      backgroundColor: dark ? "#111827" : "#ffffff",
      border: `1px solid ${dark ? "#374151" : "#e5e7eb"}`,
      color: dark ? "#f3f4f6" : "#111827",
      fontSize: 13,
      borderRadius: 6,
    },
  };
}
