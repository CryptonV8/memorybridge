import sys
from os.path import abspath, dirname

sys.path.insert(0, dirname(dirname(abspath(__file__))))

import pytest
from pydantic import ValidationError

from src.models import User, CaregiverRelationship, Routine, AuditEvent
from src import mcp_server, schemas, auth, safety


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
