import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { formatCurrency } from "../../utils/format";
import useChartTheme from "../../hooks/useChartTheme";

export default function MonthlyBarChart({ data }) {
  const theme = useChartTheme();
  const tick = { fontSize: 12, fill: theme.axis };

  return (
    <div>
      <div aria-hidden="true">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} accessibilityLayer={false}>
            {/* accessibilityLayer disabled: see CategoryPieChart.jsx for why. */}
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.grid} />
            <XAxis dataKey="month" tick={tick} axisLine={false} tickLine={false} />
            <YAxis tick={tick} axisLine={false} tickLine={false}
                   tickFormatter={(v) => (v >= 1000 ? `${v / 1000}k` : v)} />
            <Tooltip
              formatter={(value) => formatCurrency(value)}
              contentStyle={theme.tooltip}
              itemStyle={{ color: theme.tooltip.color }}
              labelStyle={{ color: theme.tooltip.color }}
              cursor={{ fill: theme.grid, opacity: 0.4 }}
            />
            <Bar dataKey="total" fill={theme.bar} radius={[4, 4, 0, 0]} maxBarSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="sr-only">
        {data.map((d) => (
          <li key={d.month}>
            {d.month}: {formatCurrency(d.total)}
          </li>
        ))}
      </ul>
    </div>
  );
}
