"""
Document upload tests: file validation (type, size, empty), successful
OCR processing, listing, retrieval, deletion, and cross-user
authorization. Uses a real (small) image so OCR genuinely runs, rather
than mocking it, since correctness of the OCR pipeline itself matters.
"""
import io
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_documents.db")

import pytest
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings

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
    # Use a throwaway uploads directory per test run so files don't pile up.
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _register_and_get_token(email="docs@example.com"):
    resp = client.post(
        "/api/auth/register",
        json={"name": "Docs User", "email": email, "password": "supersecret123"},
    )
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _make_test_image_bytes(text="TEST RECEIPT $12.34"):
    img = Image.new("RGB", (300, 100), color="white")
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)
    draw.text((10, 40), text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_upload_requires_auth():
    files = {"file": ("receipt.png", _make_test_image_bytes(), "image/png")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 401


def test_upload_rejects_unsupported_file_type():
    token = _register_and_get_token()
    files = {"file": ("receipt.txt", b"not an image", "text/plain")}
    response = client.post("/api/documents/upload", files=files, headers=_auth_headers(token))
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_rejects_oversized_file():
    token = _register_and_get_token()
    from app.config import settings as cfg

    oversized = b"0" * ((cfg.MAX_UPLOAD_SIZE_MB * 1024 * 1024) + 1)
    files = {"file": ("receipt.png", oversized, "image/png")}
    response = client.post("/api/documents/upload", files=files, headers=_auth_headers(token))
    assert response.status_code == 400
    assert "too large" in response.json()["detail"]


def test_upload_rejects_empty_file():
    token = _register_and_get_token()
    files = {"file": ("receipt.png", b"", "image/png")}
    response = client.post("/api/documents/upload", files=files, headers=_auth_headers(token))
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


def test_successful_upload_runs_ocr():
    token = _register_and_get_token()
    files = {"file": ("receipt.png", _make_test_image_bytes(), "image/png")}
    response = client.post("/api/documents/upload", files=files, headers=_auth_headers(token))
    assert response.status_code == 201
    data = response.json()
    assert data["processing_status"] == "completed"
    assert data["file_type"] == "png"
    assert data["ocr_text"] is not None
    assert len(data["ocr_text"]) > 0
    assert data["filename"] == "receipt.png"
    assert data["file_url"].startswith("/uploads/")


def test_list_and_get_and_delete_document():
    token = _register_and_get_token()
    headers = _auth_headers(token)

    files = {"file": ("receipt.png", _make_test_image_bytes(), "image/png")}
    upload_resp = client.post("/api/documents/upload", files=files, headers=headers)
    document_id = upload_resp.json()["id"]

    list_resp = client.get("/api/documents", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = client.get(f"/api/documents/{document_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == document_id

    delete_resp = client.delete(f"/api/documents/{document_id}", headers=headers)
    assert delete_resp.status_code == 204

    get_after_delete = client.get(f"/api/documents/{document_id}", headers=headers)
    assert get_after_delete.status_code == 404


def test_user_cannot_access_another_users_document():
    token_a = _register_and_get_token("docsa@example.com")
    token_b = _register_and_get_token("docsb@example.com")

    files = {"file": ("receipt.png", _make_test_image_bytes(), "image/png")}
    upload_resp = client.post("/api/documents/upload", files=files, headers=_auth_headers(token_a))
    document_id = upload_resp.json()["id"]

    get_resp = client.get(f"/api/documents/{document_id}", headers=_auth_headers(token_b))
    assert get_resp.status_code == 404

    delete_resp = client.delete(f"/api/documents/{document_id}", headers=_auth_headers(token_b))
    assert delete_resp.status_code == 404

    # Still accessible to the owner.
    owner_get = client.get(f"/api/documents/{document_id}", headers=_auth_headers(token_a))
    assert owner_get.status_code == 200
