from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from app.services.objection_detection_service import ObjectionDetectionService


class CallIntelligenceService:
    """Transcript intelligence for batch and streaming call workflows."""

    def __init__(self) -> None:
        self.objections = ObjectionDetectionService()

    def analyze_transcript(self, transcript: str, lead_context: dict[str, Any] | None = None) -> dict[str, Any]:
        text = transcript or ""
        lowered = text.lower()
        objections = self.objections.detect(text)
        primary = objections[0] if objections else None
        sentiment = self._sentiment(lowered, objections)
        intent = self._intent(lowered)
        readiness = self._readiness(lowered, sentiment, intent)
        budget = self._extract_budget(lowered)
        follow_up_time = self._follow_up_time(primary, readiness)
        probability_update = max(-0.25, min(0.3, (sentiment - 0.5) * 0.35 + (0.15 if readiness == "ready" else 0)))
        return {
            "transcript": text,
            "summary": self._summary(intent, primary, budget),
            "sentiment": sentiment,
            "sentiment_score": sentiment,
            "intent": intent,
            "objections": objections,
            "objection_type": primary["objection_type"] if primary else None,
            "severity": primary["severity"] if primary else "low",
            "recommended_response": primary["recommended_response"] if primary else "Confirm course fit, budget, intake timeline, and preferred counselling slot.",
            "next_action": primary["next_action"] if primary else "Schedule counselling qualification call.",
            "follow_up_time": follow_up_time.isoformat(),
            "conversion_probability_update": round(probability_update, 4),
            "course_interest": self._course_interest(lowered, lead_context or {}),
            "budget_mention": budget,
            "admission_readiness": readiness,
        }

    def live_update(self, partial_transcript: str) -> dict[str, Any]:
        analysis = self.analyze_transcript(partial_transcript)
        return {
            "type": "copilot_update",
            "sentiment": analysis["sentiment"],
            "intent": analysis["intent"],
            "objections": analysis["objections"],
            "suggestion": analysis["recommended_response"],
            "next_action": analysis["next_action"],
        }

    def _sentiment(self, lowered: str, objections: list[dict]) -> float:
        positive = sum(word in lowered for word in ("interested", "yes", "visit", "apply", "admission", "ready"))
        negative = sum(word in lowered for word in ("not interested", "do not call", "expensive", "doubt", "later"))
        score = 0.5 + positive * 0.11 - negative * 0.13 - len(objections) * 0.03
        return round(max(0.05, min(score, 0.95)), 3)

    def _intent(self, lowered: str) -> str:
        if any(word in lowered for word in ("apply", "admission", "visit campus", "enroll", "seat")):
            return "admission_ready"
        if any(word in lowered for word in ("fees", "scholarship", "emi", "parents", "compare")):
            return "needs_counselling"
        if "not interested" in lowered:
            return "not_interested"
        return "information_seeking"

    def _readiness(self, lowered: str, sentiment: float, intent: str) -> str:
        if intent == "admission_ready" and sentiment >= 0.55:
            return "ready"
        if intent == "not_interested":
            return "closed_lost_risk"
        return "nurture"

    def _extract_budget(self, lowered: str) -> str | None:
        match = re.search(r"(?:rs\.?|inr|₹)?\s?(\d{2,7})(?:\s?k)?", lowered)
        if not match:
            return None
        value = match.group(1)
        return f"{value}k" if match.group(0).strip().endswith("k") else value

    def _course_interest(self, lowered: str, context: dict[str, Any]) -> str | None:
        for course in ("mba", "bba", "data science", "ai", "engineering", "medical", "product management"):
            if course in lowered:
                return course
        return context.get("course_interest")

    def _follow_up_time(self, primary: dict | None, readiness: str) -> datetime:
        if readiness == "ready":
            return datetime.utcnow() + timedelta(minutes=30)
        if primary and primary.get("objection_type") == "time_objection":
            return datetime.utcnow() + timedelta(days=1)
        return datetime.utcnow() + timedelta(hours=4)

    def _summary(self, intent: str, primary: dict | None, budget: str | None) -> str:
        parts = [f"Intent: {intent.replace('_', ' ')}"]
        if primary:
            parts.append(f"Primary objection: {primary['objection_type'].replace('_', ' ')}")
        if budget:
            parts.append(f"Budget mentioned: {budget}")
        return ". ".join(parts) + "."
