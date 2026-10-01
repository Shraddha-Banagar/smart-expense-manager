"""
Budget tests: CRUD, duplicate-category rejection, live spend computation
against the current month's expenses, status thresholds (on_track/
approaching/exceeded), and cross-user authorization.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_budgets.db")

import pytest
from datetime import date
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


def _register_and_get_token(email="budget@example.com"):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Budget User", "email": email, "password": "supersecret123"},
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


def test_budgets_require_auth():
    assert client.get("/api/budgets").status_code == 401
    assert client.post("/api/budgets", json={"category": "Food", "monthly_limit": 100}).status_code == 401


def test_create_and_list_budget():
    token = _register_and_get_token()
    resp = client.post(
        "/api/budgets", json={"category": "Food", "monthly_limit": 200.0}, headers=_auth_headers(token)
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["category"] == "Food"
    assert data["monthly_limit"] == 200.0
    assert data["spent_amount"] == 0.0
    assert data["status"] == "on_track"

    list_resp = client.get("/api/budgets", headers=_auth_headers(token))
    assert len(list_resp.json()) == 1


def test_duplicate_category_budget_rejected():
    token = _register_and_get_token()
    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 200.0}, headers=_auth_headers(token))
    resp = client.post(
        "/api/budgets", json={"category": "Food", "monthly_limit": 300.0}, headers=_auth_headers(token)
    )
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"]


def test_budget_spend_computed_from_current_month_expenses():
    token = _register_and_get_token()
    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 100.0}, headers=_auth_headers(token))

    _create_expense(token, amount=40.0, category="Food")

    resp = client.get("/api/budgets", headers=_auth_headers(token))
    budget = resp.json()[0]
    assert budget["spent_amount"] == 40.0
    assert budget["remaining_amount"] == 60.0
    assert budget["percentage_used"] == 40.0
    assert budget["status"] == "on_track"


def test_budget_ignores_other_categories_and_other_months():
    token = _register_and_get_token()
    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 100.0}, headers=_auth_headers(token))

    _create_expense(token, amount=999.0, category="Travel")  # different category, should not count
    _create_expense(token, amount=999.0, category="Food", expense_date="2020-01-01")  # old month

    resp = client.get("/api/budgets", headers=_auth_headers(token))
    assert resp.json()[0]["spent_amount"] == 0.0


def test_budget_status_approaching_and_exceeded():
    token = _register_and_get_token()
    client.post("/api/budgets", json={"category": "Food", "monthly_limit": 100.0}, headers=_auth_headers(token))

    _create_expense(token, amount=85.0, category="Food")
    resp = client.get("/api/budgets", headers=_auth_headers(token))
    assert resp.json()[0]["status"] == "approaching"

    _create_expense(token, amount=20.0, category="Food")  # total 105, over budget
    resp = client.get("/api/budgets", headers=_auth_headers(token))
    budget = resp.json()[0]
    assert budget["status"] == "exceeded"
    assert budget["remaining_amount"] < 0


def test_update_budget_limit():
    token = _register_and_get_token()
    create_resp = client.post(
        "/api/budgets", json={"category": "Food", "monthly_limit": 100.0}, headers=_auth_headers(token)
    )
    budget_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/budgets/{budget_id}", json={"monthly_limit": 250.0}, headers=_auth_headers(token)
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["monthly_limit"] == 250.0


def test_delete_budget():
    token = _register_and_get_token()
    create_resp = client.post(
        "/api/budgets", json={"category": "Food", "monthly_limit": 100.0}, headers=_auth_headers(token)
    )
    budget_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/budgets/{budget_id}", headers=_auth_headers(token))
    assert delete_resp.status_code == 204

    list_resp = client.get("/api/budgets", headers=_auth_headers(token))
    assert len(list_resp.json()) == 0


def test_user_cannot_access_another_users_budget():
    token_a = _register_and_get_token("budgeta@example.com")
    token_b = _register_and_get_token("budgetb@example.com")

    create_resp = client.post(
        "/api/budgets", json={"category": "Food", "monthly_limit": 100.0}, headers=_auth_headers(token_a)
    )
    budget_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/budgets/{budget_id}", json={"monthly_limit": 1.0}, headers=_auth_headers(token_b)
    )
    assert update_resp.status_code == 404

    delete_resp = client.delete(f"/api/budgets/{budget_id}", headers=_auth_headers(token_b))
    assert delete_resp.status_code == 404

    # Budget A's data is untouched.
    list_resp = client.get("/api/budgets", headers=_auth_headers(token_a))
    assert list_resp.json()[0]["monthly_limit"] == 100.0
