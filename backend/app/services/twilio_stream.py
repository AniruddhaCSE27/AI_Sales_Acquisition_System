import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Call, CallEventType, CallStreamEvent, CallTranscript, CallTranscriptAnalysis, Lead, LeadStatus
from app.services.whisper_service import WhisperService

logger = structlog.get_logger(__name__)


@dataclass
class StreamState:
    stream_sid: str
    call_sid: str | None = None
    call_id: int | None = None
    chunks: list[dict[str, Any]] = field(default_factory=list)
    reconnects: int = 0
    last_sequence: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)


class TwilioStreamService:
    def __init__(self) -> None:
        self.whisper = WhisperService()
        self.streams: dict[str, StreamState] = {}
        self.event_queue: defaultdict[str, deque[dict[str, Any]]] = defaultdict(deque)

    def voice_stream_response(self, websocket_url: str) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response><Connect>"
            f'<Stream url="{websocket_url}"><Parameter name="service" value="ai-sales"/></Stream>'
            "</Connect></Response>"
        )

    async def process_event(self, db: Session, payload: dict[str, Any], organization_id: int | None = None) -> dict[str, Any]:
        event = payload.get("event", "media")
        stream_sid = payload.get("streamSid") or payload.get("stream_sid") or "local-stream"
        sequence_number = int(payload.get("sequenceNumber") or payload.get("sequence_number") or 0)
        state = self.streams.setdefault(stream_sid, StreamState(stream_sid=stream_sid))
        state.last_sequence = max(state.last_sequence, sequence_number)
        self.event_queue[stream_sid].append(payload)
        if len(self.event_queue[stream_sid]) > 250:
            self.event_queue[stream_sid].popleft()

        result: dict[str, Any] = {"event": event, "stream_sid": stream_sid, "sequence_number": sequence_number}
        if event == "start":
            result.update(self._handle_start(db, state, payload, organization_id))
            event_type = CallEventType.started
        elif event == "media":
            result.update(await self._handle_media(db, state, payload, organization_id))
            event_type = CallEventType.media
        elif event == "stop":
            result.update(self._handle_stop(db, state, organization_id))
            event_type = CallEventType.stop
        elif event == "reconnect":
            state.reconnects += 1
            result["reconnects"] = state.reconnects
            event_type = CallEventType.reconnect
        else:
            event_type = CallEventType.mark

        db.add(CallStreamEvent(organization_id=organization_id, call_id=state.call_id, stream_sid=stream_sid, event_type=event_type, sequence_number=sequence_number, payload=payload))
        db.commit()
        return result

    def _handle_start(self, db: Session, state: StreamState, payload: dict[str, Any], organization_id: int | None) -> dict[str, Any]:
        start = payload.get("start", {})
        state.call_sid = start.get("callSid") or payload.get("callSid") or state.call_sid
        lead_id = _safe_int(start.get("customParameters", {}).get("lead_id") or payload.get("lead_id"))
        call = db.query(Call).filter(Call.twilio_sid == state.call_sid).first() if state.call_sid else None
        if call is None:
            lead = db.get(Lead, lead_id) if lead_id else db.query(Lead).first()
            call = Call(
                organization_id=organization_id or getattr(lead, "organization_id", None),
                lead_id=lead.id if lead else 1,
                twilio_sid=state.call_sid,
                direction=payload.get("direction", "incoming"),
                status="streaming",
                metadata_json={"stream_sid": state.stream_sid, "start": start},
            )
            db.add(call)
            db.flush()
        else:
            call.status = "streaming"
            call.metadata_json = {**(call.metadata_json or {}), "stream_sid": state.stream_sid, "start": start}
        state.call_id = call.id
        return {"call_id": call.id, "status": call.status}

    async def _handle_media(self, db: Session, state: StreamState, payload: dict[str, Any], organization_id: int | None) -> dict[str, Any]:
        await asyncio.sleep(0)
        media = payload.get("media", {})
        audio_payload = media.get("payload") or payload.get("audio") or ""
        chunk_index = len(state.chunks)
        transcription = self.whisper.transcribe_chunk(audio_payload, call_sid=state.call_sid, chunk_index=chunk_index)
        state.chunks.append(transcription)
        if not state.call_id:
            self._handle_start(db, state, payload, organization_id)
        transcript = db.query(CallTranscript).filter(CallTranscript.call_id == state.call_id).first()
        if transcript is None:
            transcript = CallTranscript(call_id=state.call_id, transcript=transcription["text"], analysis=transcription["analysis"])
            db.add(transcript)
        else:
            transcript.transcript = self.whisper.merge_transcripts(state.chunks)
            transcript.analysis = transcription["analysis"]
        db.flush()
        analysis = transcription["analysis"]
        db.add(
            CallTranscriptAnalysis(
                organization_id=organization_id,
                call_id=state.call_id,
                transcript_id=transcript.id,
                chunk_index=chunk_index,
                transcript_text=transcription["text"],
                intent=analysis["lead_intent"],
                urgency=analysis["urgency"],
                budget=analysis["budget"],
                sentiment=analysis["sentiment"],
                confidence=analysis["confidence"],
                buying_stage=analysis["buying_stage"],
                course_interest=analysis["course_interest"],
                objections=analysis["objections"],
                recommended_response=analysis["recommended_response"],
                next_action=analysis["next_action"],
            )
        )
        call = db.get(Call, state.call_id)
        if call:
            call.summary = self.whisper.merge_transcripts(state.chunks)
            call.sentiment_score = analysis["sentiment"]
            call.intent = analysis["lead_intent"]
            call.next_action = analysis["next_action"]
            call.status = "analyzing"
        return {"call_id": state.call_id, "transcript": transcription["text"], "analysis": analysis}

    def _handle_stop(self, db: Session, state: StreamState, organization_id: int | None) -> dict[str, Any]:
        call = db.get(Call, state.call_id) if state.call_id else None
        merged = self.whisper.merge_transcripts(state.chunks)
        if call:
            call.summary = merged
            call.status = "completed"
            lead = db.get(Lead, call.lead_id)
            if lead and call.intent == "high_intent":
                lead.status = LeadStatus.follow_up
                lead.sentiment_score = call.sentiment_score
        return {"call_id": state.call_id, "status": "completed", "transcript": merged}

    def retry_metadata(self, attempt: int) -> dict[str, Any]:
        retryable = attempt < settings.twilio_max_retries
        return {"attempt": attempt, "retryable": retryable, "delay_seconds": min(30, 2**attempt)}


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
