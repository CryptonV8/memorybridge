# MemoryBridge: Web Application

This is the Next.js web application for MemoryBridge. It serves as the primary caregiver web portal.

---

## 1. Local Development

### Prerequisites
Make sure the gateway API service (`agent-api` on port 8000) is running before starting the web application.

### Installation
```bash
npm install
```

### Run Server
Start the Next.js server in development mode on port 3000:
```bash
npm run dev -- -p 3000
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 2. Server-Side Security Boundary

- **Upstream Authorization:** The application gateway's `DEMO_CAREGIVER_TOKEN` is loaded purely from environment variables on the server.
- **Signed Cookie Session:** Caregivers are issued encrypted session cookies using `iron-session`. The client browser never receives the caregiver token, preventing token leakages.
- **Server-Only Execution:** Direct API fetch calls run strictly on the server (`lib/api-client.ts`). The browser never directly contacts `services/agent-api`.

---

## 3. Route Inventory

- `/login` - Demo login form.
- `/caregiver` - Dashboard.
- `/caregiver/routines/new` - Creation.
- `/caregiver/routines/[routineId]` - Detail review, safety alerts, edit form, and activation gates.
- `/caregiver/alerts` - Notifications.
- `/caregiver/audit` - Redacted logs audit trail.

---

## 4. Running Tests

### Unit & Security Tests
Verify components and static compilation bundles for caregiver token exposure:
```bash
npm test
```

### Playwright Integration (E2E)
```bash
npx playwright test
```
The integration suite automatically executes authentication, routine parsing, draft step editing, safety check validations, alerts logs, and audit logs.
