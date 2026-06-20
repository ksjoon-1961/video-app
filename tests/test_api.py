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
    {"id": "00000000-0000-0000-0000-000000000001", "name": "샘플 영상 1", "storage_path": "videos/sample1.mp4", "sort_order": 1, "is_ready": True},
    {"id": "00000000-0000-0000-0000-000000000002", "name": "샘플 영상 2", "storage_path": "videos/sample2.mp4", "sort_order": 2, "is_ready": True},
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
    assert response.status_code in (401, 403)


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


def test_videos_is_ready_field():
    mock_12 = [
        {
            "id": f"00000000-0000-0000-0000-{str(i).zfill(12)}",
            "name": f"영상 {i}",
            "storage_path": f"sample{i}.mp4" if i <= 3 else "",
            "sort_order": i,
            "is_ready": i <= 3,
        }
        for i in range(1, 13)
    ]
    with patch("app.auth._client", return_value=_mock_jwks()), \
         patch("app.services.catalog.get_videos", new_callable=AsyncMock, return_value=mock_12):
        token = _make_token()
        response = client.get("/api/videos", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert "is_ready" in data[0]
    assert data[0]["is_ready"] is True
    assert data[3]["is_ready"] is False


# ── /api/videos/{id}/url ──────────────────────────────────────────────────────

_MOCK_VIDEO = {
    "id": "00000000-0000-0000-0000-000000000001",
    "name": "샘플 영상 1",
    "storage_path": "Sample-1.mp4",
    "sort_order": 1,
    "is_ready": True,
}
_MOCK_VIDEO_NOT_READY = {
    "id": "00000000-0000-0000-0000-000000000004",
    "name": "영상 4",
    "storage_path": "",
    "sort_order": 4,
    "is_ready": False,
}
_MOCK_SIGNED_URL = "https://inwkwmhjsuwdafvgogio.supabase.co/storage/v1/object/sign/videos/Sample-1.mp4?token=test"


def test_video_url_no_token():
    response = client.get("/api/videos/some-id/url")
    assert response.status_code in (401, 403)


def test_video_url_not_found():
    with patch("app.auth._client", return_value=_mock_jwks()), \
         patch("app.services.catalog.get_video_by_id", new_callable=AsyncMock, return_value=None):
        token = _make_token()
        response = client.get("/api/videos/nonexistent/url", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_video_url_not_ready():
    with patch("app.auth._client", return_value=_mock_jwks()), \
         patch("app.services.catalog.get_video_by_id", new_callable=AsyncMock, return_value=_MOCK_VIDEO_NOT_READY):
        token = _make_token()
        response = client.get(
            f"/api/videos/{_MOCK_VIDEO_NOT_READY['id']}/url",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 409
    assert response.json()["detail"] == "video not ready"


def test_video_url_returns_signed_url():
    with patch("app.auth._client", return_value=_mock_jwks()), \
         patch("app.services.catalog.get_video_by_id", new_callable=AsyncMock, return_value=_MOCK_VIDEO), \
         patch("app.services.storage.create_signed_url", new_callable=AsyncMock, return_value=_MOCK_SIGNED_URL):
        token = _make_token()
        response = client.get(
            f"/api/videos/{_MOCK_VIDEO['id']}/url",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == _MOCK_SIGNED_URL
    assert data["expires_in"] == 3600
