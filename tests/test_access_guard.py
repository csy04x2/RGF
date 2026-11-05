from fastapi.testclient import TestClient
from app.web import app


def test_access_guard_challenges_anonymous_user(monkeypatch):
    monkeypatch.setenv("RGF_ACCESS_PASSWORD", "test-only-password")
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == 'Basic realm="RGF"'
    assert client.get("/", auth=("rgf", "wrong")).status_code == 401
    assert client.get("/", auth=("rgf", "test-only-password")).status_code == 200


def test_hosted_service_fails_closed_without_password(monkeypatch):
    monkeypatch.delenv("RGF_ACCESS_PASSWORD", raising=False)
    monkeypatch.setenv("RAILWAY_PROJECT_ID", "example")
    response = TestClient(app).get("/")
    assert response.status_code == 503


def test_local_can_still_open_upload_without_password(monkeypatch):
    monkeypatch.delenv("RGF_ACCESS_PASSWORD", raising=False)
    monkeypatch.delenv("RAILWAY_PROJECT_ID", raising=False)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT_NAME", raising=False)
    assert TestClient(app).get("/").status_code == 200
