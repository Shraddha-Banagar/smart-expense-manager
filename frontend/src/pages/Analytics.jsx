import { useCallback, useEffect, useState } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import SummaryCard from "../components/SummaryCard";
import Input from "../components/Input";
import CategoryPieChart from "../components/charts/CategoryPieChart";
import MonthlyBarChart from "../components/charts/MonthlyBarChart";
import TopCategoriesList from "../components/TopCategoriesList";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingSpinner from "../components/LoadingSpinner";
import { fetchSummary, fetchCategoryBreakdown, fetchMonthlyTrend } from "../services/analyticsService";
import { formatCurrency } from "../utils/format";
import { TIME_RANGES } from "../utils/constants";
import { getErrorMessage } from "../utils/errors";

export default function Analytics() {
  const [range, setRange] = useState("this_month");
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");

  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const isCustomIncomplete = range === "custom" && (!customFrom || !customTo);

  const loadAnalytics = useCallback(async () => {
    if (isCustomIncomplete) return;

    setIsLoading(true);
    setError(null);
    try {
      const params = { range };
      if (range === "custom") {
        params.date_from = customFrom;
        params.date_to = customTo;
      }
      const [summaryData, categoryData, monthlyData] = await Promise.all([
        fetchSummary(params),
        fetchCategoryBreakdown(params),
        fetchMonthlyTrend(6),
      ]);
      setSummary(summaryData);
      setCategories(categoryData);
      setMonthly(monthlyData);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load analytics."));
    } finally {
      setIsLoading(false);
    }
  }, [range, customFrom, customTo, isCustomIncomplete]);

  useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);

  const momChange = summary?.month_over_month_change;
  const MomIcon = momChange == null ? Minus : momChange > 0 ? TrendingUp : momChange < 0 ? TrendingDown : Minus;
  const momColor =
    momChange == null
      ? "text-gray-500 dark:text-gray-400"
      : momChange > 0
      ? "text-red-500"
      : momChange < 0
      ? "text-green-600"
      : "text-gray-500 dark:text-gray-400";

  return (
    <>
      <div className="mx-auto max-w-6xl">
        {/* Time range tabs */}
        <div className="mb-5 flex flex-wrap items-center gap-2">
          {TIME_RANGES.map((r) => (
            <button
              key={r.key}
              onClick={() => setRange(r.key)}
              aria-pressed={range === r.key}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                range === r.key
                  ? "bg-accent text-white"
                  : "bg-white text-gray-600 border border-gray-300 hover:bg-gray-50 dark:bg-gray-900 dark:text-gray-300 dark:border-gray-700 dark:hover:bg-gray-800"
              }`}
            >
              {r.label}
            </button>
          ))}

          {range === "custom" && (
            <div className="flex items-center gap-2">
              <Input
                id="date_from"
                type="date"
                aria-label="Custom range start date"
                value={customFrom}
                onChange={(e) => setCustomFrom(e.target.value)}
              />
              <span className="text-sm text-gray-500 dark:text-gray-400">to</span>
              <Input
                id="date_to"
                type="date"
                aria-label="Custom range end date"
                value={customTo}
                onChange={(e) => setCustomTo(e.target.value)}
              />
            </div>
          )}
        </div>

        {isCustomIncomplete ? (
          <EmptyState title="Select a date range" description="Pick a start and end date to view analytics for that period." />
        ) : isLoading ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={loadAnalytics} />
        ) : summary.transaction_count === 0 ? (
          <EmptyState title="No expenses in this period" description="Try a different time range, or add some expenses first." />
        ) : (
          <>
            {/* Summary metrics */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <SummaryCard label="Total Spending" value={formatCurrency(summary.total_expenses)} />
              <SummaryCard
                label="Average Transaction"
                value={formatCurrency(summary.average_expense)}
              />
              <SummaryCard label="Highest Transaction" value={formatCurrency(summary.highest_transaction)} />
              <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
                <p className="text-sm text-gray-500 dark:text-gray-400">Month-over-Month</p>
                <div className={`mt-2 flex items-center gap-1.5 text-2xl font-semibold ${momColor}`}>
                  <MomIcon size={20} />
                  {momChange == null ? "N/A" : `${Math.abs(momChange)}%`}
                </div>
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  {momChange == null ? "No data for last month" : momChange > 0 ? "Spending increased" : momChange < 0 ? "Spending decreased" : "No change"}
                </p>
              </div>
            </div>

            {/* Charts */}
            <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
                <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Category Distribution
                </h2>
                {categories.length === 0 ? (
                  <p className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">No category data for this period.</p>
                ) : (
                  <CategoryPieChart data={categories} />
                )}
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
                <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Monthly Trend (last 6 months)
                </h2>
                <MonthlyBarChart data={monthly} />
              </div>
            </div>

            {/* Category breakdown list */}
            <div className="mt-6 rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
              <h2 className="mb-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                Spending by Category
              </h2>
              <TopCategoriesList data={categories} limit={categories.length} />
            </div>
          </>
        )}
      </div>
    </>
  );
}
