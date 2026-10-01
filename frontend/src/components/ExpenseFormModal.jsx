import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import Modal from "./Modal";
import Input from "./Input";
import Select from "./Select";
import Button from "./Button";
import { CATEGORIES, PAYMENT_METHODS } from "../utils/constants";
import { getErrorMessage } from "../utils/errors";
import { focusFirstError } from "../utils/validation";
import { todayLocalISO } from "../utils/format";

const FIELD_ORDER = ["merchant", "amount", "expense_date", "category", "payment_method", "description"];

const emptyForm = () => ({
  merchant: "",
  amount: "",
  category: "",
  expense_date: todayLocalISO(),
  payment_method: "",
  description: "",
});

/**
 * Shared modal for creating and editing an expense.
 *
 * - Pass `expense` to edit an existing one.
 * - Pass `aiSuggestion` (+ optional `documentId`) to pre-fill from an AI
 *   extraction result — the user still must review and submit; nothing
 *   from `aiSuggestion` is ever saved without going through this form.
 * - Pass neither for a blank manual-entry form.
 */
export default function ExpenseFormModal({ isOpen, onClose, onSubmit, expense, aiSuggestion, documentId }) {
  const [form, setForm] = useState(emptyForm);
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = !!expense;

  useEffect(() => {
    if (expense) {
      setForm({
        merchant: expense.merchant,
        amount: String(expense.amount),
        category: expense.category,
        expense_date: expense.expense_date,
        payment_method: expense.payment_method,
        description: expense.description || "",
      });
    } else if (aiSuggestion) {
      setForm({
        merchant: aiSuggestion.merchant || "",
        amount: aiSuggestion.amount != null ? String(aiSuggestion.amount) : "",
        category: aiSuggestion.category || "",
        expense_date: aiSuggestion.expense_date || "",
        payment_method: aiSuggestion.payment_method || "",
        description: aiSuggestion.description || "",
      });
    } else {
      setForm(emptyForm());
    }
    setFieldErrors({});
    setError("");
  }, [expense, aiSuggestion, isOpen]);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  function validate() {
    const errors = {};
    const amountNum = parseFloat(form.amount);
    if (!form.merchant.trim()) errors.merchant = "Enter the merchant name.";
    else if (form.merchant.trim().length > 255) errors.merchant = "Merchant must be 255 characters or fewer.";
    if (form.amount === "" || isNaN(amountNum)) errors.amount = "Enter the amount.";
    else if (amountNum <= 0) errors.amount = "Amount must be greater than 0.";
    if (!form.expense_date) errors.expense_date = "Choose the date.";
    if (!form.category) errors.category = "Choose a category.";
    if (!form.payment_method) errors.payment_method = "Choose a payment method.";
    if (form.description.length > 2000) errors.description = "Description must be 2000 characters or fewer.";
    return errors;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      focusFirstError(errors, FIELD_ORDER);
      return;
    }

    setIsSubmitting(true);
    try {
      const payload = {
        ...form,
        merchant: form.merchant.trim(),
        description: form.description.trim(),
        amount: parseFloat(form.amount),
      };
      if (!isEditing && documentId) payload.document_id = documentId;
      await onSubmit(payload);
      onClose();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to save expense. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  const showLowConfidenceWarning = aiSuggestion && aiSuggestion.confidence < 0.5;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isEditing ? "Edit expense" : aiSuggestion ? "Review AI-extracted expense" : "Add expense"}
    >
      {aiSuggestion && (
        <div
          className={`mb-4 flex items-start gap-2 rounded-md px-3 py-2 text-sm ${
            showLowConfidenceWarning
              ? "bg-amber-50 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
              : "bg-blue-50 text-blue-800 dark:bg-blue-950 dark:text-blue-300"
          }`}
        >
          <Sparkles size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
          <span>
            {showLowConfidenceWarning
              ? "The AI wasn't very confident reading this receipt — please double-check every field before saving."
              : "Pre-filled from the receipt using AI. Please review before saving — nothing is saved automatically."}
          </span>
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <Input
          id="merchant" name="merchant" label="Merchant" autoComplete="off"
          value={form.merchant} onChange={handleChange} error={fieldErrors.merchant}
        />

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Input
            id="amount" name="amount" type="number" step="0.01" min="0.01" inputMode="decimal" label="Amount"
            value={form.amount} onChange={handleChange} error={fieldErrors.amount}
          />
          <Input
            id="expense_date" name="expense_date" type="date" label="Date"
            value={form.expense_date} onChange={handleChange} error={fieldErrors.expense_date}
          />
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Select
            id="category" name="category" label="Category" placeholder="Select category" options={CATEGORIES}
            value={form.category} onChange={handleChange} error={fieldErrors.category}
          />
          <Select
            id="payment_method" name="payment_method" label="Payment method" placeholder="Select method"
            options={PAYMENT_METHODS} value={form.payment_method} onChange={handleChange}
            error={fieldErrors.payment_method}
          />
        </div>

        <Input
          id="description" name="description" label="Description (optional)"
          value={form.description} onChange={handleChange} error={fieldErrors.description}
        />

        {error && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : isEditing ? "Save changes" : "Add expense"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
