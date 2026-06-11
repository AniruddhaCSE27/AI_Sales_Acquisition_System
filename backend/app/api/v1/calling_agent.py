from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.models import AICallSession, AuditLog, User
from app.schemas import CallingAgentRequest, CallingAgentSaveRequest, CallingAgentScriptResponse, CallingAgentSimulationResponse
from app.services.calling_agent_service import CallingAgentService

router = APIRouter()
service = CallingAgentService()


@router.post("/script", response_model=CallingAgentScriptResponse)
def generate_script(payload: CallingAgentRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    result = service.generate_script(payload)
    session = AICallSession(
        organization_id=user.organization_id,
        user_id=user.id,
        lead_name=payload.lead_name,
        phone_number=payload.phone_number,
        objective=payload.objective,
        product=payload.product,
        script=result["full_script"],
        status="script_generated",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {**result, "session_id": session.id}


@router.post("/simulate", response_model=CallingAgentSimulationResponse)
def simulate_call(payload: CallingAgentRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    result = service.simulate(payload)
    session = AICallSession(
        organization_id=user.organization_id,
        user_id=user.id,
        lead_name=payload.lead_name,
        phone_number=payload.phone_number,
        objective=payload.objective,
        product=payload.product,
        script=result["ai_agent_message"],
        simulation=str(result),
        status="simulated",
        summary=result["call_summary"],
        interest_level=result["interest_level"],
        sentiment=result["sentiment"],
        lead_score=result["lead_score"],
        objection=result["detected_objection"],
        suggested_response=result["ai_suggested_response"],
        next_action=result["next_best_action"],
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return {**result, "session_id": session.id}


@router.get("/status")
def voice_agent_status(_: User = Depends(current_user)):
    configured = service.twilio_configured()
    return {"twilio_configured": configured, "status": "connected" if configured else "not_configured"}


@router.post("/save-interaction")
def save_interaction(payload: CallingAgentSaveRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    session = AICallSession(
        organization_id=user.organization_id,
        user_id=user.id,
        lead_name=payload.lead_name,
        phone_number=payload.phone_number,
        objective=payload.objective,
        product=payload.product,
        script=payload.script,
        simulation=str(payload.simulation),
        status="saved",
        summary=payload.summary,
        interest_level=payload.interest_level,
        sentiment=payload.sentiment,
        lead_score=payload.lead_score,
        objection=payload.objection,
        suggested_response=payload.suggested_response,
        next_action=payload.next_action,
    )
    db.add(session)
    db.flush()
    db.add(
        AuditLog(
            organization_id=user.organization_id,
            user_id=user.id,
            action="ai.calling_agent.interaction_saved",
            entity_type="ai_call_session",
            entity_id=session.id,
            metadata_json={"lead_score": payload.lead_score, "objection": payload.objection},
        )
    )
    db.commit()
    return {"saved": True, "session_id": session.id, "message": "Interaction saved."}


@router.post("/start-call")
def start_real_call(payload: CallingAgentRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        result = service.start_real_call(payload)
    except ValueError as exc:
        db.add(
            AuditLog(
                organization_id=user.organization_id,
                user_id=user.id,
                action="ai.calling_agent.real_call_blocked",
                entity_type="ai_call_session",
                metadata_json={
                    "reason": str(exc),
                    "consent": payload.consent,
                    "phone_valid": service.valid_phone(payload.phone_number),
                },
            )
        )
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session = AICallSession(
        organization_id=user.organization_id,
        user_id=user.id,
        lead_name=payload.lead_name,
        phone_number=payload.phone_number,
        objective=payload.objective,
        product=payload.product,
        status=result["status"],
        summary=result["message"],
        twilio_sid=result["call_sid"],
    )
    db.add(session)
    db.flush()
    db.add(
        AuditLog(
            organization_id=user.organization_id,
            user_id=user.id,
            action="ai.calling_agent.real_call_attempt",
            entity_type="ai_call_session",
            entity_id=session.id,
            metadata_json={"status": result["status"], "consent": payload.consent, "phone_valid": True},
        )
    )
    db.commit()
    return {**result, "session_id": session.id}
