from io import BytesIO

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.seed import run_seed


def _headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": "admin@demo.com", "password": "Password123!"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _lead_id(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/v1/leads/",
        headers=headers,
        json={
            "name": "LeadForge V3 Lead",
            "phone": "9990003333",
            "email": "leadforge-v3@example.com",
            "city": "Delhi",
            "course_interest": "MBA",
            "budget": 175000,
            "lead_source": "referral",
            "lead_notes": "Interested but worried about fees and placement outcomes.",
        },
    )
    if response.status_code == 409:
        listing = client.get("/api/v1/leads/?search=leadforge-v3@example.com", headers=headers)
        return listing.json()["items"][0]["id"]
    assert response.status_code == 200
    return response.json()["id"]


def test_customer_memory_and_followup_generation():
    with SessionLocal() as db:
        run_seed(db)
    client = TestClient(app)
    headers = _headers(client)
    lead_id = _lead_id(client, headers)

    analysis = client.post(f"/api/v1/lead-intelligence/{lead_id}/analyze", headers=headers, json={"notes": "Parents need fee details tomorrow evening."})
    assert analysis.status_code == 200
    assert "price" in analysis.json()["objections"]

    memory = client.get(f"/api/v1/customer-memory/{lead_id}", headers=headers)
    assert memory.status_code == 200
    assert memory.json()["lead_id"] == lead_id

    updated = client.put(
        f"/api/v1/customer-memory/{lead_id}",
        headers=headers,
        json={"objections": ["price"], "sentiment": "positive", "budget": 175000, "preferred_contact_time": "Evening", "summary": "Needs fee clarity.", "next_action": "book a counselling call", "metadata_json": {}},
    )
    assert updated.status_code == 200
    assert updated.json()["next_action"] == "book a counselling call"

    followup = client.post(f"/api/v1/followups/lead/{lead_id}", headers=headers, json={"objective": "book a counselling call", "tone": "warm"})
    assert followup.status_code == 200
    assert followup.json()["whatsapp_message"]
    assert followup.json()["email_body"]
    assert followup.json()["call_script"]

    ai_followup = client.post("/api/v1/ai/followup", headers=headers, json={"lead_id": lead_id, "objective": "send scholarship details", "tone": "warm"})
    assert ai_followup.status_code == 200
    assert "send scholarship details" in ai_followup.json()["email_body"]


def test_knowledge_base_upload_search_and_ask():
    with SessionLocal() as db:
        run_seed(db)
    client = TestClient(app)
    headers = _headers(client)
    content = b"Scholarship options are available for eligible MBA students. Placement support includes mock interviews."

    upload = client.post(
        "/api/v1/knowledge-base/documents",
        headers=headers,
        data={"title": "MBA FAQ"},
        files={"file": ("mba-faq.txt", BytesIO(content), "text/plain")},
    )
    assert upload.status_code == 200
    assert upload.json()["title"] == "MBA FAQ"

    search = client.get("/api/v1/knowledge-base/search?q=scholarship", headers=headers)
    assert search.status_code == 200
    assert search.json()

    ask = client.post("/api/v1/knowledge-base/ask", headers=headers, json={"question": "What scholarship support exists?"})
    assert ask.status_code == 200
    assert ask.json()["citations"]


def test_manager_copilot_analytics_endpoints():
    with SessionLocal() as db:
        run_seed(db)
    client = TestClient(app)
    headers = _headers(client)
    assert client.get("/api/v1/manager-copilot/summary", headers=headers).status_code == 200
    assert client.get("/api/v1/manager-copilot/hot-leads", headers=headers).status_code == 200
    assert client.get("/api/v1/manager-copilot/followups-due", headers=headers).status_code == 200
    assert client.get("/api/v1/manager-copilot/objection-analytics", headers=headers).status_code == 200
    assert client.get("/api/v1/manager-copilot/conversion-analytics", headers=headers).status_code == 200
