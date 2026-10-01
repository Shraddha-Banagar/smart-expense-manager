/**
 * Budget API calls, isolated from components.
 */
import api from "./api";

export async function fetchBudgets() {
  const { data } = await api.get("/budgets");
  return data; // [{ id, category, monthly_limit, spent_amount, remaining_amount, percentage_used, status }]
}

export async function createBudget(category, monthlyLimit) {
  const { data } = await api.post("/budgets", { category, monthly_limit: monthlyLimit });
  return data;
}

export async function updateBudget(id, monthlyLimit) {
  const { data } = await api.put(`/budgets/${id}`, { monthly_limit: monthlyLimit });
  return data;
}

export async function deleteBudget(id) {
  await api.delete(`/budgets/${id}`);
}
