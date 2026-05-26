from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db.session import SessionLocal
from app.models import Lead
from app.services.objection_service import ObjectionDetectionService
from app.services.twilio_stream import TwilioStreamService

router = APIRouter()
stream_service = TwilioStreamService()
objection_service = ObjectionDetectionService()


@router.websocket("/telecaller-copilot/{lead_id}")
async def telecaller_copilot(websocket: WebSocket, lead_id: int):
    await websocket.accept()
    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        await websocket.send_json(
            {
                "type": "ready",
                "lead_id": lead_id,
                "lead_score": getattr(lead, "lead_score", 0),
                "intent": "unknown",
                "sentiment": getattr(lead, "sentiment_score", 0),
                "recommendations": ["Confirm course interest", "Ask timeline", "Offer counsellor slot"],
            }
        )
    try:
        while True:
            payload = await websocket.receive_json()
            text = payload.get("text") or payload.get("transcript") or ""
            objections = objection_service.detect(text)
            await websocket.send_json(
                {
                    "type": "copilot_update",
                    "lead_id": lead_id,
                    "sentiment": 0.75 if "interested" in text.lower() else 0.35,
                    "intent": "high_intent" if "admission" in text.lower() or "apply" in text.lower() else "needs_nurture",
                    "objections": objections,
                    "suggested_script": objections[0]["recommended_response"] if objections else "Ask one qualifying question and confirm next step.",
                    "next_best_action": objections[0]["next_action"] if objections else "Schedule follow-up.",
                }
            )
    except WebSocketDisconnect:
        return


@router.websocket("/twilio/media")
async def twilio_media_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            payload = await websocket.receive_json()
            with SessionLocal() as db:
                result = await stream_service.process_event(db, payload)
            await websocket.send_json({"type": "processed", **result})
    except WebSocketDisconnect:
        return
