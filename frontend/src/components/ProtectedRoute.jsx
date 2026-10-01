import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import FullPageSpinner from "./FullPageSpinner";

/**
 * Wraps routes that require authentication. Remembers where the user was going
 * (location.state.from) so Login can send them back there afterwards — the
 * Login page already read this, but nothing used to set it.
 */
export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <FullPageSpinner />;
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}
