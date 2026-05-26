import base64
import tempfile
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.core.config import settings
from app.services.objection_service import ObjectionDetectionService


class WhisperService:
    def __init__(self) -> None:
        self.objections = ObjectionDetectionService()
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def decode_audio_payload(self, payload: str) -> bytes:
        try:
            return base64.b64decode(payload)
        except Exception:
            return payload.encode("utf-8")

    def transcribe_chunk(self, audio_payload: str | bytes, *, call_sid: str | None = None, chunk_index: int = 0) -> dict[str, Any]:
        audio_bytes = self.decode_audio_payload(audio_payload) if isinstance(audio_payload, str) else audio_payload
        if self.client and audio_bytes:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = Path(tmp.name)
            try:
                with tmp_path.open("rb") as audio_file:
                    result = self.client.audio.transcriptions.create(model=settings.whisper_model, file=audio_file)
                text = getattr(result, "text", "") or ""
            finally:
                tmp_path.unlink(missing_ok=True)
        else:
            text = self._fallback_transcript(audio_bytes, call_sid, chunk_index)
        analysis = self.analyze_transcript(text)
        return {"call_sid": call_sid, "chunk_index": chunk_index, "text": text, "analysis": analysis, "partial": True}

    def merge_transcripts(self, chunks: list[dict[str, Any]]) -> str:
        return " ".join(chunk.get("text", "").strip() for chunk in sorted(chunks, key=lambda item: item.get("chunk_index", 0)) if chunk.get("text")).strip()

    def analyze_transcript(self, transcript: str) -> dict[str, Any]:
        lowered = transcript.lower()
        sentiment = 0.75 if any(word in lowered for word in ("interested", "yes", "visit", "apply", "admission")) else 0.35
        urgency = "high" if any(word in lowered for word in ("today", "urgent", "this week", "now")) else "medium" if "later" in lowered else "low"
        budget = "mentioned" if any(word in lowered for word in ("budget", "fees", "emi", "scholarship", "cost")) else "unknown"
        buying_stage = "decision" if any(word in lowered for word in ("apply", "admission", "visit")) else "evaluation" if "thinking" in lowered or "compare" in lowered else "awareness"
        course_interest = self._course_interest(lowered)
        objections = self.objections.detect(transcript)
        primary = self.objections.primary(transcript)
        high_intent = sentiment > 0.65 and (buying_stage in {"evaluation", "decision"} or course_interest is not None)
        return {
            "lead_intent": "high_intent" if high_intent else "needs_nurture",
            "urgency": urgency,
            "budget": budget,
            "sentiment": sentiment,
            "confidence": 0.84 if transcript else 0.25,
            "buying_stage": buying_stage,
            "course_interest": course_interest,
            "objections": objections,
            "recommended_response": primary["recommended_response"] if primary else "Confirm goals, timeline, and preferred counselling slot.",
            "next_action": primary["next_action"] if primary else "Schedule counsellor follow-up.",
        }

    def _fallback_transcript(self, audio_bytes: bytes, call_sid: str | None, chunk_index: int) -> str:
        try:
            decoded = audio_bytes.decode("utf-8").strip()
            if decoded:
                return decoded
        except UnicodeDecodeError:
            pass
        if chunk_index % 2 == 0:
            return "Lead is interested in MBA admission but says fees too high and parents decide."
        return "Lead asked to call later and wants scholarship details."

    def _course_interest(self, lowered: str) -> str | None:
        for course in ("mba", "data science", "ai", "engineering", "bba", "medical"):
            if course in lowered:
                return course.title()
        return None
