from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models import AuditLog, Lead, User
from app.schemas import FollowUpRequest, FollowUpResponse
from app.services.customer_memory_service import CustomerMemoryService
from app.services.followup_service import FollowUpService

router = APIRouter()


@router.post("/lead/{lead_id:int}", response_model=FollowUpResponse)
def generate_followup(lead_id: int, payload: FollowUpRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    memory = CustomerMemoryService().get_or_create(db, lead)
    generated = FollowUpService().generate(lead, memory, objective=payload.objective, tone=payload.tone)
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="ai.followup_generate", entity_type="lead", entity_id=lead.id, metadata_json={"channel": payload.channel, "tone": payload.tone}))
    db.commit()
    return {"lead_id": lead.id, **generated}
