from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sw_js_returns_200_with_js_content_type():
    response = client.get("/sw.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers["content-type"]
    assert response.headers.get("service-worker-allowed") == "/"


def test_manifest_json_returns_200():
    response = client.get("/static/manifest.json")
    assert response.status_code == 200
