from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.seed import run_seed


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": "admin@demo.com", "password": "Password123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_core_api_smoke_paths():
    with SessionLocal() as db:
        run_seed(db)

    client = TestClient(app)
    headers = auth_headers(client)

    assert client.get("/api/v1/analytics/dashboard", headers=headers).status_code == 200
    assert client.get("/api/v1/analytics/leaderboard", headers=headers).status_code == 200
    assert client.get("/api/v1/leads/", headers=headers).status_code == 200
    assert client.get("/api/v1/publishers/", headers=headers).status_code == 200
    assert client.post("/api/v1/reports/weekly", headers=headers).status_code == 200

    lead = client.post(
        "/api/v1/leads/",
        headers=headers,
        json={
            "name": "Smoke Test Lead",
            "phone": "9990001999",
            "email": "smoke@example.com",
            "city": "Delhi",
            "course_interest": "MBA",
            "budget": 150000,
            "lead_source": "manual",
        },
    )
    assert lead.status_code in {200, 409}


def test_websocket_smoke():
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/telecaller-assistant/1") as websocket:
        ready = websocket.receive_json()
        assert ready["type"] == "ready"
        websocket.send_json({"text": "The lead is interested but asked about fees"})
        guidance = websocket.receive_json()
        assert guidance["type"] == "guidance"
        assert guidance["suggestions"]
