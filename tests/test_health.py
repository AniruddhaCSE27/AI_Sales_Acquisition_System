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

    ready = client.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "api_requests_total" in metrics.text
