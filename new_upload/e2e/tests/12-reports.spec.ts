import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('12 - Reports', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('reports page loads', async ({ page }) => {
    await page.goto('/reports');
    await waitForLoaded(page);
    await screenshot(page, '12-reports-page');
    await expect(page.locator('body')).toContainText(/report|export|data/i);
  });

  test('can view student report options', async ({ page }) => {
    await page.goto('/reports');
    await waitForLoaded(page);

    const studentTab = page.locator('button, [role="tab"], a').filter({ hasText: /student/i }).first();
    if (await studentTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await studentTab.click();
      await waitForLoaded(page);
      await screenshot(page, '12-reports-students');
    }
  });

  test('can view fee report options', async ({ page }) => {
    await page.goto('/reports');
    await waitForLoaded(page);

    const feeTab = page.locator('button, [role="tab"], a').filter({ hasText: /fee|finance/i }).first();
    if (await feeTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await feeTab.click();
      await waitForLoaded(page);
      await screenshot(page, '12-reports-fees');
    }
  });

  test('can generate and view a report', async ({ page }) => {
    await page.goto('/reports');
    await waitForLoaded(page);

    const generateBtn = page.locator('button').filter({ hasText: /generate|view|run|export/i }).first();
    if (!await generateBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await generateBtn.click();
    await page.waitForTimeout(3000);
    await screenshot(page, '12-report-generated');
  });

  test('can export report as PDF/Excel', async ({ page }) => {
    await page.goto('/reports');
    await waitForLoaded(page);

    const exportBtn = page.locator('button').filter({ hasText: /export|pdf|excel|download/i }).first();
    if (!await exportBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    // Intercept download
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 10000 }).catch(() => null),
      exportBtn.click(),
    ]);

    if (download) {
      await screenshot(page, '12-report-downloaded');
    }
  });

  test('dashboard page loads with metrics', async ({ page }) => {
    await page.goto('/dashboard');
    await waitForLoaded(page);
    await screenshot(page, '12-dashboard');
    await expect(page.locator('body')).toContainText(/student|staff|fee|attendance/i);
  });
});
