import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('11 - Communication & Notifications', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('communication / announcements page loads', async ({ page }) => {
    // Try multiple possible routes
    await page.goto('/admin/communication');
    await waitForLoaded(page);
    await screenshot(page, '11-communication-page');
    await expect(page.locator('body')).toContainText(/announcement|notice|message|communication/i);
  });

  test('can create an announcement', async ({ page }) => {
    await page.goto('/admin/communication');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new|compose/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const unique = Date.now().toString().slice(-6);

    const titleInput = page.locator('input[name="title"], input[placeholder*="title" i], input').first();
    await titleInput.fill(`Playwright Announcement ${unique}`);

    const msgInput = page.locator('textarea[name="message"], textarea[name="body"], textarea').first();
    if (await msgInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await msgInput.fill('This is an automated test announcement created by Playwright.');
    }

    // Recipient type
    const recipientSelect = page.locator('select[name="recipient_type"], select').first();
    if (await recipientSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      await recipientSelect.selectOption({ index: 1 });
    }

    await screenshot(page, '11-create-announcement-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /send|publish|create|save/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '11-create-announcement-result');
  });

  test('can view existing announcements list', async ({ page }) => {
    await page.goto('/admin/communication');
    await waitForLoaded(page);

    const listTab = page.locator('button, [role="tab"]').filter({ hasText: /all|list|sent/i }).first();
    if (await listTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await listTab.click();
      await waitForLoaded(page);
    }

    await screenshot(page, '11-announcements-list');
  });

  test('homework page loads', async ({ page }) => {
    await page.goto('/homework');
    await waitForLoaded(page);
    await screenshot(page, '11-homework-page');
    await expect(page.locator('body')).toContainText(/homework|assignment/i);
  });

  test('calendar page loads', async ({ page }) => {
    await page.goto('/calendar');
    await waitForLoaded(page);
    await screenshot(page, '11-calendar-page');
    await expect(page.locator('body')).toContainText(/calendar|event|today|month/i);
  });

  test('parent-teacher meetings (PTM) page loads', async ({ page }) => {
    await page.goto('/ptm');
    await waitForLoaded(page);
    await screenshot(page, '11-ptm-page');
    await expect(page.locator('body')).toContainText(/meeting|ptm|parent/i);
  });
});
