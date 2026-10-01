"""
Authentication tests: registration, login, duplicate-email handling,
and protected-route access.

Run with an isolated SQLite database so tests don't touch real data:
    DATABASE_URL=sqlite:///./test.db pytest
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

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

TEST_USER = {
    "name": "Test User",
    "email": "testuser@example.com",
    "password": "supersecret123",
}


def test_register_new_user():
    response = client.post("/api/auth/register", json=TEST_USER)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == TEST_USER["email"]
    assert "access_token" in data


def test_register_duplicate_email_fails():
    client.post("/api/auth/register", json=TEST_USER)
    response = client.post("/api/auth/register", json=TEST_USER)
    assert response.status_code == 400


def test_login_with_correct_credentials():
    client.post("/api/auth/register", json=TEST_USER)
    response = client.post(
        "/api/auth/login",
        json={"email": TEST_USER["email"], "password": TEST_USER["password"]},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_fails():
    client.post("/api/auth/register", json=TEST_USER)
    response = client.post(
        "/api/auth/login",
        json={"email": TEST_USER["email"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_get_me_requires_auth():
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_get_me_with_valid_token():
    register_resp = client.post("/api/auth/register", json=TEST_USER)
    token = register_resp.json()["access_token"]
    response = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == TEST_USER["email"]
