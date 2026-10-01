const STATUS_STYLES = {
  pending: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
  processing: "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  completed: "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300",
  failed: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
};

const STATUS_LABELS = {
  pending: "Pending",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
};

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || STATUS_STYLES.pending;
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}
