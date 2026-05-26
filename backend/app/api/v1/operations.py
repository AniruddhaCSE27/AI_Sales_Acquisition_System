from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import AIJob, ModelRegistryEntry, Role
from app.seed import run_seed

router = APIRouter()


@router.post("/seed", dependencies=[Depends(require_roles(Role.manager))])
def seed_database(db: Session = Depends(get_db)):
    return {"status": "ok", "counts": run_seed(db)}


@router.get("/model-registry", dependencies=[Depends(require_roles(Role.manager))])
def model_registry(db: Session = Depends(get_db)):
    rows = db.query(ModelRegistryEntry).order_by(ModelRegistryEntry.created_at.desc()).limit(20).all()
    return [
        {
            "model_name": row.model_name,
            "version": row.version,
            "artifact_path": row.artifact_path,
            "metrics": row.metrics,
            "is_active": row.is_active,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/jobs", dependencies=[Depends(require_roles(Role.manager))])
def jobs(db: Session = Depends(get_db)):
    rows = db.query(AIJob).order_by(AIJob.created_at.desc()).limit(50).all()
    return [
        {
            "id": row.id,
            "task_name": row.task_name,
            "celery_task_id": row.celery_task_id,
            "status": row.status,
            "attempts": row.attempts,
            "result": row.result,
            "error": row.error,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


@router.post("/jobs/reindex-rag", dependencies=[Depends(require_roles(Role.manager))])
def enqueue_rag_reindex(db: Session = Depends(get_db)):
    from app.workers.tasks import generate_embeddings

    job = AIJob(task_name="generate_embeddings", status="queued", payload={})
    db.add(job)
    db.commit()
    task = generate_embeddings.delay(None, job.id)
    job.celery_task_id = task.id
    db.commit()
    return {"job_id": job.id, "celery_task_id": task.id}
