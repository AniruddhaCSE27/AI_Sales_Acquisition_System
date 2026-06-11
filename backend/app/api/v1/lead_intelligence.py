from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models import AuditLog, Lead, User
from app.schemas import LeadIntelligenceRequest, LeadIntelligenceResponse
from app.services.customer_memory_service import CustomerMemoryService
from app.services.lead_ai_service import LeadAIService

router = APIRouter()


def _sentiment(text: str) -> tuple[str, float]:
    lowered = text.lower()
    positive = sum(word in lowered for word in ("interested", "ready", "visit", "enroll", "yes"))
    negative = sum(word in lowered for word in ("expensive", "not interested", "angry", "reject", "no"))
    score = max(-1.0, min(1.0, (positive - negative) / 3))
    label = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
    return label, round(score, 3)


def _intent(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ("admission", "enroll", "visit", "application")):
        return "admission_intent"
    if any(word in lowered for word in ("fees", "budget", "scholarship", "emi")):
        return "fee_discussion"
    if any(word in lowered for word in ("placement", "job", "salary")):
        return "outcome_research"
    return "qualification"


@router.post("/{lead_id:int}/analyze", response_model=LeadIntelligenceResponse)
def analyze_lead(lead_id: int, payload: LeadIntelligenceRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    text = " ".join(filter(None, [lead.lead_notes, payload.notes, lead.next_best_action, lead.course_interest]))
    memory = CustomerMemoryService().get_or_create(db, lead)
    CustomerMemoryService().merge_from_text(memory, text)
    score = LeadAIService().score_lead(lead, {"follow_up_count": 1 if lead.follow_up_date else 0})
    sentiment, sentiment_score = _sentiment(text)
    lead.lead_score = score["lead_score"]
    lead.conversion_probability = score["conversion_probability"]
    lead.predicted_revenue = score["predicted_revenue"]
    lead.quality_class = score["quality_class"]
    lead.score_explanation = score["explanation"]
    lead.next_best_action = score["next_best_action"]
    lead.sentiment_score = sentiment_score
    memory.sentiment = sentiment
    memory.next_action = score["next_best_action"]
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="ai.lead_intelligence", entity_type="lead", entity_id=lead.id))
    db.commit()
    return {
        "lead_id": lead.id,
        "lead_score": lead.lead_score,
        "lead_score_explanation": lead.score_explanation,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "intent": _intent(text),
        "objections": memory.objections or [],
        "next_best_action": lead.next_best_action or score["next_best_action"],
    }
