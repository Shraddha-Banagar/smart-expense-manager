"""
Expense Q&A assistant tests. The LLM call (ai_service._call_llm) is
monkeypatched — what we're actually verifying is that the context handed
to the model is built correctly and scoped to the right user, that
conversation history is forwarded, and that config/failure states are
handled the same way as expense extraction (503 for missing config,
graceful fallback text for other failures).
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ask.db")

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.services import ai_service, ask_service

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


def _register_and_get_token(email="ask@example.com"):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Ask User", "email": email, "password": "supersecret123"},
    )
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _create_expense(token, amount, category="Food"):
    payload = {
        "merchant": "Test Merchant",
        "amount": amount,
        "category": category,
        "expense_date": date.today().isoformat(),
        "payment_method": "Cash",
    }
    client.post("/api/expenses", json=payload, headers=_auth_headers(token))


def test_ask_requires_auth():
    resp = client.post("/api/ai/ask", json={"question": "How much did I spend?"})
    assert resp.status_code == 401


def test_ask_returns_answer_and_disclaimer(monkeypatch):
    token = _register_and_get_token()
    _create_expense(token, amount=42.0, category="Food")

    monkeypatch.setattr(ai_service, "_call_llm", lambda prompt: "You spent ₹42.00 on Food this month.")

    resp = client.post(
        "/api/ai/ask", json={"question": "How much did I spend on food?"}, headers=_auth_headers(token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "42" in data["answer"]
    assert "informational" in data["disclaimer"].lower()


def test_ask_context_only_contains_requesting_users_data(monkeypatch):
    token_a = _register_and_get_token("aska@example.com")
    token_b = _register_and_get_token("askb@example.com")
    _create_expense(token_a, amount=999.0, category="Shopping")

    captured_prompts = []

    def fake_call(prompt):
        captured_prompts.append(prompt)
        return "answer"

    monkeypatch.setattr(ai_service, "_call_llm", fake_call)

    client.post("/api/ai/ask", json={"question": "How much have I spent?"}, headers=_auth_headers(token_b))
    # The prompt built for user B must not contain user A's 999.0 Shopping expense.
    assert "999" not in captured_prompts[0]


def test_ask_forwards_conversation_history(monkeypatch):
    token = _register_and_get_token()
    captured_prompts = []

    def fake_call(prompt):
        captured_prompts.append(prompt)
        return "Following up on that..."

    monkeypatch.setattr(ai_service, "_call_llm", fake_call)

    resp = client.post(
        "/api/ai/ask",
        json={
            "question": "And last month?",
            "history": [
                {"role": "user", "content": "How much did I spend this month?"},
                {"role": "assistant", "content": "You spent ₹0.00 this month."},
            ],
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert "How much did I spend this month?" in captured_prompts[0]


def test_ask_unconfigured_provider_returns_503(monkeypatch):
    token = _register_and_get_token()
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    resp = client.post("/api/ai/ask", json={"question": "How much did I spend?"}, headers=_auth_headers(token))
    assert resp.status_code == 503


def test_ask_llm_failure_falls_back_gracefully(monkeypatch):
    token = _register_and_get_token()

    def raise_error(prompt):
        raise RuntimeError("network error")

    monkeypatch.setattr(ai_service, "_call_llm", raise_error)

    resp = client.post("/api/ai/ask", json={"question": "How much did I spend?"}, headers=_auth_headers(token))
    assert resp.status_code == 200
    assert "couldn't process" in resp.json()["answer"].lower()


def test_ask_validates_question_length():
    token = _register_and_get_token()
    resp = client.post("/api/ai/ask", json={"question": ""}, headers=_auth_headers(token))
    assert resp.status_code == 422

    resp2 = client.post("/api/ai/ask", json={"question": "x" * 501}, headers=_auth_headers(token))
    assert resp2.status_code == 422


def test_ask_context_separates_this_month_from_all_time(monkeypatch):
    from dateutil.relativedelta import relativedelta

    token = _register_and_get_token()
    last_month = (date.today().replace(day=1) - relativedelta(days=1)).isoformat()
    # Big Travel spend last month, small Food spend this month:
    client.post("/api/expenses", json={"merchant": "M", "amount": 5000.0, "category": "Travel",
        "expense_date": last_month, "payment_method": "Cash"}, headers=_auth_headers(token))
    _create_expense(token, amount=10.0, category="Food")

    context = ask_service.build_financial_context(
        next(override_get_db()), user_id=client.get("/api/auth/me", headers=_auth_headers(token)).json()["id"]
    )
    this_month = {c["category"]: c["total"] for c in context["spending_by_category_this_month"]}
    last_month_cats = {c["category"]: c["total"] for c in context["spending_by_category_last_month"]}
    assert this_month == {"Food": 10.0}
    assert last_month_cats == {"Travel": 5000.0}
