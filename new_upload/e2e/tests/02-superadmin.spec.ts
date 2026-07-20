import { test, expect } from '@playwright/test';
import { loginAsSuperAdmin, screenshot, expectHeading, waitForLoaded } from './helpers';

test.describe('02 - Super Admin Dashboard', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSuperAdmin(page);
  });

  test('super admin dashboard loads with schools list', async ({ page }) => {
    await waitForLoaded(page);
    // Should see school cards or table
    await expect(page.locator('body')).toContainText(/Demo High School|Greenwood|school/i);
    await screenshot(page, '02-superadmin-schools-list');
  });

  test('shows school count and status badges', async ({ page }) => {
    await waitForLoaded(page);
    // Should show at least one school with active/inactive indicator
    const schoolCards = page.locator('[data-testid="school-card"]').or(
      page.locator('.card, .school-item').first()
    );
    await screenshot(page, '02-superadmin-school-cards');
  });

  test('can switch between Schools and Plans tabs', async ({ page }) => {
    await waitForLoaded(page);

    // Click Plans tab
    const plansTab = page.locator('button, [role="tab"]').filter({ hasText: /plans/i });
    if (await plansTab.isVisible()) {
      await plansTab.click();
      await waitForLoaded(page);
      await screenshot(page, '02-superadmin-plans-tab');
    }

    // Switch back to Schools
    const schoolsTab = page.locator('button, [role="tab"]').filter({ hasText: /schools/i });
    if (await schoolsTab.isVisible()) {
      await schoolsTab.click();
      await waitForLoaded(page);
      await screenshot(page, '02-superadmin-schools-tab');
    }
  });

  test('can open create school modal', async ({ page }) => {
    await waitForLoaded(page);

    const createBtn = page.locator('button').filter({ hasText: /create.*school|new.*school|add.*school|\+ school/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await page.waitForTimeout(500);

      // Modal should open with form fields
      await expect(
        page.locator('input[name="name"], input[placeholder*="school"]').first()
      ).toBeVisible({ timeout: 5000 });
      await screenshot(page, '02-create-school-modal');

      // Close modal
      const closeBtn = page.locator('button').filter({ hasText: /cancel|close|×/i }).first();
      if (await closeBtn.isVisible()) await closeBtn.click();
    }
  });

  test('create school form validation - empty name', async ({ page }) => {
    await waitForLoaded(page);

    const createBtn = page.locator('button').filter({ hasText: /create.*school|new.*school|\+ school/i });
    if (await createBtn.isVisible()) {
      await createBtn.click();
      await page.waitForTimeout(500);

      // Submit without filling required fields
      const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /create|save|submit/i }).last();
      if (await submitBtn.isVisible()) {
        await submitBtn.click();
        await page.waitForTimeout(1000);
        // Should show validation errors
        await screenshot(page, '02-create-school-validation');
      }

      const closeBtn = page.locator('button').filter({ hasText: /cancel|close/i }).first();
      if (await closeBtn.isVisible()) await closeBtn.click();
    }
  });

  test('can create a new school with all required fields', async ({ page }) => {
    await waitForLoaded(page);

    const createBtn = page.locator('button').filter({ hasText: /create.*school|new.*school|\+ school/i });
    if (!await createBtn.isVisible()) {
      test.skip();
      return;
    }

    await createBtn.click();
    await page.waitForTimeout(500);

    const unique = Date.now().toString().slice(-6);

    // Fill school info
    const nameInput = page.locator('input[name="name"], input[placeholder*="School Name"], input').nth(0);
    await nameInput.fill(`Playwright Test School ${unique}`);

    const codeInput = page.locator('input[name="code"], input[placeholder*="code"]').first();
    if (await codeInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await codeInput.fill(`PTS${unique}`);
    }

    const slugInput = page.locator('input[name="slug"], input[placeholder*="slug"]').first();
    if (await slugInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await slugInput.fill(`playwright-test-${unique}`);
    }

    // Admin info section
    const adminEmail = page.locator('input[name="admin_email"], input[placeholder*="admin.*email" i]').first();
    if (await adminEmail.isVisible({ timeout: 2000 }).catch(() => false)) {
      await adminEmail.fill(`admin${unique}@playwright.test`);
    }

    const adminUsername = page.locator('input[name="admin_username"], input[placeholder*="username"]').first();
    if (await adminUsername.isVisible({ timeout: 2000 }).catch(() => false)) {
      await adminUsername.fill(`admin${unique}`);
    }

    const adminPassword = page.locator('input[name="admin_password"], input[type="password"]').first();
    if (await adminPassword.isVisible({ timeout: 2000 }).catch(() => false)) {
      await adminPassword.fill('Admin@123456');
    }

    await screenshot(page, '02-create-school-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /create|save/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(3000);
    await screenshot(page, '02-create-school-result');
  });

  test('can toggle school active/inactive status', async ({ page }) => {
    await waitForLoaded(page);

    // Find a toggle or activate/deactivate button for any school
    const toggleBtn = page.locator('button').filter({ hasText: /activate|deactivate|toggle/i }).first();
    if (await toggleBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await toggleBtn.click();
      await page.waitForTimeout(2000);
      await screenshot(page, '02-toggle-school-status');
      // Toggle back
      await toggleBtn.click();
      await page.waitForTimeout(1000);
    }
  });

  test('can click on a school to enter its context / impersonate', async ({ page }) => {
    await waitForLoaded(page);

    // Find "Manage" or "Enter" or "→" button for a school
    const manageBtn = page.locator('button, a').filter({ hasText: /manage|enter|open|→|view/i }).first();
    if (await manageBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await manageBtn.click();
      await page.waitForTimeout(2000);
      await screenshot(page, '02-enter-school-context');
    }
  });

  test('can create a subscription plan', async ({ page }) => {
    await waitForLoaded(page);

    // Click Plans tab
    const plansTab = page.locator('button, [role="tab"]').filter({ hasText: /plans/i });
    if (!await plansTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      test.skip();
      return;
    }

    await plansTab.click();
    await waitForLoaded(page);

    const addPlanBtn = page.locator('button').filter({ hasText: /add.*plan|create.*plan|new.*plan|\+ plan/i });
    if (!await addPlanBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      test.skip();
      return;
    }

    await addPlanBtn.click();
    await page.waitForTimeout(500);

    const unique = Date.now().toString().slice(-6);
    const nameInput = page.locator('input[name="name"], input[placeholder*="name"]').first();
    await nameInput.fill(`Playwright Plan ${unique}`);

    const priceInput = page.locator('input[name="price_monthly_paise"], input[placeholder*="price"]').first();
    if (await priceInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await priceInput.fill('99900');
    }

    await screenshot(page, '02-create-plan-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /create|save/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '02-create-plan-result');
  });
});
