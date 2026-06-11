from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import CustomerMemory, Lead


class CustomerMemoryService:
    def get_or_create(self, db: Session, lead: Lead) -> CustomerMemory:
        memory = db.query(CustomerMemory).filter(CustomerMemory.lead_id == lead.id).first()
        if memory is None:
            memory = CustomerMemory(
                organization_id=lead.organization_id,
                lead_id=lead.id,
                budget=lead.budget,
                sentiment="neutral",
                summary=lead.lead_notes,
                next_action=lead.next_best_action,
            )
            db.add(memory)
            db.flush()
        return memory

    def merge_from_text(self, memory: CustomerMemory, text: str) -> None:
        lowered = (text or "").lower()
        objections = set(memory.objections or [])
        if any(word in lowered for word in ("fee", "fees", "price", "cost", "expensive", "budget")):
            objections.add("price")
        if any(word in lowered for word in ("parent", "parents", "family", "spouse")):
            objections.add("decision_maker")
        if any(word in lowered for word in ("placement", "job", "salary")):
            objections.add("outcomes")
        if any(word in lowered for word in ("later", "tomorrow", "evening", "morning", "weekend")):
            memory.preferred_contact_time = "Customer requested a later follow-up window."
        if any(word in lowered for word in ("interested", "ready", "visit", "enroll")):
            memory.sentiment = "positive"
        elif any(word in lowered for word in ("not interested", "angry", "stop", "reject")):
            memory.sentiment = "negative"
        memory.objections = sorted(objections)
