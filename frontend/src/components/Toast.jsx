import { useEffect } from "react";
import { CheckCircle2, XCircle, X } from "lucide-react";

/**
 * A single toast. Errors use role="alert" (announced immediately); successes use
 * role="status" (announced politely). Auto-dismisses after `duration` ms.
 */
export default function Toast({ id, message, type = "success", onDismiss, duration = 5000 }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(id), duration);
    return () => clearTimeout(timer);
  }, [id, duration, onDismiss]);

  const isSuccess = type === "success";

  return (
    <div
      role={isSuccess ? "status" : "alert"}
      className={`flex items-center gap-2 rounded-md border px-4 py-3 shadow-sm ${
        isSuccess
          ? "border-green-200 bg-green-50 text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-300"
          : "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-300"
      }`}
    >
      {isSuccess ? <CheckCircle2 size={18} aria-hidden="true" /> : <XCircle size={18} aria-hidden="true" />}
      <span className="text-sm">{message}</span>
      <button
        onClick={() => onDismiss(id)}
        className="ml-2 rounded p-0.5 opacity-70 hover:opacity-100"
        aria-label="Dismiss notification"
      >
        <X size={14} aria-hidden="true" />
      </button>
    </div>
  );
}
