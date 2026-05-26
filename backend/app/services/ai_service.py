from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import Lead, LeadStatus


class AIService:
    def analyze_call(self, transcript: str) -> dict:
        lowered = transcript.lower()
        sentiment = 0.75 if any(w in lowered for w in ["interested", "yes", "admission", "visit"]) else 0.35
        objections = [w for w in ["budget", "fees", "parents", "time", "location"] if w in lowered]
        intent = "high_intent" if "admission" in lowered or "apply" in lowered else "needs_nurture"
        next_action = "Schedule counsellor callback within 2 hours" if sentiment > 0.6 else "Send nurturing WhatsApp and follow up tomorrow"
        return {
            "summary": f"Lead discussed {', '.join(objections) if objections else 'course options'} and showed {intent.replace('_', ' ')}.",
            "sentiment_score": sentiment,
            "intent": intent,
            "objections": objections,
            "interest_level": "High" if sentiment > 0.65 else "Medium",
            "next_action": next_action,
            "quality_score": round(sentiment * 100, 2),
        }

    def live_call_guidance(self, text: str) -> dict:
        analysis = self.analyze_call(text)
        suggestions = ["Confirm preferred course and intake", "Ask budget range", "Offer counsellor consultation slot"]
        if "fees" in text.lower() or "budget" in text.lower():
            suggestions.insert(0, "Handle fee objection with EMI, scholarship, and ROI examples")
        return {"sentiment": analysis["sentiment_score"], "intent": analysis["intent"], "suggestions": suggestions, "next_action": analysis["next_action"]}

    def answer_manager_question(self, db: Session, question: str) -> dict:
        total = db.query(Lead).count()
        converted = db.query(Lead).filter(Lead.status == LeadStatus.converted).count()
        best_source = db.query(Lead.lead_source, func.count(Lead.id).label("n")).group_by(Lead.lead_source).order_by(func.count(Lead.id).desc()).first()
        answer = (
            f"Current conversion is {round((converted / total) * 100, 2) if total else 0}%. "
            f"The strongest lead volume source is {best_source[0] if best_source else 'not enough data'}. "
            "Prioritize Hot leads with recent engagement and route fee objections to senior counsellors."
        )
        return {"answer": answer, "recommendations": ["Call Hot leads within 15 minutes", "Audit low quality publishers weekly", "Coach telecallers with low sentiment scores"]}

    def lead_recommendations(self, db: Session, lead_id: int) -> dict:
        lead = db.get(Lead, lead_id)
        if not lead:
            return {"recommendations": []}
        return {
            "best_time_to_call": "10:00-12:00 or 17:00-19:00",
            "script": f"Open with {lead.course_interest or 'course'} outcomes, ask timeline, then qualify budget.",
            "next_actions": ["Click-to-call now" if lead.quality_class == "Hot" else "Send nurturing WhatsApp", "Schedule counsellor handoff", "Add objection notes"],
        }

