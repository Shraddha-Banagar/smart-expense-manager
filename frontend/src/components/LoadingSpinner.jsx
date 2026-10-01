export default function LoadingSpinner({ size = "md" }) {
  const sizes = {
    sm: "h-4 w-4 border-2",
    md: "h-8 w-8 border-2",
    lg: "h-12 w-12 border-[3px]",
  };

  return (
    <div
      role="status"
      aria-label="Loading"
      className={`${sizes[size]} animate-spin rounded-full border-gray-300 border-t-accent dark:border-gray-700 dark:border-t-accent`}
    />
  );
}
