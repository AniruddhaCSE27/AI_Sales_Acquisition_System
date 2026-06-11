from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models import Activity, AuditLog, CustomerMemory, Lead, User
from app.schemas import CustomerMemoryRead, CustomerMemoryUpdate
from app.services.customer_memory_service import CustomerMemoryService

router = APIRouter()


def _lead(db: Session, lead_id: int, user: User) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead or (user.organization_id and lead.organization_id not in (None, user.organization_id)):
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.get("/{lead_id:int}", response_model=CustomerMemoryRead)
def read_memory(lead_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = _lead(db, lead_id, user)
    memory = CustomerMemoryService().get_or_create(db, lead)
    db.commit()
    db.refresh(memory)
    return memory


@router.put("/{lead_id:int}", response_model=CustomerMemoryRead)
def update_memory(lead_id: int, payload: CustomerMemoryUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = _lead(db, lead_id, user)
    memory = CustomerMemoryService().get_or_create(db, lead)
    for key, value in payload.model_dump().items():
        setattr(memory, key, value)
    db.add(Activity(lead_id=lead.id, user_id=user.id, action="customer_memory_updated", metadata_json=payload.model_dump(mode="json")))
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="memory.update", entity_type="lead", entity_id=lead.id, metadata_json=payload.model_dump(mode="json")))
    db.commit()
    db.refresh(memory)
    return memory


@router.get("/", response_model=list[CustomerMemoryRead])
def list_memory(db: Session = Depends(get_db), user: User = Depends(current_user)):
    query = db.query(CustomerMemory)
    if user.organization_id:
        query = query.filter(CustomerMemory.organization_id == user.organization_id)
    return query.order_by(CustomerMemory.updated_at.desc()).limit(100).all()
