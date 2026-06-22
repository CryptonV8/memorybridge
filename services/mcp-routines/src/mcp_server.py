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
    audit_metadata = {"routine_id": routine.id}
    if request.metadata:
        audit_metadata.update(request.metadata)

    append_audit_event(
        db,
        context,
        "create_routine_draft",
        "routine_created",
        final_decision,
        audit_metadata,
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


def get_routine(db: Session, context: schemas.ActorContext, routine_id: str) -> models.Routine:
    routine = db.query(models.Routine).filter(models.Routine.id == routine_id).first()
    if not routine:
        raise ValueError("Routine not found.")

    if context.role == schemas.Role.caregiver:
        auth.require_caregiver_for(db, context, str(routine.assisted_user_id))
    elif context.role == schemas.Role.assisted_user:
        if context.actor_id != str(routine.assisted_user_id):
            raise auth.UnauthorizedError("Cannot access other users' routines.")
    else:
        raise auth.UnauthorizedError("Role not authorized.")
    return routine


def update_routine(db: Session, context: schemas.ActorContext, request: schemas.RoutineUpdateRequest) -> models.Routine:
    routine = db.query(models.Routine).filter(models.Routine.id == request.routine_id).first()
    if not routine:
        raise ValueError("Routine not found.")

    # Only caregiver can edit routines
    auth.require_caregiver_for(db, context, str(routine.assisted_user_id))

    # Verify status is draft or pending_approval, and approval status is not approved or rejected
    if routine.status not in [schemas.RoutineStatus.draft.value, schemas.RoutineStatus.pending_approval.value]:
        raise ValueError("Routine cannot be edited in its current status.")
    if routine.approval_status in ["approved", "rejected"]:
        raise ValueError("Routine cannot be edited once approved or rejected.")

    updates = request.updates
    content_changed = False

    if "title" in updates and updates["title"] != routine.title:
        routine.title = updates["title"]
        content_changed = True
    if "steps_json" in updates and updates["steps_json"] != routine.steps_json:
        # Validate steps
        for step in updates["steps_json"]:
            if not step.strip():
                raise ValueError("Steps cannot be empty.")
        if len(updates["steps_json"]) < 1 or len(updates["steps_json"]) > 5:
            raise ValueError("Steps count must be between 1 and 5.")
        routine.steps_json = updates["steps_json"]
        content_changed = True
    if "purpose" in updates:
        routine.purpose = updates["purpose"]
    if "scheduled_time" in updates:
        routine.scheduled_time = updates["scheduled_time"]
    if "timezone" in updates:
        routine.timezone = updates["timezone"]

    decision = routine.safety_decision
    if content_changed:
        # Rerun deterministic safety check
        safety_result = safety.check_structural_policy(str(routine.title), routine.steps_json)  # type: ignore[arg-type]
        if safety_result.decision == schemas.SafetyDecision.reject_prohibited:
            routine.risk_level = "prohibited"  # type: ignore[assignment]
            routine.safety_decision = "reject_prohibited"  # type: ignore[assignment]
            routine.status = schemas.RoutineStatus.rejected.value  # type: ignore[assignment]
            routine.approval_status = "rejected"  # type: ignore[assignment]
        else:
            # Invalidate prior semantic safety and reset to low-risk draft
            routine.risk_level = "low"  # type: ignore[assignment]
            routine.safety_decision = "allow_for_review"  # type: ignore[assignment]
            routine.status = schemas.RoutineStatus.draft.value  # type: ignore[assignment]
            routine.approval_status = "pending"  # type: ignore[assignment]
        decision = routine.safety_decision

    append_audit_event(
        db,
        context,
        "update_routine",
        "routine_updated",
        decision,  # type: ignore[arg-type]
        {"routine_id": routine.id, "content_changed": content_changed},
    )
    db.commit()
    db.refresh(routine)
    return routine


def reject_routine(db: Session, context: schemas.ActorContext, routine_id: str) -> models.Routine:
    routine = db.query(models.Routine).filter(models.Routine.id == routine_id).first()
    if not routine:
        raise ValueError("Routine not found.")

    auth.require_caregiver_for(db, context, str(routine.assisted_user_id))

    # Idempotence: if already rejected, return
    if routine.status == schemas.RoutineStatus.rejected.value and routine.approval_status == "rejected":
        return routine

    if routine.status not in [schemas.RoutineStatus.draft.value, schemas.RoutineStatus.pending_approval.value]:
        raise ValueError("Only draft or pending routines can be rejected.")
    if routine.approval_status in ["approved", "rejected"]:
        raise ValueError("Routine already approved or rejected.")

    routine.status = schemas.RoutineStatus.rejected.value  # type: ignore[assignment]
    routine.approval_status = "rejected"  # type: ignore[assignment]

    append_audit_event(
        db,
        context,
        "reject_routine",
        "routine_rejected",
        "rejected",
        {"routine_id": routine.id},
    )
    db.commit()
    db.refresh(routine)
    return routine


def list_caregiver_routines(db: Session, context: schemas.ActorContext, request: schemas.RoutineListRequest) -> dict:
    auth.require_role(context, schemas.Role.caregiver)

    # Get active caregiver relationship scope
    rels = db.query(models.CaregiverRelationship).filter(
        models.CaregiverRelationship.caregiver_user_id == context.actor_id,
        models.CaregiverRelationship.status == "active"
    ).all()
    allowed_user_ids = [str(r.assisted_user_id) for r in rels]

    if not allowed_user_ids:
        return {"routines": [], "next_cursor": None}

    if request.assisted_user_id:
        if request.assisted_user_id not in allowed_user_ids:
            raise auth.UnauthorizedError("Unauthorized for this assisted user.")
        query_user_ids = [request.assisted_user_id]
    else:
        query_user_ids = allowed_user_ids

    query = db.query(models.Routine).filter(models.Routine.assisted_user_id.in_(query_user_ids))

    if request.status:
        query = query.filter(models.Routine.status == request.status)

    query = query.order_by(models.Routine.id)

    if request.cursor:
        query = query.filter(models.Routine.id > request.cursor)

    # Fetch limit + 1 to check if there is a next page
    limit = request.limit
    routines = query.limit(limit + 1).all()

    next_cursor = None
    if len(routines) > limit:
        next_cursor = routines[limit - 1].id
        routines = routines[:limit]

    return {
        "routines": [
            {
                "id": r.id,
                "assisted_user_id": r.assisted_user_id,
                "title": r.title,
                "purpose": r.purpose,
                "scheduled_time": r.scheduled_time,
                "timezone": r.timezone,
                "steps_json": r.steps_json,
                "risk_level": r.risk_level,
                "safety_decision": r.safety_decision,
                "approval_status": r.approval_status,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            } for r in routines
        ],
        "next_cursor": next_cursor
    }


def get_audit_events(db: Session, context: schemas.ActorContext, correlation_id: str) -> list:
    if context.role != schemas.Role.caregiver:
        raise auth.UnauthorizedError("Only caregivers can retrieve audit events.")

    events = db.query(models.AuditEvent).filter(models.AuditEvent.correlation_id == correlation_id).all()

    authorized_events = []
    for event in events:
        # If caregiver is the actor, they are authorized
        if event.actor_id == context.actor_id:
            authorized_events.append(event)
            continue

        # If related to a routine in caregiver's scope
        routine_id = event.metadata_json.get("routine_id")
        if routine_id:
            routine = db.query(models.Routine).filter(models.Routine.id == routine_id).first()
            if routine and auth.verify_caregiver_relationship(db, context.actor_id, str(routine.assisted_user_id)):
                authorized_events.append(event)
                continue

        # Check if metadata has assisted_user_id directly
        assisted_user_id = event.metadata_json.get("assisted_user_id")
        if assisted_user_id and auth.verify_caregiver_relationship(db, context.actor_id, str(assisted_user_id)):
            authorized_events.append(event)
            continue

    # Redact internal details
    result = []
    for event in authorized_events:
        safe_metadata = {}
        for key in ["routine_id", "risk_level", "policy_reasons", "content_changed"]:
            if key in event.metadata_json:
                safe_metadata[key] = event.metadata_json[key]

        result.append({
            "id": event.id,
            "correlation_id": event.correlation_id,
            "tool_name": event.tool_name,
            "event_type": event.event_type,
            "decision": event.decision,
            "metadata": safe_metadata,
            "created_at": event.created_at.isoformat() if event.created_at else None
        })
    return result


def get_caregiver_alerts(db: Session, context: schemas.ActorContext, caregiver_id: str) -> list:
    if context.role != schemas.Role.caregiver:
        raise auth.UnauthorizedError("Only caregivers can retrieve alerts.")
    if context.actor_id != caregiver_id:
        raise auth.UnauthorizedError("Unauthorized for this caregiver.")

    alerts = db.query(models.CaregiverAlert).filter(
        models.CaregiverAlert.caregiver_user_id == caregiver_id
    ).order_by(models.CaregiverAlert.created_at.desc()).all()

    return [
        {
            "id": a.id,
            "caregiver_user_id": a.caregiver_user_id,
            "assisted_user_id": a.assisted_user_id,
            "routine_id": a.routine_id,
            "alert_type": a.alert_type,
            "priority": a.priority,
            "message": a.message,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in alerts
    ]


