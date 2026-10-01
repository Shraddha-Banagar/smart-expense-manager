import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import Button from "../components/Button";
import Input from "../components/Input";
import Select from "../components/Select";
import ReportView from "../components/ReportView";
import ErrorState from "../components/ErrorState";
import LoadingSpinner from "../components/LoadingSpinner";
import { useToast } from "../context/ToastContext";
import { fetchMonthlyReport, downloadReportPdf } from "../services/reportService";
import { CATEGORIES } from "../utils/constants";
import { getErrorMessage } from "../utils/errors";

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const now = new Date();
const CURRENT_YEAR = now.getFullYear();
const YEAR_OPTIONS = Array.from({ length: 6 }, (_, i) => String(CURRENT_YEAR - i));

function toMonthParam(monthName, year) {
  return `${year}-${String(MONTH_NAMES.indexOf(monthName) + 1).padStart(2, "0")}`;
}

export default function Reports() {
  const { showToast } = useToast();

  // Filter controls (editing these does NOT re-run the report; "Generate" does,
  // so an accidental change can't trigger a paid AI call.)
  const [mode, setMode] = useState("month"); // "month" | "custom"
  const [monthName, setMonthName] = useState(MONTH_NAMES[now.getMonth()]);
  const [year, setYear] = useState(String(CURRENT_YEAR));
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [category, setCategory] = useState("");
  const [aiSummary, setAiSummary] = useState(false);

  const [report, setReport] = useState(null);
  // The exact params the displayed report was generated with. The PDF download
  // uses these, so it always matches what's on screen even if the controls above
  // have been changed since.
  const [appliedParams, setAppliedParams] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const customIncomplete = mode === "custom" && (!dateFrom || !dateTo);

  function buildParams() {
    const params = mode === "month"
      ? { month: toMonthParam(monthName, year) }
      : { date_from: dateFrom, date_to: dateTo };
    if (category) params.category = category;
    if (aiSummary) params.ai_summary = true;
    return params;
  }

  async function generate(params = buildParams()) {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchMonthlyReport(params);
      setReport(data);
      setAppliedParams(params);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to generate the report."));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    generate({ month: toMonthParam(MONTH_NAMES[now.getMonth()], String(CURRENT_YEAR)) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleDownload() {
    if (!appliedParams || !report) return;
    setIsDownloading(true);
    try {
      await downloadReportPdf(
        appliedParams,
        `expense-report-${report.period_start}_${report.period_end}.pdf`
      );
    } catch {
      showToast("Failed to download the PDF. Please try again.", "error");
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <>
      <div className="mx-auto max-w-5xl">
        {/* Filters */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-5 dark:border-gray-800 dark:bg-gray-900">
          <div className="mb-4 flex gap-2">
            {[["month", "Monthly"], ["custom", "Custom range"]].map(([key, label]) => (
              <button
                key={key}
                onClick={() => setMode(key)}
                aria-pressed={mode === key}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  mode === key
                    ? "bg-accent text-white"
                    : "border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end">
            {mode === "month" ? (
              <>
                <Select id="report-month" label="Month" options={MONTH_NAMES} value={monthName}
                        onChange={(e) => setMonthName(e.target.value)} />
                <Select id="report-year" label="Year" options={YEAR_OPTIONS} value={year}
                        onChange={(e) => setYear(e.target.value)} />
              </>
            ) : (
              <>
                <Input id="report-from" type="date" label="From" value={dateFrom}
                       onChange={(e) => setDateFrom(e.target.value)} />
                <Input id="report-to" type="date" label="To" value={dateTo}
                       onChange={(e) => setDateTo(e.target.value)} />
              </>
            )}
            <Select id="report-category" label="Category" placeholder="All categories" options={CATEGORIES}
                    value={category} onChange={(e) => setCategory(e.target.value)} />

            <Button onClick={() => generate()} disabled={isLoading || customIncomplete}>
              {isLoading ? "Generating..." : "Generate report"}
            </Button>
          </div>

          <label className="mt-4 flex items-start gap-2 text-sm text-gray-600 dark:text-gray-300">
            <input
              type="checkbox"
              checked={aiSummary}
              onChange={(e) => setAiSummary(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-accent focus:ring-accent"
            />
            <span>
              Include an AI-written summary
              <span className="block text-xs text-gray-500 dark:text-gray-400">
                Sends only aggregate totals (no merchant names) to your configured AI provider.
              </span>
            </span>
          </label>
        </div>

        {/* Report */}
        {isLoading && !report ? (
          <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => generate()} />
        ) : report ? (
          <div className={isLoading ? "opacity-60 transition-opacity" : ""}>
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{report.period_label}</h2>
                {report.category_filter && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">Category: {report.category_filter}</p>
                )}
              </div>
              <div className="flex flex-col items-end gap-1">
                <Button variant="secondary" onClick={handleDownload} disabled={isDownloading}>
                  <Download size={16} className="mr-1.5" />
                  {isDownloading ? "Preparing PDF..." : "Download PDF"}
                </Button>
                {appliedParams?.ai_summary && (
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    The PDF&apos;s AI summary is regenerated, so its wording may differ from this page.
                  </p>
                )}
              </div>
            </div>
            <ReportView report={report} />
          </div>
        ) : null}
      </div>
    </>
  );
}
