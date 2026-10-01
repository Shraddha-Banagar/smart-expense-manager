import { Info, CheckCircle2, AlertTriangle } from "lucide-react";

const STYLES = {
  info: {
    icon: Info,
    classes: "bg-blue-50 text-blue-800 border-blue-100 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-900",
  },
  positive: {
    // CheckCircle2 rather than a trend-up arrow: "positive" insights include
    // spending having DECREASED, where an upward arrow would visually
    // contradict the message it's next to.
    icon: CheckCircle2,
    classes: "bg-green-50 text-green-800 border-green-100 dark:bg-green-950 dark:text-green-300 dark:border-green-900",
  },
  warning: {
    icon: AlertTriangle,
    classes: "bg-amber-50 text-amber-800 border-amber-100 dark:bg-amber-950 dark:text-amber-300 dark:border-amber-900",
  },
};

export default function InsightCard({ message, type = "info" }) {
  const style = STYLES[type] || STYLES.info;
  const Icon = style.icon;

  return (
    <div className={`flex items-start gap-3 rounded-lg border p-4 text-sm ${style.classes}`}>
      <Icon size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}
