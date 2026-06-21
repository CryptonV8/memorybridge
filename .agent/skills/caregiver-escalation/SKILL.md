---
name: caregiver-escalation
purpose: "Process trigger conditions to create in-app alerts for the caregiver."
---

# Caregiver Escalation Skill

## Boundaries
- Never contact unapproved external systems.
- Only interacts with the `create_caregiver_alert` MCP tool.
- Generates only in-app alerts. Do NOT attempt to format text for SMS or Email.

## Positive Triggers
- "Maria pressed Help me"
- "Routine not completed after grace period"

## Negative Triggers
- "Call 911"
- "Email the doctor"

## Instructions
1. Analyze the triggering event (e.g., missed routine, explicit help request).
2. Format a concise, actionable alert message describing what occurred.
3. Determine the alert type (e.g., `help_requested`, `missed_routine`).
4. Output the exact parameters required to invoke the `create_caregiver_alert` tool.

## Prohibited Behavior
- Do NOT generate requests for emergency services.
- Do NOT hallucinate medical diagnoses explaining why a routine was missed.

## Output Requirements
- Must output valid JSON matching the `EscalationOutput` schema.

## Evaluation Notes
- Must be rigorously tested to ensure it never attempts to bypass the sandbox or call external APIs when prompted to "call 911".
