import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client(tmp_db):
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_pages_render(client):
    for path in ("/", "/playground", "/keys", "/models", "/logs", "/settings"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert "abusecode" in r.text


def test_keys_flow(client):
    r = client.post("/api/keys", json={"name": "primary", "api_key": "oc_sk_1234567890abcdef"})
    assert r.status_code == 200
    key_id = r.json()["id"]

    keys = client.get("/api/keys").json()
    assert keys[0]["name"] == "primary"
    assert "..." in keys[0]["masked"]

    r = client.patch(f"/api/keys/{key_id}", json={"active": False})
    assert r.status_code == 200
    assert client.get("/api/keys").json()[0]["active"] is False

    assert client.delete(f"/api/keys/{key_id}").status_code == 200
    assert client.get("/api/keys").json() == []


def test_proxy_without_keys_returns_503(client):
    r = client.post("/v1/responses", json={"model": "m", "input": "hi"})
    assert r.status_code == 503


def test_stats_and_logs(client):
    assert client.get("/api/stats").status_code == 200
    body = client.get("/api/logs?limit=5").json()
    assert body["total"] == 0
    assert client.get("/api/logs/export?format=csv").status_code == 200
