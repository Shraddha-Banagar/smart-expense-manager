import { useEffect } from "react";

const APP_NAME = "Smart Expense Manager";

/** Sets document.title (announced by screen readers on navigation). */
export default function usePageTitle(title) {
  useEffect(() => {
    document.title = title ? `${title} · ${APP_NAME}` : APP_NAME;
  }, [title]);
}
