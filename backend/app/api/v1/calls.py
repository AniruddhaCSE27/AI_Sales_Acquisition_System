from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.db.session import get_db
from app.models import Call, CallTranscript, Lead, User
from app.schemas import CallCreate, CallRead
from app.services.ai_service import AIService
from app.services.call_intelligence_service import CallIntelligenceService
from app.services.twilio_service import TwilioService
from app.services.twilio_stream import TwilioStreamService
from app.services.whatsapp_service import WhatsAppAutomationService
from app.core.config import settings

router = APIRouter()
stream_service = TwilioStreamService()


@router.post("/click-to-call", response_model=CallRead)
def click_to_call(payload: CallCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    twilio = TwilioService().start_streaming_call(lead.phone, lead.id)
    call = Call(organization_id=user.organization_id or lead.organization_id, lead_id=lead.id, user_id=payload.user_id or user.id, twilio_sid=twilio["call_sid"], status="initiated", metadata_json=twilio)
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@router.post("/simulate-stream/{lead_id}")
async def simulate_stream(lead_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    start = await stream_service.process_event(db, {"event": "start", "streamSid": f"sim-{lead_id}", "start": {"callSid": f"sim-call-{lead_id}", "customParameters": {"lead_id": str(lead_id)}}}, user.organization_id)
    media = await stream_service.process_event(db, {"event": "media", "streamSid": f"sim-{lead_id}", "sequenceNumber": 1, "media": {"payload": "Lead is interested in MBA admission but says fees too high and parents decide."}}, user.organization_id)
    stop = await stream_service.process_event(db, {"event": "stop", "streamSid": f"sim-{lead_id}", "sequenceNumber": 2}, user.organization_id)
    whatsapp = WhatsAppAutomationService().send(lead.phone, "scholarship", {"name": lead.name, "course": lead.course_interest or "your course"})
    return {"start": start, "media": media, "stop": stop, "whatsapp": whatsapp}


@router.post("/{call_id}/transcript")
def add_transcript(call_id: int, transcript: str, db: Session = Depends(get_db), _: User = Depends(current_user)):
    call = db.get(Call, call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    analysis = CallIntelligenceService().analyze_transcript(transcript)
    call.summary = analysis["summary"]
    call.sentiment_score = analysis["sentiment_score"]
    call.intent = analysis["intent"]
    call.next_action = analysis["next_action"]
    db.add(CallTranscript(call_id=call_id, transcript=transcript, analysis=analysis))
    db.commit()
    return analysis


@router.post("/twilio/status")
async def twilio_status(request: Request):
    form = await request.form()
    return {"received": True, "call_sid": form.get("CallSid"), "status": form.get("CallStatus")}


@router.post("/twilio/voice")
async def twilio_voice(request: Request):
    ws_url = settings.public_base_url.replace("http://", "ws://").replace("https://", "wss://") + settings.twilio_stream_path
    return Response(content=stream_service.voice_stream_response(ws_url), media_type="application/xml")


@router.post("/twilio/recording")
async def twilio_recording(request: Request):
    form = await request.form()
    return {"received": True, "recording_url": form.get("RecordingUrl")}
