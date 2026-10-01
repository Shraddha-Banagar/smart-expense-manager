import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

function getFocusable(container) {
  return Array.from(container?.querySelectorAll(FOCUSABLE) ?? []).filter((el) => el.offsetParent !== null);
}

/**
 * Accessible modal dialog:
 *  - role="dialog" + aria-modal + aria-labelledby (title)
 *  - focus moves in on open (first field, or the first non-close control), is
 *    trapped while open, and returns to the trigger on close
 *  - Escape closes; background scroll is locked
 *  - the panel scrolls (max 90% of the viewport) so tall forms remain reachable
 *    on short/mobile screens
 */
export default function Modal({ isOpen, onClose, title, children }) {
  const panelRef = useRef(null);
  const titleId = useId();
  // Keep the latest onClose without re-running the focus effect when a parent
  // re-renders with a new inline function (which would steal focus mid-typing).
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!isOpen) return undefined;

    const previouslyFocused = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const panel = panelRef.current;
    const target =
      panel.querySelector("[data-autofocus]") ||
      getFocusable(panel).find((el) => !el.hasAttribute("data-modal-close")) ||
      panel;
    target.focus();

    function onKeyDown(e) {
      if (e.key === "Escape") {
        e.stopPropagation();
        onCloseRef.current();
        return;
      }
      if (e.key !== "Tab") return;

      const focusable = getFocusable(panel);
      if (focusable.length === 0) {
        e.preventDefault();
        return;
      }
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      if (previouslyFocused instanceof HTMLElement) previouslyFocused.focus();
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40" onClick={() => onCloseRef.current()} aria-hidden="true" />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="relative z-10 max-h-[90dvh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-6 shadow-lg focus:outline-none dark:bg-gray-900"
      >
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 id={titleId} className="text-base font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h2>
          <button
            data-modal-close
            onClick={() => onCloseRef.current()}
            className="rounded-md p-1 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            aria-label="Close dialog"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
