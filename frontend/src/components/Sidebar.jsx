import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";
import { X } from "lucide-react";
import { SIDEBAR_ITEMS } from "../utils/constants";

/**
 * Desktop: fixed sidebar. Mobile: slide-over panel.
 * When the mobile panel is closed it is `invisible`, which removes it from the tab
 * order and the accessibility tree (previously its links were off-screen but still
 * keyboard-focusable). Escape closes it and returns focus to the menu button.
 */
export default function Sidebar({ isOpen, onClose }) {
  const firstLinkRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return undefined;
    firstLinkRef.current?.focus();
    function onKeyDown(e) {
      if (e.key === "Escape") {
        onClose();
        document.getElementById("menu-button")?.focus();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  return (
    <>
      {isOpen && <div className="fixed inset-0 z-30 bg-black/30 lg:hidden" onClick={onClose} aria-hidden="true" />}

      <aside
        id="sidebar"
        className={`fixed z-40 flex h-full w-64 flex-col border-r border-gray-200 bg-white transition-[transform,visibility] dark:border-gray-800 dark:bg-gray-900 lg:visible lg:static lg:translate-x-0 ${
          isOpen ? "visible translate-x-0" : "invisible -translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between px-5 py-4">
          <span className="text-base font-semibold text-gray-900 dark:text-gray-100">Expense Manager</span>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800 lg:hidden"
            aria-label="Close navigation menu"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <nav aria-label="Main" className="flex-1 space-y-1 overflow-y-auto px-3 pb-4">
          {SIDEBAR_ITEMS.map((item, index) => (
            <NavLink
              key={item.path}
              to={item.path}
              ref={index === 0 ? firstLinkRef : undefined}
              onClick={onClose}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-accent/10 text-accent-fg dark:text-blue-400"
                    : "text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
