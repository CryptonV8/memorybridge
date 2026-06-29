import { test, expect } from '@playwright/test';

const WEB_URL = process.env.WEB_URL || 'https://memorybridge-web-biavov6twq-ey.a.run.app';

test.describe('Production Verification Smoke Checks', () => {

  test('End to End production verification', async ({ page }) => {
    // 1. Caregiver dashboard
    await page.goto(`${WEB_URL}/login`);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*\/caregiver/);
    
    // Create a routine to test approve/reject and Done
    await page.goto(`${WEB_URL}/caregiver/routines/new`);
    await page.fill('#instruction', 'Water the plants at 10 AM');
    await page.click('button:has-text("Generate Draft")');
    await expect(page).toHaveURL(/\/caregiver\/routines\/[0-9a-fA-F-]+/);
    
    // 2. Routine details and review (approve and reject)
    // Approve this one
    await page.locator('#confirm-approval').check();
    await page.click('button:has-text("Approve & Activate")');
    await expect(page.locator('text=Routine is currently active')).toBeVisible();

    // Refresh to confirm persisted state
    await page.reload();
    await expect(page.locator('text=Routine is currently active')).toBeVisible();

    const routineUrl = page.url();
    const routineId = routineUrl.split('/').pop();

    // Reject a prohibited one
    await page.goto(`${WEB_URL}/caregiver/routines/new`);
    await page.fill('#instruction', 'Give her extra sleeping pills at night');
    await page.click('button:has-text("Generate Draft")');
    await expect(page.locator('text=PROHIBITED RISK')).toBeVisible({ timeout: 15000 });
    
    // Refresh to confirm prohibited state persisted
    await page.reload();
    await expect(page.locator('text=PROHIBITED RISK')).toBeVisible();

    // 3. /today & Done & Help me
    await page.goto(`${WEB_URL}/today`);
    await expect(page.locator('text=Water the plants')).toBeVisible();

    // Click Help me
    await page.click('button:has-text("Help me")');
    await page.waitForTimeout(1000);

    // Refresh to confirm persistence
    await page.reload();
    await expect(page.locator('text=Water the plants')).toBeVisible();

    // Click Done
    await page.click('button:has-text("Done")');
    await page.waitForTimeout(1000);

    // Refresh to confirm persistence
    await page.reload();
    await expect(page.locator('text=Completed')).toBeVisible();

    // 4. Alerts
    await page.goto(`${WEB_URL}/caregiver/alerts`);
    await expect(page.locator('text=Help me')).toBeVisible();

    // 5. Audit lookup
    await page.goto(`${WEB_URL}/caregiver/audit`);
    
    // valid Correlation ID (routineId)
    await page.fill('input[placeholder*="Search by correlation ID"]', routineId as string);
    await page.click('button:has-text("Search")');
    await expect(page.locator('text=routine_created')).toBeVisible();

    // invalid Correlation ID
    await page.fill('input[placeholder*="Search by correlation ID"]', 'invalid-id-1234');
    await page.click('button:has-text("Search")');
    await expect(page.locator('text=No audit events found')).toBeVisible();
  });
});
