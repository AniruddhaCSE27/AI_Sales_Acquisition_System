from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.seed import run_seed
from app.services.objection_service import ObjectionDetectionService
from app.services.whisper_service import WhisperService


def _headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": "admin@demo.com", "password": "Password123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_whisper_and_objection_analysis():
    service = WhisperService()
    result = service.transcribe_chunk("Lead is interested in MBA but fees too high and parents decide", call_sid="test", chunk_index=0)
    assert result["analysis"]["lead_intent"] == "high_intent"
    assert result["analysis"]["objections"]
    primary = ObjectionDetectionService().primary("fees too high")
    assert primary["objection_type"] == "price_objection"


def test_simulated_twilio_workflow_and_copilot_websocket():
    with SessionLocal() as db:
        run_seed(db)

    client = TestClient(app)
    headers = _headers(client)
    lead = client.post(
        "/api/v1/leads/",
        headers=headers,
        json={
            "name": "Twilio Flow Lead",
            "phone": "9990002888",
            "email": "twilio-flow@example.com",
            "city": "Delhi",
            "course": "MBA",
            "budget": 150000,
            "source": "api_test",
        },
    )
    assert lead.status_code in {200, 409}
    leads = client.get("/api/v1/leads/?search=9990002888", headers=headers).json()["items"]
    lead_id = leads[0]["id"]
    response = client.post(f"/api/v1/calls/simulate-stream/{lead_id}", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["media"]["analysis"]["objections"]
    assert payload["whatsapp"]["sid"]

    with client.websocket_connect(f"/api/v1/ws/telecaller-copilot/{lead_id}") as websocket:
        ready = websocket.receive_json()
        assert ready["type"] == "ready"
        websocket.send_json({"text": "Lead says fees too high but interested in admission"})
        update = websocket.receive_json()
        assert update["type"] == "copilot_update"
        assert update["objections"]


def test_metrics_endpoint():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "api_requests_total" in response.text
