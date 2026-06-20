# API Contracts & MCP Tool Schemas

## 1. FastAPI Endpoints (Agent Service)

### `POST /api/routines/interpret`
* **Input:** `CaregiverInputSchema`
* **Output:** `AgentDraftResponse`
* **Auth:** Caregiver session token.

```python
class CaregiverInputSchema(BaseModel):
    text: str = Field(..., max_length=500)
    assisted_user_id: str

class AgentDraftResponse(BaseModel):
    draft_id: str
    title: str
    scheduled_time: str
    steps: list[str]
    safety_decision: str  # allow_for_review, reject_medium_risk, reject_prohibited
    policy_reasons: list[str]
    visible_steps: list[str] | None
    help_text: str | None
```

### `POST /api/routines/{id}/approve`
* **Input:** `{ "caregiver_id": str, "decision": "approve" }`
* **Output:** `{ "status": "active", "routine_id": str }`

---

## 2. MCP Server Tools

All tools must validate inputs, execute within a transaction, and append to the `audit_events` table automatically. The Agent only interacts with these tools.

### `create_routine_draft`
* **Input Schema:**
  ```json
  {
    "assisted_user_id": "string",
    "title": "string",
    "steps_json": "array",
    "risk_level": "string",
    "safety_decision": "string"
  }
  ```
* **Auth Check:** Verifies caller has agent privileges. Enforces `approval_status = pending`.
* **Action:** Writes to `routines` table.

### `append_audit_event` (INTERNAL)
* **Auth Check:** Not exposed as an MCP tool to external callers.
* **Action:** Internal service function used automatically by every state-changing MCP tool to ensure audit trail integrity. Creates an immutable audit record.

### `approve_routine`
* **Input Schema:**
  ```json
  {
    "routine_id": "string",
    "caregiver_user_id": "string"
  }
  ```
* **Auth Check:** Queries `caregiver_relationships` to verify the caregiver is authorized for the routine's `assisted_user_id`. Verifies `safety_decision == allow_for_review`.
* **Action:** Sets `approval_status = approved`, `status = active`. 

### `get_user_preferences`
* **Input Schema:** `{ "user_id": "string" }`
* **Auth Check:** Accessible by UI and Agent. 
* **Action:** Returns only `approved_preferences_json`.

### `create_caregiver_alert`
* **Input Schema:**
  ```json
  {
    "assisted_user_id": "string",
    "routine_id": "string",
    "alert_type": "string",
    "message": "string"
  }
  ```
* **Auth Check:** Rate limits creation. 
* **Action:** Finds the linked caregiver from `caregiver_relationships` and writes to `caregiver_alerts`. Appends audit event.

### `mark_routine_status`
* **Input Schema:** `{ "routine_id": "string", "status": "string" }` (completed, help_requested, missed)
* **Auth Check:** Allowed for assisted user context.
* **Action:** Updates `routines.status` and appends an event to `routine_events`.

---

## 3. Trusted Actor Context Injection

To ensure that the LLM cannot impersonate different users, change their role, or bypass authorization rules, we separate the model-controlled parameters from the trusted context parameters.

### Protocol Parameters Mapping

*   **Model-controlled parameters**: Parameters exposed via standard MCP schema (e.g. `assisted_user_id`, `title`, `steps_json`, `status`, etc.). The LLM is free to suggest/provide these.
*   **Server-injected context**: The `_context` parameter. This parameter is NOT exposed in the published tool schemas (i.e. it is hidden from the LLM). It must be injected by the calling environment (e.g. the FastAPI application gateway).
*   **Authorization-sensitive properties**: The `ActorContext` containing:
    *   `actor_id`: The verified ID of the user performing the action.
    *   `role`: The verified role (`caregiver`, `assisted_user`, or `system_admin`).
    *   `correlation_id`: A UUID linking the agent invocation to the original API request.

### FastAPI Gateway Binding (Phase 2)

During Phase 2, when the FastAPI application gateway receives a request (e.g. from the Next.js caregiver UI):
1. The gateway validates the user's session cookie or bearer token.
2. It extracts the authenticated user's ID and role.
3. It constructs the `ActorContext` object.
4. When calling the MCP server over stdio transport, the gateway injects the `_context` parameter directly into the RPC `arguments` payload before dispatching it to the MCP server.
5. The MCP server validates the injected `_context` and handles permissions (e.g., checking the database to ensure the caregiver `actor_id` has an active caregiver relationship with the `assisted_user_id` before allowing the operation).

