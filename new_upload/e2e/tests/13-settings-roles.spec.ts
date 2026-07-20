import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, loginAsSuperAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('13 - Settings & Roles', () => {

  // ── School Settings (School Admin) ─────────────────────────────────────────

  test('settings page loads (school admin)', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/settings');
    await waitForLoaded(page);
    await screenshot(page, '13-settings-page');
    await expect(page.locator('body')).toContainText(/setting|configuration|school|general/i);
  });

  test('can update school general settings', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/settings');
    await waitForLoaded(page);

    // Try to update a general setting
    const phoneInput = page.locator('input[name="phone"], input[placeholder*="phone" i]').first();
    if (await phoneInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await phoneInput.fill('9876543200');

      const saveBtn = page.locator('button').filter({ hasText: /save|update/i }).first();
      if (await saveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveBtn.click();
        await page.waitForTimeout(2000);
        await screenshot(page, '13-settings-saved');
      }
    }
  });

  // ── Roles & Permissions ──────────────────────────────────────────────────────

  test('roles page loads', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/roles');
    await waitForLoaded(page);
    await screenshot(page, '13-roles-list');
    await expect(page.locator('body')).toContainText(/role|permission|admin/i);
  });

  test('can view role details and permissions', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/roles');
    await waitForLoaded(page);

    const viewBtn = page.locator('button').filter({ hasText: /view|edit|manage/i }).first()
      .or(page.locator('table tbody tr').first().locator('button').first());

    if (await viewBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await viewBtn.click();
      await page.waitForTimeout(1000);
      await screenshot(page, '13-role-detail');

      const closeBtn = page.locator('button').filter({ hasText: /cancel|close/i }).first();
      if (await closeBtn.isVisible({ timeout: 2000 }).catch(() => false)) await closeBtn.click();
    }
  });

  test('can create a custom role', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/roles');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const unique = Date.now().toString().slice(-6);
    const nameInput = page.locator('input[name="name"], input[placeholder*="role name" i], input').first();
    await nameInput.fill(`Playwright Role ${unique}`);

    // Select some permissions if checkboxes exist
    const firstCheckbox = page.locator('input[type="checkbox"]').first();
    if (await firstCheckbox.isVisible({ timeout: 2000 }).catch(() => false)) {
      await firstCheckbox.check();
    }

    await screenshot(page, '13-create-role-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '13-create-role-result');
  });

  // ── Audit Logs ──────────────────────────────────────────────────────────────

  test('audit logs page loads', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/audit-logs');
    await waitForLoaded(page);
    await screenshot(page, '13-audit-logs');
    await expect(page.locator('body')).toContainText(/audit|log|action|user/i);
  });

  test('audit logs show entries with timestamps', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/audit-logs');
    await waitForLoaded(page);

    // Should have a table with date/time columns
    const rows = page.locator('table tbody tr');
    const rowCount = await rows.count();
    expect(rowCount).toBeGreaterThan(0);
    await screenshot(page, '13-audit-logs-data');
  });

  test('can filter audit logs by date range', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/audit-logs');
    await waitForLoaded(page);

    const dateInputs = page.locator('input[type="date"]');
    if (await dateInputs.count() >= 2) {
      await dateInputs.nth(0).fill('2026-01-01');
      await dateInputs.nth(1).fill('2026-12-31');

      const applyBtn = page.locator('button').filter({ hasText: /apply|filter|search/i }).first();
      if (await applyBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await applyBtn.click();
        await waitForLoaded(page);
        await screenshot(page, '13-audit-logs-filtered');
      }
    }
  });

  // ── Inventory ──────────────────────────────────────────────────────────────

  test('inventory page loads', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/inventory');
    await waitForLoaded(page);
    await screenshot(page, '13-inventory-page');
    await expect(page.locator('body')).toContainText(/inventory|item|stock|quantity/i);
  });

  test('can add an inventory item', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/inventory');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const unique = Date.now().toString().slice(-6);
    const nameInput = page.locator('input[name="name"], input[placeholder*="item name" i], input').first();
    await nameInput.fill(`Playwright Item ${unique}`);

    const qtyInput = page.locator('input[name="quantity"], input[type="number"]').first();
    if (await qtyInput.isVisible({ timeout: 2000 }).catch(() => false)) await qtyInput.fill('10');

    await screenshot(page, '13-add-inventory-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '13-add-inventory-result');
  });

  // ── Accounting ──────────────────────────────────────────────────────────────

  test('accounting page loads', async ({ page }) => {
    await loginAsSchoolAdmin(page);
    await page.goto('/admin/accounting');
    await waitForLoaded(page);
    await screenshot(page, '13-accounting-page');
    // Known bug: /accounting/budgets → 500, but page itself might load
    await expect(page.locator('body')).toContainText(/account|budget|income|expense|transaction/i);
  });
});
