from __future__ import annotations

from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.models import AIJob, Call, CallTranscript, Lead
from app.services.call_intelligence_service import CallIntelligenceService
from app.services.lead_scoring import LeadScoringService
from app.services.rag_service import RAGService
from app.services.report_service import ReportService
from app.services.whatsapp_service import WhatsAppAutomationService
from app.workers.celery_app import celery_app


def _mark_job(job_id: int | None, status: str, result: dict | None = None, error: str | None = None) -> None:
    if job_id is None:
        return
    with SessionLocal() as db:
        job = db.get(AIJob, job_id)
        if job:
            job.status = status
            job.result = result or job.result
            job.error = error
            job.updated_at = datetime.utcnow()
            db.commit()


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def score_import_batch(self, lead_ids: list[int], job_id: int | None = None) -> dict:
    with SessionLocal() as db:
        scorer = LeadScoringService()
        updated = 0
        for lead in db.query(Lead).filter(Lead.id.in_(lead_ids)).all():
            score = scorer.score_lead(lead)
            lead.lead_score = score["lead_score"]
            lead.conversion_probability = score["conversion_probability"]
            lead.predicted_revenue = score["predicted_revenue"]
            lead.quality_class = score["quality_class"]
            lead.score_explanation = score["explanation"]
            lead.next_best_action = score.get("next_best_action")
            updated += 1
        db.commit()
    result = {"updated": updated}
    _mark_job(job_id, "completed", result)
    return result


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def analyze_call_transcript(self, call_id: int, transcript: str, job_id: int | None = None) -> dict:
    analysis = CallIntelligenceService().analyze_transcript(transcript)
    with SessionLocal() as db:
        call = db.get(Call, call_id)
        if call:
            call.summary = analysis["summary"]
            call.sentiment_score = analysis["sentiment_score"]
            call.intent = analysis["intent"]
            call.next_action = analysis["next_action"]
            db.add(CallTranscript(call_id=call_id, transcript=transcript, analysis=analysis))
            db.commit()
    _mark_job(job_id, "completed", analysis)
    return analysis


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_report(self, job_id: int | None = None) -> dict:
    with SessionLocal() as db:
        result = ReportService().generate_weekly(db, datetime.utcnow() - timedelta(days=7), datetime.utcnow())
    _mark_job(job_id, "completed", result)
    return result


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def generate_embeddings(self, organization_id: int | None = None, job_id: int | None = None) -> dict:
    with SessionLocal() as db:
        result = RAGService().index_workspace(db, organization_id)
    _mark_job(job_id, "completed", result)
    return result


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 2})
def retrain_lead_model(self, job_id: int | None = None) -> dict:
    from ai_models.train_lead_conversion import train

    result = train()
    _mark_job(job_id, "completed", result)
    return result


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def schedule_whatsapp_follow_up(self, phone: str, template: str, context: dict, job_id: int | None = None) -> dict:
    result = WhatsAppAutomationService().send(phone, template, context)
    _mark_job(job_id, "completed", result)
    return result
