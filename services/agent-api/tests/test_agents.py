import pytest
from src.memorybridge_agent.agents.providers import FakeProvider
from src.memorybridge_agent.agents.workflow import execute_interpret_workflow
from src.memorybridge_agent.dependencies import ActorContext

@pytest.mark.asyncio
async def test_workflow_successful_trajectory(mocker):
    # Mock the mcp_client call to avoid needing the real MCP server running during this unit test
    mock_mcp = mocker.patch("src.memorybridge_agent.agents.workflow.call_mcp_tool", return_value={"routine_id": "test-draft-123"})
    
    provider = FakeProvider(responses={
        "RoutinePlanOutput": {"title": "Water Plants", "steps": ["Fill can", "Water plants"], "scheduled_time": "10:00 AM", "missing_information": []},
        "SafetyReviewOutput": {"risk_level": "low", "safety_decision": "allow_for_review", "policy_reasons": ["Safe"]},
        "CommunicationOutput": {"visible_steps": ["Fill the can.", "Water the plants."], "help_text": "I am here if you need help."}
    })
    
    context = ActorContext(
        actor_id="cg-1",
        role="caregiver",
        caregiver_relationship_scope=["au-1"],
        authorization_scope="full",
        correlation_id="corr-1"
    )
    
    result = await execute_interpret_workflow("Water the plants at 10", "au-1", context, provider)
    
    assert result["draft_id"] == "test-draft-123"
    assert result["title"] == "Water Plants"
    assert result["safety_decision"] == "allow_for_review"
    assert len(result["visible_steps"]) == 2
    
    # Assert MCP was called securely
    mock_mcp.assert_called_once()
    args, kwargs = mock_mcp.call_args
    assert args[0] == "create_routine_draft"
    assert args[2] == context

@pytest.mark.asyncio
async def test_workflow_deterministic_rejection_precedence(mocker):
    mock_mcp = mocker.patch("src.memorybridge_agent.agents.workflow.call_mcp_tool", return_value={"routine_id": "test-draft-999"})
    
    provider = FakeProvider(responses={
        "RoutinePlanOutput": {"title": "Take Medication", "steps": ["Take pill"], "missing_information": []},
        # Even if semantic safety reviewer says allow, deterministic says no!
        # Actually the workflow edges should skip semantic reviewer entirely!
        "SafetyReviewOutput": {"risk_level": "low", "safety_decision": "allow_for_review", "policy_reasons": ["Should be blocked before here"]}
    })
    
    context = ActorContext(
        actor_id="cg-1", role="caregiver", caregiver_relationship_scope=["au-1"],
        authorization_scope="full", correlation_id="corr-1"
    )
    
    result = await execute_interpret_workflow("Take your medication", "au-1", context, provider)
    
    assert result["safety_decision"] == "reject_prohibited"
    assert result["visible_steps"] is None
    
    # MCP is still called to log the rejected draft
    mock_mcp.assert_called_once()
    payload = mock_mcp.call_args[0][1]
    assert payload["risk_level"] == "prohibited"
