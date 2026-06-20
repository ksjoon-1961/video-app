from unittest.mock import MagicMock, patch

import jwt as pyjwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# 테스트용 EC P-256 키 쌍 (ES256)
_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1(), default_backend())
_PUBLIC_KEY = _PRIVATE_KEY.public_key()


def _make_token(**overrides) -> str:
    payload = {
        "sub": "user-123",
        "email": "test@example.com",
        "aud": "authenticated",
        **overrides,
    }
    return pyjwt.encode(payload, _PRIVATE_KEY, algorithm="ES256")


def _mock_jwks():
    signing_key = MagicMock()
    signing_key.key = _PUBLIC_KEY
    jwks = MagicMock()
    jwks.get_signing_key_from_jwt.return_value = signing_key
    return jwks


def test_me_no_token():
    response = client.get("/api/me")
    assert response.status_code in (401, 403)


def test_me_invalid_token():
    with patch("app.auth._client", return_value=_mock_jwks()):
        response = client.get("/api/me", headers={"Authorization": "Bearer bad.token.value"})
    assert response.status_code == 401


def test_me_valid_token():
    with patch("app.auth._client", return_value=_mock_jwks()):
        token = _make_token()
        response = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["id"] == "user-123"
