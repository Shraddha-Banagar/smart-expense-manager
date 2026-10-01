"""
AI expense extraction tests. The actual LLM call (app.services.ai_service._call_llm)
is monkeypatched throughout — this is deliberate: we don't have live Gemini/
Anthropic credentials in CI, and more importantly, what we actually need to
guarantee is that OUR parsing/validation/coercion logic is correct regardless
of what the model returns, including when it returns garbage.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ai.db")

import pytest
from PIL import Image, ImageDraw
import io

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.services import ai_service

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
def setup_and_teardown_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _register_and_get_token(email="ai@example.com"):
    resp = client.post(
        "/api/auth/register",
        json={"name": "AI User", "email": email, "password": "supersecret123"},
    )
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _make_test_image_bytes():
    img = Image.new("RGB", (300, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "COFFEE SHOP $5.50", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _upload_and_get_completed_document_id(token):
    files = {"file": ("receipt.png", _make_test_image_bytes(), "image/png")}
    resp = client.post("/api/documents/upload", files=files, headers=_auth_headers(token))
    assert resp.status_code == 201
    assert resp.json()["processing_status"] == "completed"
    return resp.json()["id"]


# --- Unit tests: parsing/validation logic in ai_service, no HTTP involved ---

def test_parse_response_coerces_valid_json():
    raw = '{"merchant": "Blue Bottle", "amount": "12.5", "expense_date": "2026-09-01", "category": "food", "payment_method": "upi", "description": "Coffee", "confidence": 0.9}'
    result = ai_service._parse_response(raw)
    assert result.merchant == "Blue Bottle"
    assert result.amount == 12.5
    assert str(result.expense_date) == "2026-09-01"
    assert result.category == "Food"  # normalized casing
    assert result.payment_method == "UPI"  # normalized casing
    assert result.confidence == 0.9


def test_parse_response_strips_markdown_fences():
    raw = '```json\n{"merchant": "Uber", "amount": 30, "expense_date": null, "category": "Travel", "payment_method": "Credit Card", "description": "", "confidence": 0.8}\n```'
    result = ai_service._parse_response(raw)
    assert result.merchant == "Uber"
    assert result.amount == 30.0


def test_unknown_category_defaults_to_other():
    raw = '{"merchant": "X", "amount": 10, "expense_date": null, "category": "Groceries", "payment_method": "Venmo", "description": "", "confidence": 0.5}'
    result = ai_service._parse_response(raw)
    assert result.category == "Other"
    assert result.payment_method == "Other"


def test_negative_and_zero_amounts_become_none():
    raw = '{"merchant": "X", "amount": -5, "expense_date": null, "category": "Other", "payment_method": "Other", "description": "", "confidence": 0.5}'
    assert ai_service._parse_response(raw).amount is None

    raw_zero = '{"merchant": "X", "amount": 0, "expense_date": null, "category": "Other", "payment_method": "Other", "description": "", "confidence": 0.5}'
    assert ai_service._parse_response(raw_zero).amount is None


def test_malformed_json_falls_back_gracefully(monkeypatch):
    monkeypatch.setattr(ai_service, "_call_llm", lambda prompt: "this is not json at all")
    result = ai_service.extract_expense("some ocr text")
    assert result.confidence == 0.0
    assert result.merchant is None


def test_empty_ocr_text_returns_zero_confidence_without_calling_llm(monkeypatch):
    called = {"value": False}

    def fake_call(prompt):
        called["value"] = True
        return "{}"

    monkeypatch.setattr(ai_service, "_call_llm", fake_call)
    result = ai_service.extract_expense("   ")
    assert result.confidence == 0.0
    assert called["value"] is False


def test_llm_exception_falls_back_gracefully(monkeypatch):
    def raise_error(prompt):
        raise RuntimeError("network error")

    monkeypatch.setattr(ai_service, "_call_llm", raise_error)
    result = ai_service.extract_expense("some ocr text")
    assert result.confidence == 0.0


# --- Endpoint tests ---

def test_extract_expense_requires_auth():
    response = client.post("/api/ai/extract-expense", json={"document_id": 1})
    assert response.status_code == 401


def test_extract_expense_404_for_missing_document():
    token = _register_and_get_token()
    response = client.post(
        "/api/ai/extract-expense", json={"document_id": 999999}, headers=_auth_headers(token)
    )
    assert response.status_code == 404


def test_extract_expense_404_for_another_users_document():
    token_a = _register_and_get_token("aiusera@example.com")
    token_b = _register_and_get_token("aiuserb@example.com")
    document_id = _upload_and_get_completed_document_id(token_a)

    response = client.post(
        "/api/ai/extract-expense", json={"document_id": document_id}, headers=_auth_headers(token_b)
    )
    assert response.status_code == 404


def test_extract_expense_success(monkeypatch):
    token = _register_and_get_token()
    document_id = _upload_and_get_completed_document_id(token)

    fake_response = '{"merchant": "Coffee Shop", "amount": 5.5, "expense_date": "2026-09-15", "category": "food", "payment_method": "cash", "description": "Coffee", "confidence": 0.85}'
    monkeypatch.setattr(ai_service, "_call_llm", lambda prompt: fake_response)

    response = client.post(
        "/api/ai/extract-expense", json={"document_id": document_id}, headers=_auth_headers(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["merchant"] == "Coffee Shop"
    assert data["amount"] == 5.5
    assert data["category"] == "Food"
    assert data["payment_method"] == "Cash"
    assert data["confidence"] == 0.85


def test_extract_expense_unconfigured_provider_returns_503(monkeypatch):
    token = _register_and_get_token()
    document_id = _upload_and_get_completed_document_id(token)

    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    response = client.post(
        "/api/ai/extract-expense", json={"document_id": document_id}, headers=_auth_headers(token)
    )
    assert response.status_code == 503
    assert "not available" in response.json()["detail"]
