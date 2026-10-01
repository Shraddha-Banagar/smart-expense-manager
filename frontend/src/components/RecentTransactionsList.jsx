import Badge from "./Badge";
import { formatCurrency, formatDate } from "../utils/format";

export default function RecentTransactionsList({ expenses }) {
  return (
    <div className="divide-y divide-gray-100 dark:divide-gray-800">
      {expenses.map((expense) => (
        <div key={expense.id} className="flex items-center justify-between py-3">
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{expense.merchant}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{formatDate(expense.expense_date)}</p>
          </div>
          <div className="flex items-center gap-3">
            <Badge>{expense.category}</Badge>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {formatCurrency(expense.amount)}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
