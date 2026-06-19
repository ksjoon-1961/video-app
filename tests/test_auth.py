import jwt as pyjwt
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

_SECRET = "test-secret-key-that-is-long-enough-for-hs256"


def _make_token(**overrides) -> str:
    payload = {
        "sub": "user-123",
        "email": "test@example.com",
        "aud": "authenticated",
        **overrides,
    }
    return pyjwt.encode(payload, _SECRET, algorithm="HS256")


def test_me_no_token():
    response = client.get("/api/me")
    assert response.status_code == 403


def test_me_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", _SECRET)
    response = client.get("/api/me", headers={"Authorization": "Bearer bad.token.value"})
    assert response.status_code == 401


def test_me_valid_token(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", _SECRET)
    token = _make_token()
    response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["id"] == "user-123"
