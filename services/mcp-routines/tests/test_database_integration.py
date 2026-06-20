from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src import models


def test_timezone_behavior(db_session: Session):
    """Verify that timezone-aware datetimes are correctly stored and retrieved with timezone offset."""
    now_utc = datetime.now(timezone.utc)
    user = models.User(
        id="tz-user-1",
        display_name="Timezone User",
        role="caregiver",
        created_at=now_utc,
    )
    db_session.add(user)
    db_session.commit()

    retrieved_user = db_session.query(models.User).filter_by(id="tz-user-1").first()
    assert retrieved_user is not None
    assert retrieved_user.created_at is not None
    # Verify timezone offset is preserved (not None) and it is timezone-aware
    assert retrieved_user.created_at.tzinfo is not None
    assert (
        retrieved_user.created_at.tzinfo.utcoffset(retrieved_user.created_at)
        is not None
    )


def test_jsonb_behavior(db_session: Session):
    """Verify that JSON columns store, retrieve, and handle dictionaries correctly."""
    user = models.User(id="json-user-1", display_name="JSON User", role="assisted_user")
    db_session.add(user)
    db_session.commit()

    preferences = {
        "theme": "dark",
        "notifications": {"email": True, "sms": False},
        "approved_contacts": ["Doctor Jones", "Sonya Smith"],
    }

    profile = models.AssistedUserProfile(
        user_id=user.id,
        preferred_name="JSON Preferred",
        approved_preferences_json=preferences,
    )
    db_session.add(profile)
    db_session.commit()

    retrieved_profile = (
        db_session.query(models.AssistedUserProfile).filter_by(user_id=user.id).first()
    )
    assert retrieved_profile is not None
    assert retrieved_profile.approved_preferences_json == preferences
    # Confirm dictionary access works
    assert retrieved_profile.approved_preferences_json["theme"] == "dark"
    assert retrieved_profile.approved_preferences_json["notifications"]["email"] is True


def test_transaction_rollback(db_session: Session):
    """Verify that exceptions trigger a successful transaction rollback and no partial data is committed."""
    user = models.User(
        id="rollback-user-1", display_name="Rollback User", role="assisted_user"
    )
    db_session.add(user)
    db_session.commit()

    # Try inserting profile but fail on transaction constraints (e.g. non-existent foreign key or manual rollback)
    try:
        # Start a nested sub-transaction
        with db_session.begin_nested():
            # Add valid profile
            profile = models.AssistedUserProfile(
                user_id=user.id,
                preferred_name="Should Rollback",
                approved_preferences_json={},
            )
            db_session.add(profile)
            # Add invalid record (violates foreign key for user_id) to trigger DB error
            invalid_alert = models.CaregiverAlert(
                id="invalid-alert-id",
                assisted_user_id="non-existent-user-id",  # violates FK constraint
                caregiver_user_id="non-existent-caregiver-id",
                routine_id="non-existent-routine-id",
                alert_type="help_requested",
                message="Oops",
            )
            db_session.add(invalid_alert)
            db_session.flush()  # Forces DB execution to trigger FK exception
    except Exception:
        # Expected to fail and rollback the nested transaction
        pass

    # Verify that the profile was NOT committed and is not in session/DB
    retrieved_profile = (
        db_session.query(models.AssistedUserProfile).filter_by(user_id=user.id).first()
    )
    assert retrieved_profile is None
