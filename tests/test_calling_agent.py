from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models import AICallSession
from app.seed import ensure_demo_admin


def _headers(client: TestClient) -> dict[str, str]:
    with SessionLocal() as db:
        ensure_demo_admin(db)
    response = client.post("/api/v1/auth/login", json={"email": "admin@demo.com", "password": "Password123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _payload(**overrides) -> dict:
    payload = {
        "lead_name": "AI Calling Demo Lead",
        "phone_number": "+919876543210",
        "objective": "Schedule a counselling session",
        "product": "MBA counselling",
        "tone": "Friendly",
        "language": "Hinglish",
        "consent": True,
    }
    payload.update(overrides)
    return payload


def test_calling_agent_script_and_simulation(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "")
    client = TestClient(app)
    headers = _headers(client)

    script = client.post("/api/v1/ai/calling-agent/script", headers=headers, json=_payload())
    assert script.status_code == 200
    assert script.json()["opening_line"]
    assert script.json()["qualification_questions"]
    assert "Schedule a counselling session" in script.json()["full_script"]

    simulation = client.post("/api/v1/ai/calling-agent/simulate", headers=headers, json=_payload())
    assert simulation.status_code == 200
    assert simulation.json()["ai_agent_message"]
    assert simulation.json()["customer_possible_reply"]
    assert simulation.json()["interest_level"] in {"High", "Medium", "Low"}
    assert simulation.json()["sentiment"] in {"Positive", "Neutral", "Negative"}
    assert simulation.json()["detected_objection"] in {"Pricing", "Timing", "Competitor", "Need", "Trust"}
    assert simulation.json()["ai_suggested_response"]
    assert simulation.json()["lead_score"] > 0
    assert simulation.json()["next_best_action"]

    saved = client.post(
        "/api/v1/ai/calling-agent/save-interaction",
        headers=headers,
        json={
            **_payload(),
            "script": script.json()["full_script"],
            "simulation": simulation.json(),
            "summary": simulation.json()["call_summary"],
            "interest_level": simulation.json()["interest_level"],
            "sentiment": simulation.json()["sentiment"],
            "lead_score": simulation.json()["lead_score"],
            "objection": simulation.json()["detected_objection"],
            "suggested_response": simulation.json()["ai_suggested_response"],
            "next_action": simulation.json()["next_best_action"],
        },
    )
    assert saved.status_code == 200
    with SessionLocal() as db:
        row = db.get(AICallSession, saved.json()["session_id"])
        assert row.status == "saved"
        assert row.script
        assert row.simulation
        assert row.lead_score > 0
        assert row.objection
        assert row.next_action


def test_calling_agent_missing_consent_blocks_real_call():
    client = TestClient(app)
    response = client.post("/api/v1/ai/calling-agent/start-call", headers=_headers(client), json=_payload(consent=False))
    assert response.status_code == 400
    assert "Consent is required" in response.json()["detail"]


def test_calling_agent_missing_twilio_credentials_is_safe(monkeypatch):
    monkeypatch.setattr(settings, "twilio_account_sid", "")
    monkeypatch.setattr(settings, "twilio_auth_token", "")
    monkeypatch.setattr(settings, "twilio_phone_number", "")
    client = TestClient(app)
    response = client.post("/api/v1/ai/calling-agent/start-call", headers=_headers(client), json=_payload())
    assert response.status_code == 200
    assert response.json()["started"] is False
    assert response.json()["message"] == "Real calling is not configured. Add Twilio credentials to enable live calls."

    status = client.get("/api/v1/ai/calling-agent/status", headers=_headers(client))
    assert status.status_code == 200
    assert status.json()["twilio_configured"] is False
