import json
import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.core.config import settings
from app.db.migrations import ensure_schema
from app.db.session import SessionLocal, engine
from app.models import Lead, LeadStatus, ModelRegistryEntry, Publisher


def load_dataset() -> tuple[list[list[float]], list[int]]:
    with SessionLocal() as db:
        rows = db.query(Lead).all()
        if len(rows) < 8:
            rows = _synthetic_rows(rows)
        features: list[list[float]] = []
        labels: list[int] = []
        for lead in rows:
            publisher = db.get(Publisher, lead.publisher_id) if getattr(lead, "publisher_id", None) else None
            features.append(
                [
                    float(lead.budget or 0),
                    float(lead.lead_score or 0),
                    float(lead.conversion_probability or 0),
                    float(lead.sentiment_score or 0),
                    float(lead.engagement_score or 0),
                    float(getattr(publisher, "quality_score", 0) or 0),
                    float(getattr(publisher, "roi_score", 0) or 0),
                ]
            )
            labels.append(1 if lead.status == LeadStatus.converted else 0)
    return features, labels


def train_models() -> dict[str, Any]:
    ensure_schema(engine)
    features, labels = load_dataset()
    if len(set(labels)) < 2:
        labels[-1] = 1 - labels[-1]
    x_train, x_test, y_train, y_test = train_test_split(features, labels, test_size=0.35, random_state=42, stratify=labels if min(labels.count(0), labels.count(1)) > 1 else None)
    models = {
        "logistic_regression": Pipeline([("scaler", StandardScaler()), ("model", LogisticRegression(max_iter=1000))]),
        "random_forest": RandomForestClassifier(n_estimators=80, random_state=42),
    }
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.08, eval_metric="logloss")
    except Exception:
        pass

    registry_dir = Path(settings.model_registry_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)
    version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    results: dict[str, Any] = {"version": version, "models": {}}
    best_name = ""
    best_f1 = -1.0
    with SessionLocal() as db:
        for name, model in models.items():
            model.fit(x_train, y_train)
            predictions = model.predict(x_test)
            metrics = {
                "accuracy": round(accuracy_score(y_test, predictions), 4),
                "precision": round(precision_score(y_test, predictions, zero_division=0), 4),
                "recall": round(recall_score(y_test, predictions, zero_division=0), 4),
                "f1": round(f1_score(y_test, predictions, zero_division=0), 4),
            }
            path = registry_dir / f"{name}-{version}.pkl"
            with path.open("wb") as handle:
                pickle.dump(model, handle)
            results["models"][name] = {"metrics": metrics, "artifact_path": str(path)}
            if metrics["f1"] > best_f1:
                best_f1 = metrics["f1"]
                best_name = name
            db.add(ModelRegistryEntry(model_name=name, version=version, artifact_path=str(path), metrics=metrics, is_active=False))
        db.flush()
        for row in db.query(ModelRegistryEntry).filter(ModelRegistryEntry.version == version).all():
            row.is_active = row.model_name == best_name
        db.commit()
    results["active_model"] = best_name
    manifest = registry_dir / f"manifest-{version}.json"
    manifest.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def _synthetic_rows(existing: list[Lead]) -> list[Lead]:
    rows = list(existing)
    for index in range(10):
        lead = Lead(
            name=f"Synthetic {index}",
            phone=f"90000000{index:02d}",
            lead_source="synthetic",
            budget=80000 + index * 25000,
            lead_score=35 + index * 6,
            conversion_probability=0.2 + index * 0.06,
            sentiment_score=0.25 + index * 0.05,
            engagement_score=0.3 + index * 0.06,
            status=LeadStatus.converted if index >= 6 else LeadStatus.follow_up,
        )
        rows.append(lead)
    return rows


if __name__ == "__main__":
    print(json.dumps(train_models(), indent=2))
