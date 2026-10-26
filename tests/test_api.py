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

    duplicate = client.post(
        "/api/keys", json={"name": "again", "api_key": "oc_sk_1234567890abcdef"}
    )
    assert duplicate.status_code == 409

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


def test_dashboard_auth(tmp_db, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "ADMIN_TOKEN", "sekret")
    with TestClient(app) as c:
        page = c.get("/", follow_redirects=False)
        assert page.status_code == 303
        assert page.headers["location"] == "/login"
        assert c.get("/api/keys").status_code == 401

        assert c.post("/api/login", json={"token": "wrong"}).status_code == 401
        assert c.post("/api/login", json={"token": "sekret"}).status_code == 200
        assert c.get("/api/keys").status_code == 200
        assert c.get("/", follow_redirects=False).status_code == 200


def test_proxy_token_and_same_origin(tmp_db, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "PROXY_TOKEN", "ptok")
    with TestClient(app) as c:
        r = c.post("/v1/responses", json={"model": "m", "input": "hi"})
        assert r.status_code == 401

        for headers in (
            {"x-proxy-token": "ptok"},
            {"authorization": "Bearer ptok"},
            {"sec-fetch-site": "same-origin"},
        ):
            r = c.post("/v1/responses", json={"model": "m", "input": "hi"}, headers=headers)
            assert r.status_code == 503, headers


def test_key_change_invalidates_catalog(client):
    from app.routers import usage

    usage._catalog.update({"ts": 9e9, "data": [{"id": "stale"}], "error": None})
    r = client.post("/api/keys", json={"name": "k", "api_key": "oc_sk_catalog"})
    assert r.status_code == 200
    assert usage._catalog["data"] is None
