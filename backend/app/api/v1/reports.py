from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.db.session import get_db
from app.models import Role
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/weekly", dependencies=[Depends(require_roles(Role.manager))])
def generate_weekly_report(db: Session = Depends(get_db)):
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    return ReportService().generate_weekly(db, start, end)

