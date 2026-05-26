from typing import Any

from app.services.lead_ai_service import LeadAIService


class LeadScoringService:
    """Backward-compatible facade for the production lead AI service."""

    def __init__(self) -> None:
        self.ai = LeadAIService()

    def score_lead(self, lead: Any) -> dict:
        return self.ai.score_lead(lead)
