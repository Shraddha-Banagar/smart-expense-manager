/**
 * Turns an Axios error into a message that is safe and useful to show a user.
 *
 * Handles the cases the old `err.response?.data?.detail || "..."` pattern got wrong:
 *  - 422 validation errors (the API sends detail: "Invalid input." plus a per-field
 *    `errors` list; showing only "Invalid input." tells the user nothing)
 *  - no response at all (server down, offline, CORS) — previously showed a generic
 *    "failed" message that looked like a bug in the request
 *  - 5xx responses
 */
function humanizeField(loc) {
  const parts = (Array.isArray(loc) ? loc : []).filter((p) => typeof p === "string" && p !== "body" && p !== "query");
  const name = parts[parts.length - 1];
  if (!name) return "";
  const spaced = name.replace(/_/g, " ");
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

function cleanMessage(msg = "") {
  return msg.replace(/^Value error,\s*/i, "").replace(/\.$/, "");
}

export function getErrorMessage(err, fallback = "Something went wrong. Please try again.") {
  if (!err?.response) {
    if (err?.code === "ERR_NETWORK" || err?.code === "ECONNABORTED" || err?.request) {
      return "Can't reach the server. Check your connection and try again.";
    }
    return fallback;
  }

  const { status, data } = err.response;

  if (status === 422 && Array.isArray(data?.errors) && data.errors.length > 0) {
    const first = data.errors[0];
    const field = humanizeField(first.loc);
    const msg = cleanMessage(first.msg);
    return field ? `${field}: ${msg.charAt(0).toLowerCase()}${msg.slice(1)}` : msg;
  }

  if (typeof data?.detail === "string" && data.detail !== "Invalid input.") return data.detail;
  if (status >= 500) return "The server ran into a problem. Please try again in a moment.";
  return fallback;
}
