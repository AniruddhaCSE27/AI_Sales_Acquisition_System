from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Role
from app.schemas import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from app.services.manager_copilot import ManagerCopilotService
from app.services.rag_service import RAGService

router = APIRouter()


@router.post("/manager-chat", response_model=ChatResponse, dependencies=[Depends(require_roles(Role.manager))])
def manager_chat(payload: ChatRequest, db: Session = Depends(get_db)):
    return AIService().answer_manager_question(db, payload.question)


@router.post("/manager-copilot", response_model=ChatResponse, dependencies=[Depends(require_roles(Role.manager))])
def manager_copilot(payload: ChatRequest, db: Session = Depends(get_db)):
    result = ManagerCopilotService().answer(db, payload.question)
    return ChatResponse(answer=result["answer"], recommendations=result["recommendations"])


@router.post("/manager-rag", dependencies=[Depends(require_roles(Role.manager))])
def manager_rag(payload: ChatRequest, db: Session = Depends(get_db)):
    return RAGService().answer(db, payload.question)


@router.post("/rag/reindex", dependencies=[Depends(require_roles(Role.manager))])
def reindex_rag(db: Session = Depends(get_db)):
    return RAGService().index_workspace(db)


@router.post("/recommendations/lead/{lead_id}")
def lead_recommendations(lead_id: int, db: Session = Depends(get_db), _=Depends(require_roles(Role.manager, Role.telecaller))):
    return AIService().lead_recommendations(db, lead_id)
