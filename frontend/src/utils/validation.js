export const isValidEmail = (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

/** Focuses the first invalid field (by id) so keyboard/screen-reader users land on the problem. */
export function focusFirstError(errors, fieldOrder) {
  const firstId = fieldOrder.find((id) => errors[id]);
  if (firstId) document.getElementById(firstId)?.focus();
}
