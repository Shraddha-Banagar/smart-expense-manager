/**
 * Expense-related API calls, isolated from components.
 */
import api from "./api";

/**
 * @param {object} params - search, category, payment_method, date_from,
 *   date_to, sort_by, sort_order, page, page_size
 */
export async function fetchExpenses(params = {}) {
  const { data } = await api.get("/expenses", { params });
  return data; // { items, total, page, page_size, total_pages }
}

export async function fetchExpense(id) {
  const { data } = await api.get(`/expenses/${id}`);
  return data;
}

export async function createExpense(expense) {
  const { data } = await api.post("/expenses", expense);
  return data;
}

export async function updateExpense(id, expense) {
  const { data } = await api.put(`/expenses/${id}`, expense);
  return data;
}

export async function deleteExpense(id) {
  await api.delete(`/expenses/${id}`);
}
