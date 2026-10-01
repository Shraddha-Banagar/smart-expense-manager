import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import Button from "../components/Button";
import BudgetCard from "../components/BudgetCard";
import BudgetFormModal from "../components/BudgetFormModal";
import ConfirmDialog from "../components/ConfirmDialog";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingSpinner from "../components/LoadingSpinner";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { fetchBudgets, createBudget, updateBudget, deleteBudget } from "../services/budgetService";
import { CATEGORIES } from "../utils/constants";
import { getErrorMessage } from "../utils/errors";

export default function Settings() {
  const { user } = useAuth();
  const { showToast } = useToast();

  const [budgets, setBudgets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [deletingBudget, setDeletingBudget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadBudgets = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchBudgets();
      setBudgets(data);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to load budgets."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBudgets();
  }, [loadBudgets]);

  async function handleFormSubmit({ category, monthlyLimit }) {
    if (editingBudget) {
      await updateBudget(editingBudget.id, monthlyLimit);
      showToast("Budget updated.");
    } else {
      await createBudget(category, monthlyLimit);
      showToast("Budget created.");
    }
    await loadBudgets();
  }

  async function handleDeleteConfirmed() {
    setIsDeleting(true);
    try {
      await deleteBudget(deletingBudget.id);
      showToast("Budget deleted.");
      setDeletingBudget(null);
      await loadBudgets();
    } catch (err) {
      // Deliberately leave the dialog open on failure so the user can see the
      // error and retry, rather than silently closing and losing their place.
      showToast(getErrorMessage(err, "Failed to delete budget."), "error");
    } finally {
      setIsDeleting(false);
    }
  }

  function openAddModal() {
    setEditingBudget(null);
    setIsFormOpen(true);
  }

  function openEditModal(budget) {
    setEditingBudget(budget);
    setIsFormOpen(true);
  }

  const hasAllCategoriesBudgeted = budgets.length >= CATEGORIES.length;

  return (
    <>
      <div className="mx-auto max-w-4xl">
        {/* Profile */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
          <h2 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">Profile</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">Name</p>
          <p className="mb-2 text-sm text-gray-900 dark:text-gray-100">{user?.name}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
          <p className="text-sm text-gray-900 dark:text-gray-100">{user?.email}</p>
        </div>

        {/* Budgets */}
        <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Monthly Budgets
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                One budget per category. Spending is tracked against the current calendar month.
              </p>
            </div>
            <Button
              onClick={openAddModal}
              disabled={hasAllCategoriesBudgeted}
              title={hasAllCategoriesBudgeted ? "Every category already has a budget" : undefined}
            >
              <Plus size={16} className="mr-1.5" aria-hidden="true" /> Add budget
            </Button>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-10">
              <LoadingSpinner />
            </div>
          ) : error ? (
            <ErrorState message={error} onRetry={loadBudgets} />
          ) : budgets.length === 0 ? (
            <EmptyState
              title="No budgets set"
              description="Create a monthly budget for a category to track your spending against it."
              action={<Button onClick={openAddModal}>Add budget</Button>}
            />
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {budgets.map((budget) => (
                <BudgetCard
                  key={budget.id}
                  budget={budget}
                  onEdit={openEditModal}
                  onDelete={setDeletingBudget}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <BudgetFormModal
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
        budget={editingBudget}
        existingCategories={budgets.map((b) => b.category)}
      />

      <ConfirmDialog
        isOpen={!!deletingBudget}
        onClose={() => setDeletingBudget(null)}
        onConfirm={handleDeleteConfirmed}
        isConfirming={isDeleting}
        title="Delete budget"
        message={`Are you sure you want to delete the budget for "${deletingBudget?.category}"? This action cannot be undone.`}
      />
    </>
  );
}
