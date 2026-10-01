/**
 * Report API calls, isolated from components.
 */
import api from "./api";

/**
 * @param {object} params - { month: "YYYY-MM" } OR { date_from, date_to },
 *   plus optional { category, ai_summary }
 */
export async function fetchMonthlyReport(params) {
  const { data } = await api.get("/reports/monthly", { params });
  return data;
}

/**
 * Downloads the report as a PDF. A plain <a href> can't be used because the
 * endpoint needs the Authorization header, so we fetch the bytes with axios
 * and hand the browser a temporary object URL.
 */
export async function downloadReportPdf(params, fallbackName = "expense-report.pdf") {
  const response = await api.get("/reports/monthly/pdf", { params, responseType: "blob" });

  const disposition = response.headers["content-disposition"] || "";
  const match = /filename="?([^";]+)"?/.exec(disposition);
  const filename = match ? match[1] : fallbackName;

  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
