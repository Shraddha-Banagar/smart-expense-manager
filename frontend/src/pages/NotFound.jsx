import { Link } from "react-router-dom";
import Button from "../components/Button";
import usePageTitle from "../hooks/usePageTitle";

export default function NotFound() {
  usePageTitle("Page not found");
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center px-6 text-center">
      <p className="text-sm font-semibold text-accent-fg dark:text-blue-400">404</p>
      <h1 className="mt-2 text-2xl font-semibold text-gray-900 dark:text-gray-100">Page not found</h1>
      <p className="mt-2 max-w-sm text-sm text-gray-600 dark:text-gray-400">
        The page you&apos;re looking for doesn&apos;t exist or may have moved.
      </p>
      <Link to="/dashboard" className="mt-6">
        <Button>Go to dashboard</Button>
      </Link>
    </div>
  );
}
