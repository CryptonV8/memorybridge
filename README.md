# MemoryBridge

## Executive Summary
MemoryBridge is an educational capstone prototype and safety-first assistive application tailored for people living with early-stage dementia, alongside the family members or caregivers who support them.

The application translates natural language caregiver instructions into simple, low-risk, and structured daily routines using a multi-agent system. It incorporates strict safety policies, deterministic MCP tools, human-in-the-loop approval, and dementia-friendly communication formatting to deliver safe and accessible guidance.

## Personas
1. **Assisted User:** A person living with early-stage dementia needing minimal cognitive load, accessible interfaces, and straightforward ways to request help or mark tasks as done.
2. **Caregiver:** A trusted family member or professional needing an easy way to create routines, review AI interpretations, grant approvals, and receive alerts.
3. **System Administrator:** A role for managing policies, testing, and evaluation runs.

## Safety Boundaries & Non-Goals
**MemoryBridge is NOT a medical device.**
- **Non-Goals:** It will not diagnose dementia, provide medical advice, alter medication, detect emergencies, manage finances, unlock doors, or replace professional care.
- **Data:** Uses synthetic demo data ONLY. No real patient records will be processed.
- **Interactions:** No external communications (SMS, email, emergency services) are supported in the MVP. In-app alerts only.
- **Authorization:** Employs a deny-by-default policy. Caregivers MUST explicitly approve any routine before it becomes active.

## Monorepo Structure

```
memorybridge/
├── apps/
│   └── web/                        # Next.js Caregiver & Assisted User UI
├── services/
│   ├── agent-api/                  # FastAPI + Google ADK agent service
│   └── mcp-routines/               # MCP server for deterministic persistence
├── specs/                          # Design and planning artifacts
├── .agent/
│   └── skills/                     # ADK Agent Skills (SKILL.md)
├── evals/                          # Evaluation datasets
├── infra/                          # Cloud Run and Database infrastructure
└── scripts/                        # Seeding and evaluation runner scripts
```

## Responsible Use
MemoryBridge is a prototype demonstrating safe agent architecture. It employs sandboxed execution, strict human-in-the-loop requirements, and typed MCP schemas to guarantee deterministic persistence. High-risk actions are categorically blocked and require immediate human escalation.
