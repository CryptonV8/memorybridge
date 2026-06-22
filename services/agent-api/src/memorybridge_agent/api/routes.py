from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from ..dependencies import ActorContext, get_actor_context

router = APIRouter(prefix="/api")

class CaregiverInputSchema(BaseModel):
    text: str = Field(..., max_length=500)
    assisted_user_id: str

class AgentDraftResponse(BaseModel):
    draft_id: str
    title: str
    scheduled_time: str
    steps: list[str]
    safety_decision: str
    policy_reasons: list[str]
    visible_steps: Optional[list[str]] = None
    help_text: Optional[str] = None

class ApproveRoutineInput(BaseModel):
    decision: str = Field(..., pattern="^approve$")

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/ready")
async def readiness_check():
    return {"status": "ready"}

@router.post("/routines/interpret", response_model=AgentDraftResponse)
async def interpret_routine(
    payload: CaregiverInputSchema,
    context: ActorContext = Depends(get_actor_context)
):
    from ..config import settings
    from ..agents.providers import BaseProvider, FakeProvider, GeminiProvider
    from ..agents.workflow import execute_interpret_workflow

    provider: BaseProvider
    if settings.agent_provider == "gemini":
        provider = GeminiProvider(api_key=settings.google_api_key, model=settings.memorybridge_model)
    else:
        is_meds = any(k in payload.text.lower() for k in ["medication", "pill", "dose", "tablet", "prescription"])
        provider = FakeProvider(responses={
            "RoutinePlanOutput": {
                "title": "Change medication" if is_meds else payload.text,
                "steps": ["Take an extra pill"] if is_meds else ["Take the watering can", "Water the plants near the window"],
                "scheduled_time": "08:00" if is_meds else "10:00",
                "missing_information": []
            },
            "SafetyReviewOutput": {
                "risk_level": "prohibited" if is_meds else "low",
                "safety_decision": "reject_prohibited" if is_meds else "allow_for_review",
                "policy_reasons": ["Medication routines cannot be managed automatically."] if is_meds else ["The routine is a familiar, low-risk household activity."]
            },
            "CommunicationOutput": {
                "visible_steps": ["Take pill."] if is_meds else ["Take the watering can.", "Water the plants near the window."],
                "help_text": "Press Help me if you would like support."
            }
        })
        
    result = await execute_interpret_workflow(payload.text, payload.assisted_user_id, context, provider)
    return AgentDraftResponse(**result)

@router.post("/routines/{routine_id}/approve")
async def approve_routine(
    routine_id: str,
    payload: ApproveRoutineInput,
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    
    # Strictly deterministic, no LLM invocation
    result = await call_mcp_tool(
        "approve_routine", 
        {"routine_id": routine_id, "caregiver_user_id": context.actor_id},
        context
    )
    return {"status": "active", "routine_id": routine_id}

@router.get("/users/{assisted_user_id}/today")
async def get_today_routines(
    assisted_user_id: str,
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    result = await call_mcp_tool(
        "get_today_routines",
        {"user_id": assisted_user_id},
        context
    )
    return result

@router.post("/routines/{routine_id}/status")
async def update_routine_status(
    routine_id: str,
    status: str,
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    result = await call_mcp_tool(
        "mark_routine_status",
        {"routine_id": routine_id, "status": status},
        context
    )
    return result

@router.get("/caregivers/me/alerts")
async def get_alerts(
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    result = await call_mcp_tool(
        "get_caregiver_alerts",
        {"caregiver_id": context.actor_id},
        context
    )
    return result

@router.get("/audit/{correlation_id}")
async def get_audit(
    correlation_id: str,
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    result = await call_mcp_tool(
        "get_audit_events",
        {"correlation_id": correlation_id},
        context
    )
    return result


class UpdateRoutineInput(BaseModel):
    title: Optional[str] = None
    steps_json: Optional[List[str]] = None
    purpose: Optional[str] = None
    scheduled_time: Optional[str] = None
    timezone: Optional[str] = None


@router.get("/routines/{routine_id}")
async def get_routine(
    routine_id: str,
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    result = await call_mcp_tool(
        "get_routine",
        {"routine_id": routine_id},
        context
    )
    return result


@router.patch("/routines/{routine_id}")
async def update_routine(
    routine_id: str,
    payload: UpdateRoutineInput,
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    updates: dict[str, Any] = {}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.steps_json is not None:
        updates["steps_json"] = payload.steps_json
    if payload.purpose is not None:
        updates["purpose"] = payload.purpose
    if payload.scheduled_time is not None:
        updates["scheduled_time"] = payload.scheduled_time
    if payload.timezone is not None:
        updates["timezone"] = payload.timezone

    result = await call_mcp_tool(
        "update_routine",
        {"routine_id": routine_id, "updates": updates},
        context
    )
    return result


@router.post("/routines/{routine_id}/reject")
async def reject_routine(
    routine_id: str,
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    result = await call_mcp_tool(
        "reject_routine",
        {"routine_id": routine_id},
        context
    )
    return {"status": "rejected", "routine_id": routine_id}


@router.get("/caregivers/me/routines")
async def list_caregiver_routines(
    assisted_user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
    context: ActorContext = Depends(get_actor_context)
):
    from ..mcp_client import call_mcp_tool
    result = await call_mcp_tool(
        "list_caregiver_routines",
        {
            "assisted_user_id": assisted_user_id,
            "status": status,
            "limit": limit,
            "cursor": cursor
        },
        context
    )
    return result
