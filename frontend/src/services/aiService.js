/**
 * AI-related API calls, isolated from components.
 */
import api from "./api";

/**
 * Returns a best-effort structured reading of a document's OCR text.
 * This is always a suggestion — never saved automatically. The caller is
 * responsible for showing it to the user for review before creating the
 * actual expense via expenseService.createExpense.
 */
export async function extractExpenseFromDocument(documentId) {
  const { data } = await api.post("/ai/extract-expense", { document_id: documentId });
  return data; // { merchant, amount, expense_date, category, payment_method, description, confidence }
}

/**
 * Rule-based spending insights computed from the user's real data.
 */
export async function fetchInsights() {
  const { data } = await api.post("/ai/insights");
  return data; // { insights: [{ message, type }], disclaimer }
}

/**
 * Ask the expense assistant a natural-language question. `history` is a
 * list of { role: "user"|"assistant", content } from earlier in this
 * conversation — not persisted server-side, so the caller resends it.
 */
export async function askAssistant(question, history = []) {
  const { data } = await api.post("/ai/ask", { question, history });
  return data; // { answer, disclaimer }
}
