from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Lead, LeadStatus, Publisher, User
from app.schemas import PublisherCreate, PublisherRead

router = APIRouter()


@router.post("/", response_model=PublisherRead)
def create_publisher(payload: PublisherCreate, db: Session = Depends(get_db), _: User = Depends(current_user)):
    publisher = Publisher(**payload.model_dump())
    db.add(publisher)
    db.commit()
    db.refresh(publisher)
    return publisher


@router.get("/", response_model=list[PublisherRead])
def list_publishers(db: Session = Depends(get_db), _: User = Depends(current_user)):
    return db.query(Publisher).order_by(Publisher.quality_score.desc()).all()


@router.get("/{publisher_id}/analytics")
def publisher_analytics(publisher_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    total = db.query(Lead).filter(Lead.publisher_id == publisher_id).count()
    converted = db.query(Lead).filter(Lead.publisher_id == publisher_id, Lead.status == LeadStatus.converted).count()
    revenue = db.query(func.coalesce(func.sum(Lead.predicted_revenue), 0)).filter(Lead.publisher_id == publisher_id).scalar()
    return {"total_leads": total, "converted": converted, "conversion_rate": converted / total if total else 0, "predicted_revenue": revenue}

