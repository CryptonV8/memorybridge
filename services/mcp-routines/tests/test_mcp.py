import sys
from os.path import abspath, dirname

sys.path.insert(0, dirname(dirname(abspath(__file__))))

import pytest
from pydantic import ValidationError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.models import User, CaregiverRelationship, Routine, AuditEvent, CaregiverAlert

from src import mcp_server, schemas, auth, safety


@pytest.fixture(scope="function")
def db_session():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def setup_users(db_session):
    cg = User(id="cg1", display_name="Caregiver", role="caregiver")
    au = User(id="au1", display_name="Assisted User", role="assisted_user")
    rel = CaregiverRelationship(
        caregiver_user_id=cg.id, assisted_user_id=au.id, status="active"
    )
    db_session.add_all([cg, au, rel])
    db_session.commit()
    return {"cg": cg, "au": au}


# --- Schema Validation ---
def test_schema_reject_unknown_fields():
    with pytest.raises(ValidationError):
        schemas.RoutineDraftRequest(
            assisted_user_id="au1",
            title="test",
            scheduled_time="10:00",
            timezone="UTC",
            steps_json=["step"],
            risk_level="low",
            safety_decision="allow_for_review",
            unknown_field="bad",  # Unknown field
        )


def test_schema_reject_empty_steps():
    with pytest.raises(ValidationError):
        schemas.RoutineDraftRequest(
            assisted_user_id="au1",
            title="test",
            scheduled_time="10:00",
            timezone="UTC",
            steps_json=[" "],  # Empty step
            risk_level="low",
            safety_decision="allow_for_review",
        )


def test_schema_reject_too_many_steps():
    with pytest.raises(ValidationError):
        schemas.RoutineDraftRequest(
            assisted_user_id="au1",
            title="test",
            scheduled_time="10:00",
            timezone="UTC",
            steps_json=["1", "2", "3", "4", "5", "6"],  # > 5 steps
            risk_level="low",
            safety_decision="allow_for_review",
        )


# --- Safety Policy ---
def test_safety_policy_medication():
    res = safety.check_structural_policy("Take medication", ["take pill"])
    assert res.decision == schemas.SafetyDecision.reject_prohibited
    assert "medication" in res.matched_rules


def test_safety_policy_finance():
    res = safety.check_structural_policy("Buy groceries", ["use credit card to pay"])
    assert res.decision == schemas.SafetyDecision.reject_prohibited
    assert "finance" in res.matched_rules


def test_safety_policy_door():
    res = safety.check_structural_policy("Guests", ["unlock the door"])
    assert res.decision == schemas.SafetyDecision.reject_prohibited
    assert "doors" in res.matched_rules


def test_safety_policy_disguised():
    res = safety.check_structural_policy(
        "Help me with my prescription", ["take the tablet from the kitchen"]
    )
    assert res.decision == schemas.SafetyDecision.reject_prohibited


def test_safety_policy_low_risk():
    res = safety.check_structural_policy(
        "Water plants", ["take watering can", "water plants"]
    )
    assert res.decision == schemas.SafetyDecision.allow_for_review


# --- Authorization & Bypass Prevention ---
def test_draft_cannot_become_active_through_create(db_session, setup_users):
    ctx = schemas.ActorContext(
        actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c1"
    )
    req = schemas.RoutineDraftRequest(
        assisted_user_id="au1",
        title="Safe routine",
        scheduled_time="10:00",
        timezone="UTC",
        steps_json=["step"],
        risk_level="low",
        safety_decision="allow_for_review",
    )
    routine = mcp_server.create_routine_draft(db_session, ctx, req)
    assert routine.status == "draft"  # Must be draft

    # Audit log check
    audit = (
        db_session.query(AuditEvent).filter_by(tool_name="create_routine_draft").first()
    )
    assert audit is not None
    assert audit.decision == "allow_for_review"


def test_approval_by_unrelated_caregiver(db_session, setup_users):
    unrelated_cg = User(id="cg2", display_name="Other CG", role="caregiver")
    db_session.add(unrelated_cg)
    db_session.commit()

    routine = Routine(
        id="r1",
        assisted_user_id="au1",
        created_by="cg1",
        title="test",
        scheduled_time="10",
        timezone="UTC",
        steps_json=["s1"],
        risk_level="low",
        safety_decision="allow_for_review",
    )
    db_session.add(routine)
    db_session.commit()

    ctx = schemas.ActorContext(
        actor_id="cg2", role=schemas.Role.caregiver, correlation_id="c1"
    )
    with pytest.raises(auth.UnauthorizedError):
        mcp_server.approve_routine(
            db_session,
            ctx,
            schemas.RoutineApproveRequest(routine_id="r1", caregiver_user_id="cg2"),
        )


def test_approval_by_assisted_user(db_session, setup_users):
    routine = Routine(
        id="r1",
        assisted_user_id="au1",
        created_by="cg1",
        title="test",
        scheduled_time="10",
        timezone="UTC",
        steps_json=["s1"],
        risk_level="low",
        safety_decision="allow_for_review",
    )
    db_session.add(routine)
    db_session.commit()

    ctx = schemas.ActorContext(
        actor_id="au1", role=schemas.Role.assisted_user, correlation_id="c1"
    )
    with pytest.raises(auth.UnauthorizedError):
        mcp_server.approve_routine(
            db_session,
            ctx,
            schemas.RoutineApproveRequest(routine_id="r1", caregiver_user_id="cg1"),
        )


def test_approval_prohibited_routine(db_session, setup_users):
    routine = Routine(
        id="r1",
        assisted_user_id="au1",
        created_by="cg1",
        title="test",
        scheduled_time="10",
        timezone="UTC",
        steps_json=["s1"],
        risk_level="prohibited",
        safety_decision="reject_prohibited",
    )
    db_session.add(routine)
    db_session.commit()

    ctx = schemas.ActorContext(
        actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c1"
    )
    with pytest.raises(ValueError, match="allow_for_review"):
        mcp_server.approve_routine(
            db_session,
            ctx,
            schemas.RoutineApproveRequest(routine_id="r1", caregiver_user_id="cg1"),
        )


def test_atomic_approval_and_audit(db_session, setup_users, monkeypatch):
    routine = Routine(
        id="r1",
        assisted_user_id="au1",
        created_by="cg1",
        title="test",
        scheduled_time="10",
        timezone="UTC",
        steps_json=["s1"],
        risk_level="low",
        safety_decision="allow_for_review",
        status="draft",
        approval_status="pending",
    )
    db_session.add(routine)
    db_session.commit()

    ctx = schemas.ActorContext(
        actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c1"
    )

    # Mock append_audit_event to fail
    def mock_append(*args, **kwargs):
        raise RuntimeError("Audit failed")

    monkeypatch.setattr(mcp_server, "append_audit_event", mock_append)

    with pytest.raises(RuntimeError):
        mcp_server.approve_routine(
            db_session,
            ctx,
            schemas.RoutineApproveRequest(routine_id="r1", caregiver_user_id="cg1"),
        )

    db_session.rollback()  # Normally the caller handles rollback on exception

    # Routine status must not be active
    r_check = db_session.query(Routine).first()
    assert r_check.status == "draft"


# --- Alerts & Timezone ---
def test_create_caregiver_alert_deduplication(db_session, setup_users):
    routine = Routine(
        id="r1",
        assisted_user_id="au1",
        created_by="cg1",
        title="test",
        scheduled_time="10",
        timezone="Europe/Sofia",
        steps_json=["s1"],
        risk_level="low",
        safety_decision="allow_for_review",
        status="active",
    )
    db_session.add(routine)
    db_session.commit()

    ctx = schemas.ActorContext(
        actor_id="au1", role=schemas.Role.assisted_user, correlation_id="c1"
    )
    req = schemas.CaregiverAlertRequest(
        assisted_user_id="au1",
        routine_id="r1",
        alert_type="help_requested",
        message="Help",
    )

    # First alert
    alerts1 = mcp_server.create_caregiver_alert(db_session, ctx, req)
    assert len(alerts1) == 1

    # Second alert should be deduplicated (no new alert created if unread exists)
    alerts2 = mcp_server.create_caregiver_alert(db_session, ctx, req)
    assert len(alerts2) == 0

    # Audit log should show 1 allowed, maybe we didn't log the second or we logged it as 0 count
    audit = (
        db_session.query(AuditEvent)
        .filter_by(tool_name="create_caregiver_alert")
        .first()
    )
    assert audit is not None


def test_get_routine_authorization(db_session, setup_users):
    # Setup a draft routine
    routine = Routine(
        id="r-get-1",
        assisted_user_id="au1",
        created_by="cg1",
        title="Get test",
        scheduled_time="12:00",
        timezone="UTC",
        steps_json=["step"],
        risk_level="low",
        safety_decision="allow_for_review",
        status="draft",
        approval_status="pending",
    )
    db_session.add(routine)
    db_session.commit()

    # Authorized caregiver
    ctx_cg = schemas.ActorContext(actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c-get")
    res = mcp_server.get_routine(db_session, ctx_cg, "r-get-1")
    assert res.title == "Get test"

    # Authorized assisted user
    ctx_au = schemas.ActorContext(actor_id="au1", role=schemas.Role.assisted_user, correlation_id="c-get")
    res = mcp_server.get_routine(db_session, ctx_au, "r-get-1")
    assert res.title == "Get test"

    # Unauthorized caregiver
    other_cg = User(id="cg_other", display_name="Other Caregiver", role="caregiver")
    db_session.add(other_cg)
    db_session.commit()
    ctx_other = schemas.ActorContext(actor_id="cg_other", role=schemas.Role.caregiver, correlation_id="c-get")
    with pytest.raises(auth.UnauthorizedError):
        mcp_server.get_routine(db_session, ctx_other, "r-get-1")


def test_update_routine_validation_and_reclassification(db_session, setup_users):
    routine = Routine(
        id="r-up-1",
        assisted_user_id="au1",
        created_by="cg1",
        title="Water Plants",
        scheduled_time="12:00",
        timezone="UTC",
        steps_json=["step"],
        risk_level="low",
        safety_decision="allow_for_review",
        status="draft",
        approval_status="pending",
    )
    db_session.add(routine)
    db_session.commit()

    ctx = schemas.ActorContext(actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c-up")

    # Update non-content field: timezone
    req = schemas.RoutineUpdateRequest(routine_id="r-up-1", updates={"timezone": "EST"})
    res = mcp_server.update_routine(db_session, ctx, req)
    assert res.timezone == "EST"
    assert res.safety_decision == "allow_for_review" # preserved

    # Update content field to safe: title
    req = schemas.RoutineUpdateRequest(routine_id="r-up-1", updates={"title": "Mow Lawn"})
    res = mcp_server.update_routine(db_session, ctx, req)
    assert res.title == "Mow Lawn"
    assert res.safety_decision == "allow_for_review" # resets to low-risk draft

    # Update content field to prohibited: title
    req = schemas.RoutineUpdateRequest(routine_id="r-up-1", updates={"title": "Take Medication"})
    res = mcp_server.update_routine(db_session, ctx, req)
    assert res.title == "Take Medication"
    assert res.safety_decision == "reject_prohibited" # reclassified
    assert res.status == "rejected"

    # Try updating a rejected routine: should fail
    req = schemas.RoutineUpdateRequest(routine_id="r-up-1", updates={"title": "Safe again"})
    with pytest.raises(ValueError):
        mcp_server.update_routine(db_session, ctx, req)


def test_reject_routine_idempotence(db_session, setup_users):
    routine = Routine(
        id="r-rej-1",
        assisted_user_id="au1",
        created_by="cg1",
        title="Safe routine",
        scheduled_time="12:00",
        timezone="UTC",
        steps_json=["step"],
        risk_level="low",
        safety_decision="allow_for_review",
        status="draft",
        approval_status="pending",
    )
    db_session.add(routine)
    db_session.commit()

    ctx = schemas.ActorContext(actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c-rej")

    # First rejection
    res = mcp_server.reject_routine(db_session, ctx, "r-rej-1")
    assert res.status == "rejected"
    assert res.approval_status == "rejected"

    # Second rejection (idempotent check)
    res2 = mcp_server.reject_routine(db_session, ctx, "r-rej-1")
    assert res2.status == "rejected"


def test_list_caregiver_routines(db_session, setup_users):
    # Create another routine for au1
    r2 = Routine(
        id="r-list-2",
        assisted_user_id="au1",
        created_by="cg1",
        title="Another Routine",
        scheduled_time="13:00",
        timezone="UTC",
        steps_json=["step"],
        risk_level="low",
        safety_decision="allow_for_review",
        status="draft",
        approval_status="pending",
    )
    db_session.add(r2)
    db_session.commit()

    ctx = schemas.ActorContext(actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c-list")
    req = schemas.RoutineListRequest(status="draft")
    res = mcp_server.list_caregiver_routines(db_session, ctx, req)
    assert len(res["routines"]) >= 1


def test_get_audit_events_redaction(db_session, setup_users):
    # Log an audit event with sensitive data
    event = AuditEvent(
        correlation_id="c-audit-test",
        actor_id="cg1",
        tool_name="create_routine_draft",
        event_type="routine_created",
        decision="allow_for_review",
        metadata_json={
            "routine_id": "r-audit-123",
            "internal_prompt": "secret instructions...",
            "risk_level": "low"
        }
    )
    db_session.add(event)
    db_session.commit()

    ctx = schemas.ActorContext(actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c-audit-test")
    res = mcp_server.get_audit_events(db_session, ctx, "c-audit-test")
    assert len(res) == 1
    # Verify sensitive field redacted
    assert "internal_prompt" not in res[0]["metadata"]
    assert res[0]["metadata"]["routine_id"] == "r-audit-123"


def test_get_caregiver_alerts(db_session, setup_users):
    # Setup alert
    alert = CaregiverAlert(
        id="alert-test-1",
        assisted_user_id="au1",
        caregiver_user_id="cg1",
        routine_id="r1",
        alert_type="help_requested",
        priority="high",
        message="Emergency assistance requested",
        status="unread",
    )
    db_session.add(alert)
    db_session.commit()

    ctx_cg = schemas.ActorContext(actor_id="cg1", role=schemas.Role.caregiver, correlation_id="c-alert")
    res = mcp_server.get_caregiver_alerts(db_session, ctx_cg, "cg1")
    assert len(res) == 1
    assert res[0]["id"] == "alert-test-1"
    assert res[0]["priority"] == "high"
    assert res[0]["message"] == "Emergency assistance requested"

    # Unauthorized access check
    ctx_other = schemas.ActorContext(actor_id="cg_other", role=schemas.Role.caregiver, correlation_id="c-alert")
    with pytest.raises(auth.UnauthorizedError):
        mcp_server.get_caregiver_alerts(db_session, ctx_other, "cg1")


