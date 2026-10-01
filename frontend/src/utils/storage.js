/**
 * localStorage that never throws. Some browsers/modes (blocked storage, certain
 * private modes, sandboxed iframes) throw a SecurityError on ANY access, which
 * would otherwise crash the whole app during the first render.
 */
export const safeStorage = {
  get(key) {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch {
      /* ignore: the app still works, the value just won't persist */
    }
  },
  remove(key) {
    try {
      window.localStorage.removeItem(key);
    } catch {
      /* ignore */
    }
  },
};
