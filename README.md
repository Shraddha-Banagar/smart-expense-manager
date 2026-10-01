# Smart Expense Manager

An AI-powered expense management platform: upload receipts, extract expense
data with OCR + AI, track spending, and get insights — built as a full-stack
app with React, FastAPI, and PostgreSQL.

> **Status:** Phases 1–10 (project setup through reports, plus a full
> polish pass: responsive design, dark-theme consistency, accessibility,
> loading/error/empty states, form validation, and bundle size) are
> complete and tested. Broader test coverage and deployment come in the
> following phases.

## What works right now

- FastAPI backend with layered architecture (routers → services → models)
- PostgreSQL via SQLAlchemy, with all core tables modeled (`users`,
  `documents`, `expenses`, `categories`, `budgets`)
- JWT-based registration, login, and protected `/auth/me` endpoint,
  with bcrypt password hashing
- Full expense CRUD API: create, read (single + paginated list with
  search/filter/sort), update, delete — all scoped to the authenticated
  user, with tests confirming one user can never read/edit/delete another
  user's expenses
- Analytics API with time-range filtering (this week/month, last month,
  last 3 months, this year, or a custom date range): spending summary
  (total, average, highest transaction, month-over-month % change),
  category breakdown with percentages, and a monthly trend — all computed
  from real expense data, scoped per user
- Budget API: one budget per category, with spend/remaining/percentage/
  status (`on_track`/`approaching`/`exceeded`) always computed live from
  the current month's expenses rather than stored, so it's never stale
- Receipt/bill upload with real OCR: validates file type (JPG/JPEG/PNG/
  PDF) and a 10MB size limit, stores the file through a swappable storage
  layer (local disk by default, Cloudinary-ready via `STORAGE_PROVIDER`),
  and extracts text with EasyOCR — PDFs are rasterized with PyMuPDF first
  since EasyOCR only reads images. A failed extraction still keeps the
  upload and marks it `failed` rather than losing the file.
- AI-powered expense extraction: sends a document's OCR text to a
  configurable LLM provider (`LLM_PROVIDER`, Gemini by default per the
  spec, Anthropic supported as an alternate for local dev/testing) and
  parses the response into structured expense fields. The AI's category
  and payment-method picks are coerced onto the app's fixed option lists,
  amounts/dates are validated and rejected if unparsable, and a
  malformed or missing response always degrades to a clearly-marked
  zero-confidence result rather than an error — **the result is only ever
  a suggestion that pre-fills the expense form; nothing is saved to the
  database until the user reviews and submits it.**
- React + Vite + Tailwind frontend with:
  - Login/Register pages, persistent session (JWT in localStorage),
    protected routes, and a light/dark theme toggle
  - A sidebar dashboard layout (Dashboard, Transactions, Upload Receipt,
    Analytics, AI Insights, Reports, Settings) with a working mobile
    slide-over sidebar
  - A fully functional **Transactions** page: search, filter by category/
    payment method, sortable columns, pagination, add/edit via a shared
    modal form, delete with confirmation, toast notifications, loading/
    empty/error states
  - A real **Dashboard**: 4 summary cards, a category pie/donut chart, a
    monthly spending bar chart, a top-categories breakdown, a recent-
    transactions list, and a live **Budget Overview** — all backed by
    real data, with a proper empty state for brand-new accounts
  - A working **Upload Receipt** page: drag-and-drop or file picker,
    upload progress, a list of past uploads with status badges, a viewer
    for the extracted text, and a **"Create expense"** action that runs
    AI extraction and opens the expense form pre-filled with a visible
    confidence banner
  - A real **Analytics** page: time-range tabs (including a custom date
    picker), spending metrics with a month-over-month trend indicator,
    category distribution and monthly trend charts, and a full category
    breakdown list
  - A **Settings** page with full budget management: create (one per
    category), edit the limit, delete, and a live progress bar per
    budget that turns amber approaching the limit and red once exceeded
  - A real **Reports** page: monthly or custom-range filters, category
    filter, opt-in AI summary, an in-browser report view, and a PDF
    download that always matches the report currently on screen
  - A real **AI Insights** page: colour-coded insight cards (info/
    positive/warning) plus a chat interface for the Q&A assistant, with
    suggested starter questions, follow-up context, and the disclaimer
    shown alongside answers
- Spending insights (`POST /api/ai/insights`): highest category this
  month, month-over-month spending change, average-transaction change,
  and budget approaching/exceeded warnings. **These are deliberately
  rule-based, not LLM-generated** — each is an exact statement of fact
  computed from the user's own data, so there is nothing for a model to
  hallucinate, and they work even with no LLM key configured.
- Expense Q&A assistant (`POST /api/ai/ask`): open-ended natural-language
  questions answered by the configured LLM using *only* a compact JSON
  summary built from the authenticated user's own data (summary, category
  breakdowns for this month / last month / all time, 6-month trend,
  budgets). The prompt instructs the model to
  say so when the data doesn't cover a question, every answer carries an
  informational-only disclaimer appended by the server, and nothing the
  model says is ever written back to the database. See "A note on the AI
  assistant" below for what this does and doesn't guarantee.
- Reports (`GET /api/reports/monthly`, `GET /api/reports/monthly/pdf`):
  a calendar-month or custom-date-range report, optionally restricted to
  one category, with totals, category breakdown, a comparison against the
  preceding period (previous month, or the immediately preceding window of
  the same length for custom ranges), top expenses, and a summary. The
  same report can be viewed in the browser or downloaded as a PDF.
  The summary text is assembled from the computed figures (so it cannot
  state a number that isn't in the report); an *AI-written* narrative is
  an opt-in extra (`ai_summary=true`) that receives aggregate figures only
  — never merchant names or descriptions — and degrades to "unavailable"
  rather than failing the report if no provider is configured.
- **Polish pass**, verified with an automated Chromium audit (axe-core +
  screenshots) across all 11 pages, 2 viewports (390px mobile / 1280px
  desktop), and both themes — 44 page-views, zero accessibility
  violations, zero horizontal overflow, zero console errors:
  - **Routing/loading:** route-level code splitting (each page, and
    Recharts specifically, loads on demand — see "Bundle size" below),
    a shared error boundary per route so one broken page doesn't blank
    the app, a real 404 page, and a login/register guard that redirects
    already-signed-in users instead of showing the form again
  - **Accessibility:** keyboard focus trapping and return-focus in
    modals, a skip-to-content link, `aria-live` regions for search
    results and the chat assistant, correct `role="progressbar"` on
    budget bars, labelled icon-only buttons and filter selects, visible
    focus rings that appear for keyboard nav but not mouse clicks, and a
    contrast sweep (light gray text that read under 4.5:1 on white)
  - **Correctness bugs found and fixed while polishing:** a date-only
    field (like `expense_date`) was parsed as UTC and could display as
    the previous day west of UTC; Recharts' built-in accessibility layer
    added keyboard-focusable elements inside a chart we'd intentionally
    hidden from screen readers (in favor of an equivalent text list) —
    disabled per-chart since we already provide the accessible
    alternative; the "spending decreased" insight showed an upward trend
    arrow, which visually contradicted good news; delete confirmations
    could be double-submitted by clicking twice; API validation errors
    (422s) showed a generic "Invalid input." instead of which field
    was wrong
  - **Mobile:** the Transactions table becomes a card list below `sm`
    instead of a squeezed table; drag-and-drop upload no longer flickers
    when the pointer crosses a child element inside the drop zone;
    viewport units account for mobile browser chrome (`dvh` instead of
    `vh`) so nothing is clipped under address bars
  - **Bundle size:** route-level lazy loading plus splitting Recharts
    into its own chunk cut the entry bundle from ~690KB to ~73KB
    (React itself is a separate ~164KB chunk); only Dashboard/Analytics
    load the ~400KB charts chunk, and only when visited
  - **Forms:** inline, field-level validation with messages before
    submission (not just server-side rejection after), errors announced
    to assistive tech, and focus moves to the first invalid field
- Automated backend tests: 93/93 passing (6 auth, 7 expense CRUD, 13
  analytics — including time-range resolution and month-over-month math,
  7 document upload/OCR, 12 AI extraction, 9 budgets — including live
  spend computation, status thresholds, and duplicate-category rejection,
  8 insights, 8 Q&A assistant — including a test that one user's data
  never appears in another user's prompt, and one that this-month and
  all-time figures stay separate, 23 reports — including period-boundary
  and year-rollover cases, category-filtered comparisons, a check that no
  merchant name reaches the LLM prompt, and PDF tests that extract the
  generated PDF's text back out to verify content)
- Docker Compose setup for Postgres + backend

## Project structure

```
smart-expense-manager/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, error handling, lifespan
│   │   ├── config.py          # Settings loaded from environment variables
│   │   ├── database.py        # SQLAlchemy engine/session/Base
│   │   ├── dependencies.py    # get_current_user, etc.
│   │   ├── models/            # SQLAlchemy models (users, documents, expenses, categories, budgets)
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # API route definitions (auth.py, expenses.py, analytics.py,
│   │   │                       #   documents.py, ai.py, budgets.py, reports.py)
│   │   ├── services/          # Business logic (auth_service.py, expense_service.py,
│   │   │                       #   analytics_service.py, document_service.py, storage_service.py,
│   │   │                       #   ocr_service.py, ai_service.py, budget_service.py,
│   │   │                       #   insights_service.py, ask_service.py, report_service.py, report_pdf.py)
│   │   ├── assets/fonts/      # bundled DejaVu Sans (PDF needs a font with the ₹ glyph)
│   │   ├── utils/             # security.py (hashing, JWT)
│   │   ├── constants.py       # Default categories & payment methods
│   │   └── middleware/
│   ├── tests/                 # pytest suite (test_auth.py, test_expenses.py, test_analytics.py,
│   │                          #   test_documents.py, test_ai_extraction.py, test_budgets.py,
│   │                          #   test_insights.py, test_ask_assistant.py, test_reports.py)
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/              # Landing, Login, Register, Dashboard, Transactions, Upload Receipt,
│   │   │                       #   Analytics, Settings (budgets), AI Insights, Reports
│   │   ├── layouts/             # AuthLayout, DashboardLayout (sidebar + topbar)
│   │   ├── components/          # Button, Input, Select, Modal, Badge, StatusBadge, SummaryCard,
│   │   │                       #   TopCategoriesList, RecentTransactionsList, BudgetCard,
│   │   │                       #   BudgetFormModal, charts/ (Pie, Bar), Pagination, EmptyState,
│   │   │                       #   ErrorState, Toast, Sidebar, Topbar, ExpenseFormModal
│   │   │                       #   (handles manual/edit/AI-suggested), ConfirmDialog, ProtectedRoute
│   │   ├── context/              # AuthContext, ThemeContext, ToastContext
│   │   ├── services/              # api.js, authService.js, expenseService.js, analyticsService.js,
│   │   │                       #   documentService.js, aiService.js, budgetService.js, reportService.js
│   │   └── App.jsx
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
└── README.md
```

## Database schema (so far)

- **users**: id, name, email, password_hash, created_at
- **documents**: id, user_id, filename, file_url, file_type, ocr_text, processing_status, uploaded_at
- **expenses**: id, user_id, document_id, merchant, amount, category, expense_date, payment_method, description, created_at
- **categories**: id, user_id, name, created_at
- **budgets**: id, user_id, category, monthly_limit, created_at

Relationships: one user → many documents/expenses/categories/budgets; one
document → many expenses. All tables and relationships are created in
`app/main.py` on startup via `Base.metadata.create_all()` for development.
For production, use Alembic migrations instead (not yet added — planned
before deployment).

## API so far

| Method | Path              | Description                          | Auth required |
|--------|-------------------|---------------------------------------|----------------|
| POST   | `/api/auth/register` | Create a new account                | No |
| POST   | `/api/auth/login`    | Log in with email + password        | No |
| GET    | `/api/auth/me`        | Get the current authenticated user | Yes (Bearer)   |
| GET    | `/api/expenses`        | List expenses (search/filter/sort/paginate) | Yes |
| POST   | `/api/expenses`        | Create an expense                  | Yes |
| GET    | `/api/expenses/{id}`    | Get a single expense              | Yes |
| PUT    | `/api/expenses/{id}`    | Update an expense                 | Yes |
| DELETE | `/api/expenses/{id}`    | Delete an expense                 | Yes |
| GET    | `/api/analytics/summary`  | Total/average/highest/month-over-month spending (`range` param: this_week/this_month/last_month/last_3_months/this_year/custom/all_time) | Yes |
| GET    | `/api/analytics/categories` | Spending breakdown by category, with percentages (same `range` param) | Yes |
| GET    | `/api/analytics/monthly`   | Monthly totals for the last N months (`months` query param, default 6) | Yes |
| GET    | `/api/budgets`               | List budgets with live spend/remaining/status for the current month | Yes |
| POST   | `/api/budgets`               | Create a budget (one per category) | Yes |
| PUT    | `/api/budgets/{id}`           | Update a budget's monthly limit | Yes |
| DELETE | `/api/budgets/{id}`           | Delete a budget | Yes |
| POST   | `/api/documents/upload`    | Upload a receipt/bill; validates, stores, and OCRs it | Yes |
| GET    | `/api/documents`            | List the user's uploaded documents, newest first | Yes |
| GET    | `/api/documents/{id}`        | Get a single document, including its extracted OCR text | Yes |
| DELETE | `/api/documents/{id}`        | Delete a document | Yes |
| POST   | `/api/ai/extract-expense`     | Extract structured expense data from a document's OCR text (suggestion only — not saved) | Yes |
| GET    | `/api/reports/monthly`          | Report as JSON. Params: `month=YYYY-MM` (default current) *or* `date_from`+`date_to`; optional `category`, `ai_summary` | Yes |
| GET    | `/api/reports/monthly/pdf`      | The same report as a PDF download (same params) | Yes |
| POST   | `/api/ai/insights`             | Rule-based spending insights from the user's real data (no LLM needed) | Yes |
| POST   | `/api/ai/ask`                   | Ask the expense assistant a question (`question`, optional `history`); answered only from the user's own data | Yes |
| GET    | `/api/health`          | Health check                       | No |

`GET /api/expenses` accepts query params: `search`, `category`,
`payment_method`, `date_from`, `date_to`, `sort_by`
(`amount`/`expense_date`/`created_at`/`merchant`), `sort_order`
(`asc`/`desc`), `page`, `page_size`.

Interactive API docs are available at `/docs` once the backend is running
(FastAPI's built-in Swagger UI).

## Local setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then edit values, especially JWT_SECRET_KEY
```

You need a running PostgreSQL instance matching `DATABASE_URL` in `.env`.
Easiest path: use Docker Compose (see below) for just the database:

```bash
docker compose up postgres -d
```

Then run the API:

```bash
uvicorn app.main:app --reload
```

- API: http://localhost:8000
- Docs: http://localhost:8000/docs

Run the tests (uses an isolated SQLite database, no Postgres needed):

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env    # VITE_API_URL should point at the backend
npm run dev
```

- App: http://localhost:5173

### Try it end-to-end

1. Start Postgres (`docker compose up postgres -d`) and the backend (`uvicorn app.main:app --reload`).
2. Start the frontend (`npm run dev`).
3. Visit http://localhost:5173, click **Sign up**, create an account.
4. Add a few expenses on the **Transactions** page.
5. Go to **Dashboard** — summary cards, the category pie chart, the
   monthly bar chart, top categories, and recent transactions all update
   from the same data you just entered.
6. Go to **Upload Receipt**, drag in a photo of a receipt (or any JPG/
   PNG/PDF) — it uploads and runs OCR. Click the eye icon to see the raw
   extracted text, or click **Create expense** to have AI turn that text
   into a pre-filled expense form — review/correct the fields, then save.
7. Go to **Settings**, create a budget for one of your expense categories,
   then check **Dashboard** or **Settings** again — the progress bar
   updates live and turns amber/red as spending in that category
   approaches/exceeds the limit.
8. Go to **Analytics** and switch between time-range tabs (or pick a
   custom range) — the metrics, charts, and category breakdown all
   recompute for that window.
9. Go to **Reports**, pick a month (or a custom range) and optionally a
   category, click **Generate report**, then **Download PDF**.
10. Go to **AI Insights** — the insight cards appear immediately (no API
   key needed). To use the chat assistant, set `GEMINI_API_KEY` (or
   `LLM_PROVIDER=anthropic` + `ANTHROPIC_API_KEY`) and ask a question.

### A note on OCR

The first time the backend processes an upload in a given process, it
loads the EasyOCR model, which downloads ~65MB of weights on first use
and caches them under `~/.EasyOCR`. This requires outbound network access
once; after that, the model loads from the local cache. If you're
deploying somewhere with restricted egress, either allow that one-time
download or bake the `~/.EasyOCR` cache into your deployment image.

### A note on the AI assistant

The assistant only ever sees a compact JSON summary built server-side
from the authenticated user's own data — it has no database access and
no tools, and its output is never persisted. The prompt tells it to
answer only from that data and to admit when the data doesn't cover a
question. **What this does not guarantee:** a language model can still
misread or misstate the numbers it was given, or ignore its
instructions. The design bounds the damage (it can't fabricate
transactions that exist in the app, and it can't see other users' data),
but it can't make the model's prose provably correct, which is why every
answer carries an informational-only disclaimer and the exact-fact
insights are computed in plain Python instead. The summary is
aggregate-only, so questions about a specific individual transaction
("what did I buy at X on the 3rd?") will usually get "I don't have enough
data" — a deliberate trade-off to keep the context small and the
data-exposure surface minimal.

### A note on reports and PDFs

- **Font / currency:** the PDF is rendered with a bundled copy of DejaVu
  Sans (`backend/app/assets/fonts/`, redistributable under the DejaVu
  license) because reportlab's built-in fonts have no ₹ glyph. If the font
  files are ever missing it falls back to Helvetica and writes "Rs. ".
- **AI summary in the PDF:** the PDF endpoint regenerates the AI summary
  rather than reusing the one shown on screen, so its wording can differ
  (the UI says so). The figures never differ.
- **Text safety:** merchant names are XML-escaped before going into the
  PDF, so a merchant like `A&B <Co>` renders correctly instead of breaking
  the document (this is covered by a test).
- **Periods:** a monthly report covers the whole calendar month. The
  frontend offers the last six years in the month picker.

### A note on AI extraction

`LLM_PROVIDER=gemini` is the default, matching the spec's preferred
provider — you'll need a `GEMINI_API_KEY` for it to work. `anthropic` is
also supported (set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY`) as
a convenience for local development if you don't have a Gemini key handy;
switching providers is purely a config change, no code changes needed.
Either way, if the configured provider's key is missing, `/api/ai/extract-expense`
returns a clear `503` rather than a stack trace. If the model returns
something that can't be parsed as valid JSON, or leaves fields it isn't
confident about, the endpoint still returns `200` with a low/zero
confidence result — the frontend shows a warning banner in that case
rather than silently pre-filling bad data.

## Docker (backend + database only, for now)

```bash
docker compose up --build
```

This starts Postgres and the FastAPI backend. Run the frontend separately
with `npm run dev` during development (full docker-compose frontend service
will be added once the app is closer to deployment).

## Environment variables

See `backend/.env.example` and `frontend/.env.example`. Never commit real
`.env` files — only `.env.example` templates are tracked in git.

## Security notes (current phase)

- Passwords are hashed with bcrypt (via passlib), never stored in plain text.
- JWT tokens are signed with `JWT_SECRET_KEY` (change this in production —
  the default in `.env.example` is for local development only).
- `/api/auth/me` and all data endpoints require a valid Bearer token.
- CORS is restricted to `FRONTEND_URL`.
- Uploaded files are validated by type (JPG/JPEG/PNG/PDF only) and size
  (10MB max) before being stored.
- AI extraction results are never written to the database directly — they
  only pre-fill a form the user must review and explicitly submit through
  the normal expense-creation endpoint. This matters beyond UX: OCR text
  comes from a photographed document, which is attacker-influenced input,
  so the human-review step is also what stands between a maliciously
  crafted "receipt" and anything landing in the database unreviewed.

## A note on this phase's verification

Phase 10 touched the frontend only. I re-ran the backend test suite
(excluding the two OCR-dependent files, since this sandbox session didn't
have `easyocr`/`torch` installed — an intentional choice, not a
limitation of the code, since Phase 10 didn't touch OCR): 74/74 passed,
confirming no backend regressions. The frontend was audited with a real
headless Chromium browser (not just `npm run build` succeeding) — axe-core
for accessibility, full-page screenshots inspected for visual bugs, and
programmatic checks for horizontal overflow, console errors, and correct
theme application, across every page, both themes, and both a 390px and a
1280px viewport.

## What's next

Following the phased plan: broader test coverage — including the
frontend tests the spec calls for (login flow, expense creation/editing,
receipt upload, theme switching), which had none until now — in Phase 11,
and deployment to Vercel/Render/Neon in Phase 12.
