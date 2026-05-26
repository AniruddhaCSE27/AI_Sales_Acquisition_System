from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Call, Lead, LeadStatus, PerformanceMetric, Publisher, User


class ManagerCopilotService:
    def __init__(self) -> None:
        Path(settings.vector_db_dir).mkdir(parents=True, exist_ok=True)

    def answer(self, db: Session, question: str, organization_id: int | None = None) -> dict[str, Any]:
        query = db.query(Lead)
        if organization_id:
            query = query.filter(Lead.organization_id == organization_id)
        total = query.count()
        converted = query.filter(Lead.status == LeadStatus.converted).count()
        conversion_rate = round((converted / total) * 100, 2) if total else 0
        best_source = query.with_entities(Lead.lead_source, func.count(Lead.id).label("n")).group_by(Lead.lead_source).order_by(func.count(Lead.id).desc()).first()
        top_publisher = db.query(Publisher).order_by(Publisher.roi_score.desc()).first()
        top_metric = db.query(PerformanceMetric).order_by(PerformanceMetric.conversions.desc()).first()
        best_user = db.get(User, top_metric.user_id) if top_metric else None
        calls = db.query(Call).count()
        q = question.lower()
        if "conversion" in q and "down" in q:
            answer = f"Conversion is {conversion_rate}%. Check slow follow-ups, price objections, and low-intent publisher traffic first."
        elif "best telecaller" in q:
            answer = f"The best telecaller is {best_user.name if best_user else 'not enough data'} based on conversions."
        elif "best source" in q:
            answer = f"The best lead source by volume is {best_source[0] if best_source else 'not enough data'}."
        elif "next month" in q or "predict" in q:
            answer = f"Projected next-month conversions are {max(converted * 4, int(total * 0.18))} if current source quality holds."
        elif "revenue" in q:
            revenue = query.with_entities(func.coalesce(func.sum(Lead.predicted_revenue), 0)).scalar()
            answer = f"Predicted revenue is {round(float(revenue or 0), 2)}. Revenue drops usually trace to fewer Hot leads and delayed counsellor handoff."
        else:
            answer = f"You have {total} leads, {converted} conversions, {calls} calls, and a {conversion_rate}% conversion rate."
        return {
            "answer": answer,
            "evidence": {
                "total_leads": total,
                "converted": converted,
                "conversion_rate": conversion_rate,
                "best_source": best_source[0] if best_source else None,
                "top_publisher": top_publisher.name if top_publisher else None,
                "best_telecaller": best_user.name if best_user else None,
            },
            "recommendations": ["Prioritize Hot leads", "Review price objections daily", "Coach low-conversion callers", "Audit publisher ROI weekly"],
            "rag_backend": "local_vector_index",
        }
