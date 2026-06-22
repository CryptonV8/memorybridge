# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: caregiver.spec.ts >> Caregiver Workflow & Screenshots
- Location: e2e/caregiver.spec.ts:27:5

# Error details

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('h1')
Expected substring: "Water patio flowers"
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('h1')

```

```yaml
- alert
- link "Skip to main content":
  - /url: "#main-content"
- paragraph: Demo only. Synthetic data. MemoryBridge is not a medical device and does not replace caregivers or healthcare professionals.
- banner:
  - text: MemoryBridge Caregiver
  - navigation "Primary navigation":
    - link "Dashboard":
      - /url: /caregiver
    - link "Create Routine":
      - /url: /caregiver/routines/new
    - link "Alerts":
      - /url: /caregiver/alerts
    - link "Audit":
      - /url: /caregiver/audit
  - text: "Anna Petrova Supporting: Maria Petrova"
  - button "Log out of demo": Logout
- main:
  - link "Back to Dashboard":
    - /url: /caregiver
  - alert:
    - heading "Unable to load routine" [level=2]
    - paragraph: An error occurred
    - link "← Return to Dashboard":
      - /url: /caregiver
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | import path from 'path';
  3   | 
  4   | const ARTIFACTS_DIR = '/home/d1/.gemini/antigravity-ide/brain/de768346-52c5-444a-aba6-4f308c9c15ff';
  5   | 
  6   | async function capture(page: any, name: string) {
  7   |   // Desktop
  8   |   await page.setViewportSize({ width: 1440, height: 900 });
  9   |   await page.waitForTimeout(500);
  10  |   await page.screenshot({ path: path.join(ARTIFACTS_DIR, `${name}_desktop.png`) });
  11  | 
  12  |   // Tablet
  13  |   await page.setViewportSize({ width: 768, height: 1024 });
  14  |   await page.waitForTimeout(500);
  15  |   await page.screenshot({ path: path.join(ARTIFACTS_DIR, `${name}_tablet.png`) });
  16  | 
  17  |   // Mobile
  18  |   await page.setViewportSize({ width: 390, height: 844 });
  19  |   await page.waitForTimeout(500);
  20  |   await page.screenshot({ path: path.join(ARTIFACTS_DIR, `${name}_mobile.png`) });
  21  | 
  22  |   // Restore Desktop
  23  |   await page.setViewportSize({ width: 1440, height: 900 });
  24  |   await page.waitForTimeout(200);
  25  | }
  26  | 
  27  | test('Caregiver Workflow & Screenshots', async ({ page }) => {
  28  |   page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
  29  |   page.on('pageerror', err => console.log('BROWSER EXCEPTION:', err.message));
  30  | 
  31  |   // 1. Login View
  32  |   await page.goto('/login');
  33  |   await expect(page.locator('h1')).toContainText('MemoryBridge Demo');
  34  |   await capture(page, 'login');
  35  | 
  36  |   // Login
  37  |   await page.click('button[type="submit"]');
  38  | 
  39  |   // 2. Caregiver Dashboard View
  40  |   await expect(page).toHaveURL(/\/caregiver/);
  41  |   await expect(page.locator('h1')).toContainText('Dashboard');
  42  |   await capture(page, 'dashboard');
  43  | 
  44  |   // 3. New Routine Form
  45  |   await page.click('text=Create Routine');
  46  |   await expect(page).toHaveURL(/\/caregiver\/routines\/new/);
  47  |   await page.waitForLoadState('networkidle');
  48  |   await capture(page, 'new_routine');
  49  |   
  50  |   // Wait to ensure client-side hydration settles
  51  |   await page.waitForTimeout(1000);
  52  | 
  53  |   // Fill in form and submit
  54  |   const textarea = page.locator('#instruction');
  55  |   await textarea.waitFor({ state: 'visible' });
  56  |   await textarea.click();
  57  |   await textarea.fill('');
  58  |   await textarea.pressSequentially('Water patio flowers at 9am', { delay: 30 });
  59  |   await page.waitForTimeout(1000); // Wait longer for React to sync state
  60  |   await page.screenshot({ path: path.join(ARTIFACTS_DIR, 'filled_routine_form.png') });
  61  | 
  62  |   const submitBtn = page.locator('button:has-text("Generate Draft")');
  63  |   await expect(submitBtn).toBeEnabled();
  64  |   await submitBtn.click();
  65  | 
  66  |   // 4. Allowed Draft Review
  67  |   await expect(page).toHaveURL(/\/caregiver\/routines\/[0-9a-fA-F-]+/);
> 68  |   await expect(page.locator('h1')).toContainText('Water patio flowers');
      |                                    ^ Error: expect(locator).toContainText(expected) failed
  69  |   // It should be low risk since it is watering plants
  70  |   await expect(page.locator('text=LOW RISK')).toBeVisible();
  71  |   await capture(page, 'allowed_draft');
  72  | 
  73  |   // Check safety confirmation checkbox and approve/activate
  74  |   await page.click('#confirm-approval');
  75  |   await page.click('button:has-text("Approve & Activate")');
  76  |   await page.waitForTimeout(1000);
  77  | 
  78  |   // 5. Active Routine Details
  79  |   await expect(page.locator('text=Routine is currently active')).toBeVisible();
  80  |   await capture(page, 'active_details');
  81  | 
  82  |   // 6. View Audit Timeline
  83  |   await page.click('text=View Audit Timeline');
  84  |   await expect(page).toHaveURL(/\/caregiver\/audit/);
  85  |   await expect(page.locator('h1')).toContainText('System Audit Log');
  86  |   await capture(page, 'audit');
  87  | 
  88  |   // 7. Prohibited Draft Details
  89  |   await page.goto('/caregiver/routines/routine-4-rejected');
  90  |   await expect(page.locator('h1')).toContainText('Change medication');
  91  |   await expect(page.locator('text=PROHIBITED RISK')).toBeVisible();
  92  |   await expect(page.locator('text=Routine Blocked by Safety Policy')).toBeVisible();
  93  |   await capture(page, 'prohibited_details');
  94  | 
  95  |   // 8. Alerts view
  96  |   await page.goto('/caregiver/alerts');
  97  |   await expect(page.locator('h1')).toContainText('Caregiver Alerts');
  98  |   await capture(page, 'alerts');
  99  | });
  100 | 
  101 | 
```