"""
Report tests: period resolution, figures, filters, comparison windows,
optional AI summary (LLM mocked), and PDF rendering (content is extracted
back out of the generated PDF and checked, not just the status code).
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_reports.db")

from datetime import date

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app
from app.services import ai_service
from app.services.report_service import resolve_period

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _token(email="reports@example.com"):
    r = client.post("/api/auth/register", json={"name": "Report User", "email": email, "password": "supersecret123"})
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


def _expense(token, amount, category="Food", d="2026-03-10", merchant="Test Merchant"):
    r = client.post("/api/expenses", json={
        "merchant": merchant, "amount": amount, "category": category,
        "expense_date": d, "payment_method": "Cash",
    }, headers=_h(token))
    assert r.status_code == 201
    return r.json()


def _pdf_text(response) -> str:
    doc = pymupdf.open(stream=response.content, filetype="pdf")
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


# --- resolve_period ---------------------------------------------------------

def test_resolve_period_month_and_year_rollover():
    start, end, label, p_start, p_end, p_label = resolve_period("2026-01")
    assert (start, end) == (date(2026, 1, 1), date(2026, 1, 31))
    assert label == "January 2026"
    assert (p_start, p_end, p_label) == (date(2025, 12, 1), date(2025, 12, 31), "December 2025")


def test_resolve_period_leap_february():
    _, end, *_ = resolve_period("2024-02")
    assert end == date(2024, 2, 29)


# --- auth -------------------------------------------------------------------

def test_reports_require_auth():
    assert client.get("/api/reports/monthly").status_code == 401
    assert client.get("/api/reports/monthly/pdf").status_code == 401


# --- report data ------------------------------------------------------------

def test_empty_period_report():
    token = _token()
    r = client.get("/api/reports/monthly?month=2026-03", headers=_h(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total_expenses"] == 0 and data["transaction_count"] == 0
    assert data["category_breakdown"] == [] and data["top_expenses"] == []
    assert data["comparison"]["change_percent"] is None
    assert "No expenses were recorded" in data["summary"]
    assert data["ai_summary_status"] == "not_requested"


def test_report_figures_breakdown_top_and_comparison():
    token = _token()
    _expense(token, 100, "Food", "2026-03-05")
    _expense(token, 50, "Food", "2026-03-06")
    _expense(token, 250, "Travel", "2026-03-07", merchant="Airline")
    _expense(token, 200, "Food", "2026-02-15")  # previous month

    data = client.get("/api/reports/monthly?month=2026-03", headers=_h(token)).json()
    assert data["period_label"] == "March 2026"
    assert data["total_expenses"] == 400.0
    assert data["transaction_count"] == 3
    assert data["average_expense"] == 133.33

    assert data["category_breakdown"][0]["category"] == "Travel"
    assert data["category_breakdown"][0]["percentage"] == 62.5

    assert [e["amount"] for e in data["top_expenses"]] == [250.0, 100.0, 50.0]
    assert data["top_expenses"][0]["merchant"] == "Airline"

    cmp = data["comparison"]
    assert cmp["previous_period_label"] == "February 2026"
    assert cmp["previous_total"] == 200.0
    assert cmp["change_amount"] == 200.0
    assert cmp["change_percent"] == 100.0
    assert "higher than February 2026" in data["summary"]


def test_month_boundaries_are_inclusive_and_exclusive_correctly():
    token = _token()
    _expense(token, 1, d="2026-02-28")   # outside (previous month)
    _expense(token, 10, d="2026-03-01")  # first day: inside
    _expense(token, 20, d="2026-03-31")  # last day: inside
    _expense(token, 4, d="2026-04-01")   # outside (next month)

    data = client.get("/api/reports/monthly?month=2026-03", headers=_h(token)).json()
    assert data["total_expenses"] == 30.0
    assert data["comparison"]["previous_total"] == 1.0


def test_category_filter_applies_to_whole_report_including_comparison():
    token = _token()
    _expense(token, 100, "Food", "2026-03-05")
    _expense(token, 50, "Food", "2026-03-06")
    _expense(token, 250, "Travel", "2026-03-07")
    _expense(token, 200, "Food", "2026-02-15")
    _expense(token, 999, "Travel", "2026-02-15")

    data = client.get("/api/reports/monthly?month=2026-03&category=Food", headers=_h(token)).json()
    assert data["category_filter"] == "Food"
    assert data["total_expenses"] == 150.0
    assert data["transaction_count"] == 2
    assert [c["category"] for c in data["category_breakdown"]] == ["Food"]
    assert all(e["category"] == "Food" for e in data["top_expenses"])
    assert data["comparison"]["previous_total"] == 200.0   # Feb Food only, not the 999 Travel
    assert data["comparison"]["change_percent"] == -25.0
    assert "in Food" in data["summary"]
    assert "largest category" not in data["summary"]  # meaningless when filtered to one category


def test_custom_range_compares_against_preceding_period_of_same_length():
    token = _token()
    _expense(token, 40, d="2026-03-05")   # inside the preceding 10-day window
    _expense(token, 60, d="2026-03-12")   # inside the report window

    data = client.get(
        "/api/reports/monthly?date_from=2026-03-10&date_to=2026-03-19", headers=_h(token)
    ).json()
    assert data["total_expenses"] == 60.0
    assert data["comparison"]["previous_period_label"] == "28 Feb 2026 – 9 Mar 2026"
    assert data["comparison"]["previous_total"] == 40.0
    assert data["comparison"]["change_percent"] == 50.0


@pytest.mark.parametrize("query", [
    "month=2026-13", "month=abc", "month=2026-3",
    "date_from=2026-03-01",                       # missing date_to
    "date_from=2026-03-20&date_to=2026-03-01",    # reversed
])
def test_invalid_params_return_400(query):
    token = _token()
    assert client.get(f"/api/reports/monthly?{query}", headers=_h(token)).status_code == 400
    assert client.get(f"/api/reports/monthly/pdf?{query}", headers=_h(token)).status_code == 400


def test_report_scoped_to_user():
    a, b = _token("ra@example.com"), _token("rb@example.com")
    _expense(a, 500, "Shopping", "2026-03-05", merchant="Only A")
    data = client.get("/api/reports/monthly?month=2026-03", headers=_h(b)).json()
    assert data["total_expenses"] == 0 and data["top_expenses"] == []


# --- AI summary -------------------------------------------------------------

def test_ai_summary_not_called_unless_requested(monkeypatch):
    token = _token()
    _expense(token, 10)

    def boom(prompt):
        raise AssertionError("LLM must not be called when ai_summary is not requested")

    monkeypatch.setattr(ai_service, "_call_llm", boom)
    data = client.get("/api/reports/monthly?month=2026-03", headers=_h(token)).json()
    assert data["ai_summary"] is None and data["ai_summary_status"] == "not_requested"


def test_ai_summary_generated_and_prompt_contains_no_merchant_names(monkeypatch):
    token = _token()
    _expense(token, 321.0, "Food", merchant="Secret Merchant Ltd")
    captured = {}

    def fake(prompt):
        captured["prompt"] = prompt
        return "  Spending was concentrated in Food.  "

    monkeypatch.setattr(ai_service, "_call_llm", fake)
    data = client.get("/api/reports/monthly?month=2026-03&ai_summary=true", headers=_h(token)).json()

    assert data["ai_summary_status"] == "generated"
    assert data["ai_summary"] == "Spending was concentrated in Food."
    assert "321" in captured["prompt"]                      # aggregates are sent...
    assert "Secret Merchant Ltd" not in captured["prompt"]  # ...merchant names are not
    assert "Test Merchant" not in captured["prompt"]


def test_ai_summary_unconfigured_degrades_without_failing(monkeypatch):
    token = _token()
    _expense(token, 10)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    r = client.get("/api/reports/monthly?month=2026-03&ai_summary=true", headers=_h(token))
    assert r.status_code == 200
    data = r.json()
    assert data["ai_summary"] is None and data["ai_summary_status"] == "unavailable"
    assert data["summary"]  # deterministic summary still present


def test_ai_summary_llm_error_degrades_without_failing(monkeypatch):
    token = _token()
    _expense(token, 10)

    def raise_error(prompt):
        raise RuntimeError("network down")

    monkeypatch.setattr(ai_service, "_call_llm", raise_error)
    r = client.get("/api/reports/monthly?month=2026-03&ai_summary=true", headers=_h(token))
    assert r.status_code == 200 and r.json()["ai_summary_status"] == "unavailable"


def test_ai_summary_skipped_for_empty_period(monkeypatch):
    token = _token()

    def boom(prompt):
        raise AssertionError("LLM must not be called with no data")

    monkeypatch.setattr(ai_service, "_call_llm", boom)
    data = client.get("/api/reports/monthly?month=2026-03&ai_summary=true", headers=_h(token)).json()
    assert data["ai_summary_status"] == "unavailable"


# --- PDF --------------------------------------------------------------------

def test_pdf_response_headers_and_content():
    token = _token()
    _expense(token, 1234.50, "Food", "2026-03-05", merchant="Blue Bottle")
    r = client.get("/api/reports/monthly/pdf?month=2026-03", headers=_h(token))

    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert 'attachment; filename="expense-report-2026-03-01_2026-03-31.pdf"' == r.headers["content-disposition"]
    assert r.content.startswith(b"%PDF")

    text = _pdf_text(r)
    assert "Expense Report" in text
    assert "March 2026" in text
    assert "₹1,234.50" in text         # rupee glyph survives (bundled font), formatting intact
    assert "Blue Bottle" in text
    assert "Category breakdown" in text and "Top expenses" in text


def test_pdf_escapes_special_characters_in_user_text():
    token = _token()
    _expense(token, 10, "Food", "2026-03-05", merchant="A&B <Co> & Sons")
    r = client.get("/api/reports/monthly/pdf?month=2026-03", headers=_h(token))
    assert r.status_code == 200
    assert "A&B <Co> & Sons" in _pdf_text(r)


def test_pdf_for_empty_period_still_renders():
    token = _token()
    r = client.get("/api/reports/monthly/pdf?month=2026-03", headers=_h(token))
    assert r.status_code == 200
    assert "No expenses were recorded" in _pdf_text(r)


def test_pdf_includes_ai_summary_when_generated(monkeypatch):
    token = _token()
    _expense(token, 10)
    monkeypatch.setattr(ai_service, "_call_llm", lambda p: "A short narrative.")
    r = client.get("/api/reports/monthly/pdf?month=2026-03&ai_summary=true", headers=_h(token))
    text = _pdf_text(r)
    assert "AI-written summary" in text and "A short narrative." in text
