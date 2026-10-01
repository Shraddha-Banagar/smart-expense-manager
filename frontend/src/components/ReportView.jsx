import { TrendingUp, TrendingDown, Minus, Sparkles } from "lucide-react";
import SummaryCard from "./SummaryCard";
import TopCategoriesList from "./TopCategoriesList";
import Badge from "./Badge";
import { formatCurrency, formatDate } from "../utils/format";

/**
 * Renders a report returned by GET /api/reports/monthly. Purely presentational.
 */
export default function ReportView({ report }) {
  const { comparison } = report;
  const pct = comparison.change_percent;
  const ChangeIcon = pct == null || pct === 0 ? Minus : pct > 0 ? TrendingUp : TrendingDown;
  // Spending going up is shown in red, down in green (same convention as Analytics).
  const changeColor = pct == null || pct === 0 ? "text-gray-500 dark:text-gray-400" : pct > 0 ? "text-red-500" : "text-green-600";

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard label="Total Expenses" value={formatCurrency(report.total_expenses)} />
        <SummaryCard label="Transactions" value={report.transaction_count} />
        <SummaryCard label="Average Expense" value={formatCurrency(report.average_expense)} />
        <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
          <p className="text-sm text-gray-500 dark:text-gray-400">Vs {comparison.previous_period_label}</p>
          <div className={`mt-2 flex items-center gap-1.5 text-2xl font-semibold ${changeColor}`}>
            <ChangeIcon size={20} />
            {pct == null ? "N/A" : `${pct > 0 ? "+" : ""}${pct}%`}
          </div>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {pct == null ? "No spending in that period to compare" : `${formatCurrency(comparison.previous_total)} previously`}
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
        <h3 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">Summary</h3>
        <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-300">{report.summary}</p>

        {report.ai_summary && (
          <div className="mt-4 rounded-md bg-blue-50 p-3 dark:bg-blue-950">
            <h4 className="mb-1 flex items-center gap-1.5 text-xs font-semibold text-blue-800 dark:text-blue-300">
              <Sparkles size={13} /> AI-written summary
            </h4>
            <p className="text-sm leading-relaxed text-blue-900 dark:text-blue-200">{report.ai_summary}</p>
            <p className="mt-1.5 text-xs text-blue-700/70 dark:text-blue-300/70">
              Written by an AI model from the aggregate figures in this report; it may contain errors.
            </p>
          </div>
        )}
        {report.ai_summary_status === "unavailable" && (
          <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
            An AI-written summary was requested but isn&apos;t available right now (no AI provider configured, or
            there was no data to summarize).
          </p>
        )}
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
        <h3 className="mb-4 text-sm font-semibold text-gray-900 dark:text-gray-100">Category Breakdown</h3>
        {report.category_breakdown.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">No expenses in this period.</p>
        ) : (
          <TopCategoriesList data={report.category_breakdown} limit={report.category_breakdown.length} />
        )}
      </div>

      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
        <h3 className="px-5 pt-5 text-sm font-semibold text-gray-900 dark:text-gray-100">Top Expenses</h3>
        {report.top_expenses.length === 0 ? (
          <p className="px-5 py-4 text-sm text-gray-500 dark:text-gray-400">No expenses in this period.</p>
        ) : (
          <div className="mt-3 overflow-x-auto" tabIndex={0} role="region" aria-label="Top expenses table">
            <table className="w-full text-left text-sm">
              <thead className="border-y border-gray-200 bg-gray-50 text-xs uppercase tracking-wide text-gray-500 dark:border-gray-800 dark:bg-gray-900/60 dark:text-gray-400">
                <tr>
                  <th className="px-5 py-2.5 font-semibold">Date</th>
                  <th className="px-5 py-2.5 font-semibold">Merchant</th>
                  <th className="px-5 py-2.5 font-semibold">Category</th>
                  <th className="px-5 py-2.5 text-right font-semibold">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {report.top_expenses.map((e) => (
                  <tr key={e.id}>
                    <td className="px-5 py-3 text-gray-600 dark:text-gray-300">{formatDate(e.expense_date)}</td>
                    <td className="px-5 py-3 font-medium text-gray-900 dark:text-gray-100">{e.merchant}</td>
                    <td className="px-5 py-3"><Badge>{e.category}</Badge></td>
                    <td className="px-5 py-3 text-right font-medium text-gray-900 dark:text-gray-100">
                      {formatCurrency(e.amount)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <p className="text-xs text-gray-500 dark:text-gray-400">{report.disclaimer}</p>
    </div>
  );
}
