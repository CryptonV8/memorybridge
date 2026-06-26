# MemoryBridge — Video Script (4 Minutes)

**Target Duration:** ~4:00 (approx. 500–600 words)

---

### [0:00 - 0:30] Problem & Solution
*(Visual: Title slide, then transition to cover image or B-roll of caregivers/assisted users.)*

**Voiceover:**
"Millions of families face the daily challenge of caring for loved ones with early-stage dementia. Caregivers struggle to maintain structured daily routines without being overly intrusive, while assisted individuals risk losing their autonomy and dignity.
MemoryBridge is a safety-first assistive prototype built for the Agents for Good track. It helps caregivers safely draft, evaluate, and schedule daily routines, translating complex requests into accessible, dementia-friendly instructions."

---

### [0:30 - 1:15] Architecture & Why Agents
*(Visual: Architecture diagram `memorybridge-architecture.svg`. Highlight components as they are mentioned.)*

**Voiceover:**
"Translating a free-form caregiver request into a safe, structured routine requires reasoning and multi-step planning—tasks where traditional hard-coded rules fail. This is why we use an agent architecture.
MemoryBridge is orchestrated using the Google Agent Development Kit (ADK) running on a private FastAPI backend. A Root Orchestrator directs specialized sub-agents: the Routine Planning Agent, the Semantic Safety Reviewer, the Dementia-Friendly Communication Agent, and an Escalation Agent.
These agents interact with a local Model Context Protocol, or MCP, server. The MCP tools encapsulate all database operations and enforce deterministic safety gates, ensuring the AI can never directly manipulate the database without strict bounds."

---

### [1:15 - 2:00] Caregiver UI: Routine Creation & Safety Review
*(Visual: Caregiver dashboard UI. Mouse clicks 'New Routine'. Types: "Remind Maria to water the plants at 10 AM". Hits Submit. Shows the generated draft.)*

**Voiceover:**
"Let’s look at the Caregiver Portal, built with Next.js and securely authenticated.
Anna, a caregiver, enters a natural language request to schedule watering the plants.
Behind the scenes, the ADK orchestrates the workflow. The Routine Planning Agent structures the steps, and the Semantic Safety Reviewer evaluates the risk.
The generated draft is presented back to Anna. Crucially, the system employs a strict human-in-the-loop policy. The AI only proposes; no routine becomes active without explicit human approval. Anna reviews the safety assessment and approves the routine."

---

### [2:00 - 2:40] Assisted-User UI & Help Escalation
*(Visual: Transition to the `/today` assisted-user interface. Shows large buttons, high contrast. Clicks 'Listen', then clicks 'Help me'.)*

**Voiceover:**
"Now, let's look at the assisted-user experience for Maria. The Dementia-Friendly Communication Agent has translated the steps into highly accessible, low-cognitive-load instructions.
The interface features large interactive targets, high contrast, and a text-to-speech 'Listen' feature.
If Maria becomes confused or needs assistance, she can press the 'Help me' button.
*(Visual: Switch back to Caregiver UI. Show the Help Alert popping up.)*
This triggers the Escalation Agent, which immediately sends an in-app alert to Anna, bridging the gap between independent living and verifiable safety."

---

### [2:40 - 3:15] Safety Enforcement & Immutable Audit Trail
*(Visual: Caregiver UI. Types: "Increase Maria's medication dose". Shows the red rejection screen. Then show the Audit Timeline for a routine.)*

**Voiceover:**
"But what if the caregiver makes a mistake or asks the AI to do something unsafe?
If Anna attempts to create a routine involving medication changes, deterministic safety gates intercept the prohibited keywords before the semantic agent even runs, automatically rejecting the request.
Every state change—from draft creation to safety decisions and human approvals—is logged via the MCP server into an immutable audit trail. This guarantees complete transparency into how the AI arrived at a specific routine, which is vital for trust."

---

### [3:15 - 4:00] Evaluation, Limitations & Conclusion
*(Visual: Evaluation Summary slide/chart, transitioning to final project links.)*

**Voiceover:**
"We rigorously evaluated MemoryBridge using automated test pipelines. The system achieved a 100% success rate in detecting and rejecting prohibited actions, and completely prevented approval bypass attempts. It also successfully resisted 5 out of 5 prompt injection attacks designed to subvert the safety reviewer.
While MemoryBridge is a fully functional prototype, it is not a medical device. It relies on synthetic data and does not diagnose conditions or contact real emergency services.
By combining the reasoning power of the Google ADK with the strict boundaries of MCP and human oversight, MemoryBridge demonstrates how generative AI can safely support families navigating cognitive decline.
Thank you."
