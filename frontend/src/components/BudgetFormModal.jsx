import { useEffect, useState } from "react";
import Modal from "./Modal";
import Input from "./Input";
import Select from "./Select";
import Button from "./Button";
import { CATEGORIES } from "../utils/constants";
import { getErrorMessage } from "../utils/errors";
import { focusFirstError } from "../utils/validation";

/**
 * Shared modal for creating and editing a budget. Category is fixed once
 * created (one budget per category — see backend), so it's disabled when editing.
 */
export default function BudgetFormModal({ isOpen, onClose, onSubmit, budget, existingCategories }) {
  const [category, setCategory] = useState("");
  const [monthlyLimit, setMonthlyLimit] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isEditing = !!budget;
  const availableCategories = CATEGORIES.filter(
    (c) => !existingCategories?.includes(c) || c === budget?.category
  );

  useEffect(() => {
    if (budget) {
      setCategory(budget.category);
      setMonthlyLimit(String(budget.monthly_limit));
    } else {
      setCategory("");
      setMonthlyLimit("");
    }
    setFieldErrors({});
    setError("");
  }, [budget, isOpen]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const errors = {};
    const limitNum = parseFloat(monthlyLimit);
    if (!category) errors["budget-category"] = "Choose a category.";
    if (monthlyLimit === "" || isNaN(limitNum)) errors["monthly-limit"] = "Enter the monthly limit.";
    else if (limitNum <= 0) errors["monthly-limit"] = "Limit must be greater than 0.";
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      focusFirstError(errors, ["budget-category", "monthly-limit"]);
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({ category, monthlyLimit: limitNum });
      onClose();
    } catch (err) {
      setError(getErrorMessage(err, "Unable to save budget. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? "Edit budget" : "Create budget"}>
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <Select
          id="budget-category" label="Category" placeholder="Select category" options={availableCategories}
          value={category} disabled={isEditing} error={fieldErrors["budget-category"]}
          onChange={(e) => { setCategory(e.target.value); setFieldErrors((p) => ({ ...p, "budget-category": undefined })); }}
        />
        <Input
          id="monthly-limit" type="number" step="0.01" min="0.01" inputMode="decimal" label="Monthly limit"
          value={monthlyLimit} error={fieldErrors["monthly-limit"]}
          onChange={(e) => { setMonthlyLimit(e.target.value); setFieldErrors((p) => ({ ...p, "monthly-limit": undefined })); }}
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
            {isSubmitting ? "Saving..." : isEditing ? "Save changes" : "Create budget"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
