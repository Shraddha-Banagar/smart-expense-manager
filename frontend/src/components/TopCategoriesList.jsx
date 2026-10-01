import { colorForIndex } from "../utils/chartColors";
import { formatCurrency } from "../utils/format";

export default function TopCategoriesList({ data, limit = 5 }) {
  const top = data.slice(0, limit);

  return (
    <div className="flex flex-col gap-3">
      {top.map((item, index) => (
        <div key={item.category}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="font-medium text-gray-700 dark:text-gray-300">{item.category}</span>
            <span className="text-gray-500 dark:text-gray-400">
              {formatCurrency(item.total)} · {item.percentage}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
            <div
              className="h-full rounded-full"
              style={{ width: `${item.percentage}%`, backgroundColor: colorForIndex(index) }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
