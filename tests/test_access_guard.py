from fastapi.testclient import TestClient
import pytest
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


@pytest.mark.parametrize('base_url', ['http://rgf.railway.internal:8080',
                                      'http://rgf-test.up.railway.app',
                                      'https://rgf-test.up.railway.app'])
@pytest.mark.parametrize('headers', [
    {'Origin': 'https://rgf-test.up.railway.app'},
    {'Origin': 'https://rgf-test.up.railway.app:443'},
    {'Referer': 'https://rgf-test.up.railway.app/workspace/2'},
    {'Origin': 'https://rgf-test.up.railway.app',
     'X-Forwarded-Host': 'untrusted.example', 'X-Forwarded-Proto': 'http'},
])
def test_railway_public_https_origin_through_internal_http(monkeypatch, base_url, headers):
    monkeypatch.setenv('RAILWAY_PROJECT_ID', 'test-project')
    monkeypatch.setenv('RAILWAY_PUBLIC_DOMAIN', 'rgf-test.up.railway.app')
    monkeypatch.setenv('RGF_ACCESS_PASSWORD', 'test-only-password')
    client = TestClient(app, base_url=base_url)
    # POST / has no handler: 405 proves the middleware allowed it, with no DB use.
    response = client.post('/', headers=headers, auth=('rgf', 'test-only-password'))
    assert response.status_code == 405


@pytest.mark.parametrize('headers', [
    {'Origin': 'https://evil.example'},
    {'Origin': 'https://rgf-test.up.railway.app.evil.example'},
    {'Origin': 'http://rgf-test.up.railway.app'},
    {'Origin': 'https://rgf-test.up.railway.app:444'},
    {'Origin': 'http://rgf.railway.internal:8080'},
    {'Origin': 'https://rgf-test.up.railway.app', 'Sec-Fetch-Site': 'cross-site'},
    {'Origin': 'https://evil.example', 'X-Forwarded-Host': 'evil.example',
     'X-Forwarded-Proto': 'https'},
    {'Origin': 'null', 'Referer': 'https://rgf-test.up.railway.app/workspace/2'},
    {},
])
def test_railway_still_blocks_foreign_origins(monkeypatch, headers):
    monkeypatch.setenv('RAILWAY_PROJECT_ID', 'test-project')
    monkeypatch.setenv('RAILWAY_PUBLIC_DOMAIN', 'rgf-test.up.railway.app')
    monkeypatch.setenv('RGF_ACCESS_PASSWORD', 'test-only-password')
    client = TestClient(app, base_url='http://rgf.railway.internal:8080')
    response = client.post('/', headers=headers, auth=('rgf', 'test-only-password'))
    assert response.status_code == 403
    assert response.text == 'Same-origin request required'


@pytest.mark.parametrize('headers,expected', [
    ({'Origin': 'http://127.0.0.1:8000'}, 405),
    ({'Referer': 'http://127.0.0.1:8000/review?run_id=2'}, 405),
    ({'Origin': 'https://evil.example', 'X-Forwarded-Host': 'evil.example',
      'X-Forwarded-Proto': 'https'}, 403),
    ({'Origin': 'http://127.0.0.1:8000', 'Sec-Fetch-Site': 'cross-site'}, 403),
])
def test_local_origin_ignores_forwarding_headers(monkeypatch, headers, expected):
    monkeypatch.delenv('RAILWAY_PROJECT_ID', raising=False)
    monkeypatch.delenv('RAILWAY_ENVIRONMENT_NAME', raising=False)
    monkeypatch.delenv('RGF_ACCESS_PASSWORD', raising=False)
    # A copied Railway domain alone must not change the local development origin.
    monkeypatch.setenv('RAILWAY_PUBLIC_DOMAIN', 'rgf-test.up.railway.app')
    client = TestClient(app, base_url='http://127.0.0.1:8000')
    assert client.post('/', headers=headers).status_code == expected
