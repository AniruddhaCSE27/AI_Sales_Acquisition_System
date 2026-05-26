import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "ai_models") not in sys.path:
    sys.path.insert(0, str(ROOT / "ai_models"))

from app.db.session import SessionLocal
from app.models import ModelRegistryEntry
from app.seed import run_seed
from retrain_pipeline import train_models


def test_retraining_pipeline_writes_registry():
    with SessionLocal() as db:
        run_seed(db)
    result = train_models()
    assert result["active_model"]
    with SessionLocal() as db:
        assert db.query(ModelRegistryEntry).count() >= 1
