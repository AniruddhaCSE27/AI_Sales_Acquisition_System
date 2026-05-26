from fastapi.testclient import TestClient

from app.main import app


def test_liveness_and_health_payload():
    client = TestClient(app)
    live = client.get("/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    health = client.get("/health")
    assert health.status_code == 200
    payload = health.json()
    assert "dependencies" in payload
    assert "database" in payload["dependencies"]
    assert "redis" in payload["dependencies"]
    assert "openai" in payload["dependencies"]
