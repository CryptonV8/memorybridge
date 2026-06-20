# Safety Policy & Risk Register

## 1. Safety Classification Policy

All incoming routine requests must be checked against this policy deterministically, followed by semantic agent review.

### Low Risk (Allowed, requires caregiver review)
* Drinking water
* Watering plants
* Listening to music
* Pre-approved gentle exercises
* Calling a family member (must be on approved contact list)

### Medium Risk (Disabled in MVP by default, stored as rejected drafts)
* Leaving the home
* Using kitchen equipment (microwaves, etc.)
* Bathing/showering tasks
* Tasks involving stairs or sharp objects

### Prohibited (Rejected entirely, never rewritten)
* Changing medication or doses
* Financial transactions
* Unlocking doors or operating stoves/ovens
* Making medical decisions or claims
* Contacting emergency services
* Contacting non-approved individuals

---

## 2. Risk Register

| Risk ID | Category | Description | Mitigation Strategy |
|---------|----------|-------------|---------------------|
| R1 | Safety | Agent inadvertently suggests changing a medication dose. | Deterministic blocked keywords list + Safety Agent semantic rejection. Prohibit routing to UI generation. |
| R2 | Safety | Caregiver unknowingly approves an unsafe routine due to fatigue. | Require double confirmation on medium-risk actions (if enabled later). Keep text exceptionally brief to encourage actual reading. |
| R3 | Privacy | Model outputs PII or exposes another user's schedule. | Strict row-level security in MCP tools. Agent only receives data explicitly permitted for the current user ID. |
| R4 | Implementation | Prompt injection causes agent to bypass safety checks. | Separate data fields from instructions. Root orchestrator rejects attempts to reveal system prompts. Enforce output structure (JSON schemas). |
| R5 | Accessibility | UI is too confusing, causing the user to miss routines. | Enforce minimum 44px targets, maximum one active task on screen, high contrast, text-to-speech. axe-core testing. |
| R6 | Scope | Creeping requirements lead to building real SMS integration. | Strict adherence to MVP non-goals. Hardcode in-app alerts as the only escalation mechanism. |
