import { Inbox } from "lucide-react";

export default function EmptyState({ title = "Nothing here yet", description, action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 py-16 text-center dark:border-gray-700">
      <Inbox className="mb-3 text-gray-500 dark:text-gray-400" size={32} />
      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{title}</p>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-gray-500 dark:text-gray-400">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
