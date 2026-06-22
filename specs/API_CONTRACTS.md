# API Contracts & MCP Tool Schemas

## 1. FastAPI Endpoints (Agent Service Gateway)

All API responses return structured, typed payloads, including a unique correlation ID for audits.

### `POST /api/routines/interpret`
* **Input:** `CaregiverInputSchema`
* **Output:** `AgentDraftResponse`
* **Auth:** Bearer Token authentication.
```json
{
  "text": "Please remind Maria at 10:00 to water the plants near the living-room window.",
  "assisted_user_id": "user-assisted-maria"
}
```

### `POST /api/routines/{id}/approve`
* **Input:** `ApproveRoutineInput`
* **Output:** `{ "status": "active", "routine_id": "string" }`

### `PATCH /api/routines/{id}`
* **Input:** `UpdateRoutineInput`
* **Output:** `Routine` schema payload.

---

## 2. MCP Server Tools

Every state-changing tool call validates the caller's session context and writes an audit event.

### Context Param Injection
The `_context` parameter is injected into all tool arguments by the API gateway:
```json
{
  "actor_id": "user-caregiver-anna",
  "role": "caregiver",
  "correlation_id": "some-correlation-uuid"
}
```

To support this gateway-level injection, all tool definitions set `"additionalProperties": true` in their JSON schema properties:

### `create_routine_draft`
- **Input parameters:** `assisted_user_id`, `title`, `steps_json`, `risk_level`, `safety_decision`, `scheduled_time`, `timezone`, `metadata`.
- **Action:** Creates a routine with `status = draft` and `approval_status = pending` (or `status = rejected`, `approval_status = rejected` for prohibited requests).

### `approve_routine`
- **Input parameters:** `routine_id`, `caregiver_user_id`.
- **Action:** Checks relationship authorizations, sets `approval_status = approved`, and sets `status = active`.

### `update_routine`
- **Input parameters:** `routine_id`, `updates`.
- **Action:** Reruns deterministic policy checks and resets approval status if steps/details are modified.
