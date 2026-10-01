/**
 * Simple, professional button. Deliberately avoids large/pill shapes
 * and decorative animation per the design guidelines.
 */
export default function Button({
  children,
  variant = "primary",
  type = "button",
  disabled = false,
  className = "",
  ...rest
}) {
  // focus-visible (not focus) so the ring appears for keyboard navigation but not
  // on mouse click, matching the global rule in index.css. ring-offset-color is set
  // explicitly for both themes — Tailwind's default offset colour is white, which
  // shows as a stray white halo around buttons on dark surfaces.
  const base =
    "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-accent focus-visible:ring-offset-white dark:focus-visible:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed";

  const variants = {
    primary: "bg-accent text-white hover:bg-accent-hover",
    secondary:
      "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700 dark:hover:bg-gray-700",
    danger: "bg-red-600 text-white hover:bg-red-700",
  };

  return (
    <button
      type={type}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}
