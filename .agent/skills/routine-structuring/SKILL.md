---
name: routine-structuring
purpose: "Transform caregiver input into a small, structured routine (max 5 steps, one action per step) without inventing details."
---

# Routine Structuring Skill

## Boundaries
- Must leave `missing_information` array populated instead of assuming times, places, or contacts.
- Do not invent, hallucinate, or infer any details not explicitly provided by the caregiver.
- Maximum 5 steps allowed.

## Positive Triggers
- "Create a routine for watering the plants at 10"
- "Remind Maria to call Anna"

## Negative Triggers
- "Approve this routine"
- "Send an emergency message"

## Instructions
1. Parse the caregiver's raw text input.
2. Extract the routine's title.
3. Extract up to 5 individual steps. Each step must contain exactly one action.
4. Extract the scheduled time, if provided.
5. If any critical details (like time, contact person, or location) are missing but necessary for the task, list them in the `missing_information` array.
6. Format the output strictly matching the provided JSON schema.

## Prohibited Behavior
- Do NOT generate more than 5 steps.
- Do NOT combine multiple actions into a single step (e.g., "Get the cup and pour water" must be split).
- Do NOT assume the time if not mentioned.

## Output Requirements
- Must output valid JSON matching the `RoutinePlanOutput` schema.

## Evaluation Notes
- Tested against inputs with implicit details to ensure the agent uses the `missing_information` array rather than hallucinating details.
