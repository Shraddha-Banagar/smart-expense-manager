import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { colorForIndex } from "../../utils/chartColors";
import { formatCurrency } from "../../utils/format";
import useChartTheme from "../../hooks/useChartTheme";

export default function CategoryPieChart({ data }) {
  const theme = useChartTheme();
  const chartData = data.map((d) => ({ name: d.category, value: d.total }));

  return (
    <div>
      <div aria-hidden="true">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart accessibilityLayer={false}>
            {/* accessibilityLayer disabled: Recharts' built-in a11y layer adds
                keyboard-focusable elements to the chart, which conflicts with the
                aria-hidden wrapper above (a focusable element inside aria-hidden
                content is itself a WCAG failure). The <ul> below is our accessible
                equivalent, so the chart is purely decorative for assistive tech. */}
            <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                 innerRadius={60} outerRadius={90} paddingAngle={2} rootTabIndex={-1}>
              {/* rootTabIndex=-1: Pie sets tabIndex=0 on its root <g> by default,
                  independent of accessibilityLayer above — same aria-hidden
                  conflict, different Recharts feature causing it. */}
              {chartData.map((_, index) => (
                <Cell key={index} fill={colorForIndex(index)} stroke="none" />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => formatCurrency(value)}
              contentStyle={theme.tooltip}
              itemStyle={{ color: theme.tooltip.color }}
            />
            <Legend
              wrapperStyle={{ fontSize: 12 }}
              formatter={(value) => <span style={{ color: theme.text }}>{value}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="sr-only">
        {data.map((d) => (
          <li key={d.category}>
            {d.category}: {formatCurrency(d.total)} ({d.percentage}% of total)
          </li>
        ))}
      </ul>
    </div>
  );
}
