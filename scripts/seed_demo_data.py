import os
import sys
import json
from os.path import abspath, dirname, join
sys.path.insert(0, join(dirname(dirname(abspath(__file__))), "services", "mcp-routines"))

from src.database import SessionLocal, engine, Base
from src import models
from datetime import datetime, timezone

def seed_data():
    db = SessionLocal()

    # Safe reset for demo local data
    print("Clearing old demo data...")
    db.query(models.AuditEvent).delete()
    db.query(models.CaregiverAlert).delete()
    db.query(models.RoutineEvent).delete()
    db.query(models.Routine).delete()
    db.query(models.CaregiverRelationship).delete()
    db.query(models.AssistedUserProfile).delete()
    db.query(models.User).delete()
    db.commit()

    print("Seeding new demo data...")
    
    # 1. Users
    caregiver = models.User(
        id="user-caregiver-anna",
        display_name="Anna Petrova",
        role="caregiver"
    )
    assisted_user = models.User(
        id="user-assisted-maria",
        display_name="Maria Petrova",
        role="assisted_user"
    )
    db.add(caregiver)
    db.add(assisted_user)
    db.commit()

    # 2. Profile
    profile = models.AssistedUserProfile(
        user_id=assisted_user.id,
        preferred_name="Maria",
        approved_preferences_json={"approved_contacts": ["Anna Petrova"]}
    )
    db.add(profile)

    # 3. Relationship
    rel = models.CaregiverRelationship(
        caregiver_user_id=caregiver.id,
        assisted_user_id=assisted_user.id,
        status="active"
    )
    db.add(rel)
    db.commit()

    # 4. Routines (3 low risk, 1 rejected, 1 completed)
    r1 = models.Routine(
        id="routine-1",
        assisted_user_id=assisted_user.id,
        created_by=caregiver.id,
        title="Water the plants",
        scheduled_time="10:00",
        timezone="Europe/Sofia",
        steps_json=["Take the watering can", "Water the plants near the window"],
        risk_level="low",
        safety_decision="allow_for_review",
        approval_status="approved",
        status="active",
        approved_at=datetime.now(timezone.utc)
    )
    r2 = models.Routine(
        id="routine-2",
        assisted_user_id=assisted_user.id,
        created_by=caregiver.id,
        title="Drink water",
        scheduled_time="12:00",
        timezone="Europe/Sofia",
        steps_json=["Take a glass", "Fill it with water", "Drink"],
        risk_level="low",
        safety_decision="allow_for_review",
        approval_status="approved",
        status="active",
        approved_at=datetime.now(timezone.utc)
    )
    r3 = models.Routine(
        id="routine-3",
        assisted_user_id=assisted_user.id,
        created_by=caregiver.id,
        title="Listen to music",
        scheduled_time="15:00",
        timezone="Europe/Sofia",
        steps_json=["Turn on the radio", "Listen to classical music"],
        risk_level="low",
        safety_decision="allow_for_review",
        approval_status="approved",
        status="active",
        approved_at=datetime.now(timezone.utc)
    )
    r4 = models.Routine(
        id="routine-4-rejected",
        assisted_user_id=assisted_user.id,
        created_by=caregiver.id,
        title="Change medication",
        scheduled_time="08:00",
        timezone="Europe/Sofia",
        steps_json=["Take an extra pill"],
        risk_level="prohibited",
        safety_decision="reject_prohibited",
        approval_status="rejected",
        status="rejected"
    )
    r5 = models.Routine(
        id="routine-5-completed",
        assisted_user_id=assisted_user.id,
        created_by=caregiver.id,
        title="Morning tea",
        scheduled_time="09:00",
        timezone="Europe/Sofia",
        steps_json=["Drink tea"],
        risk_level="low",
        safety_decision="allow_for_review",
        approval_status="approved",
        status="completed",
        approved_at=datetime.now(timezone.utc)
    )

    db.add_all([r1, r2, r3, r4, r5])
    db.commit()

    # 5. Caregiver Alert
    alert = models.CaregiverAlert(
        id="alert-1",
        assisted_user_id=assisted_user.id,
        caregiver_user_id=caregiver.id,
        routine_id=r1.id,
        alert_type="help_requested",
        message="Maria requested help with: Water the plants"
    )
    db.add(alert)
    db.commit()

    print("Seed complete. Test personas: 'user-caregiver-anna' and 'user-assisted-maria'.")

if __name__ == "__main__":
    seed_data()
