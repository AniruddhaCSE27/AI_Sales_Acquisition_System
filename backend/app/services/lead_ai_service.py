from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import settings


class LeadAIService:
    """Production lead scoring facade with trained-model and deterministic fallbacks."""

    def __init__(self, registry_dir: str | None = None) -> None:
        self.registry_dir = Path(registry_dir or settings.model_registry_dir)
        self._model_bundle: dict[str, Any] | None = None

    def score_lead(self, lead: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
        features = self.extract_features(lead, context or {})
        bundle = self._load_active_bundle()
        if bundle:
            probability, explanation = self._predict_with_bundle(bundle, features)
        else:
            probability, explanation = self._heuristic_probability(features)

        score = round(max(0.0, min(probability * 100, 100.0)), 2)
        quality = "Hot" if score >= 72 else "Warm" if score >= 45 else "Cold"
        budget = float(features["budget"] or 0)
        return {
            "lead_score": score,
            "conversion_probability": round(probability, 4),
            "predicted_revenue": round((budget or 120000) * probability, 2),
            "quality_class": quality,
            "next_best_action": self.next_best_action(score, features),
            "explanation": explanation,
        }

    def extract_features(self, lead: Any, context: dict[str, Any]) -> dict[str, Any]:
        created_at = getattr(lead, "created_at", None) or datetime.utcnow()
        age_hours = max((datetime.utcnow() - created_at.replace(tzinfo=None)).total_seconds() / 3600, 0)
        return {
            "source": (getattr(lead, "lead_source", "") or "unknown").lower(),
            "publisher": str(getattr(lead, "publisher_id", "") or context.get("publisher", "unknown")),
            "course": (getattr(lead, "course_interest", "") or "unknown").lower(),
            "city": (getattr(lead, "city", "") or "unknown").lower(),
            "budget": float(getattr(lead, "budget", 0) or 0),
            "lead_age_hours": age_hours,
            "call_attempts": int(context.get("call_attempts", 0)),
            "response_status": str(context.get("response_status", getattr(lead, "status", "new"))).lower(),
            "follow_up_count": int(context.get("follow_up_count", 0)),
            "whatsapp_response": 1 if context.get("whatsapp_response") else 0,
            "counsellor_outcome": str(context.get("counsellor_outcome", "unknown")).lower(),
            "engagement_score": float(getattr(lead, "engagement_score", 0) or 0),
        }

    def next_best_action(self, score: float, features: dict[str, Any]) -> str:
        if score >= 72:
            return "Call within 15 minutes and offer a counsellor slot."
        if features["call_attempts"] >= 3:
            return "Switch to WhatsApp nurture and schedule a specific follow-up."
        if features["budget"] and features["budget"] < 80000:
            return "Send scholarship and EMI options before fee discussion."
        return "Qualify course, budget, intake timeline, and decision maker."

    def _heuristic_probability(self, features: dict[str, Any]) -> tuple[float, dict[str, float]]:
        source_score = 0.24 if features["source"] in {"referral", "organic", "webinar"} else 0.16 if features["source"] in {"publisher", "merrito", "csv", "import"} else 0.1
        budget_score = min(features["budget"] / 250000, 1.0) * 0.25
        course_score = 0.18 if any(key in features["course"] for key in ("mba", "data", "ai", "medical", "engineering")) else 0.1
        city_score = 0.12 if features["city"] in {"delhi", "mumbai", "bengaluru", "bangalore", "pune", "hyderabad"} else 0.07
        recency_score = max(0.0, 0.1 - min(features["lead_age_hours"], 240) / 2400)
        engagement_score = min(features["engagement_score"], 1.0) * 0.11
        follow_up_penalty = min(features["follow_up_count"], 5) * 0.015
        call_penalty = max(0, features["call_attempts"] - 2) * 0.025
        raw = source_score + budget_score + course_score + city_score + recency_score + engagement_score - follow_up_penalty - call_penalty
        probability = max(0.03, min(raw, 0.95))
        return probability, {
            "source_quality": round(source_score, 4),
            "budget_fit": round(budget_score, 4),
            "course_intent": round(course_score, 4),
            "city_demand": round(city_score, 4),
            "lead_recency": round(recency_score, 4),
            "engagement": round(engagement_score, 4),
            "follow_up_penalty": round(-follow_up_penalty, 4),
            "call_attempt_penalty": round(-call_penalty, 4),
            "explainability": "heuristic_fallback",
        }

    def _load_active_bundle(self) -> dict[str, Any] | None:
        if self._model_bundle is not None:
            return self._model_bundle
        manifest = self.registry_dir / "lead_conversion_active.json"
        if not manifest.exists():
            return None
        try:
            import joblib

            meta = json.loads(manifest.read_text(encoding="utf-8"))
            model = joblib.load(meta["artifact_path"])
            self._model_bundle = {"model": model, "metadata": meta}
            return self._model_bundle
        except Exception:
            return None

    def _predict_with_bundle(self, bundle: dict[str, Any], features: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        model = bundle["model"]
        feature_order = bundle["metadata"].get("feature_order", [])
        row = [[self._encode_feature(features.get(name)) for name in feature_order]]
        if hasattr(model, "predict_proba"):
            probability = float(model.predict_proba(row)[0][1])
        else:
            probability = 1 / (1 + math.exp(-float(model.predict(row)[0])))
        importances = getattr(model, "feature_importances_", None)
        if importances is None:
            importances = getattr(model, "coef_", [[0] * len(feature_order)])[0]
        explanation = {name: round(float(value), 4) for name, value in zip(feature_order, importances)}
        explanation["explainability"] = "model_feature_importance"
        return max(0.01, min(probability, 0.99)), explanation

    def _encode_feature(self, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        return (abs(hash(str(value))) % 1000) / 1000
