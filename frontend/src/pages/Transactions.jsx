import { useCallback, useEffect, useRef, useState } from "react";
import { Plus, Pencil, Trash2, Search, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import Button from "../components/Button";
import Input from "../components/Input";
import Select from "../components/Select";
import Badge from "../components/Badge";
import Pagination from "../components/Pagination";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import LoadingSpinner from "../components/LoadingSpinner";
import ExpenseFormModal from "../components/ExpenseFormModal";
import ConfirmDialog from "../components/ConfirmDialog";
import { useToast } from "../context/ToastContext";
import { fetchExpenses, createExpense, updateExpense, deleteExpense } from "../services/expenseService";
import { CATEGORIES, PAYMENT_METHODS } from "../utils/constants";
import { formatCurrency, formatDate } from "../utils/format";
import { getErrorMessage } from "../utils/errors";
import useDebouncedValue from "../hooks/useDebouncedValue";

const PAGE_SIZE = 10;

export default function Transactions() {
  const { showToast } = useToast();

  const [data, setData] = useState({ items: [], total: 0, page: 1, total_pages: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchInput, setSearchInput] = useState("");
  const search = useDebouncedValue(searchInput, 350);
  const [category, setCategory] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("");
  const [sortBy, setSortBy] = useState("expense_date");
  const [sortOrder, setSortOrder] = useState("desc");
  const [page, setPage] = useState(1);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const deletingExpense = data.items.find((e) => e.id === deletingId);

  // Guards against an earlier, slower request overwriting a later one's result.
  const requestIdRef = useRef(0);

  const loadExpenses = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetchExpenses({
        search: search || undefined,
        category: category || undefined,
        payment_method: paymentMethod || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        page,
        page_size: PAGE_SIZE,
      });
      if (requestId === requestIdRef.current) setData(result);
    } catch (err) {
      if (requestId === requestIdRef.current) setError(getErrorMessage(err, "Failed to load transactions."));
    } finally {
      if (requestId === requestIdRef.current) setIsLoading(false);
    }
  }, [search, category, paymentMethod, sortBy, sortOrder, page]);

  useEffect(() => {
    loadExpenses();
  }, [loadExpenses]);

  useEffect(() => {
    setPage(1);
  }, [search, category, paymentMethod, sortBy, sortOrder]);

  function toggleSort(field) {
    if (sortBy === field) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  }

  async function handleFormSubmit(formValues) {
    if (editingExpense) {
      await updateExpense(editingExpense.id, formValues);
      showToast("Expense updated.");
    } else {
      await createExpense(formValues);
      showToast("Expense added.");
    }
    await loadExpenses();
  }

  async function handleDeleteConfirmed() {
    setIsDeleting(true);
    try {
      await deleteExpense(deletingId);
      showToast("Expense deleted.");
      setDeletingId(null);
      if (data.items.length === 1 && data.page > 1) setPage((p) => p - 1);
      else await loadExpenses();
    } catch (err) {
      showToast(getErrorMessage(err, "Failed to delete expense."), "error");
    } finally {
      setIsDeleting(false);
    }
  }

  function openAddModal() {
    setEditingExpense(null);
    setIsFormOpen(true);
  }

  function openEditModal(expense) {
    setEditingExpense(expense);
    setIsFormOpen(true);
  }

  // aria-sort belongs on the <th> (a cell/columnheader), not on the button inside
  // it — axe's aria-allowed-attr rule flags aria-sort on a plain button. SortHeader
  // returns just the button; callers wrap it in <th aria-sort={...}>.
  function sortState(field) {
    if (sortBy !== field) return "none";
    return sortOrder === "asc" ? "ascending" : "descending";
  }

  const SortHeader = ({ field, children, className = "" }) => {
    const active = sortBy === field;
    const Icon = active ? (sortOrder === "asc" ? ArrowUp : ArrowDown) : ArrowUpDown;
    return (
      <button
        onClick={() => toggleSort(field)}
        className={`flex items-center gap-1 text-xs font-semibold uppercase tracking-wide text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 ${className}`}
      >
        {children}
        <Icon size={12} className={active ? "text-accent-fg dark:text-blue-400" : "opacity-40"} aria-hidden="true" />
      </button>
    );
  };

  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-1 flex-col gap-3 sm:flex-row">
          <div className="relative flex-1 sm:max-w-xs">
            <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} aria-hidden="true" />
            <label htmlFor="txn-search" className="sr-only">Search transactions</label>
            <Input id="txn-search" placeholder="Search merchant or description" className="pl-9"
                   value={searchInput} onChange={(e) => setSearchInput(e.target.value)} />
          </div>
          <Select id="category-filter" aria-label="Filter by category" placeholder="All categories" options={CATEGORIES}
                  value={category} onChange={(e) => setCategory(e.target.value)} className="sm:w-44" />
          <Select id="payment-filter" aria-label="Filter by payment method" placeholder="All payment methods"
                  options={PAYMENT_METHODS} value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}
                  className="sm:w-48" />
        </div>

        <Button onClick={openAddModal} className="whitespace-nowrap">
          <Plus size={16} className="mr-1.5" aria-hidden="true" /> Add expense
        </Button>
      </div>

      <p aria-live="polite" className="sr-only">
        {isLoading ? "Loading transactions" : `${data.total} transaction${data.total === 1 ? "" : "s"} found`}
      </p>

      {isLoading && data.items.length === 0 ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={loadExpenses} />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="No transactions found"
          description="Try adjusting your filters, or add your first expense."
          action={<Button onClick={openAddModal}>Add expense</Button>}
        />
      ) : (
        <div className={`overflow-hidden rounded-lg border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900 ${isLoading ? "opacity-60" : ""}`}>
          <div className="hidden overflow-x-auto sm:block">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900/60">
                <tr>
                  <th scope="col" aria-sort={sortState("merchant")} className="px-4 py-3"><SortHeader field="merchant">Merchant</SortHeader></th>
                  <th scope="col" aria-sort={sortState("amount")} className="px-4 py-3"><SortHeader field="amount">Amount</SortHeader></th>
                  <th scope="col" className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Category</th>
                  <th scope="col" aria-sort={sortState("expense_date")} className="px-4 py-3"><SortHeader field="expense_date">Date</SortHeader></th>
                  <th scope="col" className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Payment</th>
                  <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {data.items.map((expense) => (
                  <tr key={expense.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900 dark:text-gray-100">{expense.merchant}</p>
                      {expense.description && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">{expense.description}</p>
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{formatCurrency(expense.amount)}</td>
                    <td className="px-4 py-3"><Badge>{expense.category}</Badge></td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{formatDate(expense.expense_date)}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-300">{expense.payment_method}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1">
                        <button onClick={() => openEditModal(expense)} aria-label={`Edit ${expense.merchant} expense`}
                                className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800">
                          <Pencil size={15} aria-hidden="true" />
                        </button>
                        <button onClick={() => setDeletingId(expense.id)} aria-label={`Delete ${expense.merchant} expense`}
                                className="rounded-md p-1.5 text-gray-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950">
                          <Trash2 size={15} aria-hidden="true" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ul className="divide-y divide-gray-100 sm:hidden dark:divide-gray-800">
            {data.items.map((expense) => (
              <li key={expense.id} className="px-4 py-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-gray-900 dark:text-gray-100">{expense.merchant}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {formatDate(expense.expense_date)} · {expense.payment_method}
                    </p>
                    {expense.description && (
                      <p className="mt-0.5 truncate text-xs text-gray-500 dark:text-gray-400">{expense.description}</p>
                    )}
                  </div>
                  <span className="shrink-0 font-medium text-gray-900 dark:text-gray-100">
                    {formatCurrency(expense.amount)}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between">
                  <Badge>{expense.category}</Badge>
                  <div className="flex gap-1">
                    <button onClick={() => openEditModal(expense)} aria-label={`Edit ${expense.merchant} expense`}
                            className="rounded-md p-1.5 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800">
                      <Pencil size={15} aria-hidden="true" />
                    </button>
                    <button onClick={() => setDeletingId(expense.id)} aria-label={`Delete ${expense.merchant} expense`}
                            className="rounded-md p-1.5 text-gray-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950">
                      <Trash2 size={15} aria-hidden="true" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>

          <div className="px-4 py-3">
            <Pagination page={data.page} totalPages={data.total_pages} onPageChange={setPage} />
          </div>
        </div>
      )}

      <ExpenseFormModal
        isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} onSubmit={handleFormSubmit} expense={editingExpense}
      />

      <ConfirmDialog
        isOpen={!!deletingId} onClose={() => setDeletingId(null)} onConfirm={handleDeleteConfirmed}
        isConfirming={isDeleting}
        title="Delete expense"
        message={`Are you sure you want to delete ${deletingExpense ? `"${deletingExpense.merchant}"` : "this expense"}? This action cannot be undone.`}
      />
    </div>
  );
}
