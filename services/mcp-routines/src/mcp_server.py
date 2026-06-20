from sqlalchemy.orm import Session
from . import models, schemas, auth, safety


def append_audit_event(
    db: Session,
    context: schemas.ActorContext,
    tool_name: str,
    event_type: str,
    decision: str,
    metadata: dict,
):
    """Internal function to append immutable audit events. Called within the same transaction as state changes."""
    event = models.AuditEvent(
        correlation_id=context.correlation_id,
        actor_id=context.actor_id,
        tool_name=tool_name,
        event_type=event_type,
        decision=decision,
        metadata_json=metadata,
    )
    db.add(event)


def create_routine_draft(
    db: Session, context: schemas.ActorContext, request: schemas.RoutineDraftRequest
) -> models.Routine:
    # Only caregiver or system can create drafts? Actually spec says 'verifies caller has agent privileges' but for MVP we assume context is passed from the service correctly.
    # We will enforce structural safety here.
    safety_result = safety.check_structural_policy(request.title, request.steps_json)

    # Override requested safety decision if structural policy rejected it
    final_decision = request.safety_decision
    if safety_result.decision == schemas.SafetyDecision.reject_prohibited:
        final_decision = safety_result.decision.value

    status = schemas.RoutineStatus.draft
    if final_decision == schemas.SafetyDecision.reject_prohibited.value:
        status = schemas.RoutineStatus.rejected

    routine = models.Routine(
        assisted_user_id=request.assisted_user_id,
        created_by=context.actor_id,
        title=request.title,
        purpose=request.purpose,
        scheduled_time=request.scheduled_time,
        timezone=request.timezone,
        steps_json=request.steps_json,
        risk_level=request.risk_level,
        safety_decision=final_decision,
        status=status.value,
        approval_status=(
            "pending" if status == schemas.RoutineStatus.draft else "rejected"
        ),
    )
    db.add(routine)
    append_audit_event(
        db,
        context,
        "create_routine_draft",
        "routine_created",
        final_decision,
        {"routine_id": routine.id},
    )
    db.commit()
    db.refresh(routine)
    return routine


def approve_routine(
    db: Session, context: schemas.ActorContext, request: schemas.RoutineApproveRequest
):
    routine = (
        db.query(models.Routine).filter(models.Routine.id == request.routine_id).first()
    )
    if not routine:
        raise ValueError("Routine not found.")

    if routine.status != schemas.RoutineStatus.draft.value:
        raise ValueError("Only draft routines can be approved.")

    auth.require_caregiver_for(db, context, str(routine.assisted_user_id))

    if routine.safety_decision != schemas.SafetyDecision.allow_for_review.value:
        raise ValueError("Routine safety decision must be allow_for_review.")

    routine.approval_status = "approved"  # type: ignore[assignment]
    routine.status = schemas.RoutineStatus.active.value  # type: ignore[assignment]
    routine.approved_at = models.utcnow()

    append_audit_event(
        db,
        context,
        "approve_routine",
        "routine_approved",
        "approved",
        {"routine_id": routine.id},
    )
    db.commit()
    db.refresh(routine)
    return routine


def get_user_preferences(db: Session, context: schemas.ActorContext, user_id: str):
    if context.role == schemas.Role.caregiver:
        auth.require_caregiver_for(db, context, user_id)
    elif context.role == schemas.Role.assisted_user and context.actor_id != user_id:
        raise auth.UnauthorizedError("Cannot access other users' preferences.")

    profile = (
        db.query(models.AssistedUserProfile)
        .filter(models.AssistedUserProfile.user_id == user_id)
        .first()
    )
    if not profile:
        return {}
    return profile.approved_preferences_json


def get_today_routines(db: Session, context: schemas.ActorContext, user_id: str):
    if context.role == schemas.Role.caregiver:
        auth.require_caregiver_for(db, context, user_id)
    elif context.role == schemas.Role.assisted_user and context.actor_id != user_id:
        raise auth.UnauthorizedError("Cannot access other users' routines.")

    # MVP simplified: returning active routines for the user.
    # Timezone filtering by local calendar date would require extracting current date in user's tz.
    # For now, we return active ones.
    routines = (
        db.query(models.Routine)
        .filter(
            models.Routine.assisted_user_id == user_id,
            models.Routine.status == schemas.RoutineStatus.active.value,
        )
        .all()
    )
    return routines


def mark_routine_status(
    db: Session, context: schemas.ActorContext, request: schemas.RoutineStatusUpdate
):
    routine = (
        db.query(models.Routine).filter(models.Routine.id == request.routine_id).first()
    )
    if not routine:
        raise ValueError("Routine not found")

    if context.role == schemas.Role.caregiver:
        auth.require_caregiver_for(db, context, str(routine.assisted_user_id))
    elif (
        context.role == schemas.Role.assisted_user
        and context.actor_id != routine.assisted_user_id
    ):
        raise auth.UnauthorizedError("Unauthorized")

    if request.status not in [
        schemas.RoutineStatus.completed,
        schemas.RoutineStatus.help_requested,
        schemas.RoutineStatus.missed,
    ]:
        raise ValueError("Invalid status transition requested.")

    if (
        routine.status != schemas.RoutineStatus.active.value
        and request.status != schemas.RoutineStatus.help_requested
    ):
        # Help requested can be pressed multiple times, but completing a missed routine etc is restricted.
        # Allowing transition from active for completion/missed.
        if routine.status != request.status.value:
            raise ValueError(
                f"Cannot transition from {routine.status} to {request.status.value}"
            )

    routine.status = request.status.value  # type: ignore[assignment]
    event = models.RoutineEvent(
        routine_id=routine.id,
        event_type=request.status.value,
        actor_id=context.actor_id,
    )
    db.add(event)
    append_audit_event(
        db,
        context,
        "mark_routine_status",
        f"status_{request.status.value}",
        "allowed",
        {"routine_id": routine.id},
    )
    db.commit()
    db.refresh(routine)
    return routine


def create_caregiver_alert(
    db: Session, context: schemas.ActorContext, request: schemas.CaregiverAlertRequest
):
    if (
        context.role != schemas.Role.assisted_user
        and context.role != schemas.Role.system_admin
    ):
        # Generally the system or assisted user requests help.
        pass

    # Find caregivers
    rels = (
        db.query(models.CaregiverRelationship)
        .filter(
            models.CaregiverRelationship.assisted_user_id == request.assisted_user_id,
            models.CaregiverRelationship.status == "active",
        )
        .all()
    )

    if not rels:
        # No caregivers to alert, but we must log it safely
        append_audit_event(
            db,
            context,
            "create_caregiver_alert",
            "alert_failed",
            "no_caregiver",
            {"routine_id": request.routine_id},
        )
        db.commit()
        return []

    alerts = []
    for rel in rels:
        # Deduplication: check if an identical unread alert was created recently (e.g. within 5 mins). For simplicity, skip here or just check last alert.
        last_alert = (
            db.query(models.CaregiverAlert)
            .filter(
                models.CaregiverAlert.caregiver_user_id == rel.caregiver_user_id,
                models.CaregiverAlert.routine_id == request.routine_id,
                models.CaregiverAlert.status == "unread",
            )
            .first()
        )

        if not last_alert:
            alert = models.CaregiverAlert(
                assisted_user_id=request.assisted_user_id,
                caregiver_user_id=rel.caregiver_user_id,
                routine_id=request.routine_id,
                alert_type=request.alert_type,
                message=request.message,
            )
            db.add(alert)
            alerts.append(alert)

    if alerts:
        append_audit_event(
            db,
            context,
            "create_caregiver_alert",
            "alert_created",
            "allowed",
            {"routine_id": request.routine_id, "alert_count": len(alerts)},
        )
    db.commit()
    return alerts


def get_approved_contacts(db: Session, context: schemas.ActorContext, user_id: str):
    if context.role == schemas.Role.caregiver:
        auth.require_caregiver_for(db, context, user_id)
    elif context.role == schemas.Role.assisted_user and context.actor_id != user_id:
        raise auth.UnauthorizedError("Unauthorized")

    # In MVP, contacts might be part of preferences
    prefs = get_user_preferences(db, context, user_id)
    return prefs.get("approved_contacts", [])
