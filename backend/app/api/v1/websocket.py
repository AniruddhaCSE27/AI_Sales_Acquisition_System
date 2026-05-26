from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ai_service import AIService

router = APIRouter()


@router.websocket("/telecaller-assistant/{lead_id}")
async def telecaller_assistant(websocket: WebSocket, lead_id: int):
    await websocket.accept()
    assistant = AIService()
    await websocket.send_json({"type": "ready", "message": "AI assistant connected", "lead_id": lead_id})
    try:
        while True:
            payload = await websocket.receive_json()
            text = payload.get("text", "")
            await websocket.send_json({"type": "guidance", **assistant.live_call_guidance(text)})
    except WebSocketDisconnect:
        return

