import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Wallet, Calendar, Receipt, TrendingUp } from "lucide-react";
import SummaryCard from "../components/SummaryCard";
import CategoryPieChart from "../components/charts/CategoryPieChart";
import MonthlyBarChart from "../components/charts/MonthlyBarChart";
import TopCategoriesList from "../components/TopCategoriesList";
import RecentTransactionsList from "../components/RecentTransactionsList";
import BudgetCard from "../components/BudgetCard";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingSpinner from "../components/LoadingSpinner";
import Button from "../components/Button";
import { fetchSummary, fetchCategoryBreakdown, fetchMonthlyTrend } from "../services/analyticsService";
import { fetchExpenses } from "../services/expenseService";
import { fetchBudgets } from "../services/budgetService";
import { formatCurrency } from "../utils/format";
import { getErrorMessage } from "../utils/errors";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [recentExpenses, setRecentExpenses] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryData, categoryData, monthlyData, recentData, budgetData] = await Promise.all([
        fetchSummary(),
        fetchCategoryBreakdown(),
        fetchMonthlyTrend(6),
        fetchExpenses({ sort_by: "created_at", sort_order: "desc", page: 1, page_size: 5 }),
        fetchBudgets(),
      ]);
      setSummary(summaryData);
      setCategories(categoryData);
      setMonthly(monthlyData);
      setRecentExpenses(recentData.items);
      setBudgets(budgetData);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load dashboard data."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (isLoading) {
    return (
      <>
        <div className="flex justify-center py-24">
          <LoadingSpinner size="lg" />
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <ErrorState message={error} onRetry={loadDashboard} />
      </>
    );
  }

  const hasNoExpenses = summary.transaction_count === 0;

  return (
    <>
      <div className="mx-auto max-w-6xl">
        {hasNoExpenses ? (
          <EmptyState
            title="No expenses yet"
            description="Add your first expense to see your spending summary, charts, and insights here."
            action={
              <Link to="/transactions">
                <Button>Add an expense</Button>
              </Link>
            }
          />
        ) : (
          <>
            {/* Summary cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <SummaryCard
                label="Total Expenses"
                value={formatCurrency(summary.total_expenses)}
                icon={Wallet}
              />
              <SummaryCard
                label="This Month"
                value={formatCurrency(summary.this_month_total)}
                icon={Calendar}
              />
              <SummaryCard
                label="Transactions"
                value={summary.transaction_count}
                icon={Receipt}
              />
              <SummaryCard
                label="Average Expense"
                value={formatCurrency(summary.average_expense)}
                icon={TrendingUp}
              />
            </div>

            {/* Charts */}
            <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
                <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Expenses by Category
                </h2>
                {categories.length === 0 ? (
                  <p className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">No category data yet.</p>
                ) : (
                  <CategoryPieChart data={categories} />
                )}
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
                <h2 className="mb-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Monthly Spending Trend
                </h2>
                <MonthlyBarChart data={monthly} />
              </div>
            </div>

            {/* Top categories + Recent transactions */}
            <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
                <h2 className="mb-4 text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Top Spending Categories
                </h2>
                <TopCategoriesList data={categories} />
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
                <div className="mb-2 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    Recent Transactions
                  </h2>
                  <Link to="/transactions" className="text-xs font-medium text-accent-fg dark:text-blue-400 hover:underline">
                    View all
                  </Link>
                </div>
                <RecentTransactionsList expenses={recentExpenses} />
              </div>
            </div>

            {/* Budget overview */}
            <div className="mt-6 rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Budget Overview
                </h2>
                <Link to="/settings" className="text-xs font-medium text-accent-fg dark:text-blue-400 hover:underline">
                  Manage budgets
                </Link>
              </div>
              {budgets.length === 0 ? (
                <EmptyState
                  title="No budgets set"
                  description="Set a monthly budget per category in Settings to track your spending against it."
                  action={
                    <Link to="/settings">
                      <Button variant="secondary">Set up a budget</Button>
                    </Link>
                  }
                />
              ) : (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {budgets.slice(0, 6).map((budget) => (
                    <BudgetCard key={budget.id} budget={budget} readOnly />
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  );
}
