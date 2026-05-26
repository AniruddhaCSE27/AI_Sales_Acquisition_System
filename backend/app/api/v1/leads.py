import csv
import json
from difflib import SequenceMatcher
from io import StringIO
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Activity, AuditLog, ImportBatch, Lead, LeadStatus, Publisher, User
from app.schemas import BulkAction, ImportPreview, ImportResult, LeadCreate, LeadRead, LeadTimelineEvent, LeadUpdate, PaginatedLeads
from app.services.lead_scoring import LeadScoringService

router = APIRouter()


def score_and_apply(lead: Lead) -> None:
    score = LeadScoringService().score_lead(lead)
    lead.lead_score = score["lead_score"]
    lead.conversion_probability = score["conversion_probability"]
    lead.predicted_revenue = score["predicted_revenue"]
    lead.quality_class = score["quality_class"]
    lead.score_explanation = score["explanation"]
    lead.next_best_action = score.get("next_best_action")


def normalize_phone(value: str | None) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit() or ch == "+")


def lead_payload(payload: LeadCreate, db: Session, user: User) -> dict:
    data = payload.model_dump(exclude={"course", "source", "publisher"})
    data["phone"] = normalize_phone(data["phone"])
    data["organization_id"] = user.organization_id
    if payload.publisher and not data.get("publisher_id"):
        publisher = db.query(Publisher).filter(Publisher.name == payload.publisher).first()
        if not publisher:
            publisher = Publisher(name=payload.publisher, organization_id=user.organization_id)
            db.add(publisher)
            db.flush()
        data["publisher_id"] = publisher.id
    return data


def find_duplicate(db: Session, name: str, phone: str | None, email: str | None) -> tuple[Lead | None, str | None]:
    checks = []
    clean_phone = normalize_phone(phone)
    if clean_phone:
        checks.append(Lead.phone == clean_phone)
    if email:
        checks.append(Lead.email == email)
    if checks:
        duplicate = db.query(Lead).filter(or_(*checks)).first()
        if duplicate:
            return duplicate, "phone_or_email"
    candidates = db.query(Lead).limit(500).all()
    for candidate in candidates:
        if SequenceMatcher(None, candidate.name.lower(), name.lower()).ratio() >= 0.92:
            return candidate, "fuzzy_name"
    return None, None


def read_tabular(file: UploadFile) -> list[dict]:
    from io import BytesIO

    raw = file.file.read()
    filename = (file.filename or "").lower()
    if filename.endswith((".xlsx", ".xls")):
        import pandas as pd

        frame = pd.read_excel(BytesIO(raw))
        return frame.fillna("").to_dict(orient="records")
    content = raw.decode("utf-8-sig")
    return list(csv.DictReader(StringIO(content)))


FIELD_ALIASES = {
    "name": ["name", "student name", "full name", "lead name"],
    "phone": ["phone", "mobile", "mobile number", "contact", "contact number"],
    "email": ["email", "email id", "mail"],
    "course_interest": ["course", "program", "course_interest", "course interest"],
    "lead_source": ["source", "campaign", "lead source", "utm source"],
    "publisher": ["publisher", "partner"],
    "status": ["status", "lead status"],
    "city": ["city", "location"],
    "budget": ["budget", "fee budget"],
}


def suggest_mapping(headers: list[str]) -> dict[str, str]:
    normalized = {header.lower().strip(): header for header in headers}
    mapping = {}
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def row_to_payload(row: dict, mapping: dict[str, str]) -> LeadCreate:
    mapped = {field: row.get(source) for field, source in mapping.items() if row.get(source) not in (None, "")}
    if "lead_source" not in mapped:
        mapped["lead_source"] = "import"
    return LeadCreate(**mapped)


@router.post("/", response_model=LeadRead)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    data = lead_payload(payload, db, user)
    duplicate, reason = find_duplicate(db, data["name"], data["phone"], data.get("email"))
    if duplicate:
        raise HTTPException(status_code=409, detail={"message": "Duplicate lead detected", "reason": reason, "lead_id": duplicate.id})
    lead = Lead(**data)
    score_and_apply(lead)
    db.add(lead)
    db.flush()
    db.add(Activity(lead_id=lead.id, user_id=user.id, action="lead_created", metadata_json={"source": lead.lead_source}))
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="lead.create", entity_type="lead", entity_id=lead.id))
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/", response_model=PaginatedLeads)
def list_leads(
    search: str | None = None,
    status: LeadStatus | None = None,
    quality: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(current_user),
):
    query = db.query(Lead)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Lead.name.ilike(like), Lead.phone.ilike(like), Lead.email.ilike(like), Lead.city.ilike(like)))
    if status:
        query = query.filter(Lead.status == status)
    if quality:
        query = query.filter(Lead.quality_class == quality)
    total = query.count()
    items = query.order_by(Lead.lead_score.desc(), Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{lead_id:int}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id:int}", response_model=LeadRead)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(lead, key, value)
    action = "status_changed" if "status" in changes else "lead_updated"
    db.add(Activity(lead_id=lead.id, user_id=user.id, action=action, metadata_json=payload.model_dump(exclude_unset=True, mode="json")))
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action=f"lead.{action}", entity_type="lead", entity_id=lead.id, metadata_json=payload.model_dump(exclude_unset=True, mode="json")))
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/{lead_id:int}/timeline", response_model=list[LeadTimelineEvent])
def lead_timeline(lead_id: int, db: Session = Depends(get_db), _: User = Depends(current_user)):
    if not db.get(Lead, lead_id):
        raise HTTPException(status_code=404, detail="Lead not found")
    return db.query(Activity).filter(Activity.lead_id == lead_id).order_by(Activity.created_at.desc()).all()


@router.post("/bulk-action")
def bulk_action(payload: BulkAction, db: Session = Depends(get_db), user: User = Depends(current_user)):
    changes = payload.model_dump(exclude={"lead_ids"}, exclude_none=True, mode="json")
    if not changes:
        raise HTTPException(status_code=400, detail="No bulk changes supplied")
    updated = 0
    for lead in db.query(Lead).filter(Lead.id.in_(payload.lead_ids)).all():
        for key, value in changes.items():
            setattr(lead, key, value)
        db.add(Activity(lead_id=lead.id, user_id=user.id, action="bulk_updated", metadata_json=changes))
        updated += 1
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="lead.bulk_update", entity_type="lead", metadata_json={"updated": updated, **changes}))
    db.commit()
    return {"updated": updated}


@router.post("/import/preview", response_model=ImportPreview)
def import_preview(file: UploadFile = File(...), _: User = Depends(current_user)):
    rows = read_tabular(file)
    headers = list(rows[0].keys()) if rows else []
    return {"headers": headers, "suggested_mapping": suggest_mapping(headers), "rows": rows[:5]}


@router.post("/bulk-upload", response_model=ImportResult)
def bulk_upload(
    file: UploadFile = File(...),
    mapping_json: str | None = Form(None),
    source_type: str = Form("csv"),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    rows = read_tabular(file)
    headers = list(rows[0].keys()) if rows else []
    mapping = json.loads(mapping_json) if mapping_json else suggest_mapping(headers)
    created = 0
    skipped = 0
    errors = 0
    duplicate_report = []
    logs = []
    batch = ImportBatch(organization_id=user.organization_id, user_id=user.id, filename=file.filename or "upload", source_type=source_type, mapping=mapping, total_rows=len(rows))
    db.add(batch)
    db.flush()
    for index, row in enumerate(rows, start=1):
        try:
            payload = row_to_payload(row, mapping)
        except Exception as exc:
            errors += 1
            logs.append({"row": index, "level": "error", "message": str(exc)})
            continue
        data = lead_payload(payload, db, user)
        duplicate, reason = find_duplicate(db, data["name"], data["phone"], data.get("email"))
        if duplicate:
            skipped += 1
            duplicate_report.append({"row": index, "lead_id": duplicate.id, "reason": reason, "name": data["name"]})
            continue
        lead = Lead(**data)
        score_and_apply(lead)
        db.add(lead)
        db.flush()
        db.add(Activity(lead_id=lead.id, user_id=user.id, action="lead_imported", metadata_json={"batch_id": batch.id, "source_type": source_type}))
        created += 1
    batch.created_count = created
    batch.duplicate_count = skipped
    batch.error_count = errors
    batch.duplicate_report = duplicate_report
    batch.import_log = logs
    db.add(Activity(user_id=user.id, action="bulk_upload", metadata_json={"file": file.filename, "created": created, "skipped": skipped, "errors": errors}))
    db.add(AuditLog(organization_id=user.organization_id, user_id=user.id, action="lead.import", entity_type="import_batch", entity_id=batch.id, metadata_json={"created": created, "duplicates": skipped, "errors": errors}))
    db.commit()
    return {"batch_id": batch.id, "total_rows": len(rows), "created": created, "skipped_duplicates": skipped, "errors": errors, "duplicate_report": duplicate_report}


@router.post("/merrito-import", response_model=ImportResult)
def merrito_import(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    return bulk_upload(file=file, mapping_json=None, source_type="merrito", db=db, user=user)
