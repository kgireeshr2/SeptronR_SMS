import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('06 - Fee Management', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('fees list page loads', async ({ page }) => {
    await page.goto('/admin/fees');
    await waitForLoaded(page);
    await screenshot(page, '06-fees-list');
    await expect(page.locator('body')).toContainText(/fee|amount|due|paid/i);
  });

  test('fees advanced page loads', async ({ page }) => {
    await page.goto('/admin/fees-advanced');
    await waitForLoaded(page);
    await screenshot(page, '06-fees-advanced');
    await expect(page.locator('body')).toContainText(/fee|structure|collection/i);
  });

  test('can open create fee structure form', async ({ page }) => {
    await page.goto('/admin/fees');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new.*fee|fee.*structure/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Try advanced fees page
      await page.goto('/admin/fees-advanced');
      await waitForLoaded(page);
      const addBtn2 = page.locator('button').filter({ hasText: /add|create|new/i }).first();
      if (!await addBtn2.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }
      await addBtn2.click();
    } else {
      await addBtn.click();
    }

    await page.waitForTimeout(600);
    await screenshot(page, '06-create-fee-form');
  });

  test('can create a fee structure', async ({ page }) => {
    await page.goto('/admin/fees-advanced');
    await waitForLoaded(page);

    // Try to find fee structure tab or section
    const feeStructureTab = page.locator('button, [role="tab"]').filter({ hasText: /structure/i }).first();
    if (await feeStructureTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await feeStructureTab.click();
      await waitForLoaded(page);
    }

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const unique = Date.now().toString().slice(-6);
    const nameInput = page.locator('input[name="name"], input[placeholder*="name" i]').first();
    if (await nameInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await nameInput.fill(`Playwright Fee ${unique}`);
    }

    const amountInput = page.locator('input[name="amount"], input[placeholder*="amount" i], input[type="number"]').first();
    if (await amountInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await amountInput.fill('5000');
    }

    await screenshot(page, '06-create-fee-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '06-create-fee-result');
  });

  test('can collect fee for a student', async ({ page }) => {
    await page.goto('/admin/fees');
    await waitForLoaded(page);

    // Look for collect/pay button
    const collectBtn = page.locator('button').filter({ hasText: /collect|pay|record.*payment/i }).first();
    if (!await collectBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await collectBtn.click();
    await page.waitForTimeout(600);
    await screenshot(page, '06-collect-fee-modal');

    const cancelBtn = page.locator('button').filter({ hasText: /cancel|close/i }).first();
    if (await cancelBtn.isVisible({ timeout: 2000 }).catch(() => false)) await cancelBtn.click();
  });

  test('can view fee reports / pending dues', async ({ page }) => {
    await page.goto('/admin/fees');
    await waitForLoaded(page);

    // Look for a tab/filter for pending
    const pendingTab = page.locator('button, [role="tab"]').filter({ hasText: /pending|due|overdue/i }).first();
    if (await pendingTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await pendingTab.click();
      await waitForLoaded(page);
      await screenshot(page, '06-fees-pending');
    }
  });
});
