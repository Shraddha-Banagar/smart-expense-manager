/**
 * Analytics API calls, isolated from components.
 */
import api from "./api";

/**
 * @param {object} params - { range: "this_week"|"this_month"|"last_month"|
 *   "last_3_months"|"this_year"|"custom"|"all_time", date_from, date_to }
 */
export async function fetchSummary(params = {}) {
  const { data } = await api.get("/analytics/summary", { params });
  return data; // { total_expenses, this_month_total, transaction_count, average_expense, highest_transaction, month_over_month_change }
}

export async function fetchCategoryBreakdown(params = {}) {
  const { data } = await api.get("/analytics/categories", { params });
  return data; // [{ category, total, percentage, transaction_count }]
}

export async function fetchMonthlyTrend(months = 6) {
  const { data } = await api.get("/analytics/monthly", { params: { months } });
  return data; // [{ month, total }]
}
