from app.db.session import SessionLocal
from app.models import Lead
from app.services.call_intelligence_service import CallIntelligenceService
from app.services.lead_ai_service import LeadAIService
from app.services.rag_service import RAGService


def test_lead_ai_service_scores_and_explains():
    lead = Lead(name="AI Upgrade Lead", phone="9000000001", email="ai-upgrade@example.com", city="Delhi", course_interest="MBA", budget=220000, lead_source="referral")
    result = LeadAIService().score_lead(lead)
    assert 0 <= result["lead_score"] <= 100
    assert 0 <= result["conversion_probability"] <= 1
    assert result["quality_class"] in {"Hot", "Warm", "Cold"}
    assert result["next_best_action"]
    assert result["explanation"]


def test_call_intelligence_detects_objection_and_next_action():
    result = CallIntelligenceService().analyze_transcript("I am interested in MBA admission but fees are too high and parents decide.")
    assert result["intent"] in {"admission_ready", "needs_counselling"}
    assert result["objection_type"] in {"price_objection", "family_objection"}
    assert result["recommended_response"]
    assert result["follow_up_time"]


def test_rag_indexes_and_retrieves_lead_notes():
    with SessionLocal() as db:
        lead = Lead(name="RAG Lead", phone="9000000002", email="rag@example.com", city="Pune", course_interest="Data Science", budget=180000, lead_source="webinar", lead_notes="Asked about scholarship and placement outcomes")
        db.add(lead)
        db.commit()
        RAGService().index_workspace(db)
        answer = RAGService().answer(db, "Which leads asked about scholarship?")
        assert answer["sources"]
        assert "scholarship" in answer["answer"].lower()
