import pytest
from fastapi.testclient import TestClient
from src.memorybridge_agent.main import app

client = TestClient(app)

@pytest.fixture
def mock_call_mcp(mocker):
    return mocker.patch("src.memorybridge_agent.mcp_client.call_mcp_tool")


def test_root_health_and_readiness():
    # Test root endpoints
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json() == {"status": "ok"}

    r_ready = client.get("/ready")
    assert r_ready.status_code == 200
    assert r_ready.json() == {"status": "ready"}

    # Test api prefix endpoints
    r_api_health = client.get("/api/health")
    assert r_api_health.status_code == 200
    assert r_api_health.json() == {"status": "ok"}

    r_api_ready = client.get("/api/ready")
    assert r_api_ready.status_code == 200
    assert r_api_ready.json() == {"status": "ready"}


def test_auth_missing_or_invalid():
    r = client.get("/api/routines/r-123")
    assert r.status_code in [401, 403]  # HTTPBearer returns 401 or 403
    
    headers = {"Authorization": "Bearer bad_token"}
    r = client.get("/api/routines/r-123", headers=headers)
    assert r.status_code == 401  # Invalid token returns 401 Unauthorized


def test_get_routine_success(mock_call_mcp):
    mock_call_mcp.return_value = {
        "id": "r-123",
        "assisted_user_id": "au-456",
        "title": "Water Plants",
        "status": "draft"
    }

    headers = {"Authorization": "Bearer caregiver_demo_token"}
    r = client.get("/api/routines/r-123", headers=headers)
    
    assert r.status_code == 200
    assert r.json()["title"] == "Water Plants"
    
    # Assert MCP call parameters
    mock_call_mcp.assert_called_once()
    args, kwargs = mock_call_mcp.call_args
    assert args[0] == "get_routine"
    assert args[1]["routine_id"] == "r-123"
    # Ensure trusted ActorContext contains correct caregiver actor_id
    assert args[2].actor_id == "cg-123"


def test_update_routine_patch(mock_call_mcp):
    mock_call_mcp.return_value = {
        "id": "r-123",
        "title": "New Title",
        "status": "draft"
    }

    headers = {"Authorization": "Bearer caregiver_demo_token"}
    payload = {"title": "New Title", "steps_json": ["Step 1"]}
    r = client.patch("/api/routines/r-123", json=payload, headers=headers)

    assert r.status_code == 200
    assert r.json()["title"] == "New Title"

    mock_call_mcp.assert_called_once()
    args, kwargs = mock_call_mcp.call_args
    assert args[0] == "update_routine"
    assert args[1]["routine_id"] == "r-123"
    assert args[1]["updates"]["title"] == "New Title"
    assert args[1]["updates"]["steps_json"] == ["Step 1"]


def test_reject_routine_post(mock_call_mcp):
    mock_call_mcp.return_value = {
        "id": "r-123",
        "status": "rejected"
    }

    headers = {"Authorization": "Bearer caregiver_demo_token"}
    r = client.post("/api/routines/r-123/reject", headers=headers)

    assert r.status_code == 200
    assert r.json()["status"] == "rejected"

    mock_call_mcp.assert_called_once()
    args, kwargs = mock_call_mcp.call_args
    assert args[0] == "reject_routine"
    assert args[1]["routine_id"] == "r-123"


def test_list_caregiver_routines(mock_call_mcp):
    mock_call_mcp.return_value = {
        "routines": [{"id": "r-123", "title": "Water Plants"}]
    }

    headers = {"Authorization": "Bearer caregiver_demo_token"}
    r = client.get("/api/caregivers/me/routines?status=draft&assisted_user_id=au-456", headers=headers)

    assert r.status_code == 200
    assert len(r.json()["routines"]) == 1

    mock_call_mcp.assert_called_once()
    args, kwargs = mock_call_mcp.call_args
    assert args[0] == "list_caregiver_routines"
    assert args[1]["status"] == "draft"
    assert args[1]["assisted_user_id"] == "au-456"


def test_zero_llm_calls_on_rejection_and_approval(mock_call_mcp, mocker):
    # Mock LLM provider to ensure it's not even instantiated or called
    mock_provider = mocker.patch("src.memorybridge_agent.agents.providers.FakeProvider.generate_structured")
    
    headers = {"Authorization": "Bearer caregiver_demo_token"}
    
    # Call approve
    mock_call_mcp.return_value = {"status": "active"}
    r_approve = client.post("/api/routines/r-123/approve", json={"decision": "approve"}, headers=headers)
    assert r_approve.status_code == 200

    # Call reject
    mock_call_mcp.return_value = {"status": "rejected"}
    r_reject = client.post("/api/routines/r-123/reject", headers=headers)
    assert r_reject.status_code == 200

    # Ensure no LLM methods were called
    mock_provider.assert_not_called()
