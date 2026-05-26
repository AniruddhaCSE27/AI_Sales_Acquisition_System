import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import Call, Lead, LeadStatus, Report


class ReportService:
    def generate_weekly(self, db: Session, start: datetime, end: datetime) -> dict:
        os.makedirs(settings.reports_dir, exist_ok=True)
        total = db.query(Lead).count()
        converted = db.query(Lead).filter(Lead.status == LeadStatus.converted).count()
        followups = db.query(Lead).filter(Lead.status == LeadStatus.follow_up).count()
        hot = db.query(Lead).filter(Lead.quality_class == "Hot").count()
        calls = db.query(Call).count()
        conversion_rate = round(converted / total * 100, 2) if total else 0
        if total:
            summary = f"{total} leads are active with {conversion_rate}% conversion, {hot} hot leads, and {followups} follow-ups requiring attention."
            actions = []
            if hot:
                actions.append("Assign hot leads to the highest converting counsellors today")
            if followups:
                actions.append("Clear due follow-ups before importing another publisher batch")
            if not calls:
                actions.append("Start the telecaller queue to capture call outcomes and objections")
            if not actions:
                actions.append("Maintain SLA discipline and monitor source quality")
        else:
            summary = "No leads exist yet. Import publisher/Merrito data or add leads manually to activate sales reporting."
            actions = ["Upload a clean lead source", "Create telecaller and counsellor users", "Review integration settings before calling"]
        insights = {
            "summary": summary,
            "conversion_rate": conversion_rate,
            "actions": actions,
        }
        path = os.path.join(settings.reports_dir, f"weekly-report-{end.date()}.pdf")
        pdf = canvas.Canvas(path, pagesize=A4)
        pdf.setTitle("Weekly AI Sales Report")
        pdf.drawString(72, 800, "Weekly AI Sales Report")
        pdf.drawString(72, 770, f"Period: {start.date()} to {end.date()}")
        pdf.drawString(72, 740, f"Total leads: {total} | Converted: {converted} | Conversion: {insights['conversion_rate']}%")
        y = 700
        for action in insights["actions"]:
            pdf.drawString(90, y, f"- {action}")
            y -= 24
        pdf.save()
        report = Report(title="Weekly AI Sales Report", period_start=start, period_end=end, file_path=path, insights=insights)
        db.add(report)
        db.commit()
        return {"report_id": report.id, "file_path": path, "insights": insights}
