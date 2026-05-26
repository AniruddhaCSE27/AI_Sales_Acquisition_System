from __future__ import annotations

import random
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from ai_models.model_registry import LocalModelRegistry

FEATURE_ORDER = [
    "source",
    "publisher",
    "course",
    "city",
    "budget",
    "lead_age_hours",
    "call_attempts",
    "response_status",
    "follow_up_count",
    "whatsapp_response",
    "counsellor_outcome",
    "engagement_score",
]


def _encode(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return (abs(hash(str(value))) % 1000) / 1000


def _synthetic_training_rows(n: int = 240) -> tuple[np.ndarray, np.ndarray]:
    sources = ["referral", "organic", "webinar", "publisher", "merrito", "manual"]
    courses = ["mba", "data science", "ai engineering", "bba", "medical"]
    cities = ["delhi", "mumbai", "pune", "jaipur", "lucknow"]
    X, y = [], []
    for _ in range(n):
        row = {
            "source": random.choice(sources),
            "publisher": random.randint(0, 8),
            "course": random.choice(courses),
            "city": random.choice(cities),
            "budget": random.choice([60000, 90000, 140000, 220000, 300000]),
            "lead_age_hours": random.randint(1, 240),
            "call_attempts": random.randint(0, 5),
            "response_status": random.choice(["new", "interested", "follow_up", "contacted"]),
            "follow_up_count": random.randint(0, 4),
            "whatsapp_response": random.randint(0, 1),
            "counsellor_outcome": random.choice(["unknown", "positive", "negative"]),
            "engagement_score": random.random(),
        }
        intent = (
            (row["source"] in {"referral", "organic", "webinar"}) * 0.18
            + (row["budget"] >= 140000) * 0.22
            + (row["course"] in {"mba", "data science", "ai engineering"}) * 0.18
            + (row["city"] in {"delhi", "mumbai", "pune"}) * 0.1
            + row["whatsapp_response"] * 0.12
            + row["engagement_score"] * 0.2
            - max(row["call_attempts"] - 2, 0) * 0.07
        )
        X.append([_encode(row[name]) for name in FEATURE_ORDER])
        y.append(1 if intent > 0.52 else 0)
    return np.array(X), np.array(y)


def _preferred_model():
    try:
        from lightgbm import LGBMClassifier

        return "lightgbm", LGBMClassifier(n_estimators=80, learning_rate=0.05, random_state=42)
    except Exception:
        try:
            from xgboost import XGBClassifier

            return "xgboost", XGBClassifier(n_estimators=80, learning_rate=0.05, max_depth=3, eval_metric="logloss", random_state=42)
        except Exception:
            return "logistic_regression", make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))


def train(registry_dir: str = "ai_models/registry") -> dict:
    X, y = _synthetic_training_rows()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    model_type, model = _preferred_model()
    baseline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)).fit(X_train, y_train)
    model.fit(X_train, y_train)

    probability = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test)
    baseline_probability = baseline.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, probability >= 0.5)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probability)), 4),
        "baseline_roc_auc": round(float(roc_auc_score(y_test, baseline_probability)), 4),
        "training_rows": int(len(X)),
    }
    Path(registry_dir).mkdir(parents=True, exist_ok=True)
    artifact_path = str(Path(registry_dir) / f"lead_conversion_{model_type}.joblib")
    joblib.dump(model, artifact_path)
    manifest = LocalModelRegistry(registry_dir).register("lead_conversion", model_type, artifact_path, metrics, FEATURE_ORDER)
    return {"manifest": manifest, "metrics": metrics}


if __name__ == "__main__":
    print(train())
