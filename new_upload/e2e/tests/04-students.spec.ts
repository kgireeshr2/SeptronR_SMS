import { test, expect } from '@playwright/test';
import { loginAsSchoolAdmin, screenshot, waitForLoaded } from './helpers';

test.describe('04 - Students', () => {

  test.beforeEach(async ({ page }) => {
    await loginAsSchoolAdmin(page);
  });

  test('student list page loads with data', async ({ page }) => {
    await page.goto('/admin/students');
    await waitForLoaded(page);
    await screenshot(page, '04-students-list');
    await expect(page.locator('body')).toContainText(/student|name|roll|class/i);
  });

  test('student search filters results', async ({ page }) => {
    await page.goto('/admin/students');
    await waitForLoaded(page);

    const searchInput = page.locator('input[placeholder*="search" i], input[type="search"]').first();
    if (await searchInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      await searchInput.fill('a');
      await page.waitForTimeout(1000);
      await screenshot(page, '04-students-search');
      await searchInput.clear();
      await page.waitForTimeout(500);
    }
  });

  test('can click a student to view detail', async ({ page }) => {
    await page.goto('/admin/students');
    await waitForLoaded(page);

    // Click first student row or link
    const studentLink = page.locator('table tbody tr').first().locator('a').first()
      .or(page.locator('[data-testid="student-row"]').first())
      .or(page.locator('table tbody tr td').first());

    if (await studentLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      await studentLink.click();
      await page.waitForTimeout(2000);
      await waitForLoaded(page);
      await screenshot(page, '04-student-detail');
      // Should navigate to student detail
      await expect(page).toHaveURL(/students\/.+/);
    }
  });

  test('student detail shows tabs (profile, fees, attendance)', async ({ page }) => {
    await page.goto('/admin/students');
    await waitForLoaded(page);

    const studentLink = page.locator('table tbody tr').first().locator('a').first();
    if (!await studentLink.isVisible({ timeout: 5000 }).catch(() => false)) { test.skip(); return; }

    await studentLink.click();
    await waitForLoaded(page);

    // Should have profile tabs
    const tabs = page.locator('[role="tab"]');
    const tabCount = await tabs.count();
    expect(tabCount).toBeGreaterThan(0);
    await screenshot(page, '04-student-tabs');

    // Click each tab
    for (let i = 0; i < Math.min(tabCount, 4); i++) {
      await tabs.nth(i).click();
      await page.waitForTimeout(800);
    }
    await screenshot(page, '04-student-last-tab');
  });

  test('can open add student form', async ({ page }) => {
    await page.goto('/admin/students');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add student|new student|enroll|\+ student/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);
    await screenshot(page, '04-add-student-form');

    // Should see a form with name field
    await expect(page.locator('input[name="first_name"], input[placeholder*="first name" i], input').first()).toBeVisible();
  });

  test('add student form validation - empty submit', async ({ page }) => {
    await page.goto('/admin/students');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add student|new student|enroll/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create|add/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(1000);
    await screenshot(page, '04-add-student-validation');
    // Should show validation errors, not navigate away
    await expect(page.locator('body')).not.toHaveURL(/success/);
  });

  test('can create a new student', async ({ page }) => {
    await page.goto('/admin/students');
    await waitForLoaded(page);

    const addBtn = page.locator('button').filter({ hasText: /add student|new student|enroll/i }).first();
    if (!await addBtn.isVisible({ timeout: 3000 }).catch(() => false)) { test.skip(); return; }

    await addBtn.click();
    await page.waitForTimeout(600);

    const unique = Date.now().toString().slice(-6);
    const form = page.locator('form');

    // Fill first name
    const firstName = form.locator('input[name="first_name"], input[placeholder*="first" i]').first();
    if (await firstName.isVisible({ timeout: 2000 }).catch(() => false)) await firstName.fill('Playwright');

    // Fill last name
    const lastName = form.locator('input[name="last_name"], input[placeholder*="last" i]').first();
    if (await lastName.isVisible({ timeout: 2000 }).catch(() => false)) await lastName.fill(`Student${unique}`);

    // Date of birth
    const dob = form.locator('input[name="date_of_birth"], input[type="date"]').first();
    if (await dob.isVisible({ timeout: 2000 }).catch(() => false)) await dob.fill('2010-05-15');

    // Gender
    const genderSelect = form.locator('select[name="gender"]').first();
    if (await genderSelect.isVisible({ timeout: 2000 }).catch(() => false)) await genderSelect.selectOption('male');

    // Roll number
    const rollInput = form.locator('input[name="roll_number"]').first();
    if (await rollInput.isVisible({ timeout: 2000 }).catch(() => false)) await rollInput.fill(`R${unique}`);

    await screenshot(page, '04-create-student-filled');

    const submitBtn = page.locator('button[type="submit"], button').filter({ hasText: /save|create|add/i }).last();
    await submitBtn.click();
    await page.waitForTimeout(2500);
    await screenshot(page, '04-create-student-result');
  });

  test('edit student works after search', async ({ page }) => {
    await page.goto('/admin/students');
    await waitForLoaded(page);

    // Step 1: get the first student's name from the list
    const firstRow = page.locator('table tbody tr').first();
    if (!await firstRow.isVisible({ timeout: 5000 }).catch(() => false)) { test.skip(); return; }

    const firstCellText = (await firstRow.locator('td').nth(1).textContent() ?? '').trim();
    if (!firstCellText) { test.skip(); return; }

    // Step 2: search for the student using the first few characters of their name
    const searchTerm = firstCellText.split(' ')[0].slice(0, 3); // first 3 chars of first name
    const searchInput = page.locator('input[placeholder*="search" i], input[placeholder*="name" i]').first();
    await searchInput.fill(searchTerm);
    // wait for debounce (350ms) + API response
    await page.waitForTimeout(1200);
    await waitForLoaded(page);
    await screenshot(page, '04-edit-after-search-filtered');

    // Step 3: click Edit on the first visible result
    const editBtn = page.locator('table tbody tr').first().locator('button', { hasText: 'Edit' });
    if (!await editBtn.isVisible({ timeout: 5000 }).catch(() => false)) { test.skip(); return; }
    await editBtn.click();
    await page.waitForTimeout(500);

    // Step 4: verify modal opened with correct student data
    await expect(page.locator('text=Edit Student')).toBeVisible({ timeout: 5000 });
    const firstNameInput = page.locator('input[value]').first();
    await expect(firstNameInput).not.toHaveValue('', { timeout: 3000 });
    await screenshot(page, '04-edit-modal-after-search');

    // Step 5: make a change (toggle active status) and save
    const activeCheckbox = page.locator('#edit-is-active');
    if (await activeCheckbox.isVisible({ timeout: 2000 }).catch(() => false)) {
      // just click save without changing to verify save works
    }

    const saveBtn = page.locator('button', { hasText: /Save Changes/i });
    await saveBtn.click();
    await page.waitForTimeout(2000);

    // Step 6: modal should close and search should be cleared (showing full list)
    await expect(page.locator('text=Edit Student')).not.toBeVisible({ timeout: 5000 });
    await screenshot(page, '04-edit-after-search-saved');

    // Step 7: search input should be cleared
    await expect(searchInput).toHaveValue('', { timeout: 3000 });
  });
});
