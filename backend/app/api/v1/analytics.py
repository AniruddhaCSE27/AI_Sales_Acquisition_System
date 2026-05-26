from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Call, Lead, LeadStatus, PerformanceMetric, User

router = APIRouter()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(current_user)):
    total = db.query(Lead).count()
    converted = db.query(Lead).filter(Lead.status == LeadStatus.converted).count()
    hot = db.query(Lead).filter(Lead.quality_class == "Hot").count()
    revenue = db.query(func.coalesce(func.sum(Lead.predicted_revenue), 0)).scalar()
    calls = db.query(Call).count()
    avg_sentiment = db.query(func.coalesce(func.avg(Call.sentiment_score), 0)).scalar()
    source_rows = db.query(Lead.lead_source, func.count(Lead.id), func.avg(Lead.conversion_probability)).group_by(Lead.lead_source).all()
    trend_rows = (
        db.query(func.date(Lead.created_at), func.count(Lead.id), func.sum(Lead.predicted_revenue))
        .group_by(func.date(Lead.created_at))
        .order_by(func.date(Lead.created_at))
        .limit(30)
        .all()
    )
    funnel = [
        {"stage": "New", "value": db.query(Lead).filter(Lead.status == LeadStatus.new).count()},
        {"stage": "Contacted", "value": db.query(Lead).filter(Lead.status == LeadStatus.contacted).count()},
        {"stage": "Follow-up", "value": db.query(Lead).filter(Lead.status == LeadStatus.follow_up).count()},
        {"stage": "Converted", "value": converted},
    ]
    return {
        "kpis": {
            "total_leads": total,
            "converted_leads": converted,
            "conversion_rate": round((converted / total) * 100, 2) if total else 0,
            "hot_leads": hot,
            "predicted_revenue": round(float(revenue or 0), 2),
            "calls": calls,
            "avg_sentiment": round(float(avg_sentiment or 0), 2),
        },
        "lead_sources": [{"source": r[0], "leads": r[1], "avg_probability": round(float(r[2] or 0), 2)} for r in source_rows],
        "funnel": funnel,
        "trends": [
            {
                "date": str(r[0]),
                "leads": r[1],
                "conversions": db.query(Lead).filter(func.date(Lead.created_at) == r[0], Lead.status == LeadStatus.converted).count(),
                "revenue": round(float(r[2] or 0), 2),
            }
            for r in trend_rows
        ],
    }


@router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db), _: User = Depends(current_user)):
    rows = db.query(PerformanceMetric).order_by(PerformanceMetric.conversions.desc()).limit(10).all()
    return [
        {
            "user_id": row.user_id,
            "calls_made": row.calls_made,
            "successful_calls": row.successful_calls,
            "conversions": row.conversions,
            "quality": row.avg_call_quality,
            "burnout_risk": row.burnout_risk,
        }
        for row in rows
    ]
