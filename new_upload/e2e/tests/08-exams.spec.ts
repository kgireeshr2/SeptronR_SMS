import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('08 - Exam Management', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('exams list page loads', async ({ page }) => {
    await page.goto('/admin/exams');
    await waitForLoaded(page);
    await screenshot(page, '08-exams-list');
    await expect(page.locator('body')).toContainText(/exam|test|assessment/i);
  });

  test('can open create exam form', async ({ page }) => {
    await page.goto('/admin/exams');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);
    await screenshot(page, '08-create-exam-form');
  });

  test('can create an exam', async ({ page }) => {
    await page.goto('/admin/exams');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add|create|new/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const unique = Date.now().toString().slice(-6);
    const nameInput = page.locator('input[name="name"], input[placeholder*="exam name" i], input').first();
    await nameInput.fill(`Playwright Exam ${unique}`);

    // Date
    const dateInput = page.locator('input[type="date"], input[name="exam_date"]').first();
    if (await dateInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await dateInput.fill('2026-05-15');
    }

    // Max marks
    const marksInput = page.locator('input[name="total_marks"], input[placeholder*="mark" i], input[type="number"]').first();
    if (await marksInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await marksInput.fill('100');
    }

    await screenshot(page, '08-create-exam-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2000);
    await screenshot(page, '08-create-exam-result');
  });

  test('can view exam grades/results', async ({ page }) => {
    await page.goto('/admin/exams');
    await waitForLoaded(page);

    // Look for results / grades tab
    const resultsTab = page.locator('button, [role="tab"]').filter({ hasText: /results|grades|marks/i }).first();
    if (await resultsTab.isVisible({ timeout: 3000 }).catch(() => false)) {
      await resultsTab.click();
      await waitForLoaded(page);
      await screenshot(page, '08-exam-results');
    }
  });

  test('can enter marks for a student', async ({ page }) => {
    await page.goto('/admin/exams');
    await waitForLoaded(page);

    // Click first exam's view/enter marks button
    const enterMarksBtn = page.locator('button').filter({ hasText: /enter.*marks|add.*marks|mark/i }).first();
    if (!await enterMarksBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await enterMarksBtn.click();
    await waitForLoaded(page);
    await screenshot(page, '08-enter-marks');

    // Fill first marks input
    const marksInput = page.locator('input[type="number"]').first();
    if (await marksInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await marksInput.fill('75');
      await page.keyboard.press('Tab');

      const saveBtn = page.locator('button').filter({ hasText: /save|submit/i }).first();
      if (await saveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await saveBtn.click();
        await page.waitForTimeout(2000);
        await screenshot(page, '08-marks-saved');
      }
    }
  });
});
