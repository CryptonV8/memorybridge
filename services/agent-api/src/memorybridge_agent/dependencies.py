from typing import Any
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

security = HTTPBearer()

# Demo Static Token Lookup
DEMO_TOKENS: dict[str, dict[str, Any]] = {
    "caregiver_demo_token": {
        "actor_id": "cg-123",
        "role": "caregiver",
        "caregiver_relationship_scope": ["au-456"],
        "authorization_scope": "full"
    },
    "assisted_user_demo_token": {
        "actor_id": "au-456",
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
    if token not in DEMO_TOKENS:
        raise HTTPException(status_code=401, detail="Invalid or missing demo token")
    
    actor_data = DEMO_TOKENS[token]
    return ActorContext(
        actor_id=actor_data["actor_id"],
        role=actor_data["role"],
        caregiver_relationship_scope=actor_data["caregiver_relationship_scope"],
        authorization_scope=actor_data["authorization_scope"],
        correlation_id=get_correlation_id(request)
    )
