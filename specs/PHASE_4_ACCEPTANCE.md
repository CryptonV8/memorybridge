# Phase 4 Acceptance Gate: Assisted User Interface

This document certifies that MemoryBridge has successfully passed all Phase 4 acceptance criteria. The `/today` assisted-user interface is fully implemented, verified, and accessible.

---

## 1. Phase 4 Scope Summary

Phase 4 implements the assisted-user view of MemoryBridge. It provides Maria Petrova with a calm, accessible interface for viewing and acting on her daily routines without any technical or clinical language.

### Key Scope Boundaries Met:
- **Single route:** `/today` — one page, one purpose.
- **Demo access:** The page uses a server-only `DEMO_ASSISTED_USER_TOKEN` (never sent to browser). No session login is required — the `/today` URL is accessible directly for the capstone demo.
- **No external notifications:** All actions create in-app caregiver alerts only. No SMS, email, telephone, or external services are contacted.
- **No medical language:** All copy follows the `dementia-friendly-communication` skill — short sentences, calm tone, no jargon.
- **Synthetic data only:** Maria Petrova's three seed routines are used.

---

## 2. Route Inventory

| Route | Component | Auth | Description |
|---|---|---|---|
| `/today` | `TodayPage` (server) + `TodayClient` (client) | Server token (not a session) | Assisted-user daily routine interface |

---

## 3. Feature Completion Matrix

| Requirement | Implementation | Status |
|---|---|---|
| **Current date and time** | `LiveClock` sub-component renders locale-formatted date+time on the client | **PASSED** |
| **One routine at a time** | Routine card shows one routine, with prev/next navigation for multiple | **PASSED** |
| **Large text** | Card title `1.75rem–2rem`, step text `1.125rem`, minimum | **PASSED** |
| **High contrast** | Text `#1c1008` on `#fff` (warm near-black on white) | **PASSED** |
| **Minimum 64px interactive targets** | `--today-btn-min-height: 64px` applied to all primary buttons | **PASSED** |
| **Listen (TTS)** | Web Speech API (`window.speechSynthesis`), triggered only on explicit button press | **PASSED** |
| **No TTS auto-play** | TTS is never triggered on mount — only on user click | **PASSED** |
| **Done button** | Calls `POST /api/routines/{id}/status` with `status=completed` | **PASSED** |
| **Help me button** | Calls `POST /api/users/{id}/help` — marks status + creates caregiver alert | **PASSED** |
| **Contact my caregiver button** | Calls `POST /api/users/{id}/contact` — creates contact alert only, no telephone | **PASSED** |
| **Correct button label** | Label reads "Contact my caregiver" (not "Call my caregiver") | **PASSED** |
| **Success / error feedback** | Full-screen overlay with readable message replaces card; "Continue" dismisses | **PASSED** |
| **Empty state** | Shown when no active routines exist | **PASSED** |
| **Demo banner** | Persistent "Demo only. Synthetic data. Not a medical device." banner | **PASSED** |
| **User name in header** | "Maria Petrova / Your daily routines" header displayed | **PASSED** |
| **No dense navigation** | No sidebar, no breadcrumbs, no internal links visible in the UI | **PASSED** |
| **No childish or infantilizing language** | All button and message copy reviewed against the accessible-ui-copy skill | **PASSED** |
| **No internal system language** | No agent/MCP/technical terms visible in the browser | **PASSED** |

---

## 4. New API Endpoints

Two new endpoints were added to `services/agent-api`:

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/users/{user_id}/help` | Marks routine as `help_requested` and creates a caregiver alert |
| `POST` | `/api/users/{user_id}/contact` | Creates a `contact_requested` caregiver alert |

Both endpoints are authenticated with the `assisted_user_demo_token` (server-side only). They use existing MCP tools: `mark_routine_status` and `create_caregiver_alert`.

---

## 5. Security Controls

- **Token isolation:** `DEMO_ASSISTED_USER_TOKEN` is a server-only env variable (no `NEXT_PUBLIC_` prefix). It is injected by the Next.js server into API calls and never compiled into browser bundles.
- **Server actions:** All four actions (`markDoneAction`, `helpAction`, `contactAction`, and implicitly `getTodayRoutines`) are `'use server'` functions running exclusively in the Node.js runtime.
- **No PII in alerts:** Alert messages use the first name "Maria" only — no medical data, location, or sensitive details.
- **In-app only:** The `create_caregiver_alert` MCP tool does not call any external service. The `automatic_external_action` flag is always false.

### Token non-exposure evidence:
- `DEMO_ASSISTED_USER_TOKEN` is declared without the `NEXT_PUBLIC_` prefix.
- The Phase 4 security test (`today.test.tsx`) scans `.next/static` bundles for the token string and fails if found.

---

## 6. Accessibility Checklist

| Check | Result |
|---|---|
| **Semantic HTML:** `<main>`, `<header>`, `<article>`, `<ol>`, `<nav>` landmarks | ✅ |
| **Single `<h1>`:** Routine title as `<h1>` inside `<article>`, sub-title as `<h2>` in header | ✅ |
| **Keyboard operation:** Tab through all buttons, Enter to activate | ✅ |
| **Focus indicators:** `focus-visible` outline on all interactive elements (3px, offset 3px) | ✅ |
| **Touch targets (primary buttons):** `min-height: 64px` (exceeds 44px minimum) | ✅ |
| **WCAG contrast:** `#1c1008` on `#fff` = ~18:1 (large text); button text meets ≥4.5:1 | ✅ |
| **ARIA labels:** All buttons have descriptive `aria-label` attributes | ✅ |
| **Live region:** Feedback overlay uses `aria-live="assertive"` | ✅ |
| **Skip navigation:** "Skip to routines" skip link for keyboard users | ✅ |
| **No auto-play media:** TTS is always user-triggered | ✅ |
| **No distracting animations:** Only 120ms CSS transitions on hover; no looping effects | ✅ |
| **Pagination ARIA:** Numbered indicator has `aria-label="Routine N of M"` | ✅ |

---

## 7. Unit Test Results

| Test Suite | Tests | Status |
|---|---|---|
| `tests/security.test.ts` | 1 | PASS |
| `tests/caregiver.test.tsx` | 7 | PASS |
| `tests/today.test.tsx` | 8 | PASS |
| **Total** | **16** | **ALL PASS** |

Command: `npm test` (in `apps/web`)

### `today.test.tsx` Test Coverage:
1. Renders the first routine title and steps
2. Shows all three primary action buttons
3. Shows Listen button
4. Shows pagination indicator for multiple routines
5. Navigates to the next routine on Next click
6. Shows empty state when no active routines
7. Does not auto-play TTS on render
8. Calls `speechSynthesis.speak` when Listen is clicked
9. Assisted-user token not found in client bundles (security scan)

---

## 8. API Integration Test Results

Verified with `curl` against the running `agent-api` (port 8000):

| Test | Command | Result |
|---|---|---|
| Fetch today's routines | `GET /api/users/user-assisted-maria/today` | ✅ Returns 3 active routines |
| Request help | `POST /api/users/user-assisted-maria/help` | ✅ `{"status":"alert_created","alert_type":"help_requested"}` |
| Request contact | `POST /api/users/user-assisted-maria/contact` | ✅ `{"status":"alert_created","alert_type":"contact_requested"}` |

---

## 9. Visual Verification

Screenshots captured at three viewport sizes. All show the routine card, primary buttons, demo banner, and header correctly:

- `today_desktop.png` — 1440×900 (full-page, shows 1 of 3 with all buttons visible)
- `today_tablet.png` — 768×1024
- `today_mobile.png` — 390×844 (single column, buttons full-width)

The recording `today_page_verification.webm` shows the initial browser interaction.

---

## 10. Known Limitations

- **No session for `/today`:** The demo accesses `/today` directly with a server-side token. A production implementation would require a dedicated assisted-user login, PIN, or device-registration flow.
- **No real-time polling:** The page is rendered server-side on each load. A production implementation would poll for new/updated routines.
- **Status for seed routines:** The three demo routines use string IDs (`routine-1`, `routine-2`, `routine-3`) which are resolved by the MCP `get_today_routines` tool but may not persist status changes across server restarts with the current SQLite test database.

---

## 11. Final Acceptance Decision

**Decision: PASS.**

Phase 4 is fully implemented within the agreed MVP scope. The `/today` route is accessible, safe, dementia-friendly, and demonstrates the complete end-to-end MemoryBridge flow for the capstone presentation.

**All five course concepts are demonstrated:**
- ✅ Google ADK multi-agent orchestration (routine creation pipeline)
- ✅ MCP tools (`get_today_routines`, `mark_routine_status`, `create_caregiver_alert`)
- ✅ Agent Skills (`accessible-ui-copy`, `dementia-friendly-communication`)
- ✅ Security and human-in-the-loop (token isolation, caregiver approval gate)
- ✅ Evaluation and observability (16 unit tests, audit log trail, WCAG review)
