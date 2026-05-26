from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ObjectionRule:
    objection_type: str
    severity: str
    keywords: tuple[str, ...]
    recommended_response: str
    next_action: str


class ObjectionDetectionService:
    RULES = (
        ObjectionRule(
            "price_objection",
            "high",
            ("fees too high", "expensive", "budget", "costly", "scholarship", "emi"),
            "Acknowledge the concern, explain EMI and scholarship options, then anchor the program ROI.",
            "Send scholarship template and schedule counsellor fee discussion.",
        ),
        ObjectionRule(
            "time_objection",
            "medium",
            ("call later", "busy", "tomorrow", "next week", "no time"),
            "Confirm a specific callback slot and summarize the value in one sentence before ending.",
            "Create follow-up task with exact callback time.",
        ),
        ObjectionRule(
            "family_objection",
            "medium",
            ("parents decide", "father", "mother", "family", "guardian"),
            "Offer a joint counselling call and share parent-facing outcome proof.",
            "Schedule family counselling call.",
        ),
        ObjectionRule(
            "trust_objection",
            "high",
            ("thinking", "not sure", "trust", "reviews", "placement", "guarantee"),
            "Share alumni outcomes, accreditation, and transparent placement data.",
            "Send proof pack and assign senior counsellor.",
        ),
        ObjectionRule(
            "competition_objection",
            "medium",
            ("other college", "competitor", "another institute", "comparing"),
            "Ask comparison criteria and position differentiators around outcomes and support.",
            "Send comparison sheet.",
        ),
        ObjectionRule(
            "not_interested",
            "critical",
            ("not interested", "do not call", "remove my number"),
            "Respectfully acknowledge and ask for permission to close the inquiry.",
            "Mark lead lost or do-not-contact based on consent.",
        ),
    )

    def detect(self, text: str) -> list[dict[str, Any]]:
        lowered = (text or "").lower()
        matches: list[dict[str, Any]] = []
        for rule in self.RULES:
            matched = [keyword for keyword in rule.keywords if keyword in lowered]
            if not matched:
                continue
            matches.append(
                {
                    "objection_type": rule.objection_type,
                    "severity": rule.severity,
                    "matched_terms": matched,
                    "recommended_response": rule.recommended_response,
                    "next_action": rule.next_action,
                    "confidence": min(0.95, 0.55 + len(matched) * 0.15),
                }
            )
        return matches

    def primary(self, text: str) -> dict[str, Any] | None:
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        matches = self.detect(text)
        if not matches:
            return None
        return sorted(matches, key=lambda item: severity_order.get(item["severity"], 0), reverse=True)[0]
