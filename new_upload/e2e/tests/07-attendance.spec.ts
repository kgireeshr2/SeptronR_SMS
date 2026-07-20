import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('07 - Attendance', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('attendance page loads', async ({ page }) => {
    await page.goto('/admin/attendance');
    await waitForLoaded(page);
    await screenshot(page, '07-attendance-page');
    await expect(page.locator('body')).toContainText(/attendance|present|absent|class/i);
  });

  test('can select a class and section for attendance', async ({ page }) => {
    await page.goto('/admin/attendance');
    await waitForLoaded(page);

    // Try to select class from dropdown
    const classSelect = page.locator('select[name="class_id"], select').first();
    if (await classSelect.isVisible({ timeout: 3000 }).catch(() => false)) {
      const options = await classSelect.locator('option').count();
      if (options > 1) {
        await classSelect.selectOption({ index: 1 });
        await page.waitForTimeout(1000);
        await screenshot(page, '07-attendance-class-selected');
      }
    }

    // Try section
    const sectionSelect = page.locator('select[name="section_id"], select').nth(1);
    if (await sectionSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      const opts = await sectionSelect.locator('option').count();
      if (opts > 1) {
        await sectionSelect.selectOption({ index: 1 });
        await page.waitForTimeout(1000);
      }
    }

    await screenshot(page, '07-attendance-section-selected');
  });

  test('can mark attendance for students', async ({ page }) => {
    await page.goto('/admin/attendance');
    await waitForLoaded(page);

    // Select date if date input exists
    const dateInput = page.locator('input[type="date"]').first();
    if (await dateInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      const today = new Date().toISOString().split('T')[0];
      await dateInput.fill(today);
    }

    // Select class
    const classSelect = page.locator('select[name="class_id"], select').first();
    if (await classSelect.isVisible({ timeout: 2000 }).catch(() => false)) {
      const opts = await classSelect.locator('option').count();
      if (opts > 1) await classSelect.selectOption({ index: 1 });
    }

    await waitForLoaded(page);

    // Mark first student as present
    const presentBtn = page.locator('button').filter({ hasText: /present|P/i }).first();
    if (await presentBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await presentBtn.click();
      await page.waitForTimeout(500);
    }

    // Mark first student as absent
    const absentBtn = page.locator('button').filter({ hasText: /absent|A/i }).first();
    if (await absentBtn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await absentBtn.click();
      await page.waitForTimeout(500);
    }

    await screenshot(page, '07-mark-attendance');

    // Submit
    const saveBtn = page.locator('button').filter({ hasText: /save|submit/i }).first();
    if (await saveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await saveBtn.click();
      await page.waitForTimeout(2000);
      await screenshot(page, '07-attendance-submitted');
    }
  });

  test('attendance report / summary view', async ({ page }) => {
    await page.goto('/admin/attendance');
    await waitForLoaded(page);

    const reportTab = page.locator('button, [role="tab"]').filter({ hasText: /report|summary|history/i }).first();
    if (await reportTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await reportTab.click();
      await waitForLoaded(page);
      await screenshot(page, '07-attendance-report');
    }
  });
});
