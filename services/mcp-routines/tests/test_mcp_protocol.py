import os
import sys
import json
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent
from sqlalchemy.orm import Session
from src import models

# Configure StdioServerParameters to launch our src/server.py script
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
server_py_path = os.path.join(project_root, "src", "server.py")

# Ensure the subprocess has the same python path and database settings
server_params = StdioServerParameters(
    command=sys.executable,
    args=[server_py_path],
    env={**os.environ, "DATABASE_URL": os.environ.get("TEST_DATABASE_URL", "")},
)


def get_text_content(result) -> str:
    content = result.content[0]
    assert isinstance(content, TextContent)
    return content.text


@pytest.fixture
def seed_test_data(db_session: Session):
    """Seed data required for the protocol tests inside the active postgres transaction."""
    cg = models.User(id="cg-proto-1", display_name="Anna Petrova", role="caregiver")
    au = models.User(
        id="au-proto-1", display_name="Maria Petrova", role="assisted_user"
    )
    rel = models.CaregiverRelationship(
        caregiver_user_id=cg.id, assisted_user_id=au.id, status="active"
    )
    profile = models.AssistedUserProfile(
        user_id=au.id,
        preferred_name="Maria",
        approved_preferences_json={"approved_contacts": ["Anna Petrova"]},
    )
    db_session.add_all([cg, au, rel, profile])
    db_session.commit()
    return {"cg": cg, "au": au}


@pytest.mark.anyio
async def test_mcp_protocol_lifecycle(seed_test_data, db_session: Session):
    """Test the complete MCP server protocol cycle using a real client over stdio."""
    # 1. Initialize a session
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 2. List tools
            tools_result = await session.list_tools()
            tool_names = [tool.name for tool in tools_result.tools]

            # 3. Validate published tool names (append_audit_event must NOT be exposed)
            expected_tools = {
                "get_user_preferences",
                "create_routine_draft",
                "approve_routine",
                "get_today_routines",
                "mark_routine_status",
                "create_caregiver_alert",
                "get_approved_contacts",
            }
            for name in expected_tools:
                assert name in tool_names
            assert "append_audit_event" not in tool_names

            # 4. Inspect their schemas (e.g. no _context field in list schema, additionalProperties=False)
            draft_tool = next(
                t for t in tools_result.tools if t.name == "create_routine_draft"
            )
            schema = draft_tool.inputSchema
            assert schema["type"] == "object"
            assert "_context" not in schema["properties"]
            assert schema["additionalProperties"] is False

            # 5. Call a safe read tool (get_approved_contacts) with trusted context
            read_result = await session.call_tool(
                "get_approved_contacts",
                {
                    "user_id": "au-proto-1",
                    "_context": {
                        "actor_id": "cg-proto-1",
                        "role": "caregiver",
                        "correlation_id": "corr-get-contacts",
                    },
                },
            )
            assert not read_result.isError
            contacts = json.loads(get_text_content(read_result))
            assert "Anna Petrova" in contacts

            # 6. Call create_routine_draft in an isolated transaction
            draft_result = await session.call_tool(
                "create_routine_draft",
                {
                    "assisted_user_id": "au-proto-1",
                    "title": "Water plants",
                    "purpose": "Morning chore",
                    "scheduled_time": "10:00",
                    "timezone": "Europe/Sofia",
                    "steps_json": ["Go near the window", "Water the plants"],
                    "risk_level": "low",
                    "safety_decision": "allow_for_review",
                    "_context": {
                        "actor_id": "cg-proto-1",
                        "role": "caregiver",
                        "correlation_id": "corr-create-draft",
                    },
                },
            )
            assert not draft_result.isError
            draft_data = json.loads(get_text_content(draft_result))
            assert draft_data["status"] == "draft"
            routine_id = draft_data["id"]

            # 7. Verify prohibited input is rejected (medication safety rule)
            prohibited_result = await session.call_tool(
                "create_routine_draft",
                {
                    "assisted_user_id": "au-proto-1",
                    "title": "Take extra medication",
                    "purpose": "Pills",
                    "scheduled_time": "11:00",
                    "timezone": "Europe/Sofia",
                    "steps_json": ["Double the dose"],
                    "risk_level": "low",
                    "safety_decision": "allow_for_review",
                    "_context": {
                        "actor_id": "cg-proto-1",
                        "role": "caregiver",
                        "correlation_id": "corr-prohibited",
                    },
                },
            )
            assert not prohibited_result.isError
            prohibited_data = json.loads(get_text_content(prohibited_result))
            assert prohibited_data["status"] == "rejected"

            # 8. Verify unauthorized approval is rejected (caregiver without relationship)
            unauth_result = await session.call_tool(
                "approve_routine",
                {
                    "routine_id": routine_id,
                    "caregiver_user_id": "random-caregiver-id",
                    "_context": {
                        "actor_id": "random-caregiver-id",
                        "role": "caregiver",
                        "correlation_id": "corr-unauth",
                    },
                },
            )
            assert unauth_result.isError
            unauth_data = json.loads(get_text_content(unauth_result))
            assert unauth_data["error"] == "UnauthorizedError"

            # 9. Verify no tool can activate a routine without approval (try to complete draft)
            activate_result = await session.call_tool(
                "mark_routine_status",
                {
                    "routine_id": routine_id,
                    "status": "completed",
                    "_context": {
                        "actor_id": "cg-proto-1",
                        "role": "caregiver",
                        "correlation_id": "corr-activate",
                    },
                },
            )
            assert activate_result.isError
            activate_data = json.loads(get_text_content(activate_result))
            assert "Cannot transition" in activate_data["message"]

            # 10. Verify protocol errors do not leak stack traces or credentials (validation error)
            error_result = await session.call_tool(
                "create_routine_draft",
                {
                    "assisted_user_id": "au-proto-1",
                    "title": "Invalid fields",
                    "scheduled_time": "10:00",
                    "timezone": "Europe/Sofia",
                    "steps_json": ["Step 1"],
                    "risk_level": "low",
                    "safety_decision": "allow_for_review",
                    "unsupported_extra_field": "malicious-input",
                    "_context": {
                        "actor_id": "cg-proto-1",
                        "role": "caregiver",
                        "correlation_id": "corr-validation-fail",
                    },
                },
            )
            assert error_result.isError
            error_data = json.loads(get_text_content(error_result))
            assert error_data["error"] == "ValidationError"
            assert "unsupported_extra_field" in get_text_content(error_result)
            assert "Traceback" not in get_text_content(error_result)
