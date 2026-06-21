---
name: accessible-ui-copy
purpose: "Generate concise labels, error messages, and confirmations for the accessible assisted-user UI."
---

# Accessible UI Copy Skill

## Boundaries
- Keeps text extremely short.
- Ensures a high readability index.
- Uses large, distinct target words suitable for buttons.

## Positive Triggers
- "Generate label for the done button"
- "Create an error message for when the network fails"

## Negative Triggers
- "Write a routine"
- "Determine if this is safe"

## Instructions
1. Understand the UI context requiring copy.
2. Generate extremely brief, direct text for the requested element.
3. Prioritize words that are easily recognizable.

## Prohibited Behavior
- Do NOT generate paragraphs of text.
- Do NOT use technical error codes (e.g., "Error 404").
- Do NOT use ambiguous terms (e.g., "Submit" instead of "Done").

## Output Requirements
- Must output valid JSON matching the `UICopyOutput` schema.

## Evaluation Notes
- Tested alongside axe-core accessibility evaluations to verify text length fits within standard 44px touch targets without truncation.
