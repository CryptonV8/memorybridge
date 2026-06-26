# MemoryBridge — Demo Pre-Recording Checklist

Follow this checklist strictly before starting the screen recording for the Kaggle submission video.

## 1. Environment & Privacy Setup
- [ ] Ensure browser is at 1080p resolution or zoomed appropriately (125%-150% on 4K) for text readability.
- [ ] Hide browser bookmarks bar.
- [ ] Close all other browser tabs to prevent accidental exposure of private data.
- [ ] Turn on OS "Do Not Disturb" to block desktop notifications.
- [ ] Ensure terminal windows and Cloud Console tabs are hidden (no `.env` or Secret Manager values visible).
- [ ] Ensure the desktop background is neutral if visible.

## 2. System Health Check
- [ ] Verify the backend is healthy (`https://memorybridge-web-707123898547.europe-west3.run.app/api/health` should not return 500).
- [ ] Verify the Caregiver Portal loads (`https://memorybridge-web-707123898547.europe-west3.run.app/caregiver`).
- [ ] Verify the Assisted-User Portal loads (`https://memorybridge-web-707123898547.europe-west3.run.app/today`).
- [ ] Check for any unexpected red API error banners on the dashboards.

## 3. Data Reset (Mandatory)
To ensure the demo runs perfectly without duplicate data, reset the database to the clean synthetic state:
1. Open a terminal (off-screen).
2. Run the idempotent seed script:
   ```bash
   ./infra/cloudrun/seed.sh --reset --confirm-reset
   ```
3. Refresh both dashboards to verify only the default synthetic routines (e.g., "Morning tea") are present.

## 4. Flow Pre-Flight Check (Dry Run)
*Perform this dry run off-camera before the final recording.*
- [ ] **Routine Creation:** Submit "Remind Maria to water the plants at 10 AM". Ensure it drafts correctly with an `allow_for_review` badge.
- [ ] **Approval:** Click "Approve". Verify it moves to active status.
- [ ] **Assisted UI:** Open `/today`. Verify "Water the plants" appears.
- [ ] **Help Alert:** Click "Help me". Verify the Caregiver dashboard receives the alert.
- [ ] **Medication Rule:** Submit "Increase medication dose". Verify it is strictly rejected.
- [ ] **Audit Trail:** Check the audit logs on the completed routine.
- [ ] **RESET DATA AGAIN:** Run `./infra/cloudrun/seed.sh --reset --confirm-reset` one final time to wipe the dry-run data before hitting record.

## 5. Live Failure Recovery Procedure
If a network error or API timeout occurs *during* the live recording:
1. **Do not panic.** Stop the recording.
2. Check the Cloud Run logs for `memorybridge-backend` to identify the issue.
3. If it was a Gemini API timeout, simply reset the data (Step 3) and start the recording again.
4. If a bug is found, fix it, redeploy, run the smoke checks (`./infra/cloudrun/smoke-check.sh`), reset the data, and retry.
5. If the live model continues to fail, use the deterministic fallback by redeploying the backend with `AGENT_PROVIDER=fake`. (Note: Be transparent in the video if using the fallback mode).

## 6. Backup Assets
- [ ] Ensure `submission/MEDIA_GALLERY.md` screenshots are readily available in case the live application experiences a severe outage right before the deadline.
