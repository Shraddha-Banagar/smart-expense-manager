"""
Expense CRUD tests: creation, retrieval, updates, deletion, search/filter/
sort/pagination, and cross-user authorization (a user must never be able
to see or modify another user's expenses).
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_expenses.db")

import pytest
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


def _register_and_get_token(email="user@example.com"):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "supersecret123"},
    )
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


SAMPLE_EXPENSE = {
    "merchant": "Blue Bottle Coffee",
    "amount": 12.50,
    "category": "Food",
    "expense_date": "2026-09-01",
    "payment_method": "Credit Card",
    "description": "Morning coffee",
}


def test_create_expense_requires_auth():
    response = client.post("/api/expenses", json=SAMPLE_EXPENSE)
    assert response.status_code == 401


def test_create_and_get_expense():
    token = _register_and_get_token()
    create_resp = client.post("/api/expenses", json=SAMPLE_EXPENSE, headers=_auth_headers(token))
    assert create_resp.status_code == 201
    expense = create_resp.json()
    assert expense["merchant"] == SAMPLE_EXPENSE["merchant"]
    assert expense["amount"] == SAMPLE_EXPENSE["amount"]

    get_resp = client.get(f"/api/expenses/{expense['id']}", headers=_auth_headers(token))
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == expense["id"]


def test_update_expense():
    token = _register_and_get_token()
    create_resp = client.post("/api/expenses", json=SAMPLE_EXPENSE, headers=_auth_headers(token))
    expense_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/expenses/{expense_id}",
        json={"amount": 20.0, "category": "Entertainment"},
        headers=_auth_headers(token),
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["amount"] == 20.0
    assert updated["category"] == "Entertainment"
    # Untouched fields remain the same
    assert updated["merchant"] == SAMPLE_EXPENSE["merchant"]


def test_delete_expense():
    token = _register_and_get_token()
    create_resp = client.post("/api/expenses", json=SAMPLE_EXPENSE, headers=_auth_headers(token))
    expense_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/expenses/{expense_id}", headers=_auth_headers(token))
    assert delete_resp.status_code == 204

    get_resp = client.get(f"/api/expenses/{expense_id}", headers=_auth_headers(token))
    assert get_resp.status_code == 404


def test_user_cannot_access_another_users_expense():
    token_a = _register_and_get_token("usera@example.com")
    token_b = _register_and_get_token("userb@example.com")

    create_resp = client.post("/api/expenses", json=SAMPLE_EXPENSE, headers=_auth_headers(token_a))
    expense_id = create_resp.json()["id"]

    # User B tries to read, update, and delete User A's expense.
    get_resp = client.get(f"/api/expenses/{expense_id}", headers=_auth_headers(token_b))
    assert get_resp.status_code == 404

    update_resp = client.put(
        f"/api/expenses/{expense_id}", json={"amount": 1.0}, headers=_auth_headers(token_b)
    )
    assert update_resp.status_code == 404

    delete_resp = client.delete(f"/api/expenses/{expense_id}", headers=_auth_headers(token_b))
    assert delete_resp.status_code == 404

    # It's still there and unchanged for User A.
    get_resp_a = client.get(f"/api/expenses/{expense_id}", headers=_auth_headers(token_a))
    assert get_resp_a.status_code == 200
    assert get_resp_a.json()["amount"] == SAMPLE_EXPENSE["amount"]


def test_list_expenses_search_filter_sort_pagination():
    token = _register_and_get_token()
    headers = _auth_headers(token)

    expenses = [
        {**SAMPLE_EXPENSE, "merchant": "Blue Bottle Coffee", "amount": 12.5, "category": "Food", "expense_date": "2026-09-01"},
        {**SAMPLE_EXPENSE, "merchant": "Uber", "amount": 30.0, "category": "Travel", "expense_date": "2026-09-05"},
        {**SAMPLE_EXPENSE, "merchant": "Amazon", "amount": 75.0, "category": "Shopping", "expense_date": "2026-09-10"},
    ]
    for e in expenses:
        resp = client.post("/api/expenses", json=e, headers=headers)
        assert resp.status_code == 201

    # Search
    search_resp = client.get("/api/expenses?search=uber", headers=headers)
    assert search_resp.status_code == 200
    assert search_resp.json()["total"] == 1
    assert search_resp.json()["items"][0]["merchant"] == "Uber"

    # Filter by category
    filter_resp = client.get("/api/expenses?category=Food", headers=headers)
    assert filter_resp.json()["total"] == 1

    # Sort by amount ascending
    sort_resp = client.get("/api/expenses?sort_by=amount&sort_order=asc", headers=headers)
    amounts = [item["amount"] for item in sort_resp.json()["items"]]
    assert amounts == sorted(amounts)

    # Pagination
    page_resp = client.get("/api/expenses?page=1&page_size=2", headers=headers)
    data = page_resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["total_pages"] == 2


def test_invalid_expense_amount_rejected():
    token = _register_and_get_token()
    bad_expense = {**SAMPLE_EXPENSE, "amount": -5}
    resp = client.post("/api/expenses", json=bad_expense, headers=_auth_headers(token))
    assert resp.status_code == 422
