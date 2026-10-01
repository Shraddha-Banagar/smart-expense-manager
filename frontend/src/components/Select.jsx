import { useId } from "react";

/**
 * Native select with label + inline error support. Pass `aria-label` when there
 * is no visible `label` (e.g. table filter bars) — a select with no accessible
 * name is a WCAG failure.
 */
export default function Select({ label, id, options, placeholder, error, className = "", ...rest }) {
  const autoId = useId();
  const selectId = id || autoId;
  const errorId = `${selectId}-error`;

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={selectId} className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      )}
      <select
        id={selectId}
        aria-invalid={error ? "true" : undefined}
        aria-describedby={error ? errorId : undefined}
        className={`rounded-md border bg-white px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-accent dark:bg-gray-800 dark:text-gray-100 ${
          error ? "border-red-500 dark:border-red-400" : "border-gray-300 dark:border-gray-700"
        } ${className}`}
        {...rest}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
      {error && (
        <p id={errorId} role="alert" className="text-xs text-red-700 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
