import { Pencil, Trash2 } from "lucide-react";
import { formatCurrency } from "../utils/format";

const STATUS_BAR_COLOR = {
  on_track: "bg-accent",
  approaching: "bg-amber-500",
  exceeded: "bg-red-500",
};

const STATUS_TEXT_COLOR = {
  on_track: "text-gray-500 dark:text-gray-400",
  approaching: "text-amber-700 dark:text-amber-400",
  exceeded: "text-red-600 dark:text-red-400",
};

const STATUS_LABEL = {
  on_track: "On track",
  approaching: "Approaching limit",
  exceeded: "Over budget",
};

export default function BudgetCard({ budget, onEdit, onDelete, readOnly = false }) {
  const barWidth = Math.min(budget.percentage_used, 100);

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-2 flex items-start justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{budget.category}</p>
          <p className={`text-xs ${STATUS_TEXT_COLOR[budget.status]}`}>{STATUS_LABEL[budget.status]}</p>
        </div>
        {!readOnly && (
          <div className="flex gap-1">
            <button
              onClick={() => onEdit(budget)}
              className="rounded-md p-1.5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label={`Edit ${budget.category} budget`}
            >
              <Pencil size={14} aria-hidden="true" />
            </button>
            <button
              onClick={() => onDelete(budget)}
              className="rounded-md p-1.5 text-gray-500 dark:text-gray-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950"
              aria-label={`Delete ${budget.category} budget`}
            >
              <Trash2 size={14} aria-hidden="true" />
            </button>
          </div>
        )}
      </div>

      <div
        role="progressbar"
        aria-label={`${budget.category} budget used`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.min(Math.round(budget.percentage_used), 100)}
        aria-valuetext={`${budget.percentage_used}% used — ${STATUS_LABEL[budget.status]}`}
        className="mb-1.5 h-2 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800"
      >
        <div
          className={`h-full rounded-full transition-all ${STATUS_BAR_COLOR[budget.status]}`}
          style={{ width: `${barWidth}%` }}
        />
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
        <span>
          {formatCurrency(budget.spent_amount)} of {formatCurrency(budget.monthly_limit)}
        </span>
        <span>{budget.percentage_used}%</span>
      </div>
    </div>
  );
}
