from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "leadforage_ai",
    broker=settings.celery_broker_url or settings.redis_url,
    backend=settings.celery_result_backend or settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_routes={
        "app.workers.tasks.score_import_batch": {"queue": "ai"},
        "app.workers.tasks.analyze_call_transcript": {"queue": "ai"},
        "app.workers.tasks.generate_report": {"queue": "reports"},
        "app.workers.tasks.generate_embeddings": {"queue": "ai"},
        "app.workers.tasks.retrain_lead_model": {"queue": "mlops"},
        "app.workers.tasks.schedule_whatsapp_follow_up": {"queue": "notifications"},
    },
)
