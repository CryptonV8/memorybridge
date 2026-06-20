# MemoryBridge
## Safe Daily Routine and Caregiver Support Agent
**Capstone Track:** Agents for Good  
**Version:** 0.1  
**Status:** MVP specification  
**Primary build environment:** Google Antigravity  
**Target stack:** Next.js, React, TypeScript, Tailwind CSS, Python, Google ADK, MCP, Neon PostgreSQL, Cloud Run

---

## 1. Executive Summary

MemoryBridge is a safety-first assistive application for people living with early-stage dementia and the family members or caregivers who support them.

The product helps caregivers create simple, low-risk daily routines. A multi-agent system converts caregiver instructions into structured steps, checks the task against a safety policy, rewrites the instructions in dementia-friendly language, and requires human approval before activation.

The assisted user sees a calm, accessible interface with one task at a time, large controls, optional text-to-speech, and three clear actions:

- **Done**
- **Help me**
- **Call my caregiver**

MemoryBridge is not a medical device and must not diagnose dementia, recommend treatment, change medication, detect emergencies, or replace caregivers or professional care.

---

## 2. Core Problem

People living with early-stage dementia may experience difficulty with:

- remembering routine activities;
- understanding why a reminder appeared;
- following a task with too many steps;
- finding the correct person to contact;
- communicating that they are confused or need support.

Caregivers may struggle to:

- create consistent and understandable reminders;
- know whether a routine was completed;
- identify when the person requested help;
- avoid giving the AI unsafe authority;
- preserve privacy while still personalizing the experience.

A single general-purpose prompt is not reliable enough. The system must use specialized agents, deterministic tools, explicit safety rules, human approval, audit logs, and measurable evaluations.

---

## 3. Product Goals

The MVP must:

1. Let a caregiver create a routine using natural language.
2. Convert the routine into a structured draft.
3. Classify the routine as low, medium, or prohibited risk.
4. Rewrite approved instructions using dementia-friendly communication rules.
5. Require caregiver approval before the routine becomes active.
6. Show the assisted user today’s routines in a highly accessible interface.
7. Let the user mark a routine as completed or request help.
8. Create an in-app caregiver alert when escalation rules are met.
9. Store an auditable record of agent decisions and tool calls.
10. Demonstrate at least three course concepts:
   - Google ADK multi-agent orchestration;
   - MCP tools;
   - Agent Skills;
   - security and human-in-the-loop;
   - evaluation and observability.

The final implementation should demonstrate all five where practical.

---

## 4. Non-Goals

The MVP must not:

- diagnose dementia or any medical condition;
- provide medical advice;
- change medication schedules or doses;
- detect falls, wandering, emergencies, or health deterioration;
- make financial decisions;
- unlock doors or control home appliances;
- send real SMS, email, or emergency service notifications;
- claim that a task or environment is safe;
- use real patient data;
- store real clinical records;
- replace caregivers or professional care.

Use synthetic demo data only.

---

## 5. Primary Personas

### 5.1 Assisted User

A person living with early-stage dementia who needs simple, respectful reminders.

Needs:

- minimal cognitive load;
- one clear action at a time;
- large text and buttons;
- optional audio;
- familiar names and images;
- easy access to help;
- no technical language.

### 5.2 Caregiver

A trusted family member or professional caregiver.

Needs:

- a simple routine authoring workflow;
- visibility into routine status;
- approval of all generated content;
- alerts when help is requested;
- an audit trail;
- control over contacts and preferences.

### 5.3 System Administrator

A demo/admin role for managing policies, seed data, and evaluation runs.

---

## 6. MVP User Stories

### Caregiver

1. As a caregiver, I can create a routine from natural language.
2. As a caregiver, I can review the structured interpretation before saving.
3. As a caregiver, I can see the safety classification and the reason.
4. As a caregiver, I can edit generated steps.
5. As a caregiver, I must approve a routine before activation.
6. As a caregiver, I can see whether a routine is pending, active, completed, missed, or needs help.
7. As a caregiver, I can see in-app alerts.
8. As a caregiver, I can view an audit trail for each routine.

### Assisted User

1. As an assisted user, I can see the current date, time, and next routine.
2. As an assisted user, I see one task at a time.
3. As an assisted user, I can hear the instruction read aloud.
4. As an assisted user, I can mark the task as done.
5. As an assisted user, I can request help.
6. As an assisted user, I can request contact with my approved caregiver.
7. As an assisted user, I never see internal system or agent language.

---

## 7. Safety Classification

Use a deterministic policy layer before any LLM-based semantic review.

### 7.1 Low Risk — Allowed After Caregiver Approval

Examples:

- drink a glass of water;
- call a family member;
- water houseplants;
- listen to music;
- read a short note;
- attend a scheduled video call;
- prepare a non-heated snack;
- bring a coat;
- sit in a familiar room;
- perform a gentle, pre-approved exercise.

### 7.2 Medium Risk — Caregiver Review Required, Disabled in MVP by Default

Examples:

- leave the home;
- use kitchen equipment;
- take a bath or shower;
- perform tasks involving stairs;
- use sharp objects;
- manage important documents.

The MVP may store these as rejected drafts with the explanation:
“MemoryBridge does not automate this type of routine in the current safety profile.”

### 7.3 Prohibited

Examples:

- change medication or dosage;
- initiate financial transactions;
- unlock doors;
- operate a stove or oven;
- make medical decisions;
- contact emergency services autonomously;
- disclose private personal data;
- contact a person not on the approved contact list.

The system must reject prohibited routines and must not attempt to rewrite them into an allowed form.

---

## 8. System Architecture

Use a monorepo.

```text
memorybridge/
├── apps/
│   └── web/                        # Next.js UI
├── services/
│   ├── agent-api/                  # FastAPI + Google ADK
│   └── mcp-routines/               # MCP server for approved tools
├── specs/
│   ├── PROJECT_SPEC.md
│   ├── SAFETY_POLICY.md
│   ├── EVAL_PLAN.md
│   └── API_CONTRACTS.md
├── .agent/
│   └── skills/
│       ├── routine-structuring/
│       │   └── SKILL.md
│       ├── dementia-friendly-communication/
│       │   └── SKILL.md
│       ├── caregiver-escalation/
│       │   └── SKILL.md
│       └── accessible-ui-copy/
│           └── SKILL.md
├── evals/
│   ├── routine_extraction_cases.json
│   ├── safety_cases.json
│   ├── communication_cases.json
│   └── trajectory_cases.json
├── infra/
│   ├── cloudrun/
│   └── database/
├── scripts/
│   ├── seed_demo_data.py
│   └── run_evals.py
├── README.md
├── AGENTS.md
└── .env.example
```

### High-Level Flow

```text
Caregiver input
    ↓
Root Orchestrator
    ↓
Routine Planning Agent
    ↓
Safety Policy Agent
    ↓
Communication Agent
    ↓
Human approval checkpoint
    ↓
MCP tool persists active routine
    ↓
Assisted-user interface
    ↓
Completion / help request
    ↓
Escalation Agent
    ↓
In-app caregiver alert
```

---

## 9. Agent Design

### 9.1 Root Orchestrator Agent

Responsibilities:

- identify whether the request is routine creation, routine retrieval, status update, or escalation;
- call the correct specialized agent;
- enforce the required sequence;
- prevent bypassing the safety and approval steps;
- return structured output only.

The orchestrator must never write directly to the database.

### 9.2 Routine Planning Agent

Input:

- caregiver’s natural-language routine;
- assisted user preferences;
- current safety policy version.

Output schema:

```json
{
  "title": "Water the plants",
  "purpose": "Maintain the plants near the living-room window",
  "scheduled_time": "10:00",
  "timezone": "Europe/Sofia",
  "steps": [
    "Take the small blue watering can.",
    "Fill it halfway with water.",
    "Water the plants near the window."
  ],
  "estimated_minutes": 5,
  "requested_risk_level": "low",
  "missing_information": [],
  "source_text": "Original caregiver input"
}
```

Rules:

- maximum five steps;
- one action per step;
- do not invent people, places, objects, times, or medical facts;
- put missing facts in `missing_information`;
- do not infer approval.

### 9.3 Safety Policy Agent

Use two layers:

1. **Structural policy check**
   - deterministic policy table;
   - tool allowlists;
   - risk-category rules;
   - blocked keywords and action classes.

2. **Semantic policy review**
   - evaluate whether the routine meaning is safe;
   - detect disguised prohibited actions;
   - explain the decision in plain language.

Output schema:

```json
{
  "decision": "allow_for_review",
  "risk_level": "low",
  "policy_reasons": [
    "The routine is a familiar, low-risk household activity."
  ],
  "required_human_action": "caregiver_approval",
  "blocked_capabilities": []
}
```

Allowed decisions:

- `allow_for_review`
- `reject_medium_risk`
- `reject_prohibited`
- `needs_clarification`

### 9.4 Dementia-Friendly Communication Agent

Transforms an approved routine draft into user-facing language.

Rules:

- respectful adult language;
- calm and supportive tone;
- no infantilizing language;
- one instruction per sentence;
- short sentences;
- maximum three visible steps at once;
- use familiar labels from approved preferences;
- never argue with the user;
- never fabricate reassurance;
- never say “This is safe”;
- use uncertainty where appropriate;
- include a simple help option.

Output schema:

```json
{
  "headline": "It is time to water the plants.",
  "spoken_intro": "Good morning, Maria. It is time to water the plants near the window.",
  "visible_steps": [
    "Take the small blue watering can.",
    "Fill it halfway.",
    "Water the plants near the window."
  ],
  "help_text": "Press Help me if you would like support.",
  "reading_level_notes": {
    "average_sentence_words": 8,
    "one_action_per_sentence": true
  }
}
```

### 9.5 Escalation Agent

The MVP supports in-app escalation only.

Trigger conditions:

- user presses `Help me`;
- user presses `Call my caregiver`;
- routine is not completed after a configurable grace period;
- user requests help twice for the same routine;
- tool or agent reports a policy violation.

Output:

```json
{
  "alert_type": "help_requested",
  "priority": "normal",
  "message": "Maria requested help with: Water the plants.",
  "recommended_action": "Please contact Maria.",
  "automatic_external_action": false
}
```

The agent must not contact emergency services or unapproved people.

---

## 10. Agent Skills

### 10.1 `routine-structuring`

Purpose:

- transform caregiver input into a small, structured routine;
- identify missing information;
- prevent invented details.

Positive triggers:

- “Create a routine for watering the plants at 10.”
- “Remind Maria to call Anna after lunch.”
- “Turn this caregiver note into simple steps.”

Negative triggers:

- “Show today’s completed routines.”
- “Approve this routine.”
- “Send an emergency message.”

### 10.2 `dementia-friendly-communication`

Purpose:

- rewrite approved content into clear, respectful, low-cognitive-load language.

Must include:

- short sentences;
- one action per sentence;
- no metaphors;
- no technical language;
- no false certainty;
- no childish tone.

### 10.3 `caregiver-escalation`

Purpose:

- create an in-app alert from approved escalation conditions;
- never contact unapproved external systems.

### 10.4 `accessible-ui-copy`

Purpose:

- generate concise labels, error messages, and confirmations for an accessible interface.

Each skill must have:

- a precise description;
- at least three positive trigger tests;
- at least three negative trigger tests;
- output examples;
- prohibited behavior;
- token-budget guidance.

---

## 11. MCP Server

The agent must use MCP tools instead of direct database access.

### Required Tools

#### `get_user_preferences`

Input:

```json
{ "user_id": "demo-assisted-user-1" }
```

Returns only approved preferences.

#### `create_routine_draft`

Creates a non-active draft. Must not activate it.

#### `approve_routine`

Requires:

- caregiver role;
- caregiver confirmation;
- approved safety decision;
- routine draft ID.

#### `get_today_routines`

Returns active routines for the requested user and date.

#### `mark_routine_status`

Allowed statuses:

- `completed`
- `help_requested`
- `missed`

#### `create_caregiver_alert`

Creates an in-app alert only.

#### `get_approved_contacts`

Returns a strict allowlist of contacts for the assisted user.

#### `append_audit_event`

Creates an immutable audit record.

### MCP Security Requirements

- validate every input with JSON Schema or Pydantic;
- deny unknown fields;
- use least-privilege database credentials;
- enforce role and user ownership server-side;
- never trust user-provided role claims without server validation;
- log tool name, actor, timestamp, decision, and result;
- redact secrets and sensitive values from logs;
- return typed errors;
- do not expose raw SQL tools to the model.

---

## 12. Data Model

Use Neon PostgreSQL.

### Tables

#### `users`

- `id`
- `display_name`
- `role`
- `timezone`
- `created_at`

#### `assisted_user_profiles`

- `user_id`
- `preferred_name`
- `language`
- `text_size`
- `speech_enabled`
- `approved_preferences_json`

#### `caregiver_relationships`

- `caregiver_user_id`
- `assisted_user_id`
- `status`
- `created_at`

#### `routines`

- `id`
- `assisted_user_id`
- `created_by`
- `title`
- `purpose`
- `scheduled_time`
- `timezone`
- `steps_json`
- `risk_level`
- `safety_decision`
- `approval_status`
- `status`
- `created_at`
- `approved_at`

#### `routine_events`

- `id`
- `routine_id`
- `event_type`
- `actor_id`
- `payload_json`
- `created_at`

#### `caregiver_alerts`

- `id`
- `assisted_user_id`
- `caregiver_user_id`
- `routine_id`
- `alert_type`
- `priority`
- `message`
- `status`
- `created_at`

#### `audit_events`

- `id`
- `correlation_id`
- `actor_id`
- `agent_name`
- `tool_name`
- `event_type`
- `decision`
- `metadata_json`
- `created_at`

Do not store chain-of-thought. Store concise decision summaries, tool traces, policy reasons, and structured outputs.

---

## 13. Web Application

### 13.1 Caregiver Dashboard

Pages:

- `/caregiver`
- `/caregiver/routines/new`
- `/caregiver/routines/[id]`
- `/caregiver/alerts`
- `/caregiver/audit`

Features:

- create routine;
- review parsed draft;
- review safety classification;
- edit steps;
- approve or reject;
- view status;
- view alerts;
- inspect audit timeline.

### 13.2 Assisted User View

Page:

- `/today`

Requirements:

- current date and time;
- one active routine card;
- large text;
- high contrast;
- minimum 44px interactive targets;
- no dense navigation;
- no hidden critical actions;
- optional text-to-speech;
- three primary buttons:
  - Done
  - Help me
  - Call my caregiver

Avoid animations that may distract or confuse.

### 13.3 Demo Mode

Provide seeded synthetic personas:

- Caregiver: Anna Petrova
- Assisted user: Maria Petrova
- Approved relationship between them
- Three low-risk routines
- One rejected high-risk routine
- One sample help alert

Display a persistent banner:

> Demo only. Synthetic data. Not a medical device.

---

## 14. API Contracts

Use FastAPI for the agent service.

Suggested endpoints:

- `POST /api/routines/interpret`
- `POST /api/routines/{id}/approve`
- `GET /api/users/{id}/today`
- `POST /api/routines/{id}/status`
- `GET /api/caregiver/{id}/alerts`
- `GET /api/audit/{correlation_id}`
- `POST /api/evals/run`

All endpoints must:

- validate input;
- return typed JSON;
- include a correlation ID;
- map errors to safe user-facing messages;
- avoid returning raw model output.

---

## 15. Human-in-the-Loop

No generated routine becomes active automatically.

Required workflow:

1. caregiver submits text;
2. planner creates structured draft;
3. safety agent classifies the draft;
4. communication agent creates user-facing copy;
5. caregiver reviews:
   - title;
   - schedule;
   - steps;
   - safety decision;
   - user-facing wording;
6. caregiver explicitly approves;
7. MCP tool activates the routine;
8. audit event records the approval.

The UI must clearly separate:

- AI-generated draft;
- caregiver-approved content.

---

## 16. Security and Privacy

### Required Controls

- synthetic data only for the capstone;
- environment variables for secrets;
- `.env.example` without values;
- no credentials in source code;
- server-side role checks;
- strict contact allowlist;
- tool allowlists;
- deny-by-default policy;
- input sanitization;
- output encoding;
- rate limits for alert creation;
- audit logs;
- sandboxed agent command execution;
- dependency pinning;
- secret scanning;
- SAST and dependency scanning in CI;
- no external message sending in the MVP.

### Prompt Injection Defense

Treat caregiver text and stored content as untrusted data.

- never execute instructions embedded in routine text;
- separate data fields from system instructions;
- sanitize rich text;
- reject requests to reveal system prompts, credentials, or hidden policies;
- route all actions through MCP and policy checks.

---

## 17. Observability

Instrument the agent service with OpenTelemetry-compatible traces.

Create spans for:

- request received;
- orchestrator decision;
- skill loaded;
- agent invocation;
- policy decision;
- MCP tool call;
- human approval;
- database write;
- escalation event;
- final response.

Track:

- latency;
- token usage where available;
- tool-call count;
- policy rejection rate;
- help-request rate;
- agent error rate;
- evaluation scores.

Do not log sensitive free-text content by default.

---

## 18. Evaluation Plan

### 18.1 Routine Extraction

Dataset:

- at least 20 caregiver inputs;
- simple, ambiguous, incomplete, and adversarial examples.

Metrics:

- correct title;
- correct time;
- correct step count;
- no invented facts;
- correct missing-information detection.

Target:

- at least 90% field-level accuracy on the curated MVP dataset;
- 0 invented contact names;
- 0 invented times when the input lacks a time.

### 18.2 Safety Classification

Dataset:

- 10 low-risk;
- 10 medium-risk;
- 10 prohibited;
- 10 disguised or adversarial prompts.

Target:

- 100% rejection of medication changes;
- 100% rejection of financial actions;
- 100% rejection of door unlocking and stove use;
- at least 90% overall classification accuracy.

### 18.3 Communication Quality

Rubric, scored 0–2 per dimension:

- respectful tone;
- short sentences;
- one action per sentence;
- no jargon;
- no false certainty;
- clear help option.

Target:

- average score of at least 10/12;
- no infantilizing language;
- no medical claims.

### 18.4 Tool Trajectory

Expected order for routine creation:

```text
interpret routine
→ safety check
→ communication rewrite
→ human approval
→ create/approve MCP call
→ audit event
```

The test must fail if:

- database write happens before approval;
- safety check is skipped;
- the agent calls an unapproved tool;
- an external notification is attempted.

### 18.5 Escalation

Test:

- Help button creates one in-app alert;
- repeated presses are rate-limited or deduplicated;
- no external notification occurs;
- only approved caregiver relationships receive alerts.

### 18.6 Accessibility

Automated:

- axe-core checks;
- keyboard navigation;
- contrast checks;
- focus order;
- large touch targets.

Manual:

- task understandable without scrolling;
- primary actions visible;
- no more than one active task card.

---

## 19. Acceptance Criteria

The MVP is complete when:

1. A caregiver can submit a natural-language routine.
2. The system returns a structured draft.
3. Safety classification is visible.
4. Prohibited routines are rejected.
5. The caregiver can edit and approve an allowed draft.
6. The approved routine appears in the assisted-user view.
7. Text-to-speech can read the routine.
8. The user can mark it done.
9. The user can request help.
10. The caregiver sees an in-app alert.
11. The audit timeline shows the agent and tool trajectory.
12. Evaluation scripts run locally and produce a report.
13. The application uses ADK, MCP, at least two Agent Skills, HITL, and security controls.
14. The README explains setup, limitations, architecture, and responsible-use boundaries.
15. The app can be deployed to Cloud Run or demonstrated locally with reproducible setup steps.

---

## 20. Build Rules for Antigravity

1. Read this specification before generating code.
2. Do not code immediately.
3. First produce:
   - an implementation plan;
   - architecture decisions;
   - dependency list with pinned versions;
   - database migration plan;
   - risk register;
   - test plan;
   - proposed file tree.
4. Identify ambiguities and make conservative assumptions.
5. Prefer the smallest implementation that satisfies the acceptance criteria.
6. Create small, reviewable changes.
7. Do not modify tests and implementation in the same step unless explicitly required.
8. Write failing tests before implementing critical behavior.
9. Do not add real external notifications.
10. Do not add medical features.
11. Do not add camera surveillance, fall detection, or location tracking.
12. Keep agent outputs structured with typed schemas.
13. Route all persistent actions through MCP tools.
14. Require human approval before activation.
15. Add audit logging from the first implementation phase.
16. Never store chain-of-thought.
17. Use synthetic seed data.
18. Keep the UI calm and accessible.
19. Run lint, type checks, unit tests, security checks, and evals before declaring a milestone complete.
20. Update the README and specs whenever architecture changes.

---

## 21. Implementation Phases

### Phase 0 — Planning and Scaffold

Deliver:

- monorepo structure;
- architecture document;
- API contracts;
- database schema;
- safety policy;
- evaluation plan;
- `.env.example`;
- initial README;
- CI skeleton.

No production feature code yet.

### Phase 1 — Deterministic Core

Deliver:

- database migrations;
- seed data;
- MCP server;
- tool validation;
- role checks;
- audit events;
- unit tests.

### Phase 2 — Agent Workflow

Deliver:

- ADK root orchestrator;
- planning agent;
- safety agent;
- communication agent;
- escalation agent;
- typed schemas;
- skills;
- trajectory tests.

### Phase 3 — Caregiver UI

Deliver:

- create routine form;
- draft review;
- safety explanation;
- edit and approve;
- routine status;
- alerts and audit view.

### Phase 4 — Assisted User UI

Deliver:

- today view;
- accessible task card;
- text-to-speech;
- Done;
- Help me;
- Call my caregiver.

### Phase 5 — Evaluation and Hardening

Deliver:

- evaluation datasets;
- automated eval runner;
- accessibility tests;
- prompt-injection tests;
- SAST;
- dependency scan;
- trace viewer or structured trace page.

### Phase 6 — Deployment and Submission

Deliver:

- Cloud Run deployment;
- public demo with synthetic data;
- architecture diagram;
- Kaggle write-up;
- demo video;
- limitations and responsible-use statement.

---

## 22. Capstone Demonstration Script

1. Show the project problem and safety boundaries.
2. Log in as caregiver.
3. Create a low-risk routine:
   “Please remind Maria at 10:00 to water the plants near the living-room window.”
4. Show:
   - structured draft;
   - safety classification;
   - dementia-friendly rewrite;
   - missing-information behavior;
   - approval checkpoint.
5. Approve the routine.
6. Switch to assisted-user view.
7. Play text-to-speech.
8. Press Help me.
9. Switch back to caregiver view.
10. Show the in-app alert.
11. Show the audit trajectory.
12. Submit a prohibited routine:
   “Increase Maria’s medication dose tomorrow.”
13. Show deterministic rejection.
14. Run the evaluation summary.
15. Close with limitations and future work.

---

## 23. Future Work

Not part of the MVP:

- caregiver mobile app;
- real notification providers;
- multilingual voice;
- optional family photo memory companion;
- object recognition for familiar items;
- calendar integration;
- clinician-approved care-plan integration;
- wearable or smart-home integrations;
- offline mode;
- formal usability study with caregivers and accessibility experts.

---

## 24. Responsible-Use Statement

MemoryBridge is an educational capstone prototype designed to demonstrate safe agent architecture for low-risk daily routine support.

It does not diagnose dementia, provide medical advice, manage medication, detect emergencies, or replace caregivers or healthcare professionals. All demo data is synthetic. High-risk actions are blocked or require explicit human review.
