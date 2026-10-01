import { Menu, Moon, Sun, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

export default function Topbar({ title, onMenuClick, isMenuOpen }) {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const nextTheme = theme === "light" ? "dark" : "light";

  return (
    <header className="flex items-center justify-between gap-2 border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-900 sm:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          id="menu-button"
          onClick={onMenuClick}
          className="rounded-md p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800 lg:hidden"
          aria-label="Open navigation menu"
          aria-expanded={isMenuOpen}
          aria-controls="sidebar"
        >
          <Menu size={20} aria-hidden="true" />
        </button>
        <h1 className="truncate text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h1>
      </div>

      <div className="flex shrink-0 items-center gap-1">
        <button
          onClick={toggleTheme}
          className="rounded-md p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          aria-label={`Switch to ${nextTheme} theme`}
          title={`Switch to ${nextTheme} theme`}
        >
          {theme === "light" ? <Moon size={18} aria-hidden="true" /> : <Sun size={18} aria-hidden="true" />}
        </button>

        <span className="mx-1 hidden max-w-[10rem] truncate text-sm font-medium text-gray-900 dark:text-gray-100 sm:block">
          {user?.name}
        </span>

        <button
          onClick={logout}
          className="rounded-md p-2 text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          aria-label="Log out"
          title="Log out"
        >
          <LogOut size={18} aria-hidden="true" />
        </button>
      </div>
    </header>
  );
}
