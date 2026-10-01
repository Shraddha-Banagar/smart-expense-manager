/**
 * Authentication state: current user, login/register/logout actions,
 * and persistent session restoration on page load.
 */
import { createContext, useContext, useEffect, useState } from "react";
import { registerUser, loginUser, fetchCurrentUser } from "../services/authService";
import { safeStorage } from "../utils/storage";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // On mount, try to restore the session from a stored token.
  useEffect(() => {
    const token = safeStorage.get("access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }

    fetchCurrentUser()
      .then((currentUser) => setUser(currentUser))
      .catch(() => {
        safeStorage.remove("access_token");
        safeStorage.remove("user");
      })
      .finally(() => setIsLoading(false));
  }, []);

  async function login(email, password) {
    const data = await loginUser({ email, password });
    safeStorage.set("access_token", data.access_token);
    safeStorage.set("user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }

  async function register(name, email, password) {
    const data = await registerUser({ name, email, password });
    safeStorage.set("access_token", data.access_token);
    safeStorage.set("user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }

  function logout() {
    safeStorage.remove("access_token");
    safeStorage.remove("user");
    setUser(null);
  }

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
