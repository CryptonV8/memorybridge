# Evaluation Plan

## 1. Deterministic Unit Tests
Unit tests run locally with `pytest` and `jest`.
- **Database Schema Validation:** Checked constraints and foreign key fields.
- **Security Scans:** The unit test `security.test.ts` scans the generated production client bundles inside `.next/static` to verify that `demo-token-123` (sentinel value) is absent, preventing token leakage.

---

## 2. Dynamic Integration & E2E Workflows
Playwright verifies full workflow integration inside `e2e/caregiver.spec.ts`:
1. **Redirection Guard:** Visits protected caregiver page without a session and verifies redirection to `/login`.
2. **Authentication Flow:** Enters credentials, submits login form, and verifies routing to `/caregiver` dashboard.
3. **Routine Drafting Workflow:** Inputs a low-risk instruction ("Water patio flowers at 9am"), triggers interpretation, and validates routing to `/caregiver/routines/[id]`.
4. **Safety Verification:** Validates that the draft is marked as low risk and shows structural checks.
5. **Editing & Revalidation:** Edits step text, scheduled time, and title, confirming that the approval state is reset and safety policy re-checks are completed.
6. **Explicit Approval:** Verifies that activation requires checking the visual verification review statement before clicking the approve button.
7. **Prohibited Rejections:** Tests inputting prohibited tasks (e.g. medication changes) and checks that activation is disabled.
8. **Audit Trail Verification:** Navigates to `/caregiver/audit` and verifies the immutable audit logging events match the correlation ID.
9. **Alerts logs:** Views in-app notifications.

---

## 3. Manual Verification Checklist
- **Touch target sizing:** Verify touch sizes exceed 44 × 44 pixels.
- **Focus highlights:** Tab through input forms to verify focus ring visibility.
- **Skip navigation:** Press Tab on page load to access skip links.
