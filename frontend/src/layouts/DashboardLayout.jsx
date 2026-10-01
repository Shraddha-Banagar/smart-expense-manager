import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import ErrorBoundary from "../components/ErrorBoundary";
import LoadingSpinner from "../components/LoadingSpinner";
import usePageTitle from "../hooks/usePageTitle";
import { SIDEBAR_ITEMS } from "../utils/constants";

const TITLES = Object.fromEntries(SIDEBAR_ITEMS.map((item) => [item.path, item.label]));

/**
 * Shell for every authenticated page, used as a *layout route* (pages render
 * through <Outlet />). Because it stays mounted while you navigate, the sidebar
 * no longer re-mounts on every click, and lazily-loaded pages show their
 * spinner inside the content area instead of blanking the whole screen.
 */
export default function DashboardLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const closeSidebar = useCallback(() => setIsSidebarOpen(false), []);
  const { pathname } = useLocation();
  const mainRef = useRef(null);
  const isFirstRender = useRef(true);

  const title = TITLES[pathname] || "";
  usePageTitle(title);

  // On navigation: close the mobile menu, reset scroll, and move focus to the
  // content region so keyboard/screen-reader users start at the new page.
  useEffect(() => {
    setIsSidebarOpen(false);
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    mainRef.current?.scrollTo(0, 0);
    mainRef.current?.focus({ preventScroll: true });
  }, [pathname]);

  return (
    <div className="flex h-dvh overflow-hidden bg-gray-50 dark:bg-gray-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[60] focus:rounded-md focus:bg-white focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-accent-fg focus:shadow-lg dark:focus:bg-gray-900 dark:focus:text-blue-400"
      >
        Skip to main content
      </a>

      <Sidebar isOpen={isSidebarOpen} onClose={closeSidebar} />

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Topbar title={title} isMenuOpen={isSidebarOpen} onMenuClick={() => setIsSidebarOpen(true)} />
        <main
          id="main-content"
          ref={mainRef}
          tabIndex={-1}
          className="flex-1 overflow-y-auto p-4 focus:outline-none sm:p-6"
        >
          <ErrorBoundary key={pathname}>
            <Suspense
              fallback={
                <div className="flex justify-center py-24">
                  <LoadingSpinner size="lg" />
                </div>
              }
            >
              <Outlet />
            </Suspense>
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}
