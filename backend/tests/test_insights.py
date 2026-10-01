"""
Spending insights tests. These are deliberately rule-based (see
insights_service.py for why), so tests exercise the real computation
against real expense/budget data — no mocking needed, since there's no
LLM in this path at all.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_insights.db")

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


def _register_and_get_token(email="insights@example.com"):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Insights User", "email": email, "password": "supersecret123"},
    )
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _create_expense(token, amount, category="Food", expense_date=None):
    payload = {
        "merchant": "Test Merchant",
        "amount": amount,
        "category": category,
        "expense_date": expense_date or date.today().isoformat(),
        "payment_method": "Cash",
    }
    return client.post("/api/expenses", json=payload, headers=_auth_headers(token))


def test_insights_requires_auth():
    assert client.post("/api/ai/insights").status_code == 401


def test_insights_with_no_expenses_gives_helpful_message():
    token = _register_and_get_token()
    resp = client.post("/api/ai/insights", headers=_auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["insights"]) >= 1
    assert "haven't logged any expenses" in data["insights"][0]["message"]
    assert "informational" in data["disclaimer"].lower()


def test_insights_identify_highest_category():
    token = _register_and_get_token()
    _create_expense(token, amount=100.0, category="Food")
    _create_expense(token, amount=20.0, category="Travel")

    resp = client.post("/api/ai/insights", headers=_auth_headers(token))
    messages = [i["message"] for i in resp.json()["insights"]]
    assert any("highest spending category" in m and "Food" in m for m in messages)


def test_insights_flag_month_over_month_increase():
    token = _register_and_get_token()
    last_month = date.today().replace(day=1) - relativedelta(days=1)

    _create_expense(token, amount=100.0, expense_date=last_month.isoformat())
    _create_expense(token, amount=200.0)  # this month: +100%

    resp = client.post("/api/ai/insights", headers=_auth_headers(token))
    messages = [i["message"] for i in resp.json()["insights"]]
    assert any("spending increased" in m for m in messages)


def test_insights_flag_month_over_month_decrease():
    token = _register_and_get_token()
    last_month = date.today().replace(day=1) - relativedelta(days=1)

    _create_expense(token, amount=200.0, expense_date=last_month.isoformat())
    _create_expense(token, amount=50.0)  # this month: -75%

    resp = client.post("/api/ai/insights", headers=_auth_headers(token))
    messages = [i["message"] for i in resp.json()["insights"]]
    assert any("spending decreased" in m for m in messages)


def test_insights_flag_exceeded_budget():
    token = _register_and_get_token()
    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 50.0}, headers=_auth_headers(token))
    _create_expense(token, amount=75.0, category="Food")

    resp = client.post("/api/ai/insights", headers=_auth_headers(token))
    messages = [i["message"] for i in resp.json()["insights"]]
    assert any("more than your monthly budget on Food" in m for m in messages)
    warning_types = [i["type"] for i in resp.json()["insights"] if "monthly budget on Food" in i["message"]]
    assert warning_types == ["warning"]


def test_insights_flag_approaching_budget():
    token = _register_and_get_token()
    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 100.0}, headers=_auth_headers(token))
    _create_expense(token, amount=85.0, category="Food")

    resp = client.post("/api/ai/insights", headers=_auth_headers(token))
    messages = [i["message"] for i in resp.json()["insights"]]
    assert any("approaching your monthly budget for Food" in m for m in messages)


def test_insights_scoped_to_user():
    token_a = _register_and_get_token("insightsa@example.com")
    token_b = _register_and_get_token("insightsb@example.com")

    _create_expense(token_a, amount=500.0, category="Shopping")

    resp_b = client.post("/api/ai/insights", headers=_auth_headers(token_b))
    messages_b = [i["message"] for i in resp_b.json()["insights"]]
    assert not any("Shopping" in m for m in messages_b)
