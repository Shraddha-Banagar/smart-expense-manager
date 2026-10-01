import { Component } from "react";
import { AlertTriangle } from "lucide-react";

/**
 * Catches render-time errors so one broken component shows a recoverable message
 * instead of blanking the whole app. Used per-route (keyed by pathname in
 * DashboardLayout, so navigating away resets it) and once around the whole app.
 */
export default class ErrorBoundary extends Component {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error("Unhandled UI error:", error, info?.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div role="alert" className="mx-auto mt-16 flex max-w-md flex-col items-center rounded-lg border border-red-200 bg-red-50 p-8 text-center dark:border-red-900 dark:bg-red-950">
        <AlertTriangle className="mb-3 text-red-500" size={28} aria-hidden="true" />
        <h2 className="text-base font-semibold text-red-800 dark:text-red-200">Something went wrong</h2>
        <p className="mt-1 text-sm text-red-700 dark:text-red-300">
          This page hit an unexpected error. Your data is safe — try again, or reload the page.
        </p>
        <div className="mt-4 flex gap-2">
          <button
            onClick={() => this.setState({ hasError: false })}
            className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 dark:border-red-800 dark:bg-transparent dark:text-red-200"
          >
            Try again
          </button>
          <button
            onClick={() => window.location.reload()}
            className="rounded-md bg-red-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-red-700"
          >
            Reload page
          </button>
        </div>
      </div>
    );
  }
}
