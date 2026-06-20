from .schemas import ActorContext, Role
from sqlalchemy.orm import Session
from .models import CaregiverRelationship


class UnauthorizedError(Exception):
    pass


def verify_caregiver_relationship(
    db: Session, caregiver_id: str, assisted_user_id: str
) -> bool:
    rel = (
        db.query(CaregiverRelationship)
        .filter(
            CaregiverRelationship.caregiver_user_id == caregiver_id,
            CaregiverRelationship.assisted_user_id == assisted_user_id,
            CaregiverRelationship.status == "active",
        )
        .first()
    )
    return rel is not None


def require_role(context: ActorContext, required_role: Role):
    if context.role != required_role:
        raise UnauthorizedError(f"Actor must have role {required_role.value}")


def require_caregiver_for(db: Session, context: ActorContext, assisted_user_id: str):
    require_role(context, Role.caregiver)
    if not verify_caregiver_relationship(db, context.actor_id, assisted_user_id):
        raise UnauthorizedError(
            "No active caregiver relationship found for this assisted user."
        )
