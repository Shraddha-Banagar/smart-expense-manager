/**
 * A restrained, professional palette for charts — muted tones rather than
 * neon/rainbow colors, per the design guidelines. Falls back to gray for
 * any category beyond this list.
 */
export const CHART_COLORS = [
  "#2563eb", // blue-600 (accent)
  "#0d9488", // teal-600
  "#d97706", // amber-600
  "#dc2626", // red-600
  "#7c3aed", // violet-600
  "#059669", // emerald-600
  "#db2777", // pink-600
  "#64748b", // slate-500
];

export function colorForIndex(index) {
  return CHART_COLORS[index % CHART_COLORS.length];
}
