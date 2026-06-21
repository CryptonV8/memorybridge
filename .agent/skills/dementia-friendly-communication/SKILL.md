---
name: dementia-friendly-communication
purpose: "Rewrite approved content into clear, respectful, low-cognitive-load language."
---

# Dementia-Friendly Communication Skill

## Boundaries
- Short sentences.
- One action per sentence.
- No false certainty (e.g., "This will definitely cure you").
- No childish tone (elderspeak).
- No medical jargon.

## Positive Triggers
- "Draft user UI text for this task"
- "Rewrite this routine for the assisted user"

## Negative Triggers
- "Classify this risk"
- "Plan a routine"

## Instructions
1. Take the safety-approved routine steps.
2. Rewrite each step into a single, highly readable sentence.
3. Ensure the tone is respectful, adult-oriented, and encouraging.
4. Remove any complex metaphors or idioms.
5. Create a short, reassuring help text to accompany the routine.

## Prohibited Behavior
- Do NOT combine steps into a single paragraph.
- Do NOT use condescending language ("Good boy/girl", "It's time for our medicine").
- Do NOT use complex conditionals ("If it rains, then do X, otherwise do Y").

## Output Requirements
- Must output valid JSON matching the `CommunicationOutput` schema.
- The `visible_steps` array must have the exact same number of items as the input steps.

## Evaluation Notes
- Evaluated using automated readability index checks (e.g. Flesch-Kincaid) to ensure scores remain within the accessible target range.
