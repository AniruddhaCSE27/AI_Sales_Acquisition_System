from __future__ import annotations

from app.core.config import settings
from app.services.whisper_service import WhisperService


class SpeechService:
    """Speech abstraction for Whisper batch and Deepgram-compatible realtime providers."""

    def __init__(self) -> None:
        self.whisper = WhisperService()

    def transcribe_batch(self, audio_or_text: bytes | str, call_sid: str = "batch", chunk_index: int = 0) -> dict:
        if isinstance(audio_or_text, bytes):
            # Local safe fallback: real deployments can swap this for OpenAI Whisper audio upload.
            text = audio_or_text.decode("utf-8", errors="ignore")
        else:
            text = audio_or_text
        return self.whisper.transcribe_chunk(text, call_sid=call_sid, chunk_index=chunk_index)

    def realtime_provider(self) -> dict:
        provider = "deepgram" if getattr(settings, "deepgram_api_key", "") else "twilio_media_stream_fallback"
        return {"provider": provider, "available": provider == "deepgram"}
