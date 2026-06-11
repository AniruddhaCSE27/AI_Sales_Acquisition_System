from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models import AuditLog, KnowledgeDocument, User
from app.schemas import KnowledgeAskRequest, KnowledgeAskResponse, KnowledgeDocumentRead, KnowledgeSearchResult
from app.services.rag_service import RAGService

router = APIRouter()

TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".html", ".htm"}


def _decode_upload(file: UploadFile) -> str:
    raw = file.file.read()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix and suffix not in TEXT_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only text-like documents are supported in the local parser")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


@router.post("/documents", response_model=KnowledgeDocumentRead)
def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    content = _decode_upload(file).strip()
    if not content:
        raise HTTPException(status_code=400, detail="Document content is empty")
    document = KnowledgeDocument(
        organization_id=user.organization_id,
        title=title or Path(file.filename or "knowledge-document").stem,
        source_filename=file.filename,
        content=content,
        created_by=user.id,
        metadata_json={"parser": "text_fallback", "rag_backend": "json_vector_or_pgvector"},
    )
    db.add(document)
    db.flush()
    RAGService().index_document(db, document)
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="knowledge.upload", entity_type="knowledge_document", entity_id=document.id))
    db.commit()
    db.refresh(document)
    return document


@router.get("/documents", response_model=list[KnowledgeDocumentRead])
def list_documents(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(KnowledgeDocument)
    if user.organization_id:
        query = query.filter(KnowledgeDocument.organization_id == user.organization_id)
    return query.order_by(KnowledgeDocument.created_at.desc()).limit(100).all()


@router.get("/search", response_model=list[KnowledgeSearchResult])
def search_knowledge_base(q: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return RAGService().search_knowledge_base(db, q, user.organization_id)


@router.post("/ask", response_model=KnowledgeAskResponse)
def ask_knowledge_base(payload: KnowledgeAskRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return RAGService().answer_knowledge_base(db, payload.question, user.organization_id)
