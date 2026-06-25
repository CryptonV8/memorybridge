#!/usr/bin/env python3
"""
MemoryBridge — synthetic demo data seed script.

Populates the production/demo database with Anna Petrova (caregiver) and
Maria Petrova (assisted user) plus demo routines, one rejected prohibited
example, one help alert, and audit stubs.

SAFETY RULES:
  - Uses synthetic data only — no real names, emails, phones, or health records.
  - Idempotent: rows are upserted by stable IDs; running twice is safe.
  - Does NOT delete existing data unless --reset flag is provided.
  - --reset requires explicit --confirm-reset confirmation to prevent accidents.
  - Does NOT run destructive DDL.

Usage:
  python scripts/seed_demo_data.py
  python scripts/seed_demo_data.py --reset --confirm-reset

Environment:
  DATABASE_URL  — must be set before running (see .env.example).
"""
import os
import sys
import json
import argparse
from os.path import abspath, dirname, join

# Ensure mcp-routines src is importable
sys.path.insert(0, join(dirname(dirname(abspath(__file__))), "services", "mcp-routines"))

from src.database import SessionLocal, engine, Base
from src import models
from datetime import datetime, timezone


# ── Stable synthetic IDs — never change these between seed runs ───────────────
ANNA_ID = "user-caregiver-anna"
MARIA_ID = "user-assisted-maria"

ROUTINE_IDS = {
    "water_plants": "routine-demo-001",
    "drink_water":  "routine-demo-002",
    "music":        "routine-demo-003",
    "medication":   "routine-demo-004-rejected",
    "morning_tea":  "routine-demo-005-completed",
}

ALERT_ID = "alert-demo-001"


def _upsert_user(db, id_: str, display_name: str, role: str):
    """Insert user if not present; update display_name if changed."""
    obj = db.get(models.User, id_)
    if obj is None:
        obj = models.User(id=id_, display_name=display_name, role=role)
        db.add(obj)
    else:
        obj.display_name = display_name
        obj.role = role


def _upsert_profile(db, user_id: str):
    obj = db.get(models.AssistedUserProfile, user_id)
    prefs = {"approved_contacts": ["Anna Petrova"]}
    if obj is None:
        obj = models.AssistedUserProfile(
            user_id=user_id,
            preferred_name="Maria",
            approved_preferences_json=prefs,
        )
        db.add(obj)
    else:
        obj.preferred_name = "Maria"
        obj.approved_preferences_json = prefs


def _upsert_relationship(db, caregiver_id: str, assisted_id: str):
    obj = (
        db.query(models.CaregiverRelationship)
        .filter_by(caregiver_user_id=caregiver_id, assisted_user_id=assisted_id)
        .first()
    )
    if obj is None:
        obj = models.CaregiverRelationship(
            caregiver_user_id=caregiver_id,
            assisted_user_id=assisted_id,
            status="active",
        )
        db.add(obj)
    else:
        obj.status = "active"


def _upsert_routine(db, **kwargs):
    id_ = kwargs["id"]
    obj = db.get(models.Routine, id_)
    if obj is None:
        obj = models.Routine(**kwargs)
        db.add(obj)
    else:
        for k, v in kwargs.items():
            if k != "id":
                setattr(obj, k, v)


def _upsert_alert(db, **kwargs):
    id_ = kwargs["id"]
    obj = db.get(models.CaregiverAlert, id_)
    if obj is None:
        obj = models.CaregiverAlert(**kwargs)
        db.add(obj)


def seed(reset: bool = False):
    now = datetime.now(timezone.utc)

    db = SessionLocal()
    try:
        if reset:
            print("[seed] --reset: deleting all demo rows (IDs only, not schema)...")
            for id_ in ROUTINE_IDS.values():
                r = db.get(models.Routine, id_)
                if r:
                    db.query(models.RoutineEvent).filter_by(routine_id=id_).delete()
                    db.query(models.CaregiverAlert).filter_by(routine_id=id_).delete()
                    db.delete(r)

            alert = db.get(models.CaregiverAlert, ALERT_ID)
            if alert:
                db.delete(alert)

            rel = (
                db.query(models.CaregiverRelationship)
                .filter_by(caregiver_user_id=ANNA_ID, assisted_user_id=MARIA_ID)
                .first()
            )
            if rel:
                db.delete(rel)

            profile = db.get(models.AssistedUserProfile, MARIA_ID)
            if profile:
                db.delete(profile)

            for uid in (ANNA_ID, MARIA_ID):
                u = db.get(models.User, uid)
                if u:
                    db.delete(u)

            db.commit()
            print("[seed] Reset complete.")

        print("[seed] Upserting demo data...")

        # 1. Users (synthetic — no real personal information)
        _upsert_user(db, ANNA_ID, "Anna Petrova", "caregiver")
        _upsert_user(db, MARIA_ID, "Maria Petrova", "assisted_user")
        db.commit()

        # 2. Assisted-user profile
        _upsert_profile(db, MARIA_ID)

        # 3. Caregiver relationship
        _upsert_relationship(db, ANNA_ID, MARIA_ID)
        db.commit()

        # 4. Routines
        _upsert_routine(
            db,
            id=ROUTINE_IDS["water_plants"],
            assisted_user_id=MARIA_ID,
            created_by=ANNA_ID,
            title="Water the plants",
            scheduled_time="10:00",
            timezone="Europe/Sofia",
            steps_json=[
                "Take the small blue watering can.",
                "Fill it halfway with water.",
                "Water the plants near the window.",
            ],
            risk_level="low",
            safety_decision="allow_for_review",
            approval_status="approved",
            status="active",
            approved_at=now,
        )
        _upsert_routine(
            db,
            id=ROUTINE_IDS["drink_water"],
            assisted_user_id=MARIA_ID,
            created_by=ANNA_ID,
            title="Drink a glass of water",
            scheduled_time="12:00",
            timezone="Europe/Sofia",
            steps_json=[
                "Take a glass from the kitchen.",
                "Fill it with water.",
                "Drink the water slowly.",
            ],
            risk_level="low",
            safety_decision="allow_for_review",
            approval_status="approved",
            status="active",
            approved_at=now,
        )
        _upsert_routine(
            db,
            id=ROUTINE_IDS["music"],
            assisted_user_id=MARIA_ID,
            created_by=ANNA_ID,
            title="Listen to music",
            scheduled_time="15:00",
            timezone="Europe/Sofia",
            steps_json=[
                "Turn on the radio.",
                "Listen to classical music.",
            ],
            risk_level="low",
            safety_decision="allow_for_review",
            approval_status="approved",
            status="active",
            approved_at=now,
        )
        # Rejected prohibited routine — demo evidence of safety policy
        _upsert_routine(
            db,
            id=ROUTINE_IDS["medication"],
            assisted_user_id=MARIA_ID,
            created_by=ANNA_ID,
            title="Change medication dose",
            scheduled_time="08:00",
            timezone="Europe/Sofia",
            steps_json=["Take an extra pill."],
            risk_level="prohibited",
            safety_decision="reject_prohibited",
            approval_status="rejected",
            status="rejected",
            approved_at=None,
        )
        # Completed routine — shows audit flow
        _upsert_routine(
            db,
            id=ROUTINE_IDS["morning_tea"],
            assisted_user_id=MARIA_ID,
            created_by=ANNA_ID,
            title="Morning tea",
            scheduled_time="09:00",
            timezone="Europe/Sofia",
            steps_json=["Pour a cup of tea.", "Drink it slowly."],
            risk_level="low",
            safety_decision="allow_for_review",
            approval_status="approved",
            status="completed",
            approved_at=now,
        )
        db.commit()

        # 5. Demo caregiver alert
        _upsert_alert(
            db,
            id=ALERT_ID,
            assisted_user_id=MARIA_ID,
            caregiver_user_id=ANNA_ID,
            routine_id=ROUTINE_IDS["water_plants"],
            alert_type="help_requested",
            message="Maria requested help with: Water the plants.",
        )
        db.commit()

        print("[seed] Done. Demo personas:")
        print(f"  Caregiver: Anna Petrova  (ID: {ANNA_ID})")
        print(f"  Assisted user: Maria Petrova  (ID: {MARIA_ID})")
        print(f"  Active routines: {len([k for k in ('water_plants','drink_water','music')])}")
        print("  Rejected routine: Change medication dose (prohibited)")
        print("  Completed routine: Morning tea")
        print("  Alert: help_requested on Water the plants")

    finally:
        db.close()


def verify():
    """Quick idempotency check — verifies the seed rows exist."""
    db = SessionLocal()
    try:
        anna = db.get(models.User, ANNA_ID)
        maria = db.get(models.User, MARIA_ID)
        active = (
            db.query(models.Routine)
            .filter(models.Routine.assisted_user_id == MARIA_ID,
                    models.Routine.status == "active")
            .count()
        )
        rejected = db.get(models.Routine, ROUTINE_IDS["medication"])
        alert = db.get(models.CaregiverAlert, ALERT_ID)

        ok = all([anna, maria, active >= 3, rejected, alert])
        if ok:
            print("[verify] OK — all expected seed rows present.")
            print(f"  Users: Anna={bool(anna)}, Maria={bool(maria)}")
            print(f"  Active routines for Maria: {active}")
            print(f"  Rejected routine present: {bool(rejected)}")
            print(f"  Demo alert present: {bool(alert)}")
        else:
            print("[verify] FAIL — some expected rows are missing.")
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MemoryBridge demo data seed script")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing demo rows before re-seeding",
    )
    parser.add_argument(
        "--confirm-reset",
        action="store_true",
        help="Required together with --reset to prevent accidental deletion",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify that seed data is present without making changes",
    )
    args = parser.parse_args()

    if args.verify:
        verify()
        sys.exit(0)

    if args.reset and not args.confirm_reset:
        print("ERROR: --reset requires --confirm-reset to prevent accidental deletion.")
        sys.exit(1)

    seed(reset=args.reset)
    verify()
