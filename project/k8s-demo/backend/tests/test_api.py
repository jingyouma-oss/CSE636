from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

# Module-level client does NOT trigger lifespan/startup, so no real DB is touched.
client = TestClient(app)


def test_health_is_db_independent():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready_ok_when_db_reachable():
    with patch("app.db.ping", return_value=True):
        r = client.get("/api/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_ready_503_when_db_down():
    with patch("app.db.ping", side_effect=Exception("boom")):
        r = client.get("/api/ready")
    assert r.status_code == 503


def test_list_items():
    with patch("app.db.list_items", return_value=[{"id": 1, "name": "alpha"}]):
        r = client.get("/api/items")
    assert r.status_code == 200
    assert r.json() == {"items": [{"id": 1, "name": "alpha"}]}


def test_create_item():
    with patch("app.db.add_item", return_value={"id": 2, "name": "beta"}) as m:
        r = client.post("/api/items", json={"name": "beta"})
    assert r.status_code == 201
    assert r.json() == {"id": 2, "name": "beta"}
    m.assert_called_once_with("beta")


def test_create_item_rejects_empty():
    r = client.post("/api/items", json={"name": "   "})
    assert r.status_code == 400
