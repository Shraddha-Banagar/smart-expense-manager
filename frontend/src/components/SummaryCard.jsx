/**
 * A single dashboard summary metric card. Keeps to plain numbers and a
 * short label — no decorative gradients or icons required.
 */
export default function SummaryCard({ label, value, icon: Icon, hint }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
        {Icon && <Icon size={18} className="text-gray-500 dark:text-gray-400" aria-hidden="true" />}
      </div>
      <p className="mt-2 break-words text-2xl font-semibold text-gray-900 dark:text-gray-100">{value}</p>
      {hint && <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{hint}</p>}
    </div>
  );
}
