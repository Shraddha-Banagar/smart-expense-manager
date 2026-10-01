import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AuthLayout from "../layouts/AuthLayout";
import Input from "../components/Input";
import Button from "../components/Button";
import usePageTitle from "../hooks/usePageTitle";
import { getErrorMessage } from "../utils/errors";
import { focusFirstError, isValidEmail } from "../utils/validation";

export default function Register() {
  usePageTitle("Create account");
  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  function validate() {
    const errors = {};
    if (!form.name.trim()) errors.name = "Enter your name.";
    else if (form.name.trim().length > 255) errors.name = "Name must be 255 characters or fewer.";
    if (!form.email.trim()) errors.email = "Enter your email address.";
    else if (!isValidEmail(form.email)) errors.email = "Enter a valid email address, like name@example.com.";
    if (form.password.length < 8) errors.password = "Password must be at least 8 characters.";
    else if (form.password.length > 128) errors.password = "Password must be 128 characters or fewer.";
    return errors;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
      focusFirstError(errors, ["name", "email", "password"]);
      return;
    }

    setIsSubmitting(true);
    try {
      await register(form.name.trim(), form.email.trim(), form.password);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(getErrorMessage(err, "Unable to create account. Please try again."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Start tracking your expenses smarter">
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <Input
          id="name" name="name" type="text" label="Full name" autoComplete="name"
          value={form.name} onChange={handleChange} error={fieldErrors.name}
        />
        <Input
          id="email" name="email" type="email" label="Email" autoComplete="email"
          value={form.email} onChange={handleChange} error={fieldErrors.email}
        />
        <Input
          id="password" name="password" type="password" label="Password" autoComplete="new-password"
          hint="At least 8 characters." value={form.password} onChange={handleChange} error={fieldErrors.password}
        />

        {error && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <Button type="submit" disabled={isSubmitting} className="mt-2 w-full">
          {isSubmitting ? "Creating account..." : "Create account"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
        Already have an account?{" "}
        <Link to="/login" state={location.state} className="font-medium text-accent-fg hover:underline dark:text-blue-400">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
