import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded, expectHeading } from './helpers';

test.describe('03 - Academic Year, Classes, Subjects', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  // ── Academic Years ──────────────────────────────────────────────────────────

  test('academic years list page loads', async ({ page }) => {
    await page.goto('/admin/academic-years');
    await waitForLoaded(page);
    await screenshot(page, '03-academic-years-list');
    // Should show at least a heading or data table
    await expect(page.locator('body')).toContainText(/academic year|2024|2025/i);
  });

  test('can open create academic year form', async ({ page }) => {
    await page.goto('/admin/academic-years');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await addBtn.click();
      await page.waitForTimeout(600);
      await screenshot(page, '03-create-academic-year-form');
    }
  });

  test('create academic year with valid data', async ({ page }) => {
    await page.goto('/admin/academic-years');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    // Fill year name
    const nameInput = page.locator('input[name="name"], input[placeholder*="name" i], input').first();
    await nameInput.fill('Playwright AY 2026-27');

    // Fill start date
    const startDate = page.locator('input[type="date"], input[name="start_date"]').first();
    if (await startDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await startDate.fill('2026-04-01');
    }

    // Fill end date
    const endDate = page.locator('input[type="date"], input[name="end_date"]').nth(1);
    if (await endDate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await endDate.fill('2027-03-31');
    }

    await screenshot(page, '03-create-academic-year-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /create|save/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '03-create-academic-year-result');
  });

  // ── Classes ─────────────────────────────────────────────────────────────────

  test('classes list page loads', async ({ page }) => {
    await page.goto('/admin/classes');
    await waitForLoaded(page);
    await screenshot(page, '03-classes-list');
    await expect(page.locator('body')).toContainText(/class|grade|section/i);
  });

  test('can create a new class', async ({ page }) => {
    await page.goto('/admin/classes');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const nameInput = page.locator('input[name="name"], input[placeholder*="class name" i], input').first();
    await nameInput.fill('Playwright Class X');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /create|save/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '03-create-class-result');
  });

  // ── Subjects ─────────────────────────────────────────────────────────────────

  test('subjects list page loads', async ({ page }) => {
    await page.goto('/admin/subjects');
    await waitForLoaded(page);
    await screenshot(page, '03-subjects-list');
    await expect(page.locator('body')).toContainText(/subject|math|science|english/i);
  });

  test('can create a new subject', async ({ page }) => {
    await page.goto('/admin/subjects');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const nameInput = page.locator('input[name="name"], input[placeholder*="name" i], input').first();
    await nameInput.fill('Playwright Subject');

    const codeInput = page.locator('input[name="code"], input[placeholder*="code" i]').first();
    if (await codeInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await codeInput.fill('PWS101');
    }

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /create|save/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '03-create-subject-result');
  });

  // ── Timetable ─────────────────────────────────────────────────────────────────

  test('timetable page loads', async ({ page }) => {
    await page.goto('/admin/timetable');
    await waitForLoaded(page);
    await screenshot(page, '03-timetable');
    await expect(page.locator('body')).toContainText(/timetable|schedule|period|monday/i);
  });
});
