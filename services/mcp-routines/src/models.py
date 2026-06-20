import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    display_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    timezone = Column(String(50), nullable=False, default="UTC")
    created_at = Column(DateTime(timezone=True), default=utcnow)


class AssistedUserProfile(Base):
    __tablename__ = "assisted_user_profiles"
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    preferred_name = Column(String(255), nullable=False)
    language = Column(String(10), default="en")
    text_size = Column(String(20), default="large")
    speech_enabled = Column(String(5), default="true")  # stored as str for simplicity
    approved_preferences_json = Column(JSON, nullable=False, default=dict)


class CaregiverRelationship(Base):
    __tablename__ = "caregiver_relationships"
    caregiver_user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    assisted_user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Routine(Base):
    __tablename__ = "routines"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assisted_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    purpose = Column(String(255), nullable=True)
    scheduled_time = Column(String(50), nullable=False)
    timezone = Column(String(50), nullable=False)
    steps_json = Column(JSON, nullable=False)
    risk_level = Column(String(50), nullable=False)
    safety_decision = Column(String(50), nullable=False)
    approval_status = Column(String(50), nullable=False, default="pending")
    status = Column(String(50), nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    approved_at = Column(DateTime(timezone=True), nullable=True)


class RoutineEvent(Base):
    __tablename__ = "routine_events"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    routine_id = Column(String(36), ForeignKey("routines.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    actor_id = Column(String(36), nullable=False)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class CaregiverAlert(Base):
    __tablename__ = "caregiver_alerts"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assisted_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    caregiver_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    routine_id = Column(String(36), ForeignKey("routines.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False, default="normal")
    message = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default="unread")
    created_at = Column(DateTime(timezone=True), default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    correlation_id = Column(String(36), nullable=False)
    actor_id = Column(String(36), nullable=False)
    agent_name = Column(String(255), nullable=True)
    tool_name = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)
    decision = Column(String(50), nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)
