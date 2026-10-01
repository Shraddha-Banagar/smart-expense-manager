import { Link } from "react-router-dom";
import Button from "../components/Button";
import usePageTitle from "../hooks/usePageTitle";

export default function Landing() {
  usePageTitle(); // app name only, no " · Page" suffix for the homepage
  return (
    <div className="min-h-dvh bg-white dark:bg-gray-950">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Smart Expense Manager
        </span>
        <nav className="flex gap-3">
          <Link to="/login">
            <Button variant="secondary">Log in</Button>
          </Link>
          <Link to="/register">
            <Button>Sign up</Button>
          </Link>
        </nav>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-24 text-center">
        <h1 className="text-3xl font-semibold text-gray-900 dark:text-gray-100 sm:text-4xl">
          Understand your spending, automatically.
        </h1>
        <p className="mt-4 text-base text-gray-600 dark:text-gray-400">
          Upload receipts, let AI extract and categorize expenses, and get
          clear insights into where your money goes — all in one clean
          dashboard.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/register">
            <Button>Get started</Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary">I already have an account</Button>
          </Link>
        </div>
      </main>
    </div>
  );
}
