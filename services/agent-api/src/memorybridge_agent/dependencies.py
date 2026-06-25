from typing import Any
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

security = HTTPBearer()

from .config import settings

def get_demo_tokens() -> dict[str, dict[str, Any]]:
    return {
        settings.demo_caregiver_token: {
            "actor_id": "user-caregiver-anna",
            "role": "caregiver",
            "caregiver_relationship_scope": ["user-assisted-maria"],
            "authorization_scope": "full"
        },
        settings.demo_assisted_user_token: {
            "actor_id": "user-assisted-maria",
            "role": "assisted_user",
            "caregiver_relationship_scope": [],
            "authorization_scope": "self"
        }
    }

class ActorContext(BaseModel):
    actor_id: str
    role: str
    caregiver_relationship_scope: list[str]
    authorization_scope: str
    correlation_id: str

def get_correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")

def get_actor_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> ActorContext:
    token = credentials.credentials
    demo_tokens = get_demo_tokens()
    if token not in demo_tokens:
        raise HTTPException(status_code=401, detail="Invalid or missing demo token")
    
    actor_data = demo_tokens[token]
    return ActorContext(
        actor_id=actor_data["actor_id"],
        role=actor_data["role"],
        caregiver_relationship_scope=actor_data["caregiver_relationship_scope"],
        authorization_scope=actor_data["authorization_scope"],
        correlation_id=get_correlation_id(request)
    )
