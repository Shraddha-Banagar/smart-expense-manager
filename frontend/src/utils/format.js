export function formatCurrency(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatDate(dateString) {
  // A date-only string like "2026-03-05" is parsed by `new Date()` as UTC
  // midnight, which displays as the PREVIOUS day in timezones west of UTC.
  // Parse it as a local date instead. Full timestamps are unaffected.
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(dateString);
  const d = dateOnly
    ? new Date(Number(dateOnly[1]), Number(dateOnly[2]) - 1, Number(dateOnly[3]))
    : new Date(dateString);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

/** Today's date as YYYY-MM-DD in the user's LOCAL timezone (toISOString() would give the UTC date). */
export function todayLocalISO() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
