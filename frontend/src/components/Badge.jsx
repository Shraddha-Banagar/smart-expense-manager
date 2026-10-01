const COLOR_MAP = {
  Food: "bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300",
  Travel: "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  Shopping: "bg-purple-50 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
  Bills: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
  Healthcare: "bg-pink-50 text-pink-700 dark:bg-pink-950 dark:text-pink-300",
  Education: "bg-teal-50 text-teal-700 dark:bg-teal-950 dark:text-teal-300",
  Entertainment: "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300",
  Other: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

export default function Badge({ children }) {
  const colorClasses = COLOR_MAP[children] || COLOR_MAP.Other;
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${colorClasses}`}>
      {children}
    </span>
  );
}
