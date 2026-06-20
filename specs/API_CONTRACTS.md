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
