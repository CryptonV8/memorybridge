import { test, expect } from '@playwright/test';
import path from 'path';

const ARTIFACTS_DIR = '/home/d1/.gemini/antigravity-ide/brain/de768346-52c5-444a-aba6-4f308c9c15ff';

async function capture(page: any, name: string) {
  // Desktop
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, `${name}_desktop.png`) });

  // Tablet
  await page.setViewportSize({ width: 768, height: 1024 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, `${name}_tablet.png`) });

  // Mobile
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, `${name}_mobile.png`) });

  // Restore Desktop
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.waitForTimeout(200);
}

test('Caregiver Workflow & Screenshots', async ({ page }) => {
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER EXCEPTION:', err.message));

  // 1. Login View
  await page.goto('/login');
  await expect(page.locator('h1')).toContainText('MemoryBridge Demo');
  await capture(page, 'login');

  // Login
  await page.click('button[type="submit"]');

  // 2. Caregiver Dashboard View
  await expect(page).toHaveURL(/\/caregiver/);
  await expect(page.locator('h1')).toContainText('Dashboard');
  await capture(page, 'dashboard');

  // 3. New Routine Form
  await page.click('text=Create Routine');
  await expect(page).toHaveURL(/\/caregiver\/routines\/new/);
  await page.waitForLoadState('networkidle');
  await capture(page, 'new_routine');
  
  // Wait to ensure client-side hydration settles
  await page.waitForTimeout(1000);

  // Fill in form and submit
  const textarea = page.locator('#instruction');
  await textarea.waitFor({ state: 'visible' });
  await textarea.click();
  await textarea.fill('');
  await textarea.pressSequentially('Water patio flowers at 9am', { delay: 30 });
  await page.waitForTimeout(1000); // Wait longer for React to sync state
  await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'filled_routine_form.png') });

  const submitBtn = page.locator('button:has-text("Generate Draft")');
  await expect(submitBtn).toBeEnabled();
  await submitBtn.click();

  // 4. Allowed Draft Review
  await expect(page).toHaveURL(/\/caregiver\/routines\/[0-9a-fA-F-]+/);
  await expect(page.locator('h1')).toContainText('Water patio flowers');
  // It should be low risk since it is watering plants
  await expect(page.locator('text=LOW RISK')).toBeVisible();
  await capture(page, 'allowed_draft');

  // Check safety confirmation checkbox and approve/activate
  await page.click('#confirm-approval');
  await page.click('button:has-text("Approve & Activate")');
  await page.waitForTimeout(1000);

  // 5. Active Routine Details
  await expect(page.locator('text=Routine is currently active')).toBeVisible();
  await capture(page, 'active_details');

  // 6. View Audit Timeline
  await page.click('text=View Audit Timeline');
  await expect(page).toHaveURL(/\/caregiver\/audit/);
  await expect(page.locator('h1')).toContainText('System Audit Log');
  await capture(page, 'audit');

  // 7. Prohibited Draft Details
  await page.goto('/caregiver/routines/routine-4-rejected');
  await expect(page.locator('h1')).toContainText('Change medication');
  await expect(page.locator('text=PROHIBITED RISK')).toBeVisible();
  await expect(page.locator('text=Routine Blocked by Safety Policy')).toBeVisible();
  await capture(page, 'prohibited_details');

  // 8. Alerts view
  await page.goto('/caregiver/alerts');
  await expect(page.locator('h1')).toContainText('Caregiver Alerts');
  await capture(page, 'alerts');
});

