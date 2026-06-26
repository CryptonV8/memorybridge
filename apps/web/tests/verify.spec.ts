import { test, expect } from '@playwright/test';

const WEB_URL = process.env.WEB_URL || 'https://memorybridge-web-707123898547.europe-west3.run.app';

test.describe('MemoryBridge Remediation Smoke Checks', () => {

  test('1. Public home route loads and redirects to login', async ({ page }) => {
    const response = await page.goto(WEB_URL);
    expect(response?.ok()).toBeTruthy();
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('2. The assisted-user /maria URL correctly redirects to /today', async ({ page }) => {
    const response = await page.goto(`${WEB_URL}/maria`);
    expect(response?.ok()).toBeTruthy();
    await expect(page).toHaveURL(/.*\/today/);
    await expect(page.locator('text=Maria Petrova')).toBeVisible();
    await expect(page.locator('text=API Unavailable')).not.toBeVisible();
  });

  test('3. Caregiver dashboard loads routines without API Unavailable', async ({ page }) => {
    // Navigate directly (will redirect to login if not authenticated)
    await page.goto(`${WEB_URL}/login`);

    // Simulate login for demo caregiver
    await page.click('button:has-text("Login as Caregiver")');
    await expect(page).toHaveURL(/.*\/caregiver/);

    // Dashboard should not have API Unavailable
    await expect(page.locator('text=API Unavailable')).not.toBeVisible();

    // Check if routines loaded (assuming at least one routine exists like 'Morning tea')
    await expect(page.locator('text=Maria Petrova').first()).toBeVisible();

    // Direct unauthenticated request check inside the browser check:
    const backendRes = await page.request.get('https://memorybridge-backend-707123898547.europe-west3.run.app/health');
    // Because this doesn't have the Google ID token (IAM), it should be denied (401/403)
    expect([401, 403]).toContain(backendRes.status());
  });
});
