import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('05 - Staff Management', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('staff list page loads with data', async ({ page }) => {
    await page.goto('/admin/staff');
    await waitForLoaded(page);
    await screenshot(page, '05-staff-list');
    await expect(page.locator('body')).toContainText(/staff|teacher|employee/i);
  });

  test('can view staff member detail page', async ({ page }) => {
    await page.goto('/admin/staff');
    await waitForLoaded(page);

    const staffLink = page.locator('table tbody tr').first().locator('a').first()
      .or(page.locator('[data-testid="staff-row"]').first());

    if (await staffLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await staffLink.click();
      await waitForLoaded(page);
      await screenshot(page, '05-staff-detail');
    }
  });

  test('can navigate to add new staff form', async ({ page }) => {
    await page.goto('/admin/staff/new');
    await waitForLoaded(page);
    await screenshot(page, '05-add-staff-form');
    await expect(page.locator('input, form').first()).toBeVisible();
  });

  test('add staff form validation - empty submit', async ({ page }) => {
    await page.goto('/admin/staff/new');
    await waitForLoaded(page);

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create|add|submit/i }).last();
    if (await submitBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await submitBtn.click();
      await page.waitForTimeout(1000);
      await screenshot(page, '05-add-staff-validation');
    }
  });

  test('can create a new staff member', async ({ page }) => {
    await page.goto('/admin/staff/new');
    await waitForLoaded(page);

    const unique = Date.now().toString().slice(-6);
    const form = page.locator('form').first();

    const firstName = form.locator('input[name="first_name"], input[placeholder*="first" i]').first();
    if (await firstName.isVisible({ timeout: 2000 }).catch(() => false)) await firstName.fill('Playwright');

    const lastName = form.locator('input[name="last_name"], input[placeholder*="last" i]').first();
    if (await lastName.isVisible({ timeout: 2000 }).catch(() => false)) await lastName.fill(`Teacher${unique}`);

    const email = form.locator('input[type="email"], input[name="email"]').first();
    if (await email.isVisible({ timeout: 2000 }).catch(() => false)) await email.fill(`teacher${unique}@playwright.test`);

    const empId = form.locator('input[name="employee_id"]').first();
    if (await empId.isVisible({ timeout: 2000 }).catch(() => false)) await empId.fill(`EMP${unique}`);

    const phone = form.locator('input[name="phone"], input[placeholder*="phone" i]').first();
    if (await phone.isVisible({ timeout: 2000 }).catch(() => false)) await phone.fill(`98765${unique}`);

    await screenshot(page, '05-create-staff-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create|add/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2500);
    await screenshot(page, '05-create-staff-result');
  });

  test('departments page loads', async ({ page }) => {
    await page.goto('/admin/staff/departments');
    await waitForLoaded(page);
    await screenshot(page, '05-departments-list');
    await expect(page.locator('body')).toContainText(/department/i);
  });

  test('can create a department', async ({ page }) => {
    await page.goto('/admin/staff/departments');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(500);

    const nameInput = page.locator('input[name="name"], input[placeholder*="name" i]').first();
    await nameInput.fill(`Playwright Dept ${Date.now().toString().slice(-6)}`);

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '05-department-created');
  });
});
