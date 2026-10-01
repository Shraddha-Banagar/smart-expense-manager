"""
Analytics tests: summary totals, category breakdown percentages, monthly
trend shape, and that analytics are scoped to the authenticated user only.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_analytics.db")

import pytest
from datetime import date
from dateutil.relativedelta import relativedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

engine = create_engine(
    os.environ["DATABASE_URL"], connect_args={"check_same_thread": False}
)
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


def _register_and_get_token(email="analytics@example.com"):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Analytics User", "email": email, "password": "supersecret123"},
    )
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _create_expense(token, **overrides):
    payload = {
        "merchant": "Test Merchant",
        "amount": 10.0,
        "category": "Food",
        "expense_date": date.today().isoformat(),
        "payment_method": "Cash",
        "description": None,
        **overrides,
    }
    return client.post("/api/expenses", json=payload, headers=_auth_headers(token))


def test_analytics_requires_auth():
    assert client.get("/api/analytics/summary").status_code == 401
    assert client.get("/api/analytics/categories").status_code == 401
    assert client.get("/api/analytics/monthly").status_code == 401


def test_summary_with_no_expenses():
    token = _register_and_get_token()
    resp = client.get("/api/analytics/summary", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_expenses"] == 0
    assert data["transaction_count"] == 0
    assert data["average_expense"] == 0
    assert data["this_month_total"] == 0


def test_summary_computes_totals_correctly():
    token = _register_and_get_token()
    _create_expense(token, amount=10.0)
    _create_expense(token, amount=20.0)
    _create_expense(token, amount=30.0)

    resp = client.get("/api/analytics/summary", headers=_auth_headers(token))
    data = resp.json()
    assert data["total_expenses"] == 60.0
    assert data["transaction_count"] == 3
    assert data["average_expense"] == 20.0
    # All created "today" so this-month total should equal total.
    assert data["this_month_total"] == 60.0


def test_category_breakdown_percentages():
    token = _register_and_get_token()
    _create_expense(token, amount=75.0, category="Food")
    _create_expense(token, amount=25.0, category="Travel")

    resp = client.get("/api/analytics/categories", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    by_category = {item["category"]: item for item in data}
    assert by_category["Food"]["total"] == 75.0
    assert by_category["Food"]["percentage"] == 75.0
    assert by_category["Travel"]["percentage"] == 25.0


def test_monthly_trend_includes_current_month_and_is_ordered():
    token = _register_and_get_token()
    _create_expense(token, amount=50.0)

    resp = client.get("/api/analytics/monthly?months=6", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6
    # Last entry should be the current month and should include our expense.
    assert data[-1]["total"] == 50.0


def test_analytics_scoped_to_user():
    token_a = _register_and_get_token("usera2@example.com")
    token_b = _register_and_get_token("userb2@example.com")

    _create_expense(token_a, amount=100.0)

    resp_b = client.get("/api/analytics/summary", headers=_auth_headers(token_b))
    assert resp_b.json()["total_expenses"] == 0

    resp_a = client.get("/api/analytics/summary", headers=_auth_headers(token_a))
    assert resp_a.json()["total_expenses"] == 100.0


def test_summary_includes_highest_transaction():
    token = _register_and_get_token()
    _create_expense(token, amount=10.0)
    _create_expense(token, amount=99.99)
    _create_expense(token, amount=45.0)

    resp = client.get("/api/analytics/summary", headers=_auth_headers(token))
    assert resp.json()["highest_transaction"] == 99.99


def test_month_over_month_change_is_none_without_prior_month_data():
    token = _register_and_get_token()
    _create_expense(token, amount=50.0)  # today, no prior-month expenses

    resp = client.get("/api/analytics/summary", headers=_auth_headers(token))
    assert resp.json()["month_over_month_change"] is None


def test_month_over_month_change_computed_correctly():
    token = _register_and_get_token()
    last_month = date.today().replace(day=1) - relativedelta(days=1)

    _create_expense(token, amount=100.0, expense_date=last_month.isoformat())
    _create_expense(token, amount=150.0)  # this month

    resp = client.get("/api/analytics/summary", headers=_auth_headers(token))
    data = resp.json()
    # (150 - 100) / 100 * 100 = 50%
    assert data["month_over_month_change"] == 50.0


def test_analytics_invalid_range_returns_400():
    token = _register_and_get_token()
    resp = client.get("/api/analytics/summary?range=not_a_real_range", headers=_auth_headers(token))
    assert resp.status_code == 400


def test_analytics_custom_range_requires_dates():
    token = _register_and_get_token()
    resp = client.get("/api/analytics/summary?range=custom", headers=_auth_headers(token))
    assert resp.status_code == 400


def test_analytics_this_month_range_filters_correctly():
    token = _register_and_get_token()
    last_month = date.today().replace(day=1) - relativedelta(days=1)

    _create_expense(token, amount=200.0, expense_date=last_month.isoformat())
    _create_expense(token, amount=75.0)  # this month

    resp = client.get("/api/analytics/summary?range=this_month", headers=_auth_headers(token))
    assert resp.json()["total_expenses"] == 75.0

    resp_all = client.get("/api/analytics/summary?range=all_time", headers=_auth_headers(token))
    assert resp_all.json()["total_expenses"] == 275.0


def test_analytics_custom_range_filters_correctly():
    token = _register_and_get_token()
    _create_expense(token, amount=10.0, expense_date="2026-01-15")
    _create_expense(token, amount=20.0, expense_date="2026-02-15")
    _create_expense(token, amount=30.0, expense_date="2026-03-15")

    resp = client.get(
        "/api/analytics/summary?range=custom&date_from=2026-01-01&date_to=2026-02-28",
        headers=_auth_headers(token),
    )
    assert resp.json()["total_expenses"] == 30.0
