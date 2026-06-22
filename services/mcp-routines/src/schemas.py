from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional


class Role(str, Enum):
    caregiver = "caregiver"
    assisted_user = "assisted_user"
    system_admin = "system_admin"


class RoutineStatus(str, Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    active = "active"
    completed = "completed"
    help_requested = "help_requested"
    missed = "missed"
    rejected = "rejected"


class SafetyDecision(str, Enum):
    allow_for_review = "allow_for_review"
    reject_medium_risk = "reject_medium_risk"
    reject_prohibited = "reject_prohibited"
    needs_clarification = "needs_clarification"


class ActorContext(BaseModel):
    model_config = ConfigDict(extra="ignore")
    actor_id: str
    role: Role
    correlation_id: str


class RoutineDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assisted_user_id: str
    title: str = Field(..., max_length=255)
    purpose: Optional[str] = Field(None, max_length=255)
    scheduled_time: str
    timezone: str
    steps_json: List[str] = Field(..., min_length=1, max_length=5)
    risk_level: str
    safety_decision: str
    metadata: Optional[dict] = None

    @field_validator("steps_json")
    @classmethod
    def validate_steps(cls, v):
        for step in v:
            if not step.strip():
                raise ValueError("Steps cannot be empty.")
        return v


class RoutineApproveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    routine_id: str
    caregiver_user_id: str


class RoutineStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    routine_id: str
    status: RoutineStatus


class CaregiverAlertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assisted_user_id: str
    routine_id: str
    alert_type: str
    message: str


class SafetyPolicyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: SafetyDecision
    risk_level: str
    policy_reasons: List[str]
    matched_rules: List[str]


class UserQueryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str


class RoutineGetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    routine_id: str


class RoutineUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    routine_id: str
    updates: dict


class RoutineRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    routine_id: str


class RoutineListRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assisted_user_id: Optional[str] = None
    status: Optional[str] = None
    limit: int = 20
    cursor: Optional[str] = None


class AuditGetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    correlation_id: str


class CaregiverAlertsGetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    caregiver_id: str


