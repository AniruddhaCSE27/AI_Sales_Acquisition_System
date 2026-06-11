from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import current_user, require_roles
from app.db.session import get_db
from app.models import AuditLog, Lead, Role, User
from app.schemas import ChatRequest, ChatResponse, FollowUpRequest, FollowUpResponse
from app.services.ai_service import AIService
from app.services.customer_memory_service import CustomerMemoryService
from app.services.followup_service import FollowUpService
from app.services.manager_copilot import ManagerCopilotService
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/manager-chat", response_model=ChatResponse, dependencies=[Depends(require_roles(Role.admin, Role.manager))])
def manager_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    return AIService().answer_manager_question(db, payload.question)


@router.post("/manager-copilot", response_model=ChatResponse, dependencies=[Depends(require_roles(Role.admin, Role.manager))])
def manager_copilot(payload: ChatRequest, db: Session = Depends(get_db)):
    result = ManagerCopilotService().answer(db, payload.question)
    return ChatResponse(answer=result["answer"], recommendations=result["recommendations"])


@router.post("/manager-rag", dependencies=[Depends(require_roles(Role.admin, Role.manager))])
def manager_rag(payload: ChatRequest, db: Session = Depends(get_db)):
    return RAGService().answer(db, payload.question)


@router.post("/rag/reindex", dependencies=[Depends(require_roles(Role.admin, Role.manager))])
def reindex_rag(db: Session = Depends(get_db)):
    return RAGService().index_workspace(db)


@router.post("/recommendations/lead/{lead_id}")
def lead_recommendations(lead_id: int, db: Session = Depends(get_db), _=Depends(require_roles(Role.admin, Role.manager, Role.telecaller))):
    return AIService().lead_recommendations(db, lead_id)


@router.post("/followup", response_model=FollowUpResponse)
def ai_followup(payload: FollowUpRequest, lead_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    resolved_lead_id = payload.lead_id or lead_id
    if resolved_lead_id is None:
        raise HTTPException(status_code=400, detail="lead_id is required")
    lead = db.get(Lead, resolved_lead_id)
    if not lead or (user.organization_id and lead.organization_id not in (None, user.organization_id)):
        raise HTTPException(status_code=404, detail="Lead not found")
    memory = CustomerMemoryService().get_or_create(db, lead)
    generated = FollowUpService().generate(lead, memory, objective=payload.objective, tone=payload.tone)
    db.add(
        AuditLog(
            organization_id=user.organization_id,
            user_id=user.id,
            action="ai.followup_generate",
            entity_type="lead",
            entity_id=lead.id,
            metadata_json={"channel": payload.channel, "tone": payload.tone, "route": "/api/v1/ai/followup"},
        )
    )
    db.commit()
    return {"lead_id": lead.id, **generated}
