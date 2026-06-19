from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1(), default_backend())
_PUBLIC_KEY  = _PRIVATE_KEY.public_key()

_MOCK_VIDEOS = [
    {"id": "00000000-0000-0000-0000-000000000001", "name": "샘플 영상 1", "storage_path": "videos/sample1.mp4", "sort_order": 1},
    {"id": "00000000-0000-0000-0000-000000000002", "name": "샘플 영상 2", "storage_path": "videos/sample2.mp4", "sort_order": 2},
]


def _make_token(**overrides) -> str:
    payload = {"sub": "user-123", "email": "test@example.com", "aud": "authenticated", **overrides}
    return pyjwt.encode(payload, _PRIVATE_KEY, algorithm="ES256")


def _mock_jwks():
    signing_key = MagicMock()
    signing_key.key = _PUBLIC_KEY
    jwks = MagicMock()
    jwks.get_signing_key_from_jwt.return_value = signing_key
    return jwks


def test_videos_no_token():
    response = client.get("/api/videos")
    assert response.status_code == 403


def test_videos_invalid_token():
    with patch("app.auth._client", return_value=_mock_jwks()):
        response = client.get("/api/videos", headers={"Authorization": "Bearer bad.token.value"})
    assert response.status_code == 401


def test_videos_returns_list():
    with patch("app.auth._client", return_value=_mock_jwks()), \
         patch("app.services.catalog.get_videos", new_callable=AsyncMock, return_value=_MOCK_VIDEOS):
        token = _make_token()
        response = client.get("/api/videos", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "샘플 영상 1"
    assert data[1]["sort_order"] == 2
