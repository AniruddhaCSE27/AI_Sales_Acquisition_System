from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.core.permissions import EnterpriseRole
from app.db.session import get_db
from app.models import CallTranscriptAnalysis, CustomerMemory, Lead, LeadStatus, PerformanceMetric, User
from app.services.manager_copilot import ManagerCopilotService

router = APIRouter(dependencies=[Depends(require_permissions(EnterpriseRole.MANAGER))])


@router.get("/best-agents")
def best_agents(db: Session = Depends(get_db)):
    rows = db.query(PerformanceMetric).order_by(PerformanceMetric.conversions.desc(), PerformanceMetric.successful_calls.desc()).limit(10).all()
    result = []
    for row in rows:
        user = db.get(User, row.user_id)
        result.append(
            {
                "user_id": row.user_id,
                "name": user.name if user else f"User {row.user_id}",
                "calls_made": row.calls_made,
                "successful_calls": row.successful_calls,
                "conversions": row.conversions,
                "avg_call_quality": row.avg_call_quality,
            }
        )
    return result


@router.get("/hot-leads")
def hot_leads(db: Session = Depends(get_db)):
    rows = db.query(Lead).filter(Lead.quality_class == "Hot").order_by(Lead.lead_score.desc(), Lead.created_at.desc()).limit(25).all()
    return [{"id": row.id, "name": row.name, "score": row.lead_score, "status": row.status.value, "next_best_action": row.next_best_action} for row in rows]


@router.get("/followups-due")
def followups_due(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    rows = db.query(Lead).filter(Lead.follow_up_date.is_not(None), Lead.follow_up_date <= now, Lead.status != LeadStatus.converted).order_by(Lead.follow_up_date.asc()).limit(25).all()
    return [{"id": row.id, "name": row.name, "follow_up_date": row.follow_up_date, "status": row.status.value, "phone": row.phone} for row in rows]


@router.get("/objection-analytics")
def objection_analytics(db: Session = Depends(get_db)):
    counts: dict[str, int] = {}
    for memory in db.query(CustomerMemory).limit(1000).all():
        for objection in memory.objections or []:
            counts[str(objection)] = counts.get(str(objection), 0) + 1
    for analysis in db.query(CallTranscriptAnalysis).limit(1000).all():
        for objection in analysis.objections or []:
            counts[str(objection)] = counts.get(str(objection), 0) + 1
    return [{"objection": key, "count": value} for key, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)]


@router.get("/conversion-analytics")
def conversion_analytics(db: Session = Depends(get_db)):
    total = db.query(Lead).count()
    converted = db.query(Lead).filter(Lead.status == LeadStatus.converted).count()
    source_rows = db.query(Lead.lead_source, func.count(Lead.id), func.avg(Lead.conversion_probability)).group_by(Lead.lead_source).all()
    return {
        "total_leads": total,
        "converted_leads": converted,
        "conversion_rate": round((converted / total) * 100, 2) if total else 0,
        "by_source": [{"source": row[0], "leads": row[1], "avg_probability": round(float(row[2] or 0), 4)} for row in source_rows],
    }


@router.get("/summary")
def manager_summary(db: Session = Depends(get_db)):
    result = ManagerCopilotService().answer(db, "summarize sales performance")
    return {"summary": result["answer"], "evidence": result["evidence"], "recommendations": result["recommendations"]}
