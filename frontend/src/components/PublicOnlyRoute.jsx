import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import FullPageSpinner from "./FullPageSpinner";

/**
 * For /login and /register: signed-in users are sent on to the app instead of
 * being shown the form again. Honors the "where they were going" target so the
 * post-login redirect isn't overridden by a hard-coded /dashboard.
 */
export default function PublicOnlyRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <FullPageSpinner />;
  if (isAuthenticated) return <Navigate to={location.state?.from?.pathname || "/dashboard"} replace />;
  return children;
}
