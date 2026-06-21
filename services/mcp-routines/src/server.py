import asyncio
import sys
import json
import logging
import os
from typing import Dict, Any, List
from pydantic import ValidationError

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, CallToolResult

# Import domain components
from src.database import SessionLocal
from src import mcp_server, schemas, auth

# Configure logging to write strictly to stderr so we don't corrupt stdout (used for stdio transport JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("memorybridge-mcp-server")

app = Server("memorybridge-routines-server")


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """
    List available tools and their schemas.
    Crucially, these schemas DO NOT expose the '_context' parameter to the LLM.
    This separates the model-controlled arguments from the trusted actor context.
    """
    return [
        Tool(
            name="get_user_preferences",
            description="Retrieve approved preferences for an assisted user.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the assisted user.",
                    }
                },
                "required": ["user_id"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="create_routine_draft",
            description="Create a new routine in draft state. Performs structural safety policy checks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "assisted_user_id": {
                        "type": "string",
                        "description": "The UUID of the assisted user.",
                    },
                    "title": {
                        "type": "string",
                        "maxLength": 255,
                        "description": "Routine title.",
                    },
                    "purpose": {
                        "type": "string",
                        "maxLength": 255,
                        "description": "Optional purpose statement.",
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "HH:MM format scheduled time.",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Target timezone (e.g. Europe/Sofia).",
                    },
                    "steps_json": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 5,
                        "description": "Steps of the routine (max 5).",
                    },
                    "risk_level": {
                        "type": "string",
                        "description": "Safety risk level (e.g. low, medium, prohibited).",
                    },
                    "safety_decision": {
                        "type": "string",
                        "description": "Safety evaluation decision.",
                    },
                },
                "required": [
                    "assisted_user_id",
                    "title",
                    "scheduled_time",
                    "timezone",
                    "steps_json",
                    "risk_level",
                    "safety_decision",
                ],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="approve_routine",
            description="Approve a routine draft. Enforces caregiver authorization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "routine_id": {
                        "type": "string",
                        "description": "The UUID of the routine draft.",
                    },
                    "caregiver_user_id": {
                        "type": "string",
                        "description": "The UUID of the approving caregiver.",
                    },
                },
                "required": ["routine_id", "caregiver_user_id"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_today_routines",
            description="Retrieve today's active routines for a user.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the user.",
                    }
                },
                "required": ["user_id"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="mark_routine_status",
            description="Mark a routine's status (completed, help_requested, missed).",
            inputSchema={
                "type": "object",
                "properties": {
                    "routine_id": {
                        "type": "string",
                        "description": "The UUID of the routine.",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["completed", "help_requested", "missed"],
                    },
                },
                "required": ["routine_id", "status"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="create_caregiver_alert",
            description="Create a caregiver alert for help requests or missed routines.",
            inputSchema={
                "type": "object",
                "properties": {
                    "assisted_user_id": {
                        "type": "string",
                        "description": "The UUID of the assisted user.",
                    },
                    "routine_id": {
                        "type": "string",
                        "description": "The UUID of the routine.",
                    },
                    "alert_type": {
                        "type": "string",
                        "description": "Type of alert (e.g. help_requested).",
                    },
                    "message": {
                        "type": "string",
                        "description": "Alert message content.",
                    },
                },
                "required": ["assisted_user_id", "routine_id", "alert_type", "message"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_approved_contacts",
            description="Retrieve approved contacts list for an assisted user.",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The UUID of the assisted user.",
                    }
                },
                "required": ["user_id"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_routine",
            description="Retrieve a single routine by ID. Enforces caregiver/user authorization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "routine_id": {
                        "type": "string",
                        "description": "The UUID of the routine.",
                    }
                },
                "required": ["routine_id"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="update_routine",
            description="Update routine details. Reruns deterministic safety checks and resets approval status on content changes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "routine_id": {
                        "type": "string",
                        "description": "The UUID of the routine.",
                    },
                    "updates": {
                        "type": "object",
                        "description": "Fields to update (title, steps_json, purpose, scheduled_time, timezone).",
                    }
                },
                "required": ["routine_id", "updates"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="reject_routine",
            description="Reject an unapproved routine draft. Enforces caregiver authorization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "routine_id": {
                        "type": "string",
                        "description": "The UUID of the routine draft.",
                    }
                },
                "required": ["routine_id"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="list_caregiver_routines",
            description="List routines belonging to the caregiver's approved assisted users.",
            inputSchema={
                "type": "object",
                "properties": {
                    "assisted_user_id": {
                        "type": "string",
                        "description": "Filter by assisted user UUID.",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by routine status.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return.",
                    },
                    "cursor": {
                        "type": "string",
                        "description": "Pagination cursor.",
                    }
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_audit_events",
            description="Retrieve redacted audit events for a correlation ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "correlation_id": {
                        "type": "string",
                        "description": "The correlation UUID.",
                    }
                },
                "required": ["correlation_id"],
                "additionalProperties": False,
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """
    Execute a tool call.
    Validates input arguments strictly against Pydantic models (configured to reject unknown fields),
    injects trusted context, and catches exceptions securely to prevent stack traces leaking to stdout.
    """
    # Extract context data from arguments (injected by gateway)
    context_data = arguments.pop("_context", None)
    if not context_data:
        # Check for fallback environment variables (useful for local development/testing)
        fallback_actor_id = os.environ.get("MCP_DEV_ACTOR_ID")
        fallback_role = os.environ.get("MCP_DEV_ACTOR_ROLE")
        fallback_correlation_id = os.environ.get(
            "MCP_DEV_CORRELATION_ID", "local-dev-corr"
        )
        if fallback_actor_id and fallback_role:
            context_data = {
                "actor_id": fallback_actor_id,
                "role": fallback_role,
                "correlation_id": fallback_correlation_id,
            }
        else:
            logger.error(
                "Attempted tool call without '_context' or fallback environment variables."
            )
            return CallToolResult(
                isError=True,
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "Unauthorized",
                                "message": "Missing trusted '_context' parameter.",
                            }
                        ),
                    )
                ],
            )

    try:
        context = schemas.ActorContext.model_validate(context_data)
    except ValidationError as e:
        logger.error(f"Failed to validate ActorContext: {e}")
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": "InvalidContext",
                            "message": "ActorContext validation failed.",
                            "details": e.errors(),
                        }
                    ),
                )
            ],
        )

    db = SessionLocal()
    try:
        if name == "get_user_preferences":
            req_pref = schemas.UserQueryRequest.model_validate(arguments)
            res = mcp_server.get_user_preferences(db, context, req_pref.user_id)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "create_routine_draft":
            req_draft = schemas.RoutineDraftRequest.model_validate(arguments)
            routine = mcp_server.create_routine_draft(db, context, req_draft)
            res = {
                "id": routine.id,
                "assisted_user_id": routine.assisted_user_id,
                "title": routine.title,
                "purpose": routine.purpose,
                "scheduled_time": routine.scheduled_time,
                "timezone": routine.timezone,
                "steps_json": routine.steps_json,
                "risk_level": routine.risk_level,
                "safety_decision": routine.safety_decision,
                "approval_status": routine.approval_status,
                "status": routine.status,
                "created_at": (
                    routine.created_at.isoformat() if routine.created_at else None
                ),
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "approve_routine":
            req_approve = schemas.RoutineApproveRequest.model_validate(arguments)
            routine = mcp_server.approve_routine(db, context, req_approve)
            res = {
                "id": routine.id,
                "status": routine.status,
                "approval_status": routine.approval_status,
                "approved_at": (
                    routine.approved_at.isoformat() if routine.approved_at else None
                ),
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "get_today_routines":
            req_today = schemas.UserQueryRequest.model_validate(arguments)
            routines = mcp_server.get_today_routines(db, context, req_today.user_id)
            res = [
                {
                    "id": r.id,
                    "title": r.title,
                    "purpose": r.purpose,
                    "scheduled_time": r.scheduled_time,
                    "timezone": r.timezone,
                    "steps_json": r.steps_json,
                    "status": r.status,
                }
                for r in routines
            ]
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "mark_routine_status":
            req_status = schemas.RoutineStatusUpdate.model_validate(arguments)
            routine = mcp_server.mark_routine_status(db, context, req_status)
            res = {
                "id": routine.id,
                "status": routine.status,
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "create_caregiver_alert":
            req_alert = schemas.CaregiverAlertRequest.model_validate(arguments)
            alerts = mcp_server.create_caregiver_alert(db, context, req_alert)
            res = [
                {
                    "id": a.id,
                    "caregiver_user_id": a.caregiver_user_id,
                    "message": a.message,
                    "status": a.status,
                }
                for a in alerts
            ]
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "get_approved_contacts":
            req_contacts = schemas.UserQueryRequest.model_validate(arguments)
            contacts = mcp_server.get_approved_contacts(
                db, context, req_contacts.user_id
            )
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(contacts))]
            )

        elif name == "get_routine":
            req_get = schemas.RoutineGetRequest.model_validate(arguments)
            routine = mcp_server.get_routine(db, context, req_get.routine_id)
            res = {
                "id": routine.id,
                "assisted_user_id": routine.assisted_user_id,
                "title": routine.title,
                "purpose": routine.purpose,
                "scheduled_time": routine.scheduled_time,
                "timezone": routine.timezone,
                "steps_json": routine.steps_json,
                "risk_level": routine.risk_level,
                "safety_decision": routine.safety_decision,
                "approval_status": routine.approval_status,
                "status": routine.status,
                "created_at": routine.created_at.isoformat() if routine.created_at else None,
                "approved_at": routine.approved_at.isoformat() if routine.approved_at else None,
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "update_routine":
            req_update = schemas.RoutineUpdateRequest.model_validate(arguments)
            routine = mcp_server.update_routine(db, context, req_update)
            res = {
                "id": routine.id,
                "assisted_user_id": routine.assisted_user_id,
                "title": routine.title,
                "purpose": routine.purpose,
                "scheduled_time": routine.scheduled_time,
                "timezone": routine.timezone,
                "steps_json": routine.steps_json,
                "risk_level": routine.risk_level,
                "safety_decision": routine.safety_decision,
                "approval_status": routine.approval_status,
                "status": routine.status,
                "created_at": routine.created_at.isoformat() if routine.created_at else None,
                "approved_at": routine.approved_at.isoformat() if routine.approved_at else None,
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "reject_routine":
            req_reject = schemas.RoutineRejectRequest.model_validate(arguments)
            routine = mcp_server.reject_routine(db, context, req_reject.routine_id)
            res = {
                "id": routine.id,
                "assisted_user_id": routine.assisted_user_id,
                "title": routine.title,
                "purpose": routine.purpose,
                "scheduled_time": routine.scheduled_time,
                "timezone": routine.timezone,
                "steps_json": routine.steps_json,
                "risk_level": routine.risk_level,
                "safety_decision": routine.safety_decision,
                "approval_status": routine.approval_status,
                "status": routine.status,
                "created_at": routine.created_at.isoformat() if routine.created_at else None,
                "approved_at": routine.approved_at.isoformat() if routine.approved_at else None,
            }
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "list_caregiver_routines":
            req_list = schemas.RoutineListRequest.model_validate(arguments)
            res = mcp_server.list_caregiver_routines(db, context, req_list)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        elif name == "get_audit_events":
            req_audit = schemas.AuditGetRequest.model_validate(arguments)
            res = mcp_server.get_audit_events(db, context, req_audit.correlation_id)
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(res))]
            )

        else:
            return CallToolResult(
                isError=True,
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(
                            {
                                "error": "MethodNotFound",
                                "message": f"Unknown tool: {name}",
                            }
                        ),
                    )
                ],
            )

    except ValidationError as e:
        logger.error(f"Validation error calling tool {name}: {e}")
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": "ValidationError",
                            "message": "Input validation failed.",
                            "details": e.errors(),
                        }
                    ),
                )
            ],
        )
    except auth.UnauthorizedError as e:
        logger.error(f"Authorization error calling tool {name}: {e}")
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({"error": "UnauthorizedError", "message": str(e)}),
                )
            ],
        )
    except ValueError as e:
        logger.error(f"Value error calling tool {name}: {e}")
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({"error": "ValueError", "message": str(e)}),
                )
            ],
        )
    except Exception as e:
        # Fail-closed, log to stderr, hide internal traces from the model/client
        logger.critical(f"Internal error executing tool {name}: {e}", exc_info=True)
        return CallToolResult(
            isError=True,
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "error": "InternalServerError",
                            "message": "An unexpected server error occurred.",
                        }
                    ),
                )
            ],
        )
    finally:
        db.close()


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
