import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AuthLayout from "../layouts/AuthLayout";
import Input from "../components/Input";
import Button from "../components/Button";
import usePageTitle from "../hooks/usePageTitle";
import { getErrorMessage } from "../utils/errors";
import { focusFirstError, isValidEmail } from "../utils/validation";

export default function Login() {
  usePageTitle("Log in");
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] = useState({ email: "", password: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const redirectTo = location.state?.from?.pathname || "/dashboard";

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  function validate() {
    const errors = {};
    if (!form.email.trim()) errors.email = "Enter your email address.";
    else if (!isValidEmail(form.email)) errors.email = "Enter a valid email address, like name@example.com.";
    if (!form.password) errors.password = "Enter your password.";
    return errors;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      focusFirstError(errors, ["email", "password"]);
      return;
    }

    setIsSubmitting(true);
    try {
      await login(form.email.trim(), form.password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, "Unable to log in. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to your expense manager account">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <Input
          id="email" name="email" type="email" label="Email" autoComplete="email"
          value={form.email} onChange={handleChange} error={fieldErrors.email}
        />
        <Input
          id="password" name="password" type="password" label="Password" autoComplete="current-password"
          value={form.password} onChange={handleChange} error={fieldErrors.password}
        />

        {error && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <Button type="submit" disabled={isSubmitting} className="mt-2 w-full">
          {isSubmitting ? "Logging in..." : "Log in"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        Don&apos;t have an account?{" "}
        <Link to="/register" state={location.state} className="font-medium text-accent-fg hover:underline dark:text-blue-400">
          Sign up
        </Link>
      </p>
    </AuthLayout>
  );
}
