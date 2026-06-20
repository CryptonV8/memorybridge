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

## Local Development Commands (Phase 1.5)

Ensure you are using Python 3.11 (you can use `uv` to manage python versions). All backend commands should be run inside `services/mcp-routines`.

### 1. Setup & Dependencies

```bash
# Recreate virtual environment with Python 3.11 using uv
uv venv venv --python 3.11
source venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Database Migrations (Alembic)

```bash
# Run migrations on database defined in DATABASE_URL
alembic upgrade head
```

### 3. Run MCP Server

To start the standards-compliant MCP server locally using stdio transport:

```bash
python src/server.py
```

### 4. Client Smoke-Test Command

To smoke-test the running server from an external MCP client (verifying session initialization and tool listing):

```bash
python -c "
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def run():
    params = StdioServerParameters(command='python', args=['src/server.py'])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print('Successfully connected!')
            print('Exposed tools:', [t.name for t in tools.tools])
asyncio.run(run())
"
```

### 5. Running Tests

Note: Database integration tests and MCP protocol tests require a PostgreSQL database URL. They will fail clearly if run against SQLite or without configuration.

```bash
# To run unit tests only (no database required):
pytest -k "not integration and not protocol"

# To run all tests (requires TEST_DATABASE_URL to be set to a PostgreSQL database):
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
pytest
```

### 6. Seeding Demo Data

```bash
# To seed local/remote database (requires DATABASE_URL to be set):
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
python ../../scripts/seed_demo_data.py
```

### 7. Formatting, Linting, & Type Checking

```bash
# Formatting check
black --check src tests

# Linting
flake8 src tests

# Type Checking
mypy src
```


